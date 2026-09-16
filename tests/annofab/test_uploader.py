import logging
import traceback
from datetime import datetime, timedelta, timezone
from email.utils import format_datetime
from http import HTTPStatus
from pathlib import Path
from unittest.mock import Mock

import pytest
import requests

from anno3d.annofab import uploader
from anno3d.annofab.uploader import (
    AnnofabStorageUploader,
    HttpUploadRequestError,
    S3RequestTimeoutUploadRequestError,
    UploadRequestError,
    _get_retry_after_seconds,
    _is_retryable_upload_error,
    _parse_retry_after_seconds,
    _to_upload_request_error,
    _wait_upload_retry,
)


def _http_error(status_code: int, retry_after: str) -> requests.exceptions.HTTPError:
    response = requests.Response()
    response.status_code = status_code
    response.headers["Retry-After"] = retry_after
    return requests.exceptions.HTTPError(response=response)


def _http_error_with_body(status_code: int, body: bytes) -> requests.exceptions.HTTPError:
    response = requests.Response()
    response.status_code = status_code
    response._content = body
    return requests.exceptions.HTTPError(response=response)


def test_get_retry_after_seconds_秒数形式():
    error = _to_upload_request_error(_http_error(429, "60"))

    assert _get_retry_after_seconds(error) == 60.0


def test_get_retry_after_seconds_http_date形式():
    now = datetime(2026, 9, 16, 0, 0, 0, tzinfo=timezone.utc)
    retry_at = now + timedelta(seconds=60)

    assert _parse_retry_after_seconds(format_datetime(retry_at, usegmt=True), now=now) == 60.0


def test_get_retry_after_seconds_上限値は有効():
    assert _parse_retry_after_seconds("60") == 60.0


@pytest.mark.parametrize("retry_after", [float("inf"), -1.0, 61.0])
def test_http_upload_request_errorの範囲外_retry_afterは_noneになる(retry_after: float):
    assert HttpUploadRequestError(429, retry_after).retry_after_seconds is None


@pytest.mark.parametrize("retry_after", ["61", "9" * 400])
def test_get_retry_after_seconds_秒数形式の上限超過は_noneを返す(retry_after: str):
    assert _parse_retry_after_seconds(retry_after) is None


def test_get_retry_after_seconds_http_date形式の上限超過は_noneを返す():
    now = datetime(2026, 9, 16, 0, 0, 0, tzinfo=timezone.utc)
    retry_at = now + timedelta(seconds=61)

    assert _parse_retry_after_seconds(format_datetime(retry_at, usegmt=True), now=now) is None


def test_get_retry_after_seconds_遠い将来のhttp_date形式は_noneを返す():
    now = datetime(2026, 9, 16, 0, 0, 0, tzinfo=timezone.utc)
    retry_at = datetime(9999, 12, 31, 23, 59, 59, tzinfo=timezone.utc)

    assert _parse_retry_after_seconds(format_datetime(retry_at, usegmt=True), now=now) is None


@pytest.mark.parametrize("retry_after", ["-1", "120.5", "invalid date", "Sun, 32 Jan 9999999999 00:00:00 GMT"])
def test_get_retry_after_seconds_不正値は_noneを返す(retry_after: str):
    error = _to_upload_request_error(_http_error(429, retry_after))

    assert _get_retry_after_seconds(error) is None


def test_wait_upload_retry_retry_afterを指数バックオフの下限にする():
    retry_state = Mock()
    retry_state.attempt_number = 1
    retry_state.outcome.exception.return_value = _to_upload_request_error(_http_error(429, "60"))

    assert _wait_upload_retry(retry_state) == 60.0


def test_is_retryable_upload_error_s3_request_timeoutは再試行する():
    error = _http_error_with_body(
        400,
        b"""<?xml version="1.0" encoding="UTF-8"?>
        <Error>
            <Code>RequestTimeout</Code>
        </Error>""",
    )

    upload_error = _to_upload_request_error(error)

    assert isinstance(upload_error, S3RequestTimeoutUploadRequestError)
    assert upload_error.status_code == 400
    assert _is_retryable_upload_error(upload_error) is True


def test_s3_request_timeoutのステータスコードは400に固定される():
    error = S3RequestTimeoutUploadRequestError(None)

    assert error.status_code == HTTPStatus.BAD_REQUEST
    assert error.retryable is True


def test_httpエラーの再試行可否はステータスコードから導出される():
    assert HttpUploadRequestError(503, None).retryable is True
    assert HttpUploadRequestError(400, None).retryable is False


def test_is_retryable_upload_error_s3の他の400は再試行しない():
    error = _http_error_with_body(400, b"<Error><Code>AccessDenied</Code></Error>")

    assert _is_retryable_upload_error(_to_upload_request_error(error)) is False


@pytest.mark.parametrize("s3_error_code", ["AccessDenied", "RequestExpired"])
def test_upload_request_errorはs3エラーコードを保持する(s3_error_code: str):
    error = _http_error_with_body(HTTPStatus.FORBIDDEN, f"<Error><Code>{s3_error_code}</Code></Error>".encode())
    error.response.reason = "Forbidden"

    upload_error = _to_upload_request_error(error)

    assert f"error=HTTPError, reason=Forbidden, s3_error_code={s3_error_code}" in str(upload_error)


def test_upload_request_errorは接続リセットの例外クラス名を保持する():
    upload_error = _to_upload_request_error(requests.exceptions.ConnectionError(ConnectionResetError()))

    assert "error=ConnectionError, error=ConnectionResetError" in str(upload_error)


def test_upload_request_errorはurlを含むhttp_reasonを保持しない():
    signed_url = "https://example.com/upload?X-Amz-Credential=credential&X-Amz-Signature=signature"
    error = _http_error_with_body(HTTPStatus.FORBIDDEN, b"<Error><Code>AccessDenied</Code></Error>")
    error.response.reason = signed_url

    upload_error = _to_upload_request_error(error)

    assert "s3_error_code=AccessDenied" in str(upload_error)
    assert signed_url not in str(upload_error)


@pytest.mark.parametrize("request_exception", [requests.exceptions.ConnectionError, requests.exceptions.ReadTimeout])
def test_upload_tempdata_一時的なput失敗後に先頭から再試行して成功する(
    request_exception: type[requests.exceptions.RequestException], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    upload_file = tmp_path / "data.bin"
    upload_file.write_bytes(b"upload data")
    client = Mock()
    client.create_temp_path.return_value = (
        {"url": "https://example.com/upload", "path": "s3://temporary/data.bin"},
        None,
    )
    sent_bodies: list[bytes] = []
    successful_response = Mock()

    def put(*args, **kwargs):
        sent_bodies.append(kwargs["data"].read())
        if len(sent_bodies) < 3:
            raise request_exception()
        return successful_response

    requests_put = Mock(side_effect=put)
    monkeypatch.setattr(uploader.requests, "put", requests_put)
    monkeypatch.setattr(uploader, "_wait_upload_retry", lambda _: 0)

    result = AnnofabStorageUploader(client, project="project-id").upload_tempdata(upload_file)

    assert result == "s3://temporary/data.bin"
    client.create_temp_path.assert_called_once_with("project-id")
    assert requests_put.call_count == 3
    assert sent_bodies == [b"upload data", b"upload data", b"upload data"]
    successful_response.raise_for_status.assert_called_once_with()


def test_upload_tempdata_署名付きurlを再試行ログと最終例外へ出力しない(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
):
    upload_file = tmp_path / "data.bin"
    upload_file.write_bytes(b"upload data")
    signed_url = "https://example.com/upload?X-Amz-Credential=credential&X-Amz-Signature=signature"
    client = Mock()
    client.create_temp_path.return_value = ({"url": signed_url, "path": "s3://temporary/data.bin"}, None)
    response = requests.Response()
    response.status_code = 503
    response.url = signed_url

    monkeypatch.setattr(uploader.requests, "put", Mock(return_value=response))
    monkeypatch.setattr(uploader, "_wait_upload_retry", lambda _: 0)

    with caplog.at_level(logging.WARNING, logger="anno3d.annofab.uploader"):
        with pytest.raises(UploadRequestError) as exc_info:
            AnnofabStorageUploader(client, project="project-id").upload_tempdata(upload_file)

    rendered_traceback = "".join(traceback.format_exception(exc_info.type, exc_info.value, exc_info.tb))
    assert "X-Amz-Credential" not in caplog.text
    assert "X-Amz-Signature" not in caplog.text
    assert "X-Amz-Credential" not in rendered_traceback
    assert "X-Amz-Signature" not in rendered_traceback
    assert len(caplog.records) == 4
    assert all(
        record.getMessage()
        == "Retrying temporary storage upload: file=data.bin, status=503, type=http, attempt=" + str(i)
        for i, record in enumerate(caplog.records, start=1)
    )


def test_upload_tempdata_不正な_retry_afterでも署名付きurlを最終例外へ出力しない(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
):
    upload_file = tmp_path / "data.bin"
    upload_file.write_bytes(b"upload data")
    signed_url = "https://example.com/upload?X-Amz-Credential=credential&X-Amz-Signature=signature"
    client = Mock()
    client.create_temp_path.return_value = ({"url": signed_url, "path": "s3://temporary/data.bin"}, None)
    response = requests.Response()
    response.status_code = 503
    response.url = signed_url
    response.headers["Retry-After"] = "Sun, 32 Jan 9999999999 00:00:00 GMT"

    monkeypatch.setattr(uploader.requests, "put", Mock(return_value=response))
    monkeypatch.setattr(uploader, "_wait_upload_retry", lambda _: 0)

    with caplog.at_level(logging.WARNING, logger="anno3d.annofab.uploader"):
        with pytest.raises(UploadRequestError) as exc_info:
            AnnofabStorageUploader(client, project="project-id").upload_tempdata(upload_file)

    rendered_traceback = "".join(traceback.format_exception(exc_info.type, exc_info.value, exc_info.tb))
    assert "X-Amz-Credential" not in caplog.text
    assert "X-Amz-Signature" not in caplog.text
    assert "X-Amz-Credential" not in rendered_traceback
    assert "X-Amz-Signature" not in rendered_traceback


def test_upload_tempdata_不正なs3_xmlでも署名付きurlを例外チェーンへ出力しない(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    upload_file = tmp_path / "data.bin"
    upload_file.write_bytes(b"upload data")
    signed_url = "https://example.com/upload?X-Amz-Credential=credential&X-Amz-Signature=signature"
    client = Mock()
    client.create_temp_path.return_value = ({"url": signed_url, "path": "s3://temporary/data.bin"}, None)
    response = requests.Response()
    response.status_code = HTTPStatus.BAD_REQUEST
    response.url = signed_url
    response._content = b'<?xml version="1.0" encoding="UTF-32"?><Error><Code>RequestTimeout</Code></Error>'

    monkeypatch.setattr(uploader.requests, "put", Mock(return_value=response))

    with pytest.raises(UploadRequestError) as exc_info:
        AnnofabStorageUploader(client, project="project-id").upload_tempdata(upload_file)

    rendered_traceback = "".join(traceback.format_exception(exc_info.type, exc_info.value, exc_info.tb))
    assert exc_info.value.__context__ is None
    assert exc_info.value.__cause__ is None
    assert "X-Amz-Credential" not in rendered_traceback
    assert "X-Amz-Signature" not in rendered_traceback

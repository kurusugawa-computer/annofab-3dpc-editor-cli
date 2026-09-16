import logging
import traceback
from datetime import datetime, timedelta, timezone
from email.utils import format_datetime
from pathlib import Path
from unittest.mock import Mock

import pytest
import requests

from anno3d.annofab import uploader
from anno3d.annofab.uploader import (
    AnnofabStorageUploader,
    UploadRequestError,
    _get_retry_after_seconds,
    _is_retryable_upload_error,
    _parse_retry_after_seconds,
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
    error = _http_error(429, "120")

    assert _get_retry_after_seconds(error) == 120.0


def test_get_retry_after_seconds_http_date形式():
    now = datetime(2026, 9, 16, 0, 0, 0, tzinfo=timezone.utc)
    retry_at = now + timedelta(seconds=120)

    assert _parse_retry_after_seconds(format_datetime(retry_at, usegmt=True), now=now) == 120.0


@pytest.mark.parametrize("retry_after", ["-1", "120.5", "invalid date"])
def test_get_retry_after_seconds_不正値は_noneを返す(retry_after: str):
    error = _http_error(429, retry_after)

    assert _get_retry_after_seconds(error) is None


def test_wait_upload_retry_retry_afterを指数バックオフの下限にする():
    retry_state = Mock()
    retry_state.attempt_number = 1
    retry_state.outcome.exception.return_value = _http_error(429, "120")

    assert _wait_upload_retry(retry_state) == 120.0


def test_is_retryable_upload_error_s3_request_timeoutは再試行する():
    error = _http_error_with_body(
        400,
        b"""<?xml version="1.0" encoding="UTF-8"?>
        <Error>
            <Code>RequestTimeout</Code>
        </Error>""",
    )

    assert _is_retryable_upload_error(error) is True


def test_is_retryable_upload_error_s3の他の400は再試行しない():
    error = _http_error_with_body(400, b"<Error><Code>AccessDenied</Code></Error>")

    assert _is_retryable_upload_error(error) is False


def test_upload_tempdata_一時的なput失敗後に先頭から再試行して成功する(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
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
            raise requests.exceptions.ConnectionError()
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
        record.getMessage() == "Retrying temporary storage upload: file=data.bin, status=503, attempt=" + str(i)
        for i, record in enumerate(caplog.records, start=1)
    )

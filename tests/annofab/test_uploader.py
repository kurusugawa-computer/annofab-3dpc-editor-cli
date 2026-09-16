import logging
import traceback
from datetime import datetime, timedelta, timezone
from email.utils import format_datetime
from unittest.mock import Mock

import pytest
import requests

from anno3d.annofab.uploader import (
    AnnofabStorageUploader,
    TempDataUploadError,
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


def test_upload_tempdata_署名付きurlをログと最終例外から除去する(tmp_path, monkeypatch, caplog):
    signed_url = "https://bucket.s3.example/object?X-Amz-Signature=secret-signature"
    upload_file = tmp_path / "scene_001.pcd"
    upload_file.write_bytes(b"data")

    client = Mock()
    client.create_temp_path.return_value = ({"url": signed_url, "path": "s3://bucket/object"}, None)
    uploader = AnnofabStorageUploader(client, "project")

    response = requests.Response()
    response.status_code = 503
    response.url = signed_url
    response.request = requests.Request("PUT", signed_url).prepare()
    monkeypatch.setattr("anno3d.annofab.uploader.requests.put", Mock(return_value=response))
    monkeypatch.setattr("anno3d.annofab.uploader._wait_upload_retry", lambda _: 0)
    caplog.set_level(logging.WARNING)

    with pytest.raises(TempDataUploadError) as exc_info:
        uploader.upload_tempdata(upload_file)

    formatted_exception = "".join(traceback.format_exception(exc_info.type, exc_info.value, exc_info.tb))
    assert "scene_001.pcd" in str(exc_info.value)
    assert "status=503" in str(exc_info.value)
    assert signed_url not in caplog.text
    assert "X-Amz-Signature" not in caplog.text
    assert signed_url not in formatted_exception
    assert "X-Amz-Signature" not in formatted_exception
    assert exc_info.value.__cause__ is None
    assert exc_info.value.__context__ is None

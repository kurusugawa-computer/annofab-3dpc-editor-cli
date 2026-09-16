from datetime import datetime, timedelta, timezone
from email.utils import format_datetime
from unittest.mock import Mock

import pytest
import requests

from anno3d.annofab.uploader import _get_retry_after_seconds, _parse_retry_after_seconds, _wait_upload_retry


def _http_error(status_code: int, retry_after: str) -> requests.exceptions.HTTPError:
    response = requests.Response()
    response.status_code = status_code
    response.headers["Retry-After"] = retry_after
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

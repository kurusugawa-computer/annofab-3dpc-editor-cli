from pathlib import Path
from unittest.mock import Mock

import pytest
import requests
from tenacity import wait_none

import anno3d.annofab.uploader as uploader_module
from anno3d.annofab.uploader import AnnofabStorageUploader


def _uploader() -> AnnofabStorageUploader:
    client = Mock()
    client.create_temp_path.return_value = ({"url": "https://example.com/upload", "path": "s3://temporary/key"}, None)
    return AnnofabStorageUploader(client, project="project-id")


def test_upload_tempdata_uses_existing_timeout(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    response = Mock()
    response.raise_for_status.return_value = None
    put = Mock(return_value=response)
    monkeypatch.setattr(requests, "put", put)
    upload_file = tmp_path / "pointcloud.bin"
    upload_file.write_bytes(b"point cloud")

    _uploader().upload_tempdata(upload_file)

    assert put.call_args.kwargs["timeout"] == 600
    response.raise_for_status.assert_called_once_with()


def test_upload_tempdata_retries_connection_error_with_a_new_file_stream(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    response = Mock()
    response.raise_for_status.return_value = None
    uploaded_bodies: list[bytes] = []

    def put(*args: object, **kwargs: object) -> Mock:
        data = kwargs["data"]
        assert hasattr(data, "read")
        uploaded_bodies.append(data.read())
        if len(uploaded_bodies) == 1:
            raise requests.exceptions.ConnectionError("connection reset")
        return response

    monkeypatch.setattr(requests, "put", put)
    monkeypatch.setattr(uploader_module, "wait_random_exponential", lambda **_: wait_none())
    upload_file = tmp_path / "pointcloud.bin"
    upload_file.write_bytes(b"point cloud")

    _uploader().upload_tempdata(upload_file)

    assert uploaded_bodies == [b"point cloud", b"point cloud"]
    response.raise_for_status.assert_called_once_with()


def test_upload_tempdata_does_not_retry_non_retryable_http_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    response = Mock(status_code=400)
    error = requests.exceptions.HTTPError(response=response)
    response.raise_for_status.side_effect = error
    put = Mock(return_value=response)
    monkeypatch.setattr(requests, "put", put)
    upload_file = tmp_path / "pointcloud.bin"
    upload_file.write_bytes(b"point cloud")

    with pytest.raises(requests.exceptions.HTTPError):
        _uploader().upload_tempdata(upload_file)

    put.assert_called_once()

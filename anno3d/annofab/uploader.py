import abc
from dataclasses import dataclass
from logging import getLogger
from pathlib import Path
from typing import Any, Literal, Optional

import boto3
import more_itertools
import requests
from annofabapi import AnnofabApi
from annofabapi import Wrapper as AnnofabApiWrapper
from botocore.errorfactory import ClientError


@dataclass(frozen=True)
class DataPath:
    url: str
    path: str


logger = getLogger(__name__)


class Uploader(abc.ABC):
    """

    Args:
        client:
        project: プロジェクトID
        force: 入力データと補助データを上書きしてアップロードするかどうか。
    """

    _client: AnnofabApi
    _project: str

    def __init__(self, client: AnnofabApi, project: str, force: bool = False):
        self._client = client
        self._client_wrapper = AnnofabApiWrapper(client)
        self._project = project
        self._force = force

    def get_input_data(self, input_data_id: str) -> Optional[Any]:
        return self._client_wrapper.get_input_data_or_none(self._project, input_data_id)

    @abc.abstractmethod
    def upload_tempdata(self, upload_file: Path) -> str:
        pass

    def upload_input_data(self, input_data_id: str, file: Path) -> str:
        path = self.upload_tempdata(file)

        data_id = input_data_id
        body = {"input_data_name": file.name, "input_data_path": path}
        if self._force:
            old_input_data = self.get_input_data(input_data_id)
            if old_input_data is not None:
                body["last_updated_datetime"] = old_input_data["updated_datetime"]

        input_data, _ = self._client.put_input_data(self._project, data_id, query_params=None, request_body=body)

        logger.debug("uploaded input data: %s", input_data)
        return data_id

    def upload_supplementary(
        self,
        input_data_id: str,
        supplementary_id: str,
        file: Path,
        supplementary_data_type: Literal["custom", "image", "text"],
    ) -> str:
        path = self.upload_tempdata(file)
        body = {
            "supplementary_data_name": supplementary_id,
            "supplementary_data_path": path,
            "supplementary_data_type": supplementary_data_type,
            "supplementary_data_number": 0,
        }
        if self._force:
            supplementary_list, _ = self._client.get_supplementary_data_list(self._project, input_data_id)
            old_supplementary = more_itertools.first_true(
                supplementary_list, pred=lambda e: e["supplementary_data_id"] == supplementary_id
            )
            if old_supplementary is not None:
                body["last_updated_datetime"] = old_supplementary["updated_datetime"]

        supplementary, _ = self._client.put_supplementary_data(self._project, input_data_id, supplementary_id, body)
        logger.debug("uploaded supplementary data: %s", supplementary)
        return supplementary_id


class AnnofabStorageUploader(Uploader):
    def upload_tempdata(self, upload_file: Path) -> str:
        client = self._client

        data_path_dict, _ = client.create_temp_path(self._project)

        data_path = DataPath(data_path_dict["url"], data_path_dict["path"])
        # XXX エラー処理とか例外処理とか何もないので注意
        with upload_file.open(mode="rb") as data:
            requests.put(data_path.url, data, headers={"Content-Type": "application/octet-stream"}, timeout=30)

        return data_path.path


class S3Uploader(Uploader):
    """
    AWS S3にファイルをアップロードした上で、Annofabに入力データや補助情報を登録するクラス。
    """

    def __init__(self, client: AnnofabApi, project: str, s3_path: str, force: bool = False):
        tmp = s3_path.split("/")
        self._s3_bucket = tmp[0]
        self._s3_prefix_key = s3_path[len(self._s3_bucket + "/") :]
        self._s3_client = boto3.client("s3")
        super().__init__(client=client, project=project, force=force)

    def s3_key_exists(self, key: str) -> bool:
        try:
            self._s3_client.head_object(Bucket=self._s3_bucket, Key=key)
            return True
        except ClientError:
            return False

    def get_s3_uri(self, key: str) -> str:
        return f"s3://{self._s3_bucket}/{key}"

    def upload_tempdata(self, upload_file: Path) -> str:
        client = self._s3_client
        key = self._s3_prefix_key + f"{upload_file.parent.name}/{upload_file.name}"

        if self._force or not self.s3_key_exists(key):
            client.upload_file(Filename=str(upload_file), Bucket=self._s3_bucket, Key=key)

            return self.get_s3_uri(key)
        else:
            raise RuntimeError(f"AWS S3にオブジェクトがすでに存在します。Bucket='{self._s3_bucket}', Key='{key}'")

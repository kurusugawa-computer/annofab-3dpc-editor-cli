from dataclasses import dataclass
from logging import getLogger
from pathlib import Path
from typing import Any, Optional

import more_itertools
import requests
from annofabapi import AnnofabApi
from annofabapi.utils import allow_404_error


@dataclass(frozen=True)
class DataPath:
    url: str
    path: str


logger = getLogger(__name__)


class Uploader:
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
        self._project = project
        self._force = force

    @allow_404_error
    def get_input_data(self, input_data_id: str) -> Optional[Any]:
        result, _ = self._client.get_input_data(self._project, input_data_id)
        return result

    def upload_tempdata(self, upload_file: Path) -> str:
        client = self._client

        data_path_dict, _ = client.create_temp_path(self._project, {"Content-Type": "application/octet-stream"})

        data_path = DataPath(data_path_dict["url"], data_path_dict["path"])
        # XXX エラー処理とか例外処理とか何もないので注意
        with upload_file.open(mode="rb") as data:
            requests.put(data_path.url, data)

        return data_path.path

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

    def upload_supplementary(self, input_data_id: str, supplementary_id: str, file: Path) -> str:
        path = self.upload_tempdata(file)
        body = {
            "supplementary_data_name": supplementary_id,
            "supplementary_data_path": path,
            "supplementary_data_type": "custom",
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

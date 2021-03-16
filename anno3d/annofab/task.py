import json
from pathlib import Path
from typing import List, Optional

from annofabapi import AnnofabApi
from annofabapi import models as afm
from annofabapi.dataclass.task import Task
from annofabapi.models import TaskStatus

from anno3d.annofab.model import CuboidAnnotationDetail, TaskGenerateResponse
from anno3d.annofab.project import ProjectApi
from anno3d.annofab.uploader import AnnofabStorageUploader


class TaskApi:
    _client: AnnofabApi
    _project: ProjectApi
    _project_id: str

    def __init__(self, client: AnnofabApi, project: ProjectApi, project_id: str):
        self._client = client
        self._project = project
        self._project_id = project_id

    @property
    def project_id(self) -> str:
        return self._project_id

    @staticmethod
    def _decode_task(task: afm.Task) -> Task:
        return Task.from_dict(task)

    def create_tasks_by_csv(self, csv_path: Path) -> TaskGenerateResponse:
        client = self._client
        project_id = self._project_id
        uploader = AnnofabStorageUploader(client, project_id)
        project = self._project.get_project(project_id)
        if project is None:
            raise RuntimeError("指定されたプロジェクト(={})が見つかりませんでした。".format(project_id))

        uploaded_path = uploader.upload_tempdata(csv_path)

        body_params = {
            "task_generate_rule": {"csv_data_path": uploaded_path, "_type": "ByInputDataCsv"},
            "project_last_updated_datetime": project.updated_datetime,
        }
        task_generate_result, _ = client.initiate_tasks_generation(project_id, request_body=body_params)

        return TaskGenerateResponse.from_dict(task_generate_result)

    def get_task(self, task_id: str) -> Optional[Task]:
        client = self._client
        project_id = self._project_id
        result, response = client.get_task(project_id, task_id)
        if response.status_code != 200:
            return None

        return self._decode_task(result)

    def put_cuboid_annotations(
        self, task_id: str, input_data_id: str, annotations: List[CuboidAnnotationDetail]
    ) -> None:
        client = self._client
        project_id = self._project_id

        details: List[dict] = CuboidAnnotationDetail.schema().dump(annotations, many=True)
        for d in details:
            data: dict = d["data"]
            d["data"] = json.dumps(data, ensure_ascii=False)
            d["additional_data_list"] = []

        body = {"project_id": project_id, "task_id": task_id, "input_data_id": input_data_id, "details": details}

        client.put_annotation(project_id, task_id, input_data_id, body)

    def start_annotate(self, task_id: str) -> Optional[Task]:
        """ 対象タスクの担当者を自分自身ににして、 annotate状態にする"""
        client = self._client
        project_id = self._project_id

        task = self.get_task(task_id)
        if task is None:
            return None

        params = {
            "status": TaskStatus.WORKING,
            "last_updated_datetime": task.updated_datetime,
            "account_id": client.account_id,
        }
        result, _ = client.operate_task(project_id, task_id, params)
        return self._decode_task(result)

    def finish_annotate(self, task_id: str):
        """ 対象タスクの担当者を空にして、not_started状態にする """
        client = self._client
        project_id = self._project_id

        task = self.get_task(task_id)
        if task is None:
            return None

        params = {"status": TaskStatus.NOT_STARTED, "last_updated_datetime": task.updated_datetime}
        result, _ = client.operate_task(project_id, task_id, params)
        return self._decode_task(result)

from typing import Collection, List, Optional

from annofabapi import AnnofabApi
from annofabapi import models as afm
from annofabapi.dataclass.task import Task
from annofabapi.models import TaskStatus

from anno3d.annofab.model import CuboidAnnotationDetailCreate, CuboidAnnotations
from anno3d.annofab.project import ProjectApi


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

    def get_task(self, task_id: str) -> Optional[Task]:
        client = self._client
        project_id = self._project_id
        result, response = client.get_task(project_id, task_id)
        if response.status_code != 200:
            return None

        return self._decode_task(result)

    def put_task(self, task_id: str, input_data_ids: Collection[str]) -> Task:
        client = self._client
        project_id = self._project_id
        result, _ = client.put_task(project_id, task_id, request_body={"input_data_id_list": input_data_ids})
        return self._decode_task(result)

    def put_cuboid_annotations(
        self, task_id: str, input_data_id: str, details: List[CuboidAnnotationDetailCreate]
    ) -> None:
        client = self._client
        project_id = self._project_id
        annotations = CuboidAnnotations(
            project_id=project_id, task_id=task_id, input_data_id=input_data_id, details=details
        )

        body = annotations.to_json(ensure_ascii=False)
        client.put_annotation(project_id, task_id, input_data_id, {"v": "2"}, body)

    def start_annotate(self, task_id: str) -> Optional[Task]:
        """対象タスクの担当者を自分自身ににして、 annotate状態にする"""
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
        """対象タスクの担当者を空にして、not_started状態にする"""
        client = self._client
        project_id = self._project_id

        task = self.get_task(task_id)
        if task is None:
            return None

        params = {"status": TaskStatus.NOT_STARTED, "last_updated_datetime": task.updated_datetime}
        result, _ = client.operate_task(project_id, task_id, params)
        return self._decode_task(result)

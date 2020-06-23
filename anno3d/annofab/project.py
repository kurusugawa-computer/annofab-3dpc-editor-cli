from typing import Any, Dict

from annofabapi import AnnofabApi


class Project:
    _client: AnnofabApi

    def __init__(self, client: AnnofabApi):
        self._client = client

    def create_custom_project(
        self, project_id: str, organization_name: str, plugin_id: str, title: str = "", overview: str = ""
    ) -> str:
        """
        カスタムプロジェクトを作成し、作成したprojectのidを返します

        Args:
            project_id:
            organization_name:
            title:
            overview:

        Returns:

        """
        client = self._client

        body = {
            "title": title if len(title) != 0 else project_id,
            "overview": overview if len(overview) != 0 else project_id,
            "status": "active",
            "input_data_type": "custom",
            "organization_name": organization_name,
            "configuration": {
                "task_assignment_type": "random_and_selection",
                "input_data_set_id_list": [],
                "plugin_id": plugin_id,
            },
        }

        project: Dict[str, Any]
        project, response = client.put_project(project_id, body)
        if response.status_code != 200:
            raise RuntimeError("Project新規作成時のhttp status codeは200ですが、{}が返されました。".format(response.status_code))

        created_id: str = project["project_id"]
        return created_id

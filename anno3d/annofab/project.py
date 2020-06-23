from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from annofabapi import AnnofabApi
from annofabapi.models import AnnotationSpecsV2, LabelV2
from dataclasses_json import DataClassJsonMixin


@dataclass
class Label(DataClassJsonMixin):
    label_id: str
    ja_name: str
    en_name: str
    color: Tuple[int, int, int]


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

    @staticmethod
    def _from_annofab_label(annofab_label: LabelV2) -> Label:
        messages = annofab_label["label_name"]["messages"]
        color = annofab_label["color"]
        ja_name = next(filter(lambda e: e["lang"] == "ja", messages), "")
        en_name = next(filter(lambda e: e["lang"] == "en", messages), "")

        return Label(annofab_label["label_id"], ja_name, en_name, (color["red"], color["green"], color["blue"]))

    def put_label(
        self, project_id: str, label_id: str, ja_name: str, en_name: str, color: Tuple[int, int, int]
    ) -> List[Label]:
        client = self._client

        specs: AnnotationSpecsV2
        specs, _ = client.get_annotation_specs(project_id, {"v": "2"})
        labels: List[LabelV2] = specs["labels"]
        index: Optional[int]
        index, _ = next(filter(lambda ie: ie[1]["label_id"] == label_id, enumerate(labels)), (None, None))

        new_label: LabelV2 = {
            "label_id": label_id,
            "label_name": {
                "messages": [{"lang": "ja", "message": ja_name}, {"lang": "en", "message": en_name}],
                "default_lang": "ja",
            },
            "color": {"red": color[0], "green": color[1], "blue": color[2]},
            "keybind": [],
            "annotation_type": "custom",
            "annotation_editor_feature": {
                "append": False,
                "erase": False,
                "freehand": False,
                "rectangle_fill": False,
                "polygon_fill": False,
                "fill_near": False,
            },
            "additional_data_definitions": [],
            "allow_out_of_image_bounds": False,
        }

        if index is not None:
            labels[index] = new_label
        else:
            labels.append(new_label)

        new_specs = {
            "labels": labels,
            "additionals": specs["additionals"],
            "restrictions": specs["restrictions"],
            "inspection_phrases": specs["inspection_phrases"],
            "format_version": specs["format_version"],
            "last_updated_datetime": specs["updated_datetime"],
            "comment": "",
            "auto_marking": False,
        }

        print("last updated = {}".format(specs["updated_datetime"]))

        created_specs, _ = client.put_annotation_specs(project_id, new_specs)
        return [self._from_annofab_label(label) for label in created_specs["labels"]]

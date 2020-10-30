from typing import Any, Dict, List, Optional, Tuple, Union

from annofabapi import AnnofabApi
from annofabapi import models as afm
from annofabapi.dataclass.annotation_specs import (
    AnnotationEditorFeature,
    AnnotationSpecsV2,
    Color,
    InternationalizationMessage,
    InternationalizationMessageMessages,
    LabelV2,
)
from annofabapi.dataclass.job import JobInfo
from annofabapi.dataclass.project import Project
from annofabapi.models import AnnotationType
from more_itertools import first_true

from anno3d.annofab.constant import lang_en, lang_ja
from anno3d.annofab.model import Label
from anno3d.model.label import CuboidLabelMetadata, SegmentLabelMetadata


class ProjectApi:
    _client: AnnofabApi

    def __init__(self, client: AnnofabApi):
        self._client = client

    @staticmethod
    def _decode_project(project: afm.Project) -> Project:
        return Project.from_dict(project)

    def get_project(self, project_id) -> Optional[Project]:
        client = self._client
        result, response = client.get_project(project_id)
        if response.status_code != 200:
            return None

        return self._decode_project(result)

    @staticmethod
    def _decode_jobinfo(info: afm.JobInfo) -> JobInfo:
        return JobInfo.from_dict(info)

    def create_custom_project(
        self, project_id: str, organization_name: str, plugin_id: str, title: str = "", overview: str = ""
    ) -> str:
        """
        カスタムプロジェクトを作成し、作成したprojectのidを返します

        Args:
            project_id:
            organization_name:
            plugin_id:
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
        project, response = client.put_project(project_id, request_body=body)
        if response.status_code != 200:
            raise RuntimeError("Project新規作成時のhttp status codeは200ですが、{}が返されました。".format(response.status_code))

        created_id: str = project["project_id"]
        return created_id

    @staticmethod
    def _from_annofab_label(annofab_label: afm.LabelV2) -> Label:
        messages = annofab_label["label_name"]["messages"]
        color = annofab_label["color"]
        empty_message: dict = InternationalizationMessageMessages("", "").to_dict()
        ja_name = next(filter(lambda e: e["lang"] == lang_ja, messages), empty_message)["message"]
        en_name = next(filter(lambda e: e["lang"] == lang_en, messages), empty_message)["message"]
        metadata = annofab_label["metadata"]

        return Label(
            annofab_label["label_id"], ja_name, en_name, (color["red"], color["green"], color["blue"]), metadata
        )

    def put_cuboid_label(
        self, project_id: str, label_id: str, ja_name: str, en_name: str, color: Tuple[int, int, int]
    ) -> List[Label]:
        return self.put_label(project_id, label_id, ja_name, en_name, color, CuboidLabelMetadata())

    _default_segment_metadata = SegmentLabelMetadata()

    def put_segment_label(
        self,
        project_id: str,
        label_id: str,
        ja_name: str,
        en_name: str,
        color: Tuple[int, int, int],
        default_ignore: bool,
        segment_kind: str = _default_segment_metadata.segment_kind,
        layer: int = int(_default_segment_metadata.layer),
    ) -> List[Label]:
        metadata = SegmentLabelMetadata(layer=str(layer), segment_kind=segment_kind)

        return self.put_label(project_id, label_id, ja_name, en_name, color, metadata)

    def get_annotation_specs(self, project_id: str) -> AnnotationSpecsV2:
        client = self._client
        specs, _ = client.get_annotation_specs(project_id, {"v": "2"})

        return AnnotationSpecsV2.from_dict(specs)

    # def _put_ignore_additional_if_necessary(self, specs: AnnotationSpecsV2,):

    def put_label(
        self,
        project_id: str,
        label_id: str,
        ja_name: str,
        en_name: str,
        color: Tuple[int, int, int],
        metadata: Union[CuboidLabelMetadata, SegmentLabelMetadata],
    ) -> List[Label]:
        client = self._client

        specs = self.get_annotation_specs(project_id)
        specs_dict: dict = specs.to_dict(encode_json=True)
        labels: List[LabelV2] = specs.labels if specs.labels is not None else list([])
        index: Optional[int]
        index, _ = next(filter(lambda ie: ie[1].label_id == label_id, enumerate(labels)), (None, None))
        meta_dic: dict = metadata.to_dict(encode_json=True)

        new_label: LabelV2 = LabelV2(
            label_id=label_id,
            label_name=InternationalizationMessage(
                [
                    InternationalizationMessageMessages(lang_ja, ja_name),
                    InternationalizationMessageMessages(lang_en, en_name),
                ],
                lang_ja,
            ),
            keybind=[],
            annotation_type=AnnotationType.CUSTOM,
            bounding_box_metadata=None,
            segmentation_metadata=None,
            additional_data_definitions=[],
            color=Color(red=color[0], green=color[1], blue=color[2]),
            annotation_editor_feature=AnnotationEditorFeature(
                append=False, erase=False, freehand=False, rectangle_fill=False, polygon_fill=False, fill_near=False
            ),
            allow_out_of_image_bounds=False,
            metadata=meta_dic,
        )

        if index is not None:
            labels[index] = new_label
        else:
            labels.append(new_label)

        # XXX AnnotationSpecsRequestV2 の dataclassなかった…
        new_specs = {
            "labels": LabelV2.schema().dump(labels, many=True),
            "additionals": specs_dict["additionals"],
            "restrictions": specs_dict["restrictions"],
            "inspection_phrases": specs_dict["inspection_phrases"],
            "format_version": specs_dict["format_version"],
            "last_updated_datetime": specs_dict["updated_datetime"],
            "comment": "",
            "auto_marking": False,
        }

        created_specs, _ = client.put_annotation_specs(project_id, new_specs)
        return [self._from_annofab_label(label) for label in created_specs["labels"]]

    def get_job(self, project_id: str, job: JobInfo) -> Optional[JobInfo]:
        client = self._client
        if job.job_type is None:
            raise RuntimeError(f"ジョブ(={job.job_id})のjob_typeがありません")
        params = {"type": job.job_type.value, "limit": "200"}
        result, _ = client.get_project_job(project_id, params)
        jobs: List[afm.JobInfo] = result["list"]
        jobs2 = [self._decode_jobinfo(j) for j in jobs]

        return first_true(jobs2, pred=lambda j: j.job_id == job.job_id)

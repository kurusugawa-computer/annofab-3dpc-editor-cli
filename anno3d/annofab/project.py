import copy
from dataclasses import replace
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

import more_itertools
from annofabapi import AnnofabApi
from annofabapi import models as afm
from annofabapi.dataclass.annotation_specs import (
    AdditionalDataDefinitionV2,
    AnnotationEditorFeature,
    AnnotationSpecsV2,
    Color,
    InternationalizationMessage,
    InternationalizationMessageMessages,
    LabelV2,
)
from annofabapi.dataclass.job import JobInfo
from annofabapi.dataclass.project import Project
from annofabapi.models import AdditionalDataDefinitionType, AnnotationType
from more_itertools import first_true

from anno3d.annofab.constant import (
    IgnoreAdditionalDef,
    default_ignore_additional,
    default_non_ignore_additional,
    lang_en,
    lang_ja,
)
from anno3d.annofab.model import AnnotationSpecsRequestV2, Label
from anno3d.model.annotation_area import AnnotationArea
from anno3d.model.label import CuboidLabelMetadata, SegmentLabelMetadata
from anno3d.model.project_specs_meta import ProjectMetadata, decode_project_meta, encode_project_meta


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

    def _mod_project_specs(
        self, project_id: str, mod_func: Callable[[AnnotationSpecsV2], AnnotationSpecsV2]
    ) -> AnnotationSpecsV2:
        client = self._client

        specs = self.get_annotation_specs(project_id)
        new_specs = mod_func(specs)
        request = AnnotationSpecsRequestV2.from_specs(new_specs)

        created_specs, _ = client.put_annotation_specs(project_id, request.to_dict(encode_json=True))
        return AnnotationSpecsV2.from_dict(created_specs)

    def _mod_project_specs_metadata(
        self, project_id: str, mod_func: Callable[[ProjectMetadata], ProjectMetadata]
    ) -> ProjectMetadata:
        def mod(specs: AnnotationSpecsV2) -> AnnotationSpecsV2:
            metadata = decode_project_meta(specs.metadata if specs.metadata is not None else {})
            new_metadata = mod_func(metadata)
            return replace(specs, metadata=encode_project_meta(new_metadata))

        new_spec = self._mod_project_specs(project_id, mod)
        return decode_project_meta(new_spec.metadata if new_spec.metadata is not None else {})

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
        return self.put_label(project_id, label_id, ja_name, en_name, color, CuboidLabelMetadata(), None)

    def put_segment_label(
        self,
        project_id: str,
        label_id: str,
        ja_name: str,
        en_name: str,
        color: Tuple[int, int, int],
        default_ignore: bool,
        segment_kind: str,
        layer: int,
    ) -> List[Label]:
        additional_def = default_ignore_additional if default_ignore else default_non_ignore_additional
        metadata = SegmentLabelMetadata(ignore=additional_def.id, layer=str(layer), segment_kind=segment_kind)

        return self.put_label(project_id, label_id, ja_name, en_name, color, metadata, additional_def)

    def get_annotation_specs(self, project_id: str) -> AnnotationSpecsV2:
        client = self._client
        specs, _ = client.get_annotation_specs(project_id, {"v": "2"})

        return AnnotationSpecsV2.from_dict(specs)

    @staticmethod
    def _ignore_additional(additional_def: IgnoreAdditionalDef) -> AdditionalDataDefinitionV2:
        return AdditionalDataDefinitionV2(
            additional_data_definition_id=additional_def.id,
            read_only=False,
            name=InternationalizationMessage(
                [
                    InternationalizationMessageMessages(lang_ja, additional_def.ja_name),
                    InternationalizationMessageMessages(lang_en, additional_def.en_name),
                ],
                lang_ja,
            ),
            default=additional_def.default,
            keybind=[],
            type=AdditionalDataDefinitionType.FLAG,
            choices=[],
            metadata={},
        )

    def _create_ignore_additional_if_necessary(
        self, specs: AnnotationSpecsV2, additional_def: IgnoreAdditionalDef
    ) -> List[AdditionalDataDefinitionV2]:
        additionals: List[AdditionalDataDefinitionV2] = copy.copy(
            specs.additionals if specs.additionals is not None else []
        )

        additional = more_itertools.first_true(
            additionals, None, lambda e: e.additional_data_definition_id == additional_def.id
        )

        if additional is None:
            additionals.append(self._ignore_additional(additional_def))

        return additionals

    def mod_label(self, project_id: str, label_id: str):
        pass

    def put_label(
        self,
        project_id: str,
        label_id: str,
        ja_name: str,
        en_name: str,
        color: Tuple[int, int, int],
        metadata: Union[CuboidLabelMetadata, SegmentLabelMetadata],
        ignore_additional: Optional[IgnoreAdditionalDef],
    ) -> List[Label]:
        def update_specs(specs: AnnotationSpecsV2) -> AnnotationSpecsV2:
            labels: List[LabelV2] = specs.labels if specs.labels is not None else list([])
            index: Optional[int]
            index, _ = next(filter(lambda ie: ie[1].label_id == label_id, enumerate(labels)), (None, None))
            meta_dic: dict = metadata.to_dict(encode_json=True)

            additionals = specs.additionals
            if ignore_additional is not None:
                additionals = self._create_ignore_additional_if_necessary(specs, ignore_additional)

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
                additional_data_definitions=[ignore_additional.id] if ignore_additional is not None else [],
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

            return replace(specs, labels=labels, additionals=additionals)

        created_specs = self._mod_project_specs(project_id, update_specs)

        if created_specs.labels is None:
            return []

        return [self._from_annofab_label(label.to_dict(encode_json=True)) for label in created_specs.labels]

    def set_annotation_area(self, project_id: str, area: AnnotationArea) -> ProjectMetadata:
        def mod(meta: ProjectMetadata) -> ProjectMetadata:
            return replace(meta, annotation_area=area)

        return self._mod_project_specs_metadata(project_id, mod)

    def get_job(self, project_id: str, job: JobInfo) -> Optional[JobInfo]:
        client = self._client
        if job.job_type is None:
            raise RuntimeError(f"ジョブ(={job.job_id})のjob_typeがありません")
        params = {"type": job.job_type.value, "limit": "200"}
        result, _ = client.get_project_job(project_id, params)
        jobs: List[afm.JobInfo] = result["list"]
        jobs2 = [self._decode_jobinfo(j) for j in jobs]

        return first_true(jobs2, pred=lambda j: j.job_id == job.job_id)

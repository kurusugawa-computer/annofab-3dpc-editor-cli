from typing import Any, Callable, Dict, List, Optional, Tuple, Union

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
from annofabapi.dataclass.job import ProjectJobInfo
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
from anno3d.annofab.specifiers.label_specifiers import LabelSpecifiers
from anno3d.annofab.specifiers.project_specifiers import ProjectSpecifiers
from anno3d.model.annotation_area import AnnotationArea
from anno3d.model.label import CuboidLabelMetadata, SegmentLabelMetadata
from anno3d.model.preset_cuboids import PresetCuboidSize, PresetCuboidSizes, preset_cuboid_size_metadata_prefix
from anno3d.model.project_specs_meta import ProjectMetadata
from anno3d.util.modifier import DataModifier


class ProjectModifiers:
    specifiers = ProjectSpecifiers

    @classmethod
    def set_annotation_area(cls, area: AnnotationArea) -> DataModifier[AnnotationSpecsV2]:
        return cls.specifiers.annotation_area.mod(lambda _: area)

    @classmethod
    def remove_preset_cuboid_size(cls, key_name: str) -> DataModifier[AnnotationSpecsV2]:
        prefixed = preset_cuboid_size_metadata_prefix + key_name.title()
        return cls.specifiers.preset_cuboid_sizes.mod(
            lambda curr: dict(filter(lambda kv: kv[0] != prefixed, curr.items()))
        )

    @classmethod
    def add_preset_cuboid_size(
        cls, key_name: str, ja_name: str, en_name: str, width: float, height: float, depth: float
    ) -> DataModifier[AnnotationSpecsV2]:
        prefixed = preset_cuboid_size_metadata_prefix + key_name.title()

        def update(sizes: PresetCuboidSizes) -> PresetCuboidSizes:
            sizes.update(
                {prefixed: PresetCuboidSize(ja_name=ja_name, en_name=en_name, width=width, height=height, depth=depth)}
            )
            return sizes

        return cls.specifiers.preset_cuboid_sizes.mod(update)

    @classmethod
    def put_label(
        cls,
        label_id: str,
        ja_name: str,
        en_name: str,
        color: Tuple[int, int, int],
        metadata: Union[CuboidLabelMetadata, SegmentLabelMetadata],
        ignore_additional: Optional[IgnoreAdditionalDef],
    ) -> DataModifier[AnnotationSpecsV2]:
        def init_label() -> LabelV2:
            return LabelV2(
                label_id=label_id,
                label_name=InternationalizationMessage(
                    [
                        InternationalizationMessageMessages(lang_ja, label_id),
                        InternationalizationMessageMessages(lang_en, label_id),
                    ],
                    lang_ja,
                ),
                keybind=[],
                annotation_type=AnnotationType.CUSTOM,
                bounding_box_metadata=None,
                segmentation_metadata=None,
                additional_data_definitions=[],
                color=Color(red=0, green=0, blue=0),
                annotation_editor_feature=AnnotationEditorFeature(
                    append=False, erase=False, freehand=False, rectangle_fill=False, polygon_fill=False, fill_near=False
                ),
                allow_out_of_image_bounds=False,
                metadata={},
            )

        def mod(label_opt: Optional[LabelV2]) -> Optional[LabelV2]:
            label = label_opt if label_opt is not None else init_label()
            label.label_name = InternationalizationMessage(
                [
                    InternationalizationMessageMessages(lang_ja, ja_name),
                    InternationalizationMessageMessages(lang_en, en_name),
                ],
                lang_ja,
            )

            if ignore_additional is not None:
                label = LabelSpecifiers.additional(ignore_additional.id).set(ignore_additional.id)(label)

            label = LabelSpecifiers.color.set(Color(red=color[0], green=color[1], blue=color[2]))(label)
            meta_dic: dict = metadata.to_dict(encode_json=True)
            label.metadata = meta_dic

            return label

        label_specifier = cls.specifiers.label(label_id)
        return label_specifier.mod(mod)

    @classmethod
    def create_ignore_additional_if_necessary(
        cls, additional_def: IgnoreAdditionalDef
    ) -> DataModifier[AnnotationSpecsV2]:
        def mod(current: Optional[AdditionalDataDefinitionV2]) -> Optional[AdditionalDataDefinitionV2]:
            if current is not None:
                return current

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

        return cls.specifiers.additional(additional_def.id).mod(mod)


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
    def _decode_jobinfo(info: afm.ProjectJobInfo) -> ProjectJobInfo:
        return ProjectJobInfo.from_dict(info)

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
        """

        Args:
            project_id:
            label_id:
            ja_name:
            en_name:
            color: ラベルの表示色。 "(R,G,B)"形式 R/G/Bは、それぞれ0〜255の整数値で指定する
            metadata:
            ignore_additional:

        Returns:

        """

        mod_labels = ProjectModifiers.put_label(label_id, ja_name, en_name, color, metadata, ignore_additional)
        mod_additionals = (
            ProjectModifiers.create_ignore_additional_if_necessary(ignore_additional)
            if ignore_additional is not None
            else DataModifier.identity(AnnotationSpecsV2)
        )
        created_specs = self._mod_project_specs(project_id, mod_labels.and_then(mod_additionals))

        if created_specs.labels is None:
            return []

        return [self._from_annofab_label(label.to_dict(encode_json=True)) for label in created_specs.labels]

    def set_annotation_area(self, project_id: str, area: AnnotationArea) -> ProjectMetadata:
        new_spec = self._mod_project_specs(project_id, ProjectModifiers.set_annotation_area(area))
        return ProjectSpecifiers.metadata.get(new_spec)

    def remove_preset_cuboid_size(self, project_id: str, key_name: str) -> ProjectMetadata:
        new_spec = self._mod_project_specs(project_id, ProjectModifiers.remove_preset_cuboid_size(key_name))
        return ProjectSpecifiers.metadata.get(new_spec)

    def add_preset_cuboid_size(
        self, project_id: str, key_name: str, ja_name: str, en_name: str, width: float, height: float, depth: float
    ) -> ProjectMetadata:
        new_spec = self._mod_project_specs(
            project_id, ProjectModifiers.add_preset_cuboid_size(key_name, ja_name, en_name, width, height, depth)
        )
        return ProjectSpecifiers.metadata.get(new_spec)

    def get_job(self, project_id: str, job: ProjectJobInfo) -> Optional[ProjectJobInfo]:
        client = self._client
        if job.job_type is None:
            raise RuntimeError(f"ジョブ(={job.job_id})のjob_typeがありません")
        params = {"type": job.job_type.value, "limit": "200"}
        result, _ = client.get_project_job(project_id, params)
        jobs: List[afm.ProjectJobInfo] = result["list"]
        jobs2 = [self._decode_jobinfo(j) for j in jobs]

        return first_true(jobs2, pred=lambda j: j.job_id == job.job_id)

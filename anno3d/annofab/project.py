import colorsys
import logging
import random
import uuid
from dataclasses import replace
from typing import Any, Callable, Dict, List, Literal, Optional, Tuple

from annofabapi import AnnofabApi
from annofabapi import models as afm
from annofabapi.dataclass.annotation_specs import (
    AdditionalDataDefinitionV2,
    AnnotationSpecsV3,
    Color,
    InternationalizationMessage,
    InternationalizationMessageMessages,
    LabelV3,
)
from annofabapi.dataclass.job import ProjectJobInfo
from annofabapi.dataclass.project import Project
from annofabapi.models import AdditionalDataDefinitionType, DefaultAnnotationType
from more_itertools import first_true

from anno3d.annofab.constant import (
    IgnoreAdditionalDef,
    builtin_3d_editor_plugin_id,
    builtin_3d_extended_specs_plugin_id,
    default_ignore_additional,
    default_non_ignore_additional,
    lang_en,
    lang_ja,
)
from anno3d.annofab.model import AnnotationSpecsRequestV3, Label
from anno3d.annofab.specifiers.extended_specs_label_specifiers_v1 import ExtendedSpecsLabelSpecifiersV1
from anno3d.annofab.specifiers.label_specifiers import LabelSpecifiers
from anno3d.annofab.specifiers.metadata_label_specifiers import MetadataLabelSpecifiers
from anno3d.annofab.specifiers.project_specifiers import ProjectSpecifiers
from anno3d.model.annotation_area import AnnotationArea
from anno3d.model.preset_cuboids import PresetCuboidSize, PresetCuboidSizes, preset_cuboid_size_metadata_prefix
from anno3d.model.project_specs_meta import ProjectMetadata
from anno3d.util.modifier import DataModifier

logger: logging.Logger = logging.getLogger(__name__)


class ProjectModifiers:
    def __init__(self, label_specifiers: LabelSpecifiers):
        self._label_specifiers = label_specifiers

    specifiers = ProjectSpecifiers

    @property
    def extended_specs_plugin_version(self) -> Optional[str]:
        return self._label_specifiers.extended_specs_plugin_version()

    @classmethod
    def set_annotation_area(cls, area: AnnotationArea) -> DataModifier[AnnotationSpecsV3]:
        return cls.specifiers.annotation_area.mod(lambda _: area)

    @classmethod
    def remove_preset_cuboid_size(cls, key_name: str) -> DataModifier[AnnotationSpecsV3]:
        prefixed = preset_cuboid_size_metadata_prefix + key_name.title()
        return cls.specifiers.preset_cuboid_sizes.mod(
            lambda curr: dict(filter(lambda kv: kv[0] != prefixed, curr.items()))
        )

    @classmethod
    def add_preset_cuboid_size(
        cls, key_name: str, ja_name: str, en_name: str, width: float, height: float, depth: float, order: int
    ) -> DataModifier[AnnotationSpecsV3]:
        prefixed = preset_cuboid_size_metadata_prefix + key_name.title()

        def update(sizes: PresetCuboidSizes) -> PresetCuboidSizes:
            sizes.update(
                {
                    prefixed: PresetCuboidSize(
                        ja_name=ja_name, en_name=en_name, width=width, height=height, depth=depth, order=order
                    )
                }
            )
            return sizes

        return cls.specifiers.preset_cuboid_sizes.mod(update)

    def put_cuboid_label(
        self,
        en_name: str,
        label_id: str = "",
        ja_name: str = "",
        color: Optional[Tuple[int, int, int]] = None,
    ) -> DataModifier[AnnotationSpecsV3]:
        set_anno_type = self._label_specifiers.annotation_type.set("user_bounding_box")

        return self.put_label(
            en_name=en_name,
            mod_label_info=set_anno_type,
            ignore_additional=None,
            label_id=label_id,
            ja_name=ja_name,
            color=color,
        )

    def put_instance_segment_label(
        self,
        en_name: str,
        layer: int,
        default_ignore: Optional[bool] = None,
        label_id: str = "",
        ja_name: str = "",
        color: Optional[Tuple[int, int, int]] = None,
    ) -> DataModifier[AnnotationSpecsV3]:
        set_anno_type = self._label_specifiers.annotation_type.set("user_instance_segment")
        set_layer = self._label_specifiers.layer.set(layer)

        ignore_additional: Optional[IgnoreAdditionalDef]
        ignore_id: Optional[str]

        # 無視属性の追加は拡張仕様プラグインを使ってる場合は行わない
        # ここでifするの微妙だが、ProjectModifiersまで抽象化するのは手間なので、こうしておく
        if default_ignore is None or self._label_specifiers.extended_specs_plugin_version() is not None:
            ignore_additional = None
            ignore_id = None
        else:
            ignore_additional = default_ignore_additional if default_ignore else default_non_ignore_additional
            ignore_id = ignore_additional.id

        set_ignore = self._label_specifiers.ignore.set(ignore_id)

        return self.put_label(
            en_name=en_name,
            mod_label_info=set_anno_type.and_then(set_layer).and_then(set_ignore),
            ignore_additional=ignore_additional,
            label_id=label_id,
            ja_name=ja_name,
            color=color,
        )

    def put_semantic_segment_label(
        self,
        en_name: str,
        layer: int,
        default_ignore: Optional[bool] = None,
        label_id: str = "",
        ja_name: str = "",
        color: Optional[Tuple[int, int, int]] = None,
    ) -> DataModifier[AnnotationSpecsV3]:
        set_anno_type = self._label_specifiers.annotation_type.set("user_semantic_segment")
        set_layer = self._label_specifiers.layer.set(layer)

        ignore_additional: Optional[IgnoreAdditionalDef]
        ignore_id: Optional[str]

        # 無視属性の追加は拡張仕様プラグインを使ってる場合は行わない
        # ここでifするの微妙だが、ProjectModifiersまで抽象化するのは手間なので、こうしておく
        if default_ignore is None or self._label_specifiers.extended_specs_plugin_version() is not None:
            ignore_additional = None
            ignore_id = None
        else:
            ignore_additional = default_ignore_additional if default_ignore else default_non_ignore_additional
            ignore_id = ignore_additional.id

        set_ignore = self._label_specifiers.ignore.set(ignore_id)

        return self.put_label(
            en_name=en_name,
            mod_label_info=set_anno_type.and_then(set_layer).and_then(set_ignore),
            ignore_additional=ignore_additional,
            label_id=label_id,
            ja_name=ja_name,
            color=color,
        )

    def put_label(
        self,
        en_name: str,
        mod_label_info: DataModifier[LabelV3],
        ignore_additional: Optional[IgnoreAdditionalDef],
        label_id: str = "",
        ja_name: str = "",
        color: Optional[Tuple[int, int, int]] = None,
    ) -> DataModifier[AnnotationSpecsV3]:
        def init_label() -> LabelV3:
            return LabelV3(
                label_id=label_id if label_id != "" else str(uuid.uuid4()),
                label_name=InternationalizationMessage(
                    [
                        InternationalizationMessageMessages(lang_ja, label_id),
                        InternationalizationMessageMessages(lang_en, label_id),
                    ],
                    lang_ja,
                ),
                keybind=[],
                # 拡張仕様プラグインを使っている場合annotation_typeはmod_label_infoで上書きされるはず。 そうでなければそのまま
                annotation_type=DefaultAnnotationType.CUSTOM.value,
                field_values={},
                additional_data_definitions=[],
                color=Color(red=0, green=0, blue=0),
                metadata={},
            )

        def mod(label_opt: Optional[LabelV3]) -> Optional[LabelV3]:
            label = label_opt if label_opt is not None else init_label()
            label.label_name = InternationalizationMessage(
                [
                    InternationalizationMessageMessages(lang_ja, ja_name if ja_name != "" else en_name),
                    InternationalizationMessageMessages(lang_en, en_name),
                ],
                lang_ja,
            )

            if ignore_additional is not None:
                label = self._label_specifiers.additional(ignore_additional.id).set(ignore_additional.id)(label)

            if color is not None:
                label = self._label_specifiers.color.set(Color(red=color[0], green=color[1], blue=color[2]))(label)
            else:  # 明度彩度をMAXで固定しランダムに色を選ぶ
                random_color = colorsys.hsv_to_rgb(random.random(), 1, 1)

                label = self._label_specifiers.color.set(
                    Color(
                        red=round(255 * random_color[0]),
                        green=round(255 * random_color[1]),
                        blue=round(255 * random_color[2]),
                    )
                )(label)

            return mod_label_info(label)

        mod_additionals = (
            self.create_ignore_additional_if_necessary(ignore_additional)
            if ignore_additional is not None
            else DataModifier.identity(AnnotationSpecsV3)
        )

        label_specifier = self.specifiers.label(label_id)
        return label_specifier.mod(mod).and_then(mod_additionals)

    def create_ignore_additional_if_necessary(
        self, additional_def: IgnoreAdditionalDef
    ) -> DataModifier[AnnotationSpecsV3]:
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

        return self.specifiers.additional(additional_def.id).mod(mod)


class ProjectApi:
    _client: AnnofabApi

    def __init__(self, client: AnnofabApi):
        self._client = client

        # project_id -> ProjectModifiersの辞書
        self._modifiers_dic: Dict[str, ProjectModifiers] = {}

    def _project_modifiers(self, project_id: str) -> ProjectModifiers:
        current = self._modifiers_dic.get(project_id, None)
        if current is not None:
            return current

        project: Dict[str, Any]
        project, _ = self._client.get_project(project_id)
        conf: Dict[str, Any] = project["configuration"]
        specs_plugin = conf.get("extended_specs_plugin_id", None)

        # 拡張仕様プラグインが利用されているかどうかでLabelSpecifiersの実装を入れ替える
        if specs_plugin is None:
            new = ProjectModifiers(MetadataLabelSpecifiers())
        else:
            # TODO Pluginに埋まってるバージョンを読んで選択出来るようにしたい
            # 現状は、1.0.1しか無い＆pluginのdataclassが存在しないのでやってない
            new = ProjectModifiers(ExtendedSpecsLabelSpecifiersV1())
        self._modifiers_dic[project_id] = new
        return new

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
        self,
        title: str,
        organization_name: str,
        editor_plugin_id: str,
        specs_plugin_id: str,
        project_id: str = "",
        overview: str = "",
    ) -> str:
        """
        カスタムプロジェクトを作成し、作成したprojectのidを返します

        Args:

            title:
            organization_name:
            editor_plugin_id:
            specs_plugin_id:
            project_id:
            overview:

        Returns:

        """
        client = self._client

        if editor_plugin_id == "":
            editor_plugin_id = builtin_3d_editor_plugin_id
        if specs_plugin_id == "":
            specs_plugin_id = builtin_3d_extended_specs_plugin_id

        body = {
            "title": title,
            "overview": overview if len(overview) != 0 else None,
            "status": "active",
            "input_data_type": "custom",
            "organization_name": organization_name,
            "configuration": {"plugin_id": editor_plugin_id, "extended_specs_plugin_id": specs_plugin_id},
        }

        project: Dict[str, Any]
        if len(project_id) == 0:
            project_id = str(uuid.uuid4())

        project, response = client.put_project(project_id, request_body=body)
        if response.status_code != 200:
            raise RuntimeError(f"Project新規作成時のhttp status codeは200ですが、{response.status_code}が返されました。")

        created_id: str = project["project_id"]
        return created_id

    def _mod_project_specs(
        self, project_id: str, mod_func: Callable[[AnnotationSpecsV3], AnnotationSpecsV3]
    ) -> AnnotationSpecsV3:
        client = self._client

        specs = self.get_annotation_specs(project_id)
        annotation_type_version = self._project_modifiers(project_id).extended_specs_plugin_version
        new_specs = replace(mod_func(specs), annotation_type_version=annotation_type_version)
        request = AnnotationSpecsRequestV3.from_specs(new_specs)

        created_specs, _ = client.put_annotation_specs(project_id, {"v": "3"}, request.to_dict(encode_json=True))
        return AnnotationSpecsV3.from_dict(created_specs)

    def put_cuboid_label(
        self,
        project_id: str,
        en_name: str,
        label_id: str = "",
        ja_name: str = "",
        color: Optional[Tuple[int, int, int]] = None,
    ) -> List[Label]:
        mod_specs = self._project_modifiers(project_id).put_cuboid_label(
            en_name=en_name, label_id=label_id, ja_name=ja_name, color=color
        )
        return self.put_label(project_id, mod_specs)

    def put_segment_label(
        self,
        project_id: str,
        en_name: str,
        default_ignore: Optional[bool],
        segment_kind: Literal["SEMANTIC", "INSTANCE"],
        layer: int,
        ja_name: str = "",
        label_id: str = "",
        color: Optional[Tuple[int, int, int]] = None,
    ) -> List[Label]:
        """

        Args:
            project_id:
            en_name:
            default_ignore: デフォルトで無視属性をOnにするかどうか。　基本的にNone。 拡張仕様プラグインを利用しない古い仕様との互換性のために残っている
            segment_kind:
            layer:
            ja_name:
            label_id:
            color: ラベルの表示色。 "(R,G,B)"形式 R/G/Bは、それぞれ0〜255の整数値で指定する

        Returns:

        """
        modifiers = self._project_modifiers(project_id)
        if segment_kind == "SEMANTIC":
            mod_specs_f = modifiers.put_semantic_segment_label
        else:
            mod_specs_f = modifiers.put_instance_segment_label

        if default_ignore is not None and modifiers.extended_specs_plugin_version is not None:
            logger.warning("default_ignore(=%s)が指定されていますが、拡張仕様プラグインを利用したプロジェクトが対象であるため、無視します。", default_ignore)

        mod_specs = mod_specs_f(
            en_name=en_name,
            layer=layer,
            default_ignore=default_ignore,
            label_id=label_id,
            ja_name=ja_name,
            color=color,
        )
        return self.put_label(project_id, mod_specs)

    def get_annotation_specs(self, project_id: str) -> AnnotationSpecsV3:
        client = self._client
        specs, _ = client.get_annotation_specs(project_id, {"v": "3"})

        return AnnotationSpecsV3.from_dict(specs)

    @staticmethod
    def _from_annofab_label(annofab_label: afm.LabelV3) -> Label:
        messages = annofab_label["label_name"]["messages"]
        color = annofab_label["color"]
        empty_message: dict = InternationalizationMessageMessages("", "").to_dict()
        ja_name = next(filter(lambda e: e["lang"] == lang_ja, messages), empty_message)["message"]
        en_name = next(filter(lambda e: e["lang"] == lang_en, messages), empty_message)["message"]
        metadata = annofab_label["metadata"]

        return Label(
            label_id=annofab_label["label_id"],
            annotation_type=annofab_label["annotation_type"],
            ja_name=ja_name,
            en_name=en_name,
            color=(color["red"], color["green"], color["blue"]),
            field_values=annofab_label["field_values"],
            metadata=metadata,
        )

    def put_label(self, project_id: str, mod_specs: DataModifier[AnnotationSpecsV3]) -> List[Label]:
        """

        Args:
            project_id:
            mod_specs: ラベル更新を行うアノテーション仕様の変更関数

        Returns: 変更後のラベル一覧

        """

        created_specs = self._mod_project_specs(project_id, mod_specs)

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
        self,
        project_id: str,
        key_name: str,
        ja_name: str,
        en_name: str,
        width: float,
        height: float,
        depth: float,
        order: int,
    ) -> ProjectMetadata:
        new_spec = self._mod_project_specs(
            project_id, ProjectModifiers.add_preset_cuboid_size(key_name, ja_name, en_name, width, height, depth, order)
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

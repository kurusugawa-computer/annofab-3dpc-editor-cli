import typing
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Union

from annofabapi.dataclass.annotation_specs import (
    AdditionalDataDefinitionV2,
    AdditionalDataRestriction,
    AnnotationSpecsV3,
    InspectionPhrase,
    LabelV3,
)
from annofabapi.dataclass.job import ProjectJobInfo
from annofabapi.dataclass.project import Project
from annofabapi.models import AnnotationSpecsMovieOption
from dataclasses_json import DataClassJsonMixin, config
from marshmallow import fields


@dataclass
class Label(DataClassJsonMixin):
    label_id: str
    ja_name: str
    en_name: str
    color: Tuple[int, int, int] = field(
        # `Label.schema()`を実行するとエラーが発生するため、mm_fieldをした。https://github.com/lidatong/dataclasses-json/issues/318
        metadata=config(mm_field=fields.Tuple((fields.Integer(), fields.Integer(), fields.Integer())))
    )
    metadata: Dict[str, str]


@dataclass
class TaskGenerateResponse(DataClassJsonMixin):
    project: Project
    job: ProjectJobInfo


@dataclass
class XYZ(DataClassJsonMixin):
    x: float
    y: float
    z: float


@dataclass
class Size(DataClassJsonMixin):
    width: float
    height: float
    depth: float


@dataclass
class CuboidDirection(DataClassJsonMixin):
    front: XYZ
    up: XYZ


@dataclass
class CuboidShape(DataClassJsonMixin):
    """
    Args:
        rotation: EulerAngle での回転角。 適用順は z -> x -> y
    """

    dimensions: Size
    location: XYZ
    rotation: XYZ
    direction: CuboidDirection


@dataclass
class CuboidAnnotationDetailData(DataClassJsonMixin):
    shape: CuboidShape
    kind: str = "CUBOID"
    version: str = "2"


class UnknownDataField(fields.Field):
    """
    FullAnnotationDataUnknownのdataのserialize / deserialize定義
    FullAnnotationDataUnknownのdataは文字列型で、3d-editorのCuboidの場合、json形式文字列を埋めないといけないが、str型だと不便。
    なので、deup / load時に文字列との相互変換をするような定義をしておく
    """

    _type: typing.Any

    def __init__(self, cls: typing.Type, **additional_metadata) -> None:
        """

        Args:
            cls: 実際の型
            **additional_metadata:
        """

        super().__init__(**additional_metadata)
        self._type = cls

    def _serialize(self, value: typing.Any, attr: Union[str, None], obj: typing.Any, **kwargs) -> str:
        return typing.cast(str, value.to_json(ensure_ascii=False))

    def _deserialize(
        self, value: str, attr: Union[str, None], data: Union[typing.Mapping[str, typing.Any], None], **kwargs
    ) -> typing.Any:
        return self._type.from_json(str)


@dataclass
class CuboidFullAnnotationData(DataClassJsonMixin):
    data: CuboidAnnotationDetailData = field(metadata=config(mm_field=UnknownDataField(CuboidAnnotationDetailData)))
    _type: str = "Unknown"


@dataclass
class CuboidAnnotationDetailBody(DataClassJsonMixin):
    """Cuboid用 AnnotationDetailContentInputInner"""

    data: CuboidFullAnnotationData
    _type: str = "Inner"

    @classmethod
    def from_detail_data(cls, data: CuboidAnnotationDetailData) -> "CuboidAnnotationDetailBody":
        return CuboidAnnotationDetailBody(data=CuboidFullAnnotationData(data=data))

    @classmethod
    def from_shape(cls, shape: CuboidShape) -> "CuboidAnnotationDetailBody":
        return cls.from_detail_data(CuboidAnnotationDetailData(shape))


@dataclass
class AnnotationPropsForEditor:
    can_delete: bool


@dataclass
class CuboidAnnotationDetailCreate(DataClassJsonMixin):
    """Cuboid用AnnotationDetailV2Createに対応する型"""

    annotation_id: str
    label_id: str
    body: CuboidAnnotationDetailBody
    editor_props: AnnotationPropsForEditor
    _type: str = "Create"


@dataclass
class CuboidAnnotations(DataClassJsonMixin):
    """CLIからCuboidAnnotationを生成する場合に利用する AnnotationV2Input"""

    project_id: str
    task_id: str
    input_data_id: str
    details: List[CuboidAnnotationDetailCreate]
    additional_data_list: list = field(default_factory=list)  # 型を定義してないので空を前提としておく
    format_version: str = "2.0.0"


@dataclass
class AnnotationSpecsRequestV3(DataClassJsonMixin):
    labels: List[LabelV3]
    additionals: List[AdditionalDataDefinitionV2]
    restrictions: List[AdditionalDataRestriction]
    inspection_phrases: List[InspectionPhrase]
    comment: str
    auto_marking: bool
    format_version: str
    last_updated_datetime: Optional[str]
    option: Union[AnnotationSpecsMovieOption, None]
    metadata: Optional[Dict[str, str]]

    @staticmethod
    def from_specs(specs: AnnotationSpecsV3) -> "AnnotationSpecsRequestV3":
        return AnnotationSpecsRequestV3(
            labels=specs.labels if specs.labels is not None else [],
            additionals=specs.additionals if specs.additionals is not None else [],
            restrictions=specs.restrictions if specs.restrictions is not None else [],
            inspection_phrases=specs.inspection_phrases if specs.inspection_phrases is not None else [],
            comment="",
            auto_marking=False,
            format_version=specs.format_version if specs.format_version is not None else "3.0.0",
            last_updated_datetime=specs.updated_datetime,
            option=specs.option,
            metadata=specs.metadata,
        )

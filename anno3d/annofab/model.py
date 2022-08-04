from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Union

from annofabapi.dataclass.annotation_specs import (
    AdditionalDataDefinitionV2,
    AdditionalDataRestriction,
    AnnotationSpecsV2,
    InspectionPhrase,
    LabelV2,
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


@dataclass
class CuboidAnnotationDetail(DataClassJsonMixin):
    annotation_id: str
    account_id: str
    label_id: str
    is_protected: bool
    data: CuboidAnnotationDetailData
    data_holding_type: str = "inner"


@dataclass
class CuboidAnnotations(DataClassJsonMixin):
    project_id: str
    task_id: str
    input_data_id: str
    details: List[CuboidAnnotationDetail]


@dataclass
class AnnotationSpecsRequestV2(DataClassJsonMixin):
    labels: List[LabelV2]
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
    def from_specs(specs: AnnotationSpecsV2) -> "AnnotationSpecsRequestV2":
        return AnnotationSpecsRequestV2(
            labels=specs.labels if specs.labels is not None else [],
            additionals=specs.additionals if specs.additionals is not None else [],
            restrictions=specs.restrictions if specs.restrictions is not None else [],
            inspection_phrases=specs.inspection_phrases if specs.inspection_phrases is not None else [],
            comment="",
            auto_marking=False,
            format_version=specs.format_version if specs.format_version is not None else "2.1.0",
            last_updated_datetime=specs.updated_datetime,
            option=specs.option,
            metadata=specs.metadata,
        )

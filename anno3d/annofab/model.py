from dataclasses import dataclass
from typing import Dict, List, Tuple

from annofabapi.dataclass.job import JobInfo
from annofabapi.dataclass.project import Project
from dataclasses_json import DataClassJsonMixin


@dataclass
class Label(DataClassJsonMixin):
    label_id: str
    ja_name: str
    en_name: str
    color: Tuple[int, int, int]
    metadata: Dict[str, str]


@dataclass
class TaskGenerateResponse(DataClassJsonMixin):
    project: Project
    job: JobInfo


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
class CuboidShape(DataClassJsonMixin):
    """
    Args:
        rotation: EulerAngle での回転角。 適用順は z -> x -> y
    """

    dimensions: Size
    location: XYZ
    rotation: XYZ


@dataclass
class CuboidAnnotationDetailData(DataClassJsonMixin):
    shape: CuboidShape
    kind: str = "CUBOID"


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

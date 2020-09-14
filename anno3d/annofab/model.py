from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Tuple, Type, TypeVar

from annofabapi.dataclass.job import JobInfo
from annofabapi.dataclass.project import Project
from dataclasses_json import DataClassJsonMixin

E = TypeVar("E", bound=Enum)


def _decode_enum(enum: Type[E], value: Any) -> E:
    for e in enum:
        if e == value:
            return e

    raise ValueError("{}は有効な、{}型の値ではありません".format(value, enum.__name__))


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
class XYZ:
    x: float
    y: float
    z: float


@dataclass
class Size:
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
    data: List[CuboidAnnotationDetailData]
    data_holding_type: str = "inner"

from dataclasses import dataclass
from typing import Dict, Union

from dataclasses_json import DataClassJsonMixin

from anno3d.model.common import camelcase

annotation_area_metadata_prefix = "area"


@camelcase
@dataclass(frozen=True)
class WholeAnnotationAreaV1(DataClassJsonMixin):
    area_kind: str = "whole"


WholeAnnotationArea = WholeAnnotationAreaV1


@camelcase
@dataclass(frozen=True)
class SphereAnnotationAreaV1(DataClassJsonMixin):
    area_radius: str
    area_kind: str = "sphere"


SphereAnnotationArea = SphereAnnotationAreaV1


@camelcase
@dataclass(frozen=True)
class RectAnnotationAreaV1(DataClassJsonMixin):
    area_max_x: str
    area_max_y: str
    area_min_x: str
    area_min_y: str
    area_kind: str = "rect"


RectAnnotationArea = RectAnnotationAreaV1

AnnotationAreaV1 = Union[WholeAnnotationAreaV1, SphereAnnotationAreaV1, RectAnnotationAreaV1]

AnnotationArea = Union[WholeAnnotationArea, SphereAnnotationArea, RectAnnotationArea]


def decode_area_from_v1(data: Dict[str, str]) -> AnnotationArea:
    kind = data["areaKind"]
    if kind == "whole":
        return WholeAnnotationArea()
    elif kind == "sphere":
        return SphereAnnotationAreaV1.from_dict(data)
    elif kind == "rect":
        return RectAnnotationAreaV1.from_dict(data)
    else:
        raise RuntimeError(f"areaKindが、ありえない値(={kind})でした")


def decode_area_from_v2(data: Dict[str, str]) -> AnnotationArea:
    filtered = dict(filter(lambda kv: kv[0].startswith(annotation_area_metadata_prefix), data.items()))
    return decode_area_from_v1(filtered)

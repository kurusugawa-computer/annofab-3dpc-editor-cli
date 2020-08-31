from dataclasses import dataclass

from dataclasses_json import DataClassJsonMixin

from anno3d.model.common import pascalcase


@pascalcase
@dataclass(frozen=True)
class CuboidLabelMetadata(DataClassJsonMixin):
    type: str = "CUBOID"


@pascalcase
@dataclass(frozen=True)
class SegmentLabelMetadata(DataClassJsonMixin):
    """
    Args:
        default_ignore: "true" or "false"
        layer: レイヤーを表す数値文字列
        segment_kind: "SEMANTIC" | "INSTANCE"
        type: "SEGMENT" 固定
    """

    default_ignore: str
    layer: str = "100"
    segment_kind: str = "SEMANTIC"
    type: str = "SEGMENT"
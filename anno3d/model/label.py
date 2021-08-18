from dataclasses import dataclass

from dataclasses_json import DataClassJsonMixin

from anno3d.model.common import camelcase


@camelcase
@dataclass(frozen=True)
class CuboidLabelMetadata(DataClassJsonMixin):
    type: str = "CUBOID"


@camelcase
@dataclass(frozen=True)
class SegmentLabelMetadata(DataClassJsonMixin):
    """
    Args:
        ignore: ignore設定に利用するAdditionalDataのid
        layer: レイヤーを表す数値文字列
        segment_kind: "SEMANTIC" | "INSTANCE"
        type: "SEGMENT" 固定
    """

    ignore: str
    layer: str = "100"
    segment_kind: str = "SEMANTIC"
    type: str = "SEGMENT"
    version: str = "1"

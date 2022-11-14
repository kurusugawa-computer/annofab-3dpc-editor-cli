from dataclasses import dataclass
from typing import Optional

from dataclasses_json import DataClassJsonMixin

from anno3d.model.common import camelcase


@camelcase
@dataclass(frozen=True)
class CuboidLabelInfo(DataClassJsonMixin):
    """アノテーション仕様のうちCuboid用の部分。 現状存在しないので空"""


@camelcase
@dataclass(frozen=True)
class SegmentLabelInfo(DataClassJsonMixin):
    """
    アノテーション仕様のうちSegment用部分

    Args:
        ignore: ignore設定に利用するAdditionalDataのid。 通常None。 拡張仕様プラグインを利用しない、古い仕様の場合のみSome
        layer: レイヤーを表す数値。 0以上の整数
    """

    ignore: Optional[str] = None
    layer: int = 100

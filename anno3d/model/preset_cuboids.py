from dataclasses import dataclass
from typing import Dict

from dataclasses_json import DataClassJsonMixin

from anno3d.model.common import camelcase

preset_cuboid_size_metadata_prefix = "presetCuboidSize"


@camelcase
@dataclass(frozen=True)
class PresetCuboidSizeV2(DataClassJsonMixin):
    ja_name: str
    en_name: str
    width: float
    """y方向の幅"""
    height: float
    """z方向の幅"""
    depth: float
    """x方向の幅"""
    order: int


PresetCuboidSize = PresetCuboidSizeV2
PresetCuboidSizes = Dict[str, PresetCuboidSize]


def decode_preset_cuboid_sizes_from_v2(data: Dict[str, str]) -> PresetCuboidSizes:
    filtered = dict(filter(lambda kv: kv[0].startswith(preset_cuboid_size_metadata_prefix), data.items()))
    return dict(map(lambda kv: (kv[0], PresetCuboidSize.from_json(kv[1])), filtered.items()))

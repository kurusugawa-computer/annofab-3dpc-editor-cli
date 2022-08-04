from dataclasses import dataclass
from typing import Dict

from dataclasses_json import DataClassJsonMixin

from anno3d.model.annotation_area import AnnotationArea, WholeAnnotationArea, decode_area_from_v1, decode_area_from_v2
from anno3d.model.common import camelcase
from anno3d.model.preset_cuboids import PresetCuboidSizes, decode_preset_cuboid_sizes_from_v2


@camelcase
@dataclass(frozen=True)
class ProjectMetadataVersion(DataClassJsonMixin):
    version: str = "2"


@camelcase
@dataclass(frozen=True)
class ProjectMetadata(DataClassJsonMixin):
    annotation_area: AnnotationArea
    preset_cuboid_sizes: PresetCuboidSizes
    version: ProjectMetadataVersion = ProjectMetadataVersion()


def decode_project_meta_from_v0(data: Dict[str, str]) -> ProjectMetadata:  # pylint: disable=unused-argument
    return ProjectMetadata(annotation_area=WholeAnnotationArea(), preset_cuboid_sizes={})


def decode_project_meta_from_v1(data: Dict[str, str]) -> ProjectMetadata:
    return ProjectMetadata(annotation_area=decode_area_from_v1(data), preset_cuboid_sizes={})


def decode_project_meta_from_v2(data: Dict[str, str]) -> ProjectMetadata:
    return ProjectMetadata(
        annotation_area=decode_area_from_v2(data), preset_cuboid_sizes=decode_preset_cuboid_sizes_from_v2(data)
    )


def decode_project_meta(data: Dict[str, str]) -> ProjectMetadata:
    version = data.get("version", "0")
    if version == "0":
        return decode_project_meta_from_v0(data)
    elif version == "1":
        return decode_project_meta_from_v1(data)
    elif version == "2":
        return decode_project_meta_from_v2(data)
    else:
        raise RuntimeError(f"アノテーション仕様のメタデータバージョンが、ありえない値(={version})でした")


def encode_project_meta(meta: ProjectMetadata) -> Dict[str, str]:
    version_dict: dict = meta.version.to_dict(encode_json=True)
    area_dict: dict = meta.annotation_area.to_dict(encode_json=True)
    preset_cuboid_sizes_dict: dict = dict(
        map(lambda kv: (kv[0], kv[1].to_json(ensure_ascii=False)), meta.preset_cuboid_sizes.items())
    )

    return {**version_dict, **area_dict, **preset_cuboid_sizes_dict}

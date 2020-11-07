from dataclasses import dataclass
from typing import Dict

from dataclasses_json import DataClassJsonMixin

from anno3d.model.annotation_area import AnnotationArea, WholeAnnotationArea, decode_area_from_v1
from anno3d.model.common import pascalcase


@pascalcase
@dataclass(frozen=True)
class ProjectMetadataVersion(DataClassJsonMixin):
    version: str = "1"


@dataclass(frozen=True)
class ProjectMetadata:
    annotation_area: AnnotationArea
    version: ProjectMetadataVersion = ProjectMetadataVersion()


def decode_project_meta_from_v0(data: Dict[str, str]) -> ProjectMetadata:  # pylint: disable=unused-argument
    return ProjectMetadata(annotation_area=WholeAnnotationArea())


def decode_project_meta_from_v1(data: Dict[str, str]) -> ProjectMetadata:
    return ProjectMetadata(annotation_area=decode_area_from_v1(data))


def decode_project_meta(data: Dict[str, str]) -> ProjectMetadata:
    version = data.get("version", "0")
    if version == "0":
        return decode_project_meta_from_v0(data)
    elif version == "1":
        return decode_project_meta_from_v1(data)
    else:
        raise RuntimeError("アノテーション仕様のメタデータバージョンが、ありえない値(={})でした".format(version))


def encode_project_meta(meta: ProjectMetadata) -> Dict[str, str]:
    version_dict: dict = meta.version.to_dict(encode_json=True)
    area_dict: dict = meta.annotation_area.to_dict(encode_json=True)

    return {**version_dict, **area_dict}

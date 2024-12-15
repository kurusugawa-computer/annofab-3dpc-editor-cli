from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import List, Optional

from anno3d.model.scene import CameraViewSettings


class FrameKind(Enum):
    training = "training"
    testing = "testing"


@dataclass(frozen=True)
class FrameKey:
    kind: Optional[FrameKind]
    id: str


@dataclass(frozen=True)
class ImagePaths:
    image: Path
    extension: str
    calib: Optional[Path]
    camera_settings: Optional[CameraViewSettings]
    name: Optional[str]


@dataclass(frozen=True)
class LabelPaths:
    label: Path
    calib: Path


@dataclass(frozen=True)
class FilePaths:
    key: FrameKey
    pcd: Path
    images: List[ImagePaths]
    labels: List[LabelPaths]


def filepaths_to_image_names(data: FilePaths, dummy: List[Path]) -> List[str]:
    result = []
    names_set = set()
    for i, d in enumerate(data.images, start=1):
        if d.name and d.name not in names_set:
            result.append(d.name)
            names_set.add(d.name)
        else:
            result.append(str(i))
    result.extend(map(str, range(len(data.images) + 1, len(data.images) + len(dummy) + 1)))

    return result

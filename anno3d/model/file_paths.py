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
    calib: Optional[Path]
    camera_settings: Optional[CameraViewSettings]


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

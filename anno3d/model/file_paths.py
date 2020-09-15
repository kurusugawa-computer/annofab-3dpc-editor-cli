from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional, List


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
    calib: Path


@dataclass(frozen=True)
class LabelPaths:
    label: Path
    image: Path
    calib: Path


@dataclass(frozen=True)
class FilePaths:
    key: FrameKey
    pcd: Path
    images: List[ImagePaths]
    labels: List[LabelPaths]

from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class FrameKind(Enum):
    training = "training"
    testing = "testing"


@dataclass(frozen=True)
class FrameKey:
    kind: FrameKind
    id: str


@dataclass(frozen=True)
class FilePaths:
    key: FrameKey
    pcd: Path
    image: Path
    calib: Path

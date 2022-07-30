from dataclasses import dataclass
from typing import List, Optional

from dataclasses_json import DataClassJsonMixin

from anno3d.model.common import Vector3, camelcase


@camelcase
@dataclass(frozen=True)
class ImageCameraFov(DataClassJsonMixin):
    horizontal: float
    vertical: float


@camelcase
@dataclass(frozen=True)
class ImageCamera(DataClassJsonMixin):
    direction: Vector3
    fov: ImageCameraFov
    camera_position: Vector3


@camelcase
@dataclass(frozen=True)
class kitti3DCalib(DataClassJsonMixin):
    # 4x3行列 (P2)
    camera_matrix: List[float]

    # 3x3行列 R0_rect
    r0_matrix: List[float]

    # 3x4行列 Tr_velo_to_cam
    velo_cam_matrix: List[float]

    kind: str = "kitti3dDetection"


@camelcase
@dataclass(frozen=True)
class ImageMeta(DataClassJsonMixin):
    """画像ごとに存在するメタデータ"""

    calib: Optional[kitti3DCalib]
    camera: ImageCamera
    version: str = "2"

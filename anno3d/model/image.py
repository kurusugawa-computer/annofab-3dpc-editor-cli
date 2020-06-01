from dataclasses import dataclass
from typing import List

from dataclasses_json import DataClassJsonMixin

from anno3d.model.common import Vector3, pascalcase


@pascalcase
@dataclass(frozen=True)
class ImageCameraFov(DataClassJsonMixin):
    horizontal: float
    vertical: float


@pascalcase
@dataclass(frozen=True)
class ImageCamera(DataClassJsonMixin):
    direction: Vector3
    fov: ImageCameraFov
    camera_height: float


@pascalcase
@dataclass(frozen=True)
class kitti3DCalib(DataClassJsonMixin):
    # 4x3行列 (P2)
    camera_matrix: List[float]

    # 3x3行列 R0_rect
    r0_matrix: List[float]

    # 3x4行列 Tr_velo_to_cam
    velo_cam_matrix: List[float]

    kind: str = "kitti3dDetection"


@pascalcase
@dataclass(frozen=True)
class ImageMeta(DataClassJsonMixin):
    """ 画像ごとに存在するメタデータ """

    calib: kitti3DCalib
    camera: ImageCamera

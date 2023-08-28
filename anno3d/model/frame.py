from dataclasses import dataclass
from typing import Literal

from dataclasses_json import DataClassJsonMixin

from anno3d.model.common import Vector3, camelcase


@camelcase
@dataclass(frozen=True)
class PcdFormat(DataClassJsonMixin):
    """
    本質的には xyziとxyzirgbは別の型だが、今の定義は統一して表現できるので同居させている
    """

    format: Literal["xyzi", "xyzirgb"]


@camelcase
@dataclass(frozen=True)
class PointCloudMetaData(DataClassJsonMixin):
    is_rightHand_system: bool
    up_vector: Vector3
    sensor_height: float
    format: PcdFormat


@camelcase
@dataclass(frozen=True)
class ImagesMetaData(DataClassJsonMixin):
    image_count: int
    calib_kind: str = "kitti3dDetection"


@camelcase
@dataclass(frozen=True)
class FrameMetaData(DataClassJsonMixin):
    """フレームごとに存在するメタデータ"""

    points: PointCloudMetaData
    images: ImagesMetaData
    version: Literal["2"] = "2"

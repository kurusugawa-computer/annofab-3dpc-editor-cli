from dataclasses import dataclass

from dataclasses_json import DataClassJsonMixin

from anno3d.model.common import Vector3, pascalcase


@pascalcase
@dataclass(frozen=True)
class PointCloudMetaData(DataClassJsonMixin):
    is_rightHand_system: bool
    up_vector: Vector3
    sensor_height: float


@pascalcase
@dataclass(frozen=True)
class ImagesMetaData(DataClassJsonMixin):
    image_count: int
    calib_kind: str = "kitti3dDetection"


@pascalcase
@dataclass(frozen=True)
class FrameMetaData(DataClassJsonMixin):
    """ フレームごとに存在するメタデータ """

    points: PointCloudMetaData
    images: ImagesMetaData

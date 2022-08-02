import math
from abc import ABC
from enum import Enum
from typing import Optional

from anno3d.kitti.calib import read_calibration
from anno3d.model.file_paths import ImagePaths
from anno3d.util.value_provider import ConstValueProvider, ValueProvider

CameraHorizontalFovProvider = ValueProvider[float]


class AbstractCameraHorizontalFovProvider(ABC, ValueProvider[float]):
    """
    カメラの水平方向視野角を[rad]で取得するValueProviderです
    """

    def __init__(self):
        super().__init__("水平方向視野角")


class CalibCameraHorizontalFovProvider(AbstractCameraHorizontalFovProvider):
    def __init__(self, paths: ImagePaths):
        super().__init__()
        self._paths = paths

    def value_opt(self) -> Optional[float]:
        calib_path = self._paths.calib
        if calib_path is None:
            return None

        calib = read_calibration(calib_path)
        return calib.camera_horizontal_fov


class SettingsCameraHorizontalFovProvider(AbstractCameraHorizontalFovProvider):
    def __init__(self, paths: ImagePaths):
        super().__init__()
        self._paths = paths

    def value_opt(self) -> Optional[float]:
        if self._paths.camera_settings is None:
            return None
        return self._paths.camera_settings.fov


class CameraHorizontalFovKind(Enum):
    """
    SETTINGS => camera_view_settingが存在していればその値を利用し、無ければ"calib"と同様
    CALIB => キャリブレーションデータが存在すればそこから計算し、なければ fallback_fov とする
    """

    SETTINGS = "settings"
    CALIB = "calib"


def create_camera_horizontal_fov_provider(
    kind: CameraHorizontalFovKind, paths: ImagePaths, fallback: Optional[int]
) -> ValueProvider[float]:
    """

    Args:
        kind:
        paths:
        fallback: 値が決められなかった場合に返す水平視野角[degree]。 Noneの場合は90

    Returns:

    """
    # http://www.cvlibs.net/publications/Geiger2012CVPR.pdf 2.1. Sensors and Data Acquisition によると
    # カメラの画角は 90度 * 35度　らしい
    fallback_rad = math.radians(fallback if fallback is not None else 90)
    fallback_fov = ConstValueProvider("水平視野角", fallback_rad)
    calib_fov = CalibCameraHorizontalFovProvider(paths).or_else(fallback_fov)
    if kind == CameraHorizontalFovKind.SETTINGS:
        return SettingsCameraHorizontalFovProvider(paths).or_else(calib_fov)
    elif kind == CameraHorizontalFovKind.CALIB:
        return calib_fov
    else:
        raise RuntimeError(f"kind(={kind}) が不正な値です")

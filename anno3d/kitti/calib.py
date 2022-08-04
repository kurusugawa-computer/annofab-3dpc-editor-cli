import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import List

import numpy as np

from anno3d.model.kitti_label import KittiLabel


# https://kurusugawa.jp/confluence/pages/viewpage.action?pageId=1123123957
# ↑からコピーして書き換えた
@dataclass
class Calib:
    P0: np.ndarray
    R0_rect: np.ndarray
    V2C: np.ndarray
    V2C_R: np.ndarray = field(init=False)
    V2C_t: np.ndarray = field(init=False)
    camera_horizontal_fov: float = field(init=False)

    def __post_init__(self):
        self.V2C_R = self.V2C[:, :3]
        self.V2C_t = self.V2C[:, 3]
        self.camera_horizontal_fov = math.atan(self.P0[0, 2] / self.P0[0, 0]) * 2


# calibデータの読み込み部
def read_calibration(file_path: Path) -> Calib:
    with open(file_path, "r", encoding="utf-8") as f:
        lines = list(f.readlines())
        # P0
        line_p0 = next(filter(lambda x: "P2" in x, lines))
        p0 = np.array(line_p0.split(": ")[1].split(" "), dtype=np.float32).reshape((3, 4))
        # R0_rect
        line_r0_rect = next(filter(lambda x: "R0_rect" in x, lines))
        r0_rect = np.array(line_r0_rect.split(": ")[1].split(" "), dtype=np.float32).reshape((3, 3))
        # Tr_velo_to_cam
        line_v2c = next(filter(lambda x: "Tr_velo_to_cam" in x, lines))
        tr_velo_to_cam = np.array(line_v2c.split(": ")[1].split(" "), dtype=np.float32).reshape((3, 4))
    return Calib(P0=p0, R0_rect=r0_rect, V2C=tr_velo_to_cam)


# 座標変換
def transform_labels_into_lidar_coordinates(labels: List[KittiLabel], calib: Calib) -> List[KittiLabel]:
    """
    Args
        labels:
        calib:
    """
    transformed: List[KittiLabel] = []
    for label in labels:
        xyz = np.array([label.x, label.y, label.z])
        _xyz = np.dot(np.linalg.inv(calib.V2C_R), xyz.T - calib.V2C_t)
        _yaw = -label.yaw - np.pi / 2.0
        while _yaw < -np.pi:
            _yaw += np.pi * 2
        while _yaw > np.pi:
            _yaw -= np.pi * 2

        # new_label = Label3D(xyz=_xyz, dwh=label.dwh, yaw=_yaw, category=label.category, bbox2d=label.bbox2d)
        new_label = KittiLabel(
            type=label.type,
            height=label.height,
            width=label.width,
            depth=label.depth,
            x=_xyz[0],
            y=_xyz[1],
            z=_xyz[2],
            yaw=_yaw,
            annotation_id=label.annotation_id,
        )
        transformed.append(new_label)

    return transformed

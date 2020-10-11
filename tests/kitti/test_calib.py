import math
from pathlib import Path

from anno3d.kitti.calib import read_calibration

test_ressources_path = Path(__file__).parent.parent / "resources" / "tm20_calib.txt"


def test_read_calib():
    calib = read_calibration(test_ressources_path)
    fov_degree = calib.camera_horizontal_fov * 180 / math.pi

    assert fov_degree > 46
    assert fov_degree < 48

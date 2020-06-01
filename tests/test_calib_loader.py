from pathlib import Path

from anno3d.calib_loader import read_kitti_calib

test_ressources_path = Path(__file__).parent / "resources" / "kitti_calib.txt"


def test_read_kitti_calib():
    calib = read_kitti_calib(test_ressources_path)

    assert len(calib.camera_matrix) == 4 * 3
    assert calib.camera_matrix[0] == 721.5377
    assert calib.camera_matrix[9] == 0.0
    assert calib.camera_matrix[10] == 1.0
    assert calib.camera_matrix[11] == 2.745884000000e-03

    assert len(calib.r0_matrix) == 3 * 3
    assert calib.r0_matrix[0] == 9.999239000000e-01
    assert calib.r0_matrix[8] == 9.999631000000e-01

    assert len(calib.velo_cam_matrix) == 3 * 4
    assert calib.velo_cam_matrix[0] == 7.533745000000e-03
    assert calib.velo_cam_matrix[11] == -2.717806000000e-01

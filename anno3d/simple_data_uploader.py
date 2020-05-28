import math
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import List

from anno3d.annofab.uploader import Uploader
from anno3d.calib_loader import read_kitty_calib
from anno3d.model.common import Vector3
from anno3d.model.file_paths import FilePaths
from anno3d.model.frame import FrameMetaData, ImagesMetaData, PointCloudMetaData
from anno3d.model.image import ImageCamera, ImageCameraFov, ImageMeta
from anno3d.supplementary_id import camera_image_calib_id, camera_image_id, frame_meta_id


@dataclass
class SupplementaryData:
    data_id: str
    path: Path


def _create_frame_meta(parent_dir: Path, input_data_id: str) -> SupplementaryData:
    data_id = frame_meta_id(input_data_id)

    meta = FrameMetaData(
        PointCloudMetaData(is_rightHand_system=True, up_vector=Vector3(0, 0, 1), sensor_height=1.73),
        ImagesMetaData(image_count=1),
    )

    file = parent_dir / data_id
    with file.open("w", encoding="UTF-8") as writer:
        writer.write(meta.to_json(ensure_ascii=False, indent=3))

    return SupplementaryData(data_id, file)


def _create_image_meta(parent_dir: Path, calib_path: Path, input_data_id: str, number: int) -> SupplementaryData:
    data_id = camera_image_calib_id(input_data_id, number)

    # http://www.cvlibs.net/publications/Geiger2012CVPR.pdf 2.1. Sensors and Data Acquisition によると
    # カメラの画角は 90度 * 35度　らしい
    meta = ImageMeta(
        read_kitty_calib(calib_path),
        ImageCamera(
            direction=Vector3(1, 0, 0),
            fov=ImageCameraFov(90.0 / 180.0 * math.pi, 35.0 / 180.0 * math.pi),
            camera_height=1.65,
        ),
    )

    file = parent_dir / data_id
    with file.open("w", encoding="UTF-8") as writer:
        writer.write(meta.to_json(ensure_ascii=False, indent=3))

    return SupplementaryData(data_id, file)


def _upload_supplementaries(
    uploader: Uploader, input_data_id: str, supplementary_list: List[SupplementaryData]
) -> None:
    for supp in supplementary_list:
        uploader.upload_supplementary(input_data_id, supp.data_id, supp.path)


def upload(uploader: Uploader, paths: FilePaths) -> None:
    input_data_id = uploader.upload_input_data(paths.pcd)

    with tempfile.TemporaryDirectory() as tempdir_str:
        tempdir = Path(tempdir_str)
        frame_meta = _create_frame_meta(tempdir, input_data_id)
        image = SupplementaryData(camera_image_id(input_data_id, 0), paths.image)
        image_meta = _create_image_meta(tempdir, paths.calib, input_data_id, 0)
        _upload_supplementaries(uploader, input_data_id, [frame_meta, image, image_meta])


def create_meta_file(parent_dir: Path, paths: FilePaths) -> None:
    _create_frame_meta(parent_dir, "sample_input_id")
    _create_image_meta(parent_dir, paths.calib, "sample_input_id", 0)

import logging
import math
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple

from anno3d.annofab.uploader import Uploader
from anno3d.calib_loader import read_kitti_calib
from anno3d.model.common import Vector3
from anno3d.model.file_paths import FilePaths
from anno3d.model.frame import FrameMetaData, ImagesMetaData, PointCloudMetaData
from anno3d.model.image import ImageCamera, ImageCameraFov, ImageMeta
from anno3d.supplementary_id import camera_image_calib_id, camera_image_id, frame_meta_id

logger = logging.getLogger(__name__)


@dataclass
class SupplementaryData:
    data_id: str
    path: Path


def _create_frame_meta(parent_dir: Path, input_data_id: str, image_count: int) -> SupplementaryData:
    data_id = frame_meta_id(input_data_id)

    meta = FrameMetaData(
        PointCloudMetaData(is_rightHand_system=True, up_vector=Vector3(0, 0, 1), sensor_height=1.73),
        ImagesMetaData(image_count=image_count),
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
        read_kitti_calib(calib_path),
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


def _create_dummy_image_meta(parent_dir: Path, input_data_id: str, number: int) -> SupplementaryData:
    data_id = camera_image_calib_id(input_data_id, number)

    num = number % 4
    y = -1 if num % 2 == 0 else 1
    x = 0 if num / 2 <= 1 else -1

    meta = ImageMeta(
        None,
        ImageCamera(
            direction=Vector3(x, y, 0),
            fov=ImageCameraFov(60.0 / 180.0 * math.pi, 35.0 / 180.0 * math.pi),
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


def upload(
    input_data_id_prefix: str, uploader: Uploader, paths: FilePaths, dummy_images: List[Path]
) -> Tuple[str, List[SupplementaryData]]:
    input_data_id = uploader.upload_input_data("{}_{}".format(input_data_id_prefix, paths.key.id), paths.pcd)

    with tempfile.TemporaryDirectory() as tempdir_str:
        tempdir = Path(tempdir_str)
        frame_meta = _create_frame_meta(tempdir, input_data_id, len(dummy_images) + 1)
        image = SupplementaryData(camera_image_id(input_data_id, 0), paths.image)
        image_meta = _create_image_meta(tempdir, paths.calib, input_data_id, 0)
        dummy_image_supps = [
            meta
            for i in range(1, len(dummy_images) + 1)
            for meta in [
                _create_dummy_image_meta(tempdir, input_data_id, i),
                SupplementaryData(camera_image_id(input_data_id, i), dummy_images[i - 1]),
            ]
        ]

        all_supps = dummy_image_supps + [frame_meta, image, image_meta]
        _upload_supplementaries(uploader, input_data_id, all_supps)

        logger.info("uploaded: %s", paths.pcd)
        return input_data_id, all_supps


def create_meta_file(parent_dir: Path, paths: FilePaths) -> None:
    _create_frame_meta(parent_dir, "sample_input_id", 2)
    _create_image_meta(parent_dir, paths.calib, "sample_input_id", 0)
    _create_dummy_image_meta(parent_dir, "sample_input_id", 1)

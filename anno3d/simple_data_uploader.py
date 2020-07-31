import logging
import math
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

from anno3d.annofab.uploader import Uploader
from anno3d.calib_loader import read_kitti_calib
from anno3d.model.common import Vector3
from anno3d.model.file_paths import FilePaths
from anno3d.model.frame import FrameMetaData, ImagesMetaData, PointCloudMetaData
from anno3d.model.image import ImageCamera, ImageCameraFov, ImageMeta
from anno3d.model.input_files import InputData, InputDataBody, Supplementary, SupplementaryBody
from anno3d.supplementary_id import camera_image_calib_id, camera_image_id, frame_meta_id

logger = logging.getLogger(__name__)


@dataclass
class SupplementaryData:
    data_id: str
    path: Path


def create_frame_meta(
    parent_dir: Path, input_data_id: str, image_count: int, sensor_height: Optional[float]
) -> SupplementaryData:
    data_id = frame_meta_id(input_data_id)
    # http://www.cvlibs.net/datasets/kitti/setup.php によると、kittiのvelodyneの設置高は1.73m
    height = sensor_height if sensor_height else 1.73

    meta = FrameMetaData(
        PointCloudMetaData(is_rightHand_system=True, up_vector=Vector3(0, 0, 1), sensor_height=height),
        ImagesMetaData(image_count=image_count),
    )

    file = parent_dir / data_id
    with file.open("w", encoding="UTF-8") as writer:
        writer.write(meta.to_json(ensure_ascii=False, indent=3))

    return SupplementaryData(data_id, file)


def _create_image_meta(
    parent_dir: Path, calib_path: Path, input_data_id: str, number: int, camera_horizontal_fov: Optional[int]
) -> SupplementaryData:
    """

    Args:
        parent_dir:
        calib_path:
        input_data_id:
        number:
        camera_horizontal_fov: カメラの水平方向視野角 [degree]。

    Returns:

    """
    data_id = camera_image_calib_id(input_data_id, number)

    # http://www.cvlibs.net/publications/Geiger2012CVPR.pdf 2.1. Sensors and Data Acquisition によると
    # カメラの画角は 90度 * 35度　らしい
    horizontal_fov = camera_horizontal_fov if camera_horizontal_fov else 90
    meta = ImageMeta(
        read_kitti_calib(calib_path),
        ImageCamera(
            direction=Vector3(1, 0, 0),
            fov=ImageCameraFov(horizontal_fov / 180.0 * math.pi, 35.0 / 180.0 * math.pi),
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
    input_data_id_prefix: str,
    uploader: Uploader,
    paths: FilePaths,
    dummy_images: List[Path],
    camera_horizontal_fov: Optional[int],
    sensor_height: Optional[float],
) -> Tuple[str, List[SupplementaryData]]:
    input_data_id_prefix = input_data_id_prefix + "_" if input_data_id_prefix else ""
    input_data_id = uploader.upload_input_data("{}{}".format(input_data_id_prefix, paths.key.id), paths.pcd)

    with tempfile.TemporaryDirectory() as tempdir_str:
        tempdir = Path(tempdir_str)
        frame_meta = create_frame_meta(tempdir, input_data_id, len(dummy_images) + 1, sensor_height)
        image = SupplementaryData(camera_image_id(input_data_id, 0), paths.image)
        image_meta = _create_image_meta(tempdir, paths.calib, input_data_id, 0, camera_horizontal_fov)
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
    create_frame_meta(parent_dir, "sample_input_id", 2, None)
    _create_image_meta(parent_dir, paths.calib, "sample_input_id", 0, None)
    _create_dummy_image_meta(parent_dir, "sample_input_id", 1)


def create_supplementary(data: SupplementaryData) -> Supplementary:
    return Supplementary(data.data_id, SupplementaryBody(data.data_id, data.path.absolute().as_posix()))


def create_kitti_files(
    input_data_id_prefix: str,
    parent_dir: Path,
    paths: FilePaths,
    camera_horizontal_fov: Optional[int],
    sensor_height: Optional[float],
) -> InputData:
    input_data_id_prefix = input_data_id_prefix + "_" if input_data_id_prefix else ""
    input_data_id = "{}{}".format(input_data_id_prefix, paths.key.id)
    input_data_dir = parent_dir / paths.key.id
    if input_data_dir.exists():
        raise RuntimeError("データ生成先ディレクトリがすでに存在します: {}".format(input_data_dir.absolute()))

    input_data_dir.mkdir(parents=True)
    input_data_path = input_data_dir / paths.pcd.name
    shutil.copyfile(paths.pcd, input_data_path)

    frame_meta = create_frame_meta(input_data_dir, input_data_id, image_count=1, sensor_height=sensor_height)

    image_id = camera_image_id(input_data_id, 0)
    image_path = input_data_dir / paths.image.name
    shutil.copyfile(paths.image, image_path)
    image = SupplementaryData(image_id, paths.image)

    image_meta = _create_image_meta(input_data_dir, paths.calib, input_data_id, 0, camera_horizontal_fov)

    return InputData(
        input_data_id,
        InputDataBody(paths.pcd.name, input_data_path.absolute().as_posix()),
        [create_supplementary(frame_meta), create_supplementary(image), create_supplementary(image_meta)],
    )

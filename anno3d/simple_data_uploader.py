import asyncio
import logging
import math
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import List, Literal, Optional, Tuple

import numpy as np
from scipy.spatial.transform import Rotation

from anno3d.annofab.uploader import Uploader
from anno3d.calib_loader import read_kitti_calib
from anno3d.kitti.camera_horizontal_fov_provider import (
    CameraHorizontalFovKind,
    CameraHorizontalFovProvider,
    create_camera_horizontal_fov_provider,
)
from anno3d.model.common import Vector3
from anno3d.model.file_paths import FilePaths
from anno3d.model.frame import FrameMetaData, ImagesMetaData, PointCloudMetaData
from anno3d.model.image import ImageCamera, ImageCameraFov, ImageMeta
from anno3d.model.input_files import InputData, InputDataBody, Supplementary, SupplementaryBody
from anno3d.model.scene import CameraViewSettings
from anno3d.supplementary_id import camera_image_calib_id, camera_image_id, frame_meta_id

logger = logging.getLogger(__name__)


@dataclass
class SupplementaryData:
    data_id: str
    path: Path
    data_type: Literal["custom", "image", "text"]


def create_frame_meta(
    parent_dir: Path, input_data_id: str, image_count: int, sensor_height: Optional[float]
) -> SupplementaryData:
    data_id = frame_meta_id(input_data_id)
    # http://www.cvlibs.net/datasets/kitti/setup.php によると、kittiのvelodyneの設置高は1.73m
    height = sensor_height if sensor_height is not None else 1.73

    meta = FrameMetaData(
        PointCloudMetaData(is_rightHand_system=True, up_vector=Vector3(0, 0, 1), sensor_height=height),
        ImagesMetaData(image_count=image_count),
    )

    file = parent_dir / data_id
    with file.open("w", encoding="UTF-8") as writer:
        writer.write(meta.to_json(ensure_ascii=False, indent=3))

    return SupplementaryData(data_id, file, "text")


def _create_image_meta(
    parent_dir: Path,
    calib_path: Optional[Path],
    input_data_id: str,
    number: int,
    settings: Optional[CameraViewSettings],
    camera_horizontal_fov: CameraHorizontalFovProvider,
) -> SupplementaryData:
    """

    Args:
        parent_dir:
        calib_path:
        input_data_id:
        number:
        camera_horizontal_fov: カメラの水平方向視野角の取得器。

    Returns:

    """
    data_id = camera_image_calib_id(input_data_id, number)

    # http://www.cvlibs.net/publications/Geiger2012CVPR.pdf 2.1. Sensors and Data Acquisition によると
    # カメラの画角は 90度 * 35度　らしい
    fov = ImageCameraFov(camera_horizontal_fov.value(), 35.0 / 180.0 * math.pi)
    camera_position = Vector3(0, 0, 1.65 - 1.73)  # kittiにおける カメラ設置高(1.65) - velodyne設置高(1.73)
    yaw = 0.0

    if settings is not None:
        if settings.position is not None:
            camera_position = Vector3(settings.position.x, settings.position.y, settings.position.z)
        if settings.direction is not None:
            yaw = settings.direction

    rotation = Rotation.from_euler("xyz", np.array([0.0, 0.0, yaw]))
    direction = rotation.apply(np.array([1.0, 0.0, 0.0]))

    meta = ImageMeta(
        read_kitti_calib(calib_path) if calib_path is not None else None,
        ImageCamera(
            direction=Vector3(direction[0], direction[1], direction[2]),
            fov=fov,
            camera_position=camera_position,
        ),
    )

    file = parent_dir / data_id
    with file.open("w", encoding="UTF-8") as writer:
        writer.write(meta.to_json(ensure_ascii=False, indent=3))

    return SupplementaryData(data_id, file, "text")


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
            camera_position=Vector3(0, 0, 1.65 - 1.73),
        ),
    )

    file = parent_dir / data_id
    with file.open("w", encoding="UTF-8") as writer:
        writer.write(meta.to_json(ensure_ascii=False, indent=3))

    return SupplementaryData(data_id, file, "text")


def _upload_supplementaries(
    uploader: Uploader, input_data_id: str, supplementary_list: List[SupplementaryData]
) -> None:
    for supp in supplementary_list:
        uploader.upload_supplementary(input_data_id, supp.data_id, supp.path, supp.data_type)


async def upload_async(
    input_data_id_prefix: str,
    uploader: Uploader,
    paths: FilePaths,
    dummy_images: List[Path],
    camera_horizontal_fov: CameraHorizontalFovKind,
    fallback_horizontal_fov: Optional[int],  # degree
    sensor_height: Optional[float],
) -> Tuple[str, List[SupplementaryData]]:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None,
        upload,
        input_data_id_prefix,
        uploader,
        paths,
        dummy_images,
        camera_horizontal_fov,
        fallback_horizontal_fov,
        sensor_height,
    )


def upload(
    input_data_id_prefix: str,
    uploader: Uploader,
    paths: FilePaths,
    dummy_images: List[Path],
    camera_horizontal_fov: CameraHorizontalFovKind,
    fallback_horizontal_fov: Optional[int],  # degree
    sensor_height: Optional[float],
) -> Tuple[str, List[SupplementaryData]]:
    input_data_id_prefix = input_data_id_prefix + "_" if input_data_id_prefix else ""
    input_data_id = uploader.upload_input_data(f"{input_data_id_prefix}{paths.key.id}", paths.pcd)

    with tempfile.TemporaryDirectory() as tempdir_str:
        tempdir = Path(tempdir_str)
        frame_meta = create_frame_meta(tempdir, input_data_id, len(paths.images) + len(dummy_images), sensor_height)
        image_supps: List[SupplementaryData] = [
            meta
            for i in range(0, len(paths.images))
            for image_paths in [paths.images[i]]
            for fov_provider in [
                create_camera_horizontal_fov_provider(camera_horizontal_fov, image_paths, fallback_horizontal_fov)
            ]
            for meta in [
                SupplementaryData(camera_image_id(input_data_id, i), image_paths.image, "image"),
                _create_image_meta(
                    tempdir,
                    image_paths.calib,
                    input_data_id,
                    i,
                    image_paths.camera_settings,
                    fov_provider,
                ),
            ]
        ]
        image_count = len(paths.images)

        dummy_image_supps = [
            meta
            for i in range(0, len(dummy_images))
            for meta in [
                _create_dummy_image_meta(tempdir, input_data_id, i + image_count),
                SupplementaryData(camera_image_id(input_data_id, i + image_count), dummy_images[i], "image"),
            ]
        ]

        all_supps = dummy_image_supps + image_supps + [frame_meta]
        _upload_supplementaries(uploader, input_data_id, all_supps)

        logger.info("uploaded: %s", paths.pcd)
        return input_data_id, all_supps


def create_meta_file(parent_dir: Path, paths: FilePaths) -> None:
    create_frame_meta(parent_dir, "sample_input_id", 2, None)
    fov_provider = create_camera_horizontal_fov_provider(CameraHorizontalFovKind.SETTINGS, paths.images[0], None)
    _create_image_meta(parent_dir, paths.images[0].calib, "sample_input_id", 0, None, fov_provider)
    _create_dummy_image_meta(parent_dir, "sample_input_id", 1)


def create_supplementary(data: SupplementaryData) -> Supplementary:
    return Supplementary(data.data_id, SupplementaryBody(data.data_id, data.path.absolute().as_posix()))


def create_kitti_files(
    input_data_id_prefix: str,
    parent_dir: Path,
    paths: FilePaths,
    camera_horizontal_fov: CameraHorizontalFovKind,
    fallback_horizontal_fov: Optional[int],  # degree
    sensor_height: Optional[float],
) -> InputData:
    input_data_id_prefix = input_data_id_prefix + "_" if input_data_id_prefix else ""
    input_data_id = f"{input_data_id_prefix}{paths.key.id}".format(input_data_id_prefix, paths.key.id)
    input_data_dir = parent_dir / paths.key.id
    if input_data_dir.exists():
        raise RuntimeError(f"データ生成先ディレクトリがすでに存在します: {input_data_dir.absolute()}")

    input_data_dir.mkdir(parents=True)
    input_data_path = input_data_dir / paths.pcd.name
    shutil.copyfile(paths.pcd, input_data_path)

    frame_meta = create_frame_meta(input_data_dir, input_data_id, image_count=1, sensor_height=sensor_height)

    images = [
        meta
        for i in range(0, len(paths.images))
        for image in [paths.images[i]]
        for image_id in [camera_image_id(input_data_id, i)]
        for image_path in [input_data_dir / image.image.name]
        for fov_provider in [
            create_camera_horizontal_fov_provider(camera_horizontal_fov, image, fallback_horizontal_fov)
        ]
        for _ in [shutil.copyfile(image.image, image_path)]
        for meta in [
            SupplementaryData(image_id, image_path, "image"),
            _create_image_meta(input_data_dir, image.calib, input_data_id, i, image.camera_settings, fov_provider),
        ]
    ]

    return InputData(
        input_data_id,
        InputDataBody(paths.pcd.name, input_data_path.absolute().as_posix()),
        [create_supplementary(frame_meta)] + [create_supplementary(image) for image in images],
    )

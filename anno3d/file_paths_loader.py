import os
from pathlib import Path
from typing import List, Optional

from anno3d.kitti.scene_uploader import Defaults
from anno3d.model.file_paths import FilePaths, FrameKey, FrameKind, ImagePaths
from anno3d.model.scene import Scene


class FilePathsLoader:
    pcd_root: Path
    image_root: Path
    calib_root: Path

    def __init__(self, pcd_root: Path, image_root: Path, calib_root: Path):
        self.pcd_root = pcd_root
        self.image_root = image_root
        self.calib_root = calib_root

    def load(self, kind: Optional[FrameKind]) -> List[FilePaths]:
        if kind is not None:
            pcd_dir = self.pcd_root / kind.value / "velodyne"
            image_dir = self.image_root / kind.value / "image_2"
            calib_dir = self.calib_root / kind.value / "calib"
        else:
            pcd_dir = self.pcd_root / "velodyne"
            image_dir = self.image_root / "image_2"
            calib_dir = self.calib_root / "calib"

        def id_to_paths(pcd_file: str) -> FilePaths:
            frame_id = pcd_file[0:-4]
            return FilePaths(
                FrameKey(kind, frame_id),
                pcd=pcd_dir / f"{frame_id}.bin",
                images=[ImagePaths(image_dir / f"{frame_id}.png", calib_dir / f"{frame_id}.txt", None)],
                labels=[],
            )

        return [id_to_paths(pcd_file) for pcd_file in os.listdir(pcd_dir)]


class ScenePathsLoader:
    def __init__(self, scene_path: Path):
        self.scene_path = scene_path

    def load(self) -> List[FilePaths]:
        """
        Annofab点群形式（KITTIベース）のファイルを読み込む.

        Args:
            scene_path: 読み込み対象パス。　以下の何れかとなる
                         * scene.metaファイルのパス
                         * scene.metaファイルの存在するディレクトリのパス
                         * scene.metaが存在しないアップロード対象ディレクトリのパス
                             * "velodyne/image_2/calib/label_2" のディレクトリがあるという前提で、読み込みを行う
        """
        file = self.scene_path
        if self.scene_path.is_dir():
            file = self.scene_path / Defaults.scene_meta_file

        scene_dir = file.parent
        scene = Scene.decode_path(file) if file.is_file() else Scene.default_scene(self.scene_path)

        def scene_to_paths(frame_id: str) -> FilePaths:
            images = [
                ImagePaths(
                    scene_dir / f"{img.image_dir}/{frame_id}.{img.file_extension}",
                    scene_dir / f"{img.calib_dir}/{frame_id}.txt",
                    img.camera_view_setting,
                )
                for img in scene.images
            ]

            return FilePaths(
                FrameKey(None, frame_id),
                pcd=scene_dir / f"{scene.velodyne.velodyne_dir}/{frame_id}.bin",
                images=images,
                labels=[],
            )

        return [scene_to_paths(frame_id) for frame_id in scene.id_list]

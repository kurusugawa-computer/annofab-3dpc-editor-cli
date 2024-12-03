import os
from pathlib import Path
from typing import List, Optional

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
                images=[
                    ImagePaths(
                        image_dir / f"{frame_id}.png",
                        calib_dir / f"{frame_id}.txt",
                        None,
                    )
                ],
                labels=[],
                image_names=["1"],
            )

        return [id_to_paths(pcd_file) for pcd_file in os.listdir(pcd_dir)]


class ScenePathsLoader:
    """コンストラクタに渡されたSceneを元にFilePathsを生成する"""

    def __init__(self, scene: Scene):
        """

        Args:
            scene: 対象のscene
            scene_dir:  sceneの元になったscene.metaファイルの存在するディレクトリのパス
        """
        self.scene = scene

    def load(self) -> List[FilePaths]:
        """
        Annofab点群形式（KITTIベース）のファイルを読み込む.
        """
        scene = self.scene

        def scene_to_paths(frame_id: str) -> FilePaths:
            images = [
                ImagePaths(
                    Path(image.image_dir) / f"{frame_id}.{image.file_extension}",
                    Path(image.calib_dir) / f"{frame_id}.txt" if image.calib_dir is not None else None,
                    image.camera_view_setting,
                )
                for image in scene.images
            ]
            image_names = [
                image.display_name if image.display_name else str(index) for index, image in enumerate(scene.images, 1)
            ]
            return FilePaths(
                FrameKey(None, frame_id),
                Path(scene.velodyne.velodyne_dir) / f"{frame_id}.bin",
                images,
                labels=[],
                image_names=image_names,
            )

        return [scene_to_paths(frame_id) for frame_id in scene.id_list]

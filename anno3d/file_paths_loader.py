import os
from pathlib import Path
from typing import List, Optional

from anno3d.model.file_paths import FilePaths, FrameKey, FrameKind


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
                pcd_dir / f"{frame_id}.bin",
                image_dir / f"{frame_id}.png",
                calib_dir / f"{frame_id}.txt",
            )

        return [id_to_paths(pcd_file) for pcd_file in os.listdir(pcd_dir)]

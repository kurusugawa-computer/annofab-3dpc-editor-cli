import logging
import shutil
import sys
from pathlib import Path

from anno3d.annofab.client import ClientLoader
from anno3d.annofab.uploader import Uploader
from anno3d.file_paths_loader import FilePathsLoader
from anno3d.model.file_paths import FrameKind
from anno3d.simple_data_uploader import create_meta_file, upload


def add_stdout_handler(target: logging.Logger, level: int = logging.INFO):
    handler = logging.StreamHandler()
    handler.setLevel(level)
    handler.setFormatter(logging.Formatter("[%(asctime)s] [%(process)d] [%(name)s] [%(levelname)s] %(message)s"))
    target.addHandler(handler)


root_logger = logging.getLogger()
root_logger.level = logging.INFO
add_stdout_handler(root_logger, logging.INFO)

logger = logging.getLogger(__name__)


def upload_files():
    args = sys.argv[1:]

    annofab_id = args[0]
    password = args[1]
    kitti_dir = Path(args[2])

    project = "66241367-9175-40e3-8f2f-391d6891590b"

    loader = FilePathsLoader(kitti_dir, kitti_dir, kitti_dir)
    pathss = loader.load(FrameKind.testing)[0:10]
    client_loader = ClientLoader(annofab_id, password)
    with client_loader.open_api() as api:
        uploader = Uploader(api, project)
        for paths in pathss:
            upload(uploader, paths)


def create_meta():
    parent = Path("/tmp/meta")
    if parent.exists():
        shutil.rmtree(parent)

    args = sys.argv[1:]
    kitti_dir = Path(args[0])
    loader = FilePathsLoader(kitti_dir, kitti_dir, kitti_dir)
    pathss = loader.load(FrameKind.testing)[0:10]
    parent.mkdir(parents=True)
    create_meta_file(parent, pathss[0])


def main() -> None:
    create_meta()
    # upload_files()


if __name__ == "__main__":
    try:
        main()
    finally:
        logging.shutdown()

import logging
import sys
from pathlib import Path

from anno3d.annofab.client import ClientLoader
from anno3d.annofab.uploader import Uploader
from anno3d.file_paths_loader import FilePathsLoader
from anno3d.model.file_paths import FrameKind
from anno3d.simple_data_uploader import upload


def add_stdout_handler(logger: logging.Logger, level: int = logging.INFO):
    handler = logging.StreamHandler()
    handler.setLevel(level)
    handler.setFormatter(logging.Formatter("[%(asctime)s] [%(process)d] [%(name)s] [%(levelname)s] %(message)s"))
    logger.addHandler(handler)


root_logger = logging.getLogger()
root_logger.level = logging.INFO
add_stdout_handler(root_logger, logging.INFO)

logger = logging.getLogger(__name__)


def main() -> None:
    args = sys.argv[1:]

    annofab_id = args[0]
    password = args[1]
    kitty_dir = Path(args[2])

    project = "66241367-9175-40e3-8f2f-391d6891590b"

    loader = FilePathsLoader(kitty_dir, kitty_dir, kitty_dir)
    pathss = loader.load(FrameKind.testing)[0:10]
    client_loader = ClientLoader(annofab_id, password)
    with client_loader.open_api() as api:
        uploader = Uploader(api, project)
        for paths in pathss:
            upload(uploader, paths)


if __name__ == "__main__":
    try:
        main()
    finally:
        logging.shutdown()

from pathlib import Path

from anno3d.file_paths_loader import FilePathsLoader
from anno3d.model.file_paths import FrameKind

test_ressources_path = Path(__file__).parent / "resources" / "kitti3dobj"


def test_load_training():
    path = test_ressources_path
    loader = FilePathsLoader(path, path, path)
    pathss = loader.load(FrameKind.training)

    assert len(pathss) == 1
    assert pathss[0].key.kind == FrameKind.training
    assert pathss[0].key.id == "000001"
    assert pathss[0].pcd.name == "000001.bin"
    assert pathss[0].images[0].image.name == "000001.png"
    assert pathss[0].images[0].calib.name == "000001.txt"
    assert pathss[0].pcd.exists()
    assert pathss[0].images[0].image.exists()
    assert pathss[0].images[0].calib.exists()


def test_load_testing():
    path = test_ressources_path
    loader = FilePathsLoader(path, path, path)
    pathss = loader.load(FrameKind.testing)

    assert len(pathss) == 2
    for paths in pathss:
        assert paths.pcd.exists()
        assert paths.images[0].image.exists()
        assert paths.images[0].calib.exists()

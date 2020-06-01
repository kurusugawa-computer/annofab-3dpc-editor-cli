from pathlib import Path
from typing import Any, Callable, Iterable, List, Optional, TypeVar, cast

from anno3d.model.image import kitti3DCalib

T = TypeVar("T")


def _find(iterable: Iterable[T], pred: Callable[[T], bool]) -> Optional[T]:
    # pred をキャストしないと以下のエラーで怒られる・・・ 意味がわからない。
    # error: Argument 1 to "filter" has
    # incompatible type "Callable[[T], bool]";
    # expected "Callable[[Optional[T]], Any]"

    return next(filter(cast(Callable[[Optional[T]], Any], pred), iterable), None)


def _read_str(lines: List[str]) -> kitti3DCalib:
    p2prefix = "P2: "
    r0prefix = "R0_rect: "
    velo_cam_prefix = "Tr_velo_to_cam: "
    p2line = _find(lines, lambda s: s.startswith(p2prefix))
    r0line = _find(lines, lambda s: s.startswith(r0prefix))
    velo_cam_line = _find(lines, lambda s: s.startswith(velo_cam_prefix))
    if p2line is None:
        raise RuntimeError("p2lineが見つかりませんでした。")
    if r0line is None:
        raise RuntimeError("r0lineが見つかりませんでした。")
    if velo_cam_line is None:
        raise RuntimeError("velo_cam_lineが見つかりませんでした。")

    def to_values(line: str, prefix: str) -> List[float]:
        return [float(s) for s in line[len(prefix) :].split(" ")]

    values_p2 = to_values(p2line, p2prefix)
    values_r0 = to_values(r0line, r0prefix)
    values_velo_cam = to_values(velo_cam_line, velo_cam_prefix)
    return kitti3DCalib(camera_matrix=values_p2, r0_matrix=values_r0, velo_cam_matrix=values_velo_cam)


def read_kitti_calib(path: Path) -> kitti3DCalib:
    with path.open(mode="r", encoding="utf-8") as file:
        return _read_str(file.readlines())

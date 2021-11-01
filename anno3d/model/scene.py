import json
from dataclasses import dataclass, replace
from pathlib import Path
from typing import ClassVar, List, Optional, Type, cast

from dataclasses_json import DataClassJsonMixin
from more_itertools import first_true


@dataclass(frozen=True)
class Series(DataClassJsonMixin):
    type_value: ClassVar[str]


@dataclass(frozen=True)
class KittiVelodyneSeries(Series):
    velodyne_dir: str
    type: str = "kitti_velodyne"
    type_value: ClassVar[str] = "kitti_velodyne"


@dataclass(frozen=True)
class XYZ(DataClassJsonMixin):
    x: float
    y: float
    z: float


@dataclass(frozen=True)
class CameraViewSettings(DataClassJsonMixin):
    """
    Args:
        fov: 水平方向視野角[rad]
        direction: 回転角度。 x軸方向が0でz軸による回転（右手系） [rad]
        position: velodyne座標系におけるカメラの設置位置
    """

    fov: Optional[float] = None
    direction: Optional[float] = None
    position: Optional[XYZ] = None


@dataclass(frozen=True)
class KittiImageSeries(Series):
    image_dir: str
    calib_dir: Optional[str] = None
    camera_view_setting: Optional[CameraViewSettings] = None
    type: str = "kitti_image"
    type_value: ClassVar[str] = "kitti_image"
    file_extension: str = "png"


@dataclass(frozen=True)
class KittiLabelSeries(Series):
    label_dir: str
    image_dir: str
    calib_dir: str
    type: str = "kitti_label"
    type_value: ClassVar[str] = "kitti_label"


@dataclass(frozen=True)
class JsonScene(DataClassJsonMixin):
    id_list: List[str]
    serieses: List[Series]


class Defaults:
    scene_meta_file: ClassVar[str] = "scene.meta"
    velo_dir: ClassVar[str] = "velodyne"
    image_dir: ClassVar[str] = "image_2"
    calib_dir: ClassVar[str] = "calib"
    label_dir: ClassVar[str] = "label_2"


@dataclass(frozen=True)
class Scene(DataClassJsonMixin):
    id_list: List[str]
    velodyne: KittiVelodyneSeries
    images: List[KittiImageSeries]
    labels: List[KittiLabelSeries]

    @staticmethod
    def decode_series(series_dict: dict, all_serieses: List[Type[Series]]) -> Optional[Series]:
        tpe = series_dict["type"]
        cls = first_true(all_serieses, pred=lambda c: c.type_value == tpe)
        if cls is None:
            return None

        result = cls.from_dict(series_dict)
        return result

    @classmethod
    def decode(cls, scene_dir: Path, json_str: str) -> "Scene":
        scene_dict: dict = json.loads(json_str)

        id_list: List[str] = scene_dict["id_list"]
        series_dicts: List[dict] = scene_dict["serieses"]
        all_serieses = Series.__subclasses__()
        serieses = [cls.decode_series(s, all_serieses) for s in series_dicts]

        json_scene = JsonScene(id_list, [s for s in serieses if s is not None])

        velodyne = cast(
            Optional[KittiVelodyneSeries],
            first_true(json_scene.serieses, pred=lambda s: isinstance(s, KittiVelodyneSeries)),
        )
        if velodyne is None:
            raise RuntimeError("sceneにkitti_velodyneが含まれていません")

        def convert_path(path: str) -> str:
            return (scene_dir / path).as_posix()

        velodyne = replace(velodyne, velodyne_dir=convert_path(velodyne.velodyne_dir))

        def convert_image(image: KittiImageSeries) -> KittiImageSeries:
            calib_dir = convert_path(image.calib_dir) if image.calib_dir is not None else None
            return replace(image, image_dir=convert_path(image.image_dir), calib_dir=calib_dir)

        def convert_label(label: KittiLabelSeries) -> KittiLabelSeries:
            return replace(
                label,
                label_dir=convert_path(label.label_dir),
                image_dir=convert_path(label.image_dir),
                calib_dir=convert_path(label.calib_dir),
            )

        images = [convert_image(image) for image in json_scene.serieses if isinstance(image, KittiImageSeries)]
        labels = [convert_label(label) for label in json_scene.serieses if isinstance(label, KittiLabelSeries)]

        return Scene(json_scene.id_list, velodyne, images, labels)

    @classmethod
    def decode_path(cls, json_file: Path) -> "Scene":
        with json_file.open("r") as fp:
            return cls.decode(json_file.parent, fp.read())

    @classmethod
    def default_scene(cls, path: Path) -> "Scene":
        velo_dir = path / Defaults.velo_dir
        image_dir = path / Defaults.image_dir
        calib_dir = path / Defaults.calib_dir
        label_dir = path / Defaults.label_dir

        # 画像名から拡張子を取り除いたものがid
        id_list = [file.stem for file in image_dir.iterdir() if file.is_file()]
        id_list.sort()

        return Scene(
            id_list=id_list,
            velodyne=KittiVelodyneSeries(str(velo_dir.absolute())),
            images=[
                KittiImageSeries(
                    image_dir=str(image_dir.absolute()), calib_dir=str(calib_dir.absolute()), camera_view_setting=None
                )
            ],
            labels=[KittiLabelSeries(str(label_dir.absolute()), str(image_dir.absolute()), str(calib_dir.absolute()))],
        )

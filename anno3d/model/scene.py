import json
from dataclasses import dataclass
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
    fov: float
    direction: float
    position: XYZ


@dataclass(frozen=True)
class KittiImageSeries(Series):
    image_dir: str
    calib_dir: Optional[str] = None
    camera_view_setting: Optional[CameraViewSettings] = None
    type: str = "kitti_image"
    type_value: ClassVar[str] = "kitti_image"


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

        return cls.from_dict(series_dict)

    @classmethod
    def decode(cls, json_str: str) -> "Scene":
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

        images = [image for image in json_scene.serieses if isinstance(image, KittiImageSeries)]
        labels = [label for label in json_scene.serieses if isinstance(label, KittiLabelSeries)]

        return Scene(json_scene.id_list, velodyne, images, labels)

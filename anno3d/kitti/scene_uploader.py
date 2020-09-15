import json
import logging
import tempfile
import time
import uuid
from pathlib import Path
from typing import Dict, List, Tuple

import more_itertools
from annofabapi import AnnofabApi, dataclass
from annofabapi.dataclass.annotation_specs import LabelV2
from annofabapi.models import JobStatus

from anno3d.annofab.model import XYZ, CuboidAnnotationDetail, CuboidAnnotationDetailData, CuboidShape, Size
from anno3d.annofab.project import ProjectApi
from anno3d.annofab.task import TaskApi
from anno3d.annofab.uploader import Uploader
from anno3d.kitti.calib import read_calibration, transform_labels_into_lidar_coordinates
from anno3d.model.file_paths import FilePaths, FrameKey, ImagePaths, LabelPaths
from anno3d.model.kitti_label import KittiLabel
from anno3d.model.scene import KittiImageSeries, KittiLabelSeries, KittiVelodyneSeries, Scene
from anno3d.simple_data_uploader import upload

logger = logging.getLogger(__name__)


@dataclass
class SceneUploaderInput:
    project_id: str
    input_data_id_prefix: str
    frame_per_task: int
    sensor_height: float
    task_id_prefix: str


class Defaults:
    scene_meta_file = "scene.meta"
    velo_dir = "velodyne"
    image_dir = "image_2"
    calib_dir = "calib"
    label_dir = "label_2"


TaskId = str

DataId = str


class SceneUploader:
    _client: AnnofabApi
    _project: ProjectApi

    def __init__(self, client: AnnofabApi):
        self._client = client
        self._project = ProjectApi(client)

    @staticmethod
    def _default_scene(path: Path) -> Scene:
        velo_dir = path / Defaults.velo_dir
        image_dir = path / Defaults.image_dir
        calib_dir = path / Defaults.calib_dir
        label_dir = path / Defaults.label_dir

        # 画像名から .pngを取り除いたものがid
        id_list = [file.name[0:-4] for file in image_dir.iterdir() if file.is_file()]

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

    def upload_from_path(self, scene_path: Path, uploader_input: SceneUploaderInput) -> None:
        """
        Args:
            scene_path: 読み込み対象パス。　以下の何れかとなる
                         * scene.metaファイルのパス
                         * scene.metaファイルの存在するディレクトリのパス
                         * scene.metaが存在しないアップロード対象ディレクトリのパス
                             * "velodyne/image_2/calib/label_2" のディレクトリがあるという前提で、読み込みを行う
            uploader_input:

        Returns:

        """
        file = scene_path
        if scene_path.is_dir():
            file = scene_path / Defaults.scene_meta_file

        scene = Scene.decode_path(file) if file.is_file() else self._default_scene(scene_path)
        return self.upload_scene(scene, uploader_input)

    @staticmethod
    def _scene_to_paths(scene: Scene) -> List[FilePaths]:
        def id_to_paths(frame_id: str) -> FilePaths:
            images = [
                ImagePaths(Path(image.image_dir) / f"{frame_id}.png", Path(image.calib_dir / f"{frame_id}.txt"))
                for image in scene.images
            ]
            labels = [
                LabelPaths(
                    Path(label.label_dir) / f"{frame_id}.txt",
                    Path(label.image_dir) / f"{frame_id}.png",
                    Path(label.calib_dir / f"{frame_id}.txt"),
                )
                for label in scene.labels
            ]
            return FilePaths(
                FrameKey(None, frame_id), Path(scene.velodyne.velodyne_dir) / f"{frame_id}.bin", images, labels
            )

        return [id_to_paths(frame_id) for frame_id in scene.id_list]

    @staticmethod
    def _create_task_def_csv(
        csv_path: Path, id_prefix: str, data_and_pathss: List[Tuple[DataId, FilePaths]], chunk_size: int
    ) -> Dict[TaskId, List[Tuple[DataId, FilePaths]]]:
        chunked_by_tasks = more_itertools.chunked(data_and_pathss, chunk_size)

        task_count = 0
        result_dict: Dict[TaskId, List[Tuple[DataId, FilePaths]]] = {}
        with csv_path.open("w", encoding="UTF-8") as writer:
            for data_list in chunked_by_tasks:
                task_id = f"{id_prefix}${task_count}"
                inputs = [t[0] for t in data_list]

                line = ",".join([task_id] + inputs)
                writer.write(f"{line}\n")
                task_count += 1
                result_dict[task_id] = data_list

        return result_dict

    def _create_task(self, project_id: str, csv_path: Path) -> None:
        project = self._project
        task = TaskApi(self._client, project, project_id)
        response = task.create_tasks_by_csv(csv_path)
        job = response.job

        while job.job_status == JobStatus.PROGRESS:
            logger.info("タスクの作成完了を待っています。")
            time.sleep(5)

            job = project.get_job(project_id, response.job)

        if job.job_status == JobStatus.FAILED:
            detail = json.dumps(job.job_detail, ensure_ascii=False)
            raise RuntimeError(f"タスクの作成に失敗しました: {detail}")

    def _label_to_cuboids(
        self, id_to_label: Dict[str, LabelV2], labels: List[KittiLabel]
    ) -> List[CuboidAnnotationDetail]:
        def detail_data(kitti_label: KittiLabel) -> CuboidAnnotationDetailData:
            return CuboidAnnotationDetailData(
                CuboidShape(
                    # https://github.com/kurusugawa-computer/annofab-3dpc-editor/issues/416
                    # TODO ここの WHD の読み替えは ↑の対応後に修正したほうが良い
                    # 修正する場合 データのversionが2とかになってるはずなので、その点も対応する必要がある
                    dimensions=Size(width=kitti_label.depth, height=kitti_label.width, depth=kitti_label.height),
                    location=XYZ(x=kitti_label.x, y=kitti_label.y, z=kitti_label.z + (kitti_label.height / 2)),
                    rotation=XYZ(x=0.0, y=0.0, z=kitti_label.yaw),  # このyawがそのままでいいのか不明
                )
            )

        return [
            CuboidAnnotationDetail(
                label.annotation_id if label.annotation_id is not None else str(uuid.uuid4()),
                self._client.account_id,
                label.type,
                False,
                detail_data(label),
            )
            for label in labels
            if label.type in id_to_label
        ]
        pass

    def _create_annotations(
        self, task: TaskApi, id_to_label: Dict[str, LabelV2], task_id: str, pathss: List[Tuple[DataId, LabelPaths]]
    ) -> None:
        for input_data_id, paths in pathss:
            labels = KittiLabel.decode_path(paths.label)
            calib = read_calibration(paths.calib)
            transformed_labels = transform_labels_into_lidar_coordinates(labels, calib)

            task.put_cuboid_annotations(task_id, input_data_id, self._label_to_cuboids(id_to_label, transformed_labels))

    def upload_scene(self, scene: Scene, input: SceneUploaderInput) -> None:
        uploader = Uploader(self._client, input.project_id)
        pathss = self._scene_to_paths(scene)
        specs = self._project.get_annotation_specs(input.project_id)
        annofab_labels = specs.labels
        if annofab_labels is None:
            raise RuntimeError(f"対象プロジェクト(={input.project_id})のラベル設定が存在しません")

        data_and_pathss: List[Tuple[DataId, FilePaths]] = [
            (input_data_id, paths)
            for paths in pathss
            for input_data_id, _ in [upload(input.input_data_id_prefix, uploader, paths, [], None, input.sensor_height)]
        ]

        with tempfile.TemporaryDirectory() as tempdir_str:
            csv_path = Path(tempdir_str) / "task_create.csv"
            task_to_data_dict = self._create_task_def_csv(
                csv_path, input.task_id_prefix, data_and_pathss, input.frame_per_task
            )
            self._create_task(input.project_id, csv_path)

        id_to_label: Dict[str, LabelV2] = {anno_label.label_id: anno_label for anno_label in annofab_labels}

        for task_id, data_id_and_pathss in task_to_data_dict:
            self._create_annotations(
                TaskApi(self._client, self._project, input.project_id), id_to_label, task_id, data_id_and_pathss
            )

import json
import logging
import tempfile
import time
import uuid
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import ClassVar, Dict, List, NewType, Optional, Tuple

import more_itertools
from annofabapi import AnnofabApi
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

logger: logging.Logger = logging.getLogger(__name__)


class UploadKind(Enum):
    DATA_ONLY = "data"
    CREATE_TASK = "task"
    CREATE_ANNOTATION = "annotation"


@dataclass
class SceneUploaderInput:
    project_id: str
    input_data_id_prefix: str
    frame_per_task: Optional[int]
    sensor_height: Optional[float]
    task_id_prefix: str
    kind: UploadKind


class Defaults:
    scene_meta_file: ClassVar[str] = "scene.meta"
    velo_dir: ClassVar[str] = "velodyne"
    image_dir: ClassVar[str] = "image_2"
    calib_dir: ClassVar[str] = "calib"
    label_dir: ClassVar[str] = "label_2"


TaskId = NewType("TaskId", str)

DataId = NewType("DataId", str)


class SceneUploader:
    _client: AnnofabApi
    _project: ProjectApi

    def __init__(self, client: AnnofabApi):
        self._client = client
        self._project = ProjectApi(client)

    @staticmethod
    def default_scene(path: Path) -> Scene:
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

    def upload_from_path(self, scene_path: Path, uploader_input: SceneUploaderInput, force: bool = False) -> None:
        """
        Args:
            scene_path: 読み込み対象パス。　以下の何れかとなる
                         * scene.metaファイルのパス
                         * scene.metaファイルの存在するディレクトリのパス
                         * scene.metaが存在しないアップロード対象ディレクトリのパス
                             * "velodyne/image_2/calib/label_2" のディレクトリがあるという前提で、読み込みを行う
            uploader_input:
            force:

        Returns:

        """
        file = scene_path
        if scene_path.is_dir():
            file = scene_path / Defaults.scene_meta_file

        scene = Scene.decode_path(file) if file.is_file() else self.default_scene(scene_path)
        return self.upload_scene(scene, uploader_input, force=force)

    @staticmethod
    def _scene_to_paths(scene: Scene) -> List[FilePaths]:
        def id_to_paths(frame_id: str) -> FilePaths:
            images = [
                ImagePaths(
                    Path(image.image_dir) / f"{frame_id}.png",
                    Path(image.calib_dir) / f"{frame_id}.txt" if image.calib_dir is not None else None,
                    image.camera_view_setting,
                )
                for image in scene.images
            ]
            labels = [
                LabelPaths(
                    Path(label.label_dir) / f"{frame_id}.txt",
                    Path(label.image_dir) / f"{frame_id}.png",
                    Path(label.calib_dir) / f"{frame_id}.txt",
                )
                for label in scene.labels
            ]
            return FilePaths(
                FrameKey(None, frame_id), Path(scene.velodyne.velodyne_dir) / f"{frame_id}.bin", images, labels
            )

        return [id_to_paths(frame_id) for frame_id in scene.id_list]

    @staticmethod
    def _create_task_def_csv(
        csv_path: Path,
        id_prefix: str,
        data_and_pathss: List[Tuple[DataId, FilePaths]],
        chunk_size: Optional[int] = None,
    ) -> Dict[TaskId, List[Tuple[DataId, FilePaths]]]:

        if chunk_size is None:
            chunked_by_tasks = iter([data_and_pathss])
            task_id_template = "{id_prefix}"

        else:
            chunked_by_tasks = more_itertools.chunked(data_and_pathss, chunk_size)
            task_id_template = "{id_prefix}_{task_count}"

        result_dict: Dict[TaskId, List[Tuple[DataId, FilePaths]]] = {}
        with csv_path.open("w", encoding="UTF-8") as writer:
            for task_count, data_list in enumerate(chunked_by_tasks):
                task_id = task_id_template.format(id_prefix=id_prefix, task_count=task_count)
                result_dict[TaskId(task_id)] = data_list
                for data_id, paths in data_list:
                    # XXX ここで `paths.pcd.name` は input_data_nameの指定なんだけど、ファイル名がinput_data_nameである
                    # というのは、ただの実装詳細なので、本来はやりたくない…
                    line = f"{task_id},{paths.pcd.name},{data_id}"
                    writer.write(f"{line}\r\n")

        with csv_path.open("r") as reader:
            logger.info("task def csv: \n%s", reader.read())
        return result_dict

    def _create_task(self, project_id: str, csv_path: Path) -> None:
        project = self._project
        task = TaskApi(self._client, project, project_id)
        response = task.create_tasks_by_csv(csv_path)
        job = response.job

        while job.job_status == JobStatus.PROGRESS:
            logger.info("タスクの作成完了を待っています。")
            time.sleep(5)
            new_info = project.get_job(project_id, job)
            if new_info is None:
                raise RuntimeError(f"ジョブ(={job.job_id})が取得できませんでした。")
            job = new_info

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

    def _create_annotations(
        self,
        task: TaskApi,
        id_to_label: Dict[str, LabelV2],
        task_id: TaskId,
        pathsss: List[Tuple[DataId, List[LabelPaths]]],
    ) -> None:
        for input_data_id, pathss in pathsss:
            logger.info("アノテーションの登録を行います: %s/%s", task_id, input_data_id)
            transformed_labels = [
                transformed_label
                for paths in pathss
                for calib in [read_calibration(paths.calib)]
                for labels in [KittiLabel.decode_path(paths.label)]
                for transformed_label in transform_labels_into_lidar_coordinates(labels, calib)
            ]

            task.put_cuboid_annotations(task_id, input_data_id, self._label_to_cuboids(id_to_label, transformed_labels))

    def upload_scene(self, scene: Scene, uploader_input: SceneUploaderInput, force: bool = False) -> None:
        logger.info("upload scene: %s", scene.to_json(indent=2, ensure_ascii=False))

        uploader = Uploader(self._client, uploader_input.project_id, force=force)
        pathss = self._scene_to_paths(scene)
        specs = self._project.get_annotation_specs(uploader_input.project_id)
        annofab_labels = specs.labels
        if annofab_labels is None:
            raise RuntimeError(f"対象プロジェクト(={uploader_input.project_id})のラベル設定が存在しません")

        logger.info("input-dataのアップロードを開始します")
        data_and_pathss: List[Tuple[DataId, FilePaths]] = [
            (DataId(input_data_id), paths)
            for paths in pathss
            for input_data_id, _ in [
                upload(uploader_input.input_data_id_prefix, uploader, paths, [], None, uploader_input.sensor_height)
            ]
        ]
        logger.info("%d件のデータをアップロードしました", len(data_and_pathss))
        if uploader_input.kind == UploadKind.DATA_ONLY:
            return

        with tempfile.TemporaryDirectory() as tempdir_str:
            csv_path = Path(tempdir_str) / "task_create.csv"
            task_to_data_dict = self._create_task_def_csv(
                csv_path, uploader_input.task_id_prefix, data_and_pathss, uploader_input.frame_per_task
            )
            self._create_task(uploader_input.project_id, csv_path)

        logger.info("タスクの作成が完了しました")
        if uploader_input.kind == UploadKind.CREATE_TASK:
            return

        id_to_label: Dict[str, LabelV2] = {
            anno_label.label_id: anno_label for anno_label in annofab_labels if anno_label.label_id is not None
        }

        for task_id, data_id_and_pathss in task_to_data_dict.items():
            data_and_label_pathss = [(data_id, pathss.labels) for data_id, pathss in data_id_and_pathss]
            self._create_annotations(
                TaskApi(self._client, self._project, uploader_input.project_id),
                id_to_label,
                task_id,
                data_and_label_pathss,
            )

        logger.info("アノテーションの登録が完了しました")

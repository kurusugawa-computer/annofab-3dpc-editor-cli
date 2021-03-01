import sys
import logging
import os
import shutil
import tempfile
from enum import Enum
from pathlib import Path
from typing import Any, List, Optional, Tuple, Type, TypeVar

import fire

from anno3d.annofab.client import ClientLoader
from anno3d.annofab.constant import segment_type_instance, segment_type_semantic
from anno3d.annofab.project import Label, ProjectApi
from anno3d.annofab.uploader import Uploader
from anno3d.file_paths_loader import FilePathsLoader, load_scene_file_paths
from anno3d.kitti.scene_uploader import SceneUploader, SceneUploaderInput, UploadKind
from anno3d.model.annotation_area import RectAnnotationArea, SphereAnnotationArea, WholeAnnotationArea
from anno3d.model.file_paths import FrameKind
from anno3d.model.input_files import InputData
from anno3d.simple_data_uploader import create_frame_meta, create_kitti_files, create_meta_file, upload

E = TypeVar("E", bound=Enum)


def _decode_enum(enum: Type[E], value: Any) -> E:
    for e in enum:
        print(f"{e.value} == {value}")
        if e.value == value:
            return e

    raise ValueError("{}は有効な、{}型の値ではありません".format(value, enum.__name__))


def add_stdout_handler(target: logging.Logger, level: int = logging.INFO):
    handler = logging.StreamHandler()
    handler.setLevel(level)
    handler.setFormatter(logging.Formatter("[%(asctime)s] [%(process)d] [%(name)s] [%(levelname)s] %(message)s"))
    target.addHandler(handler)


root_logger = logging.getLogger()
root_logger.level = logging.INFO
add_stdout_handler(root_logger, logging.INFO)

logger = logging.getLogger(__name__)

resources = Path(__file__).parent / "resources"
hidari = resources / "hidari.png"
migi = resources / "migi.png"

env_annofab_user_id = os.environ.get("ANNOFAB_USER_ID")
env_annofab_password = os.environ.get("ANNOFAB_PASSWORD")


def validate_annofab_credentail(annofab_id: Optional[str], annofab_pass: Optional[str]):
    """
    AnnoFabの認証情報が指定されていることを確認します。
    どちらかが指定されていない場合は処理を終了します。
    """
    if annofab_id is None:
        print("AnnoFabのユーザIDが指定されていないため、終了します。環境変数'ANNOFAB_USER_ID' または コマンドライン引数 '--anno_id' にユーザIDを指定してください。",file=sys.stderr )
        sys.exit(1)
    if annofab_pass is None:
        print("AnnoFabのパスワードが指定されていないため、終了します。環境変数'ANNOFAB_PASSWORD' または コマンドライン引数 '--anno_pass' にパスワードを指定してください。",file=sys.stderr )
        sys.exit(1)
    return


class Sandbox:
    """ sandboxの再現 """

    @staticmethod
    def upload(
        annofab_id: str, annofab_pass: str, kitti_dir: str, skip: int = 0, size: int = 10, force: bool = False
    ) -> None:
        project = "66241367-9175-40e3-8f2f-391d6891590b"

        kitti_dir_path = Path(kitti_dir)
        loader = FilePathsLoader(kitti_dir_path, kitti_dir_path, kitti_dir_path)
        pathss = loader.load(FrameKind.testing)[skip : (skip + size)]
        client_loader = ClientLoader(annofab_id, annofab_pass)
        with client_loader.open_api() as api:
            uploader = Uploader(api, project, force=force)
            for paths in pathss:
                upload("", uploader, paths, [hidari, migi], None, None)

    @staticmethod
    def create_meta(kitti_dir: str, output: str = "/tmp/meta"):
        parent = Path(output)
        if parent.exists():
            shutil.rmtree(parent)

        kitti_dir_path = Path(kitti_dir)
        loader = FilePathsLoader(kitti_dir_path, kitti_dir_path, kitti_dir_path)
        pathss = loader.load(FrameKind.testing)[0:10]
        parent.mkdir(parents=True)
        create_meta_file(parent, pathss[0])

    @staticmethod
    def upload_velodyne(
        annofab_id: str,
        annofab_pass: str,
        project_id: str,
        velo_dir: str,
        data_id_prefix: str = "",
        sensor_height: Optional[float] = None,
        force: bool = False,
    ) -> None:
        velo_files = [Path(velo_dir) / path for path in os.listdir(velo_dir)]

        client_loader = ClientLoader(annofab_id, annofab_pass)
        with client_loader.open_api() as api:
            with tempfile.TemporaryDirectory() as tempdir_str:
                tempdir = Path(tempdir_str)
                uploader = Uploader(api, project_id, force=force)
                for velo_file in velo_files:
                    data_id = data_id_prefix + velo_file.name
                    uploader.upload_input_data(data_id, velo_file)
                    supp_data = create_frame_meta(tempdir, data_id, 0, sensor_height)
                    uploader.upload_supplementary(data_id, supp_data.data_id, supp_data.path)
                    logger.info("uploaded: %s", velo_file)


class ProjectCommand:
    """ AnnoFabプロジェクトの操作を行うためのサブコマンドです """

    @staticmethod
    def create(
        annofab_id: str,
        annofab_pass: str,
        project_id: str,
        organization_name: str,
        plugin_id: str,
        title: str = "",
        overview: str = "",
    ) -> None:
        """
        新しいカスタムプロジェクトを生成します。

        Args:
            annofab_id:
            annofab_pass:
            project_id: 作成するprojectのid
            organization_name: projectを所属させる組織の名前
            plugin_id: このプロジェクトで使用する、組織に登録されているプラグインのid。
            title: projectのタイトル。　省略した場合 project_id と同様
            overview:  projectの概要。 省略した場合 project_id と同様

        Returns:

        """
        client_loader = ClientLoader(annofab_id, annofab_pass)
        with client_loader.open_api() as api:
            created_project_id = ProjectApi(api).create_custom_project(
                project_id, organization_name, plugin_id, title, overview
            )
            logger.info("プロジェクト(=%s)を作成しました。", created_project_id)

    @staticmethod
    def put_label(
        annofab_id: str,
        annofab_pass: str,
        project_id: str,
        label_id: str,
        ja_name: str,
        en_name: str,
        color: Tuple[int, int, int],
    ) -> None:
        raise RuntimeError("この関数は廃止されました put_cuboid_label を利用してください")

    @staticmethod
    def put_segment_label(
        annofab_id: str,
        annofab_pass: str,
        project_id: str,
        label_id: str,
        ja_name: str,
        en_name: str,
        color: Tuple[int, int, int],
        default_ignore: bool,
        segment_type: str,
        layer: int = 100,
    ) -> None:
        """
        対象のプロジェクトにsegmentのlabelを追加・更新します。
        Args:
            annofab_id:
            annofab_pass:
            project_id: 対象プロジェクト
            label_id: 追加・更新するラベルのid
            ja_name: 日本語名称
            en_name: 　英語名称
            color: ラベルの表示色。 "(R,G,B)"形式の文字列 R/G/Bは、それぞれ0〜255の整数値で指定する
            default_ignore: このラベルがついた領域を、デフォルトでは他のアノテーションから除外するかどうか。 Trueであれば除外する
            segment_type: "SEMANTIC" or "INSTANCE" を指定する。
                          "SEMANTIC"の場合、このラベルのインスタンスは唯一つとなる。
                          "INSTANCE"の場合複数のインスタンスを作成可能となる
            layer: このラベルのレイヤーを指定する。 同じレイヤーのラベルは、頂点を共有することが出来ない。
                   また、大きな値のレイヤーが優先して表示される。
                   指定しない場合は 100

        Returns:

        """
        if segment_type not in (segment_type_semantic, segment_type_instance):
            raise RuntimeError(
                f"segment_typeの値は、{segment_type_semantic} もしくは {segment_type_instance} でなければなりませんが、 {segment_type} でした"
            )
        if layer < 0:
            raise RuntimeError(f"layerは、0以上の整数である必要がありますが、{layer} でした")

        client_loader = ClientLoader(annofab_id, annofab_pass)
        with client_loader.open_api() as api:
            labels = ProjectApi(api).put_segment_label(
                project_id, label_id, ja_name, en_name, color, default_ignore, segment_kind=segment_type, layer=layer,
            )
            labels_json = Label.schema().dumps(labels, many=True, ensure_ascii=False, indent=2)
            logger.info("Label(=%s) を作成・更新しました", label_id)
            logger.info(labels_json)

    @staticmethod
    def put_cuboid_label(
        project_id: str,
        label_id: str,
        ja_name: str,
        en_name: str,
        color: Tuple[int, int, int],
        annofab_id: str = env_annofab_user_id,
        annofab_pass: str = env_annofab_password,
    ) -> None:
        """
        対象のプロジェクトにcuboidのlabelを追加・更新します。
        Args:
            annofab_id:
            annofab_pass:
            project_id: 対象プロジェクト
            label_id: 追加・更新するラベルのid
            ja_name: 日本語名称
            en_name: 　英語名称
            color: ラベルの表示色。 "(R,G,B)"形式の文字列 R/G/Bは、それぞれ0〜255の整数値で指定する

        Returns:

        """
        validate_annofab_credentail(annofab_id, annofab_pass)
        client_loader = ClientLoader(annofab_id, annofab_pass)
        with client_loader.open_api() as api:
            labels = ProjectApi(api).put_cuboid_label(project_id, label_id, ja_name, en_name, color)
            labels_json = Label.schema().dumps(labels, many=True, ensure_ascii=False, indent=2)
            logger.info("Label(=%s) を作成・更新しました", label_id)
            logger.info(labels_json)

    @staticmethod
    def set_whole_annotation_area(annofab_id: str, annofab_pass: str, project_id: str,) -> None:
        """
        対象プロジェクトのアノテーション範囲を、「全体」に設定します。
        すでにアノテーション範囲が設定されていた場合、上書きされます。

        Args:
            annofab_id:
            annofab_pass:
            project_id: 対象プロジェクト

        Returns:

        """
        client_loader = ClientLoader(annofab_id, annofab_pass)
        with client_loader.open_api() as api:
            new_meta = ProjectApi(api).set_annotation_area(project_id, WholeAnnotationArea())
            logger.info("メタデータを更新しました。")
            logger.info(new_meta.to_json(ensure_ascii=False, indent=2))

    @staticmethod
    def set_sphere_annotation_area(annofab_id: str, annofab_pass: str, project_id: str, radius: float) -> None:
        """
        対象プロジェクトのアノテーション範囲を、「球形」に設定します。
        すでにアノテーション範囲が設定されていた場合、上書きされます。

        Args:
            annofab_id:
            annofab_pass:
            project_id: 対象プロジェクト
            radius: アノテーション範囲の半径

        Returns:

        """
        client_loader = ClientLoader(annofab_id, annofab_pass)
        with client_loader.open_api() as api:
            new_meta = ProjectApi(api).set_annotation_area(project_id, SphereAnnotationArea(area_radius=str(radius)))
            logger.info("メタデータを更新しました。")
            logger.info(new_meta.to_json(ensure_ascii=False, indent=2))

    @staticmethod
    def set_rect_annotation_area(
        annofab_id: str, annofab_pass: str, project_id: str, x: Tuple[float, float], y: Tuple[float, float]
    ) -> None:
        """
        対象プロジェクトのアノテーション範囲を、「矩形」に設定します。
        すでにアノテーション範囲が設定されていた場合、上書きされます。

        Args:
            annofab_id:
            annofab_pass:
            project_id: 対象プロジェクト
            x: アノテーション範囲のx座標の範囲
            y: アノテーション範囲のy座標の範囲

        Returns:

        """
        client_loader = ClientLoader(annofab_id, annofab_pass)

        min_x = str(min(x))
        max_x = str(max(x))
        min_y = str(min(y))
        max_y = str(max(y))
        with client_loader.open_api() as api:
            new_meta = ProjectApi(api).set_annotation_area(
                project_id, RectAnnotationArea(area_min_x=min_x, area_max_x=max_x, area_min_y=min_y, area_max_y=max_y)
            )
            logger.info("メタデータを更新しました。")
            logger.info(new_meta.to_json(ensure_ascii=False, indent=2))

    @staticmethod
    def upload_kitti_data(
        annofab_id: str,
        annofab_pass: str,
        project_id: str,
        kitti_dir: str,
        skip: int = 0,
        size: int = 10,
        input_id_prefix: str = "",
        camera_horizontal_fov: Optional[int] = None,
        sensor_height: Optional[float] = None,
        force: bool = False,
    ) -> None:
        """
        kitti 3d detection形式のファイル群を3dpc-editorに登録します。
        Args:
            annofab_id:
            annofab_pass:
            project_id: 登録先のプロジェクトid
            kitti_dir: 登録データの配置ディレクトリへのパス。 このディレクトリに "velodyne" / "image_2" / "calib" の3ディレクトリが存在することを期待している
            skip: 見つけたデータの先頭何件をスキップするか
            size: 最大何件のinput_dataを登録するか
            input_id_prefix: input_data_idの先頭に付与する文字列
            camera_horizontal_fov: カメラのhorizontal FOVの角度[degree] 指定が無い場合はcalibデータから計算する。 calibデータも無い場合はkittiのカメラ仕様を採用する。
            sensor_height: 点群のセンサ(velodyne)の設置高。単位は点群の単位系（=kittiであれば[m]）
                           3dpc-editorは、この値を元に地面の高さを仮定する。 指定が無い場合はkittiのvelodyneの設置高を採用する
            force: 入力データと補助データを上書きしてアップロードするかどうか。
        Returns:

        """
        project = project_id

        kitti_dir_path = Path(kitti_dir)
        loader = FilePathsLoader(kitti_dir_path, kitti_dir_path, kitti_dir_path)
        pathss = loader.load(None)[skip : (skip + size)]
        client_loader = ClientLoader(annofab_id, annofab_pass)
        with client_loader.open_api() as api:
            uploader = Uploader(api, project, force=force)
            # fmt: off
            uploaded = [
                (input_id, len(supps))
                for paths in pathss
                for input_id, supps in [
                    upload(input_id_prefix, uploader, paths, [], camera_horizontal_fov, sensor_height)
                ]
            ]
            # fmt: on

            logger.info("%d 件のinput dataをuploadしました", len(uploaded))
            for input_id, supp_count in uploaded:
                logger.info("id: %s, 補助データ件数: %d", input_id, supp_count)

    @staticmethod
    def upload_scene(
        project_id: str,
        scene_path: str,
        input_data_id_prefix: str = "",
        task_id_prefix: str = "",
        sensor_height: Optional[float] = None,
        frame_per_task: Optional[int] = None,
        upload_kind: str = UploadKind.CREATE_ANNOTATION.value,
        force: bool = False,
        annofab_id: str = env_annofab_user_id,
        annofab_pass: str = env_annofab_password,
    ) -> None:
        """
        拡張kitti形式のファイル群をAnnoFabにアップロードします

        Args:
            annofab_id:
            annofab_pass:
            project_id: 登録先のプロジェクトid
            scene_path: scene.metaファイルのファイルパス or scene.metaファイルの存在するディレクトリパス or kitti形式ディレクトリ
            input_data_id_prefix: アップロードするデータのinput_data_idにつけるprefix
            task_id_prefix: 生成するtaskのidにつけるprefix
            sensor_height: velodyneのセンサ設置高。 velodyne座標系上で -sensor_height 辺りに地面が存在すると認識する。
                           省略した場合、kittiのセンサ高(1.73)を採用する
            frame_per_task: タスクを作る場合、１タスク辺り何個のinput_dataを登録するか。 省略した場合 シーン単位でタスクを作成
            upload_kind: 処理の種類　省略した場合 "annotation" //
                         data => 入力データと補助データの登録のみを行う //
                         task => 上記に加えて、タスクの生成を行う //
                         annotation => 上記に加えて、アノテーションの登録を行う
            force: 入力データと補助データを上書きしてアップロードするかどうか。

        Returns:

        """
        validate_annofab_credentail(annofab_id, annofab_pass)
        client_loader = ClientLoader(annofab_id, annofab_pass)
        with client_loader.open_api() as api:
            uploader = SceneUploader(api)
            uploader_input = SceneUploaderInput(
                project_id=project_id,
                input_data_id_prefix=input_data_id_prefix,
                frame_per_task=frame_per_task,
                sensor_height=sensor_height,
                task_id_prefix=task_id_prefix,
                kind=_decode_enum(UploadKind, upload_kind),
            )
            uploader.upload_from_path(Path(scene_path), uploader_input, force=force)


class LocalCommand:
    """ ローカルファイルシステムに対する処理を行います """

    @staticmethod
    def _write_all_files_json(inputs: List[InputData], output_dir_path: Path):
        all_files_json = output_dir_path / "_all_data.jsonl"
        with all_files_json.open(mode="w", encoding="UTF-8") as writer:
            for input_data in inputs:
                writer.write(input_data.to_json(ensure_ascii=False, sort_keys=True))
                writer.write("\n")

        logger.info("%d 件のinput dataを、%sに出力しました", len(inputs), output_dir_path)
        logger.info("メタデータ: %s", all_files_json.absolute())

    @staticmethod
    def make_kitti_data(
        kitti_dir: str,
        output_dir: str,
        skip: int = 0,
        size: int = 10,
        input_id_prefix: str = "",
        camera_horizontal_fov: Optional[int] = None,
        sensor_height: Optional[float] = None,
    ) -> None:
        """
        kitti 3d detection形式のファイル群を3dpc-editorに登録可能なファイル群に変換します。
        annofabのプライベートストレージを利用する場合にこのコマンドを利用します。

        Args:
            kitti_dir: 登録データの配置ディレクトリへのパス。 このディレクトリに "velodyne" / "image_2" / "calib" の3ディレクトリが存在することを期待している
            output_dir: 出力先ディレクトリ。
            skip: 見つけたデータの先頭何件をスキップするか
            size: 最大何件のinput_dataを登録するか
            input_id_prefix: input_data_idの先頭に付与する文字列
            camera_horizontal_fov: カメラのhorizontal FOVの角度[degree] 指定が無い場合kittiのカメラ仕様を採用する
            sensor_height: 点群のセンサ(velodyne)の設置高。単位は点群の単位系（=kittiであれば[m]）
                           3dpc-editorは、この値を元に地面の高さを仮定する。 指定が無い場合はkittiのvelodyneの設置高を採用する

        Returns:

        """
        kitti_dir_path = Path(kitti_dir)
        output_dir_path = Path(output_dir)
        loader = FilePathsLoader(kitti_dir_path, kitti_dir_path, kitti_dir_path)
        pathss = loader.load(None)[skip : (skip + size)]

        inputs = [
            create_kitti_files(input_id_prefix, output_dir_path, paths, camera_horizontal_fov, sensor_height)
            for paths in pathss
        ]

        LocalCommand._write_all_files_json(inputs, output_dir_path)

    @staticmethod
    def make_scene(
        scene_path: str, output_dir: str, input_data_id_prefix: str = "", sensor_height: Optional[float] = None,
    ) -> None:
        """
        拡張kitti形式のファイル群を3dpc-editorに登録可能なファイル群に変換します。
        annofabのプライベートストレージを利用する場合にこのコマンドを利用します。

        Args:
            scene_path: scene.metaファイルのファイルパス or scene.metaファイルの存在するディレクトリパス or kitti形式ディレクトリ
            output_dir: 出力先ディレクトリ。
            input_data_id_prefix: input_data_idの先頭に付与する文字列
            sensor_height: 点群のセンサ(velodyne)の設置高。単位は点群の単位系（=kittiであれば[m]）
                           3dpc-editorは、この値を元に地面の高さを仮定する。 指定が無い場合はkittiのvelodyneの設置高を採用する

        Returns:

        """
        output_dir_path = Path(output_dir)
        pathss = load_scene_file_paths(Path(scene_path))

        inputs = [
            create_kitti_files(
                input_data_id_prefix, output_dir_path, paths, camera_horizontal_fov=None, sensor_height=sensor_height
            )
            for paths in pathss
        ]

        LocalCommand._write_all_files_json(inputs, output_dir_path)


class Command:
    """ root command """

    def __init__(self):
        self.sandbox = Sandbox()
        self.project = ProjectCommand()
        self.local = LocalCommand()


def main():
    fire.Fire(Command)


if __name__ == "__main__":
    main()

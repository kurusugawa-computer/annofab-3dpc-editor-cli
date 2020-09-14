import logging
import os
import shutil
import tempfile
from pathlib import Path
from typing import Optional, Tuple

import fire

from anno3d.annofab.client import ClientLoader
from anno3d.annofab.project import Label, ProjectApi
from anno3d.annofab.uploader import Uploader
from anno3d.file_paths_loader import FilePathsLoader
from anno3d.model.file_paths import FrameKind
from anno3d.simple_data_uploader import create_frame_meta, create_kitti_files, create_meta_file, upload


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


class Sandbox:
    """ sandboxの再現 """

    @staticmethod
    def upload(annofab_id: str, annofab_pass: str, kitti_dir: str, skip: int = 0, size: int = 10) -> None:
        project = "66241367-9175-40e3-8f2f-391d6891590b"

        kitti_dir_path = Path(kitti_dir)
        loader = FilePathsLoader(kitti_dir_path, kitti_dir_path, kitti_dir_path)
        pathss = loader.load(FrameKind.testing)[skip : (skip + size)]
        client_loader = ClientLoader(annofab_id, annofab_pass)
        with client_loader.open_api() as api:
            uploader = Uploader(api, project)
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
    ) -> None:
        velo_files = [Path(velo_dir) / path for path in os.listdir(velo_dir)]

        client_loader = ClientLoader(annofab_id, annofab_pass)
        with client_loader.open_api() as api:
            with tempfile.TemporaryDirectory() as tempdir_str:
                tempdir = Path(tempdir_str)
                uploader = Uploader(api, project_id)
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
    def put_cuboid_label(
        annofab_id: str,
        annofab_pass: str,
        project_id: str,
        label_id: str,
        ja_name: str,
        en_name: str,
        color: Tuple[int, int, int],
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
        client_loader = ClientLoader(annofab_id, annofab_pass)
        with client_loader.open_api() as api:
            labels = ProjectApi(api).put_cuboid_label(project_id, label_id, ja_name, en_name, color)
            labels_json = Label.schema().dumps(labels, many=True, ensure_ascii=False, indent=2)
            logger.info("Label(=%s) を作成・更新しました", label_id)
            logger.info(labels_json)

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
        # layer / segment_typeは3dpcエディタ側で未実装なので入力させない
        # layer: int,
        # segment_type: str,
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

        Returns:

        """
        client_loader = ClientLoader(annofab_id, annofab_pass)
        with client_loader.open_api() as api:
            labels = ProjectApi(api).put_segment_label(project_id, label_id, ja_name, en_name, color, default_ignore)
            labels_json = Label.schema().dumps(labels, many=True, ensure_ascii=False, indent=2)
            logger.info("Label(=%s) を作成・更新しました", label_id)
            logger.info(labels_json)

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
    ):
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
            camera_horizontal_fov: カメラのhorizontal FOVの角度[degree] 指定が無い場合kittiのカメラ仕様を採用する
            sensor_height: 点群のセンサ(velodyne)の設置高。単位は点群の単位系（=kittiであれば[m]）
                           3dpc-editorは、この値を元に地面の高さを仮定する。 指定が無い場合はkittiのvelodyneの設置高を採用する
        Returns:

        """
        project = project_id

        kitti_dir_path = Path(kitti_dir)
        loader = FilePathsLoader(kitti_dir_path, kitti_dir_path, kitti_dir_path)
        pathss = loader.load(None)[skip : (skip + size)]
        client_loader = ClientLoader(annofab_id, annofab_pass)
        with client_loader.open_api() as api:
            uploader = Uploader(api, project)
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


class LocalCommand:
    """ ローカルファイルシステムに対する処理を行います """

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

        all_files_json = output_dir_path / "_all_data.jsonl"
        with all_files_json.open(mode="w", encoding="UTF-8") as writer:
            for input_data in inputs:
                writer.write(input_data.to_json(ensure_ascii=False, sort_keys=True))
                writer.write("\n")

        logger.info("%d 件のinput dataを、%sに出力しました", len(inputs), output_dir_path)
        logger.info("メタデータ: %s", all_files_json.absolute())


class Command:
    """ root command """

    def __init__(self):
        self.sandbox = Sandbox()
        self.project = ProjectCommand()
        self.local = LocalCommand()


if __name__ == "__main__":
    fire.Fire(Command)

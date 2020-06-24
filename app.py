import logging
import shutil
from pathlib import Path
from typing import Tuple

import fire

from anno3d.annofab.client import ClientLoader
from anno3d.annofab.project import Label, Project
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
                upload("", uploader, paths, [hidari, migi])

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


class ProjectCommand:
    """ プロジェクトの操作を行うためのサブコマンドです """

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
            created_project_id = Project(api).create_custom_project(
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
        """
        対象のプロジェクトのlabelを追加・更新します。
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
            labels = Project(api).put_label(project_id, label_id, ja_name, en_name, color)
            labels_json = Label.schema().dumps(labels, many=True, ensure_ascii=False, indent=2)
            logger.info("Label(=%s) を作成・更新しました", label_id)
            logger.info(labels_json)

    @staticmethod
    def upload_kitti_data(
        annofab_id: str, annofab_pass: str, project_id: str, kitti_dir: str, skip: int = 0, size: int = 10
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
                for input_id, supps in [upload(input_id_prefix, uploader, paths, [])]
            ]
            # fmt: on

            logger.info("%d 件のinput dataをuploadしました", len(uploaded))
            for input_id, supp_count in uploaded:
                logger.info("id: %s, 補助データ件数: %d", input_id, supp_count)


class Command:
    """ root command """

    def __init__(self):
        self.sandbox = Sandbox()
        self.project = ProjectCommand()


if __name__ == "__main__":
    fire.Fire(Command)

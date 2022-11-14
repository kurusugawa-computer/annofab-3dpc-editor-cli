import asyncio
import logging
import os
import sys
from enum import Enum
from pathlib import Path
from typing import Any, List, Literal, Optional, Tuple, Type, TypeVar, cast

import boto3
import fire

from anno3d import __version__
from anno3d.annofab.client import ClientLoader
from anno3d.annofab.constant import segment_type_instance, segment_type_semantic
from anno3d.annofab.project import Label, ProjectApi
from anno3d.annofab.uploader import AnnofabStorageUploader, S3Uploader
from anno3d.file_paths_loader import FilePathsLoader, ScenePathsLoader
from anno3d.kitti.camera_horizontal_fov_provider import CameraHorizontalFovKind
from anno3d.kitti.scene_uploader import SceneUploader, SceneUploaderInput, UploadKind
from anno3d.model.annotation_area import RectAnnotationArea, SphereAnnotationArea, WholeAnnotationArea
from anno3d.model.file_paths import FilePaths
from anno3d.model.input_files import InputData
from anno3d.simple_data_uploader import SupplementaryData, create_kitti_files, upload_async

E = TypeVar("E", bound=Enum)


def _decode_enum(enum: Type[E], value: Any) -> E:
    for e in enum:
        if e.value == value:
            return e

    raise ValueError(f"{value}は有効な、{enum.__name__}型の値ではありません")


def add_stdout_handler(target: logging.Logger, level: int = logging.INFO):
    handler = logging.StreamHandler()
    handler.setLevel(level)
    handler.setFormatter(logging.Formatter("[%(asctime)s] [%(process)d] [%(name)s] [%(levelname)s] %(message)s"))
    target.addHandler(handler)


root_logger = logging.getLogger()
root_logger.level = logging.INFO
add_stdout_handler(root_logger, logging.INFO)

logger = logging.getLogger(__name__)

env_annofab_user_id = os.environ.get("ANNOFAB_USER_ID")
env_annofab_password = os.environ.get("ANNOFAB_PASSWORD")
env_annofab_endpoint = os.environ.get("ANNOFAB_ENDPOINT")


def validate_annofab_credential(annofab_id: Optional[str], annofab_pass: Optional[str]) -> bool:
    """
    Annofabの認証情報が指定されていることを確認します。
    どちらかが指定されていない場合は処理を終了します。
    """
    if annofab_id is None:
        print(
            "AnnofabのユーザIDが指定されていないため、終了します。環境変数'ANNOFAB_USER_ID' または コマンドライン引数 '--annofab_id' にユーザIDを指定してください。",
            file=sys.stderr,
        )
        return False
    if annofab_pass is None:
        print(
            "Annofabのパスワードが指定されていないため、終了します。環境変数'ANNOFAB_PASSWORD' または コマンドライン引数 '--annofab_pass' にパスワードを指定してください。",
            file=sys.stderr,
        )
        return False
    return True


def validate_aws_credentail() -> bool:
    if boto3.DEFAULT_SESSION is None:
        boto3.setup_default_session()
    result = boto3.DEFAULT_SESSION.get_credentials() is not None  # type: ignore
    if not result:
        print(
            "AWSの認証情報が正しくないため、終了します。"
            "https://boto3.amazonaws.com/v1/documentation/api/latest/guide/credentials.html "
            "を参考にして認証情報を設定してください。",
            file=sys.stderr,
        )
    return result


def validate_task_id_prefix(task_id_prefix: str, upload_kind: UploadKind) -> bool:
    if upload_kind in [UploadKind.CREATE_TASK, UploadKind.CREATE_ANNOTATION]:
        if task_id_prefix == "":
            print(
                "'--upload_kind'の値が`task`または'annotation'の場合は、'--task_id_prefix'を指定してください。",
                file=sys.stderr,
            )
            return False
    return True


class ProjectCommand:
    """Annofabプロジェクトの操作を行うためのサブコマンドです"""

    @staticmethod
    def create(
        title: str,
        organization_name: str,
        project_id: str = "",
        plugin_id: str = "",
        specs_plugin_id: str = "",
        overview: str = "",
        annofab_id: Optional[str] = env_annofab_user_id,
        annofab_pass: Optional[str] = env_annofab_password,
        annofab_endpoint: Optional[str] = env_annofab_endpoint,
    ) -> None:
        """
        新しい三次元エディタプロジェクトを生成します。

        Args:
            annofab_id: AnnofabのユーザID。指定が無い場合は環境変数`ANNOFAB_USER_ID`の値を採用する
            annofab_pass: Annofabのパスワード。指定が無い場合は環境変数`ANNOFAB_PASSWORD`の値を採用する
            annofab_endpoint: AnnofabのAPIアクセス先エンドポイントを指定します。 省略した場合は環境変数`ANNOFAB_ENDPOINT`の値を利用します。\
                              環境変数も指定されていない場合、デフォルトのエンドポイント（https://annofab.com）を利用します
            title: projectのタイトル
            organization_name: projectを所属させる組織の名前
            plugin_id: このプロジェクトで使用する、組織に登録されている三次元エディタプラグインのid。 省略時は標準プラグインを利用します
            specs_plugin_id: このプロジェクトで使用する、組織に登録されている拡張仕様プラグインのid。 省略時は標準プラグインを利用します
            project_id: 作成するprojectのid。省略した場合自動的にuuidが設定されます。
            overview:  projectの概要

        Returns:

        """
        if not validate_annofab_credential(annofab_id, annofab_pass):
            return
        assert annofab_id is not None and annofab_pass is not None
        client_loader = ClientLoader(annofab_id, annofab_pass, annofab_endpoint)
        with client_loader.open_api() as api:
            created_project_id = ProjectApi(api).create_custom_project(
                title=title,
                organization_name=organization_name,
                editor_plugin_id=plugin_id,
                specs_plugin_id=specs_plugin_id,
                project_id=project_id,
                overview=overview,
            )
            logger.info("プロジェクト(=%s)を作成しました。", created_project_id)

    @staticmethod
    def put_cuboid_label(
        project_id: str,
        en_name: str,
        label_id: str = "",
        ja_name: str = "",
        color: Optional[Tuple[int, int, int]] = None,
        annofab_id: Optional[str] = env_annofab_user_id,
        annofab_pass: Optional[str] = env_annofab_password,
        annofab_endpoint: Optional[str] = env_annofab_endpoint,
    ) -> None:
        """
        対象のプロジェクトにcuboidのlabelを追加・更新します。
        Args:
            annofab_id: AnnofabのユーザID。指定が無い場合は環境変数`ANNOFAB_USER_ID`の値を採用する
            annofab_pass: Annofabのパスワード。指定が無い場合は環境変数`ANNOFAB_PASSWORD`の値を採用する
            annofab_endpoint: AnnofabのAPIアクセス先エンドポイントを指定します。 省略した場合は環境変数`ANNOFAB_ENDPOINT`の値を利用します。\
                              環境変数も指定されていない場合、デフォルトのエンドポイント（https://annofab.com）を利用します
            project_id: 対象プロジェクト
            en_name: 　英語名称
            label_id: 追加・更新するラベルのid。指定しない場合はuuidが設定される。
            ja_name: 日本語名称。指定しない場合はen_nameと同じ名称が設定される。
            color: ラベルの表示色。 "(R,G,B)"形式の文字列 R/G/Bは、それぞれ0〜255の整数値で指定する。\
                                        指定しない場合はランダムに設定される。

        Returns:

        """
        if not validate_annofab_credential(annofab_id, annofab_pass):
            return
        assert annofab_id is not None and annofab_pass is not None
        # 数値に変換可能な場合は型がintに変わるので、strに明示的に変換する。
        label_id = str(label_id)
        validate_annofab_credential(annofab_id, annofab_pass)
        client_loader = ClientLoader(annofab_id, annofab_pass, annofab_endpoint)
        with client_loader.open_api() as api:
            labels = ProjectApi(api).put_cuboid_label(project_id, en_name, label_id, ja_name, color)
            labels_json = Label.schema().dumps(labels, many=True, ensure_ascii=False, indent=2)
            logger.info("Label(=%s) を作成・更新しました", label_id)
            logger.info(labels_json)

    @staticmethod
    def put_segment_label(
        project_id: str,
        en_name: str,
        segment_type: str,
        default_ignore: Optional[bool] = None,
        layer: int = 100,
        label_id: str = "",
        ja_name: str = "",
        color: Optional[Tuple[int, int, int]] = None,
        annofab_id: Optional[str] = env_annofab_user_id,
        annofab_pass: Optional[str] = env_annofab_password,
        annofab_endpoint: Optional[str] = env_annofab_endpoint,
    ) -> None:
        """
        対象のプロジェクトにsegmentのlabelを追加・更新します。
        Args:
            annofab_id: AnnofabのユーザID。指定が無い場合は環境変数`ANNOFAB_USER_ID`の値を採用する
            annofab_pass: Annofabのパスワード。指定が無い場合は環境変数`ANNOFAB_PASSWORD`の値を採用する
            annofab_endpoint: AnnofabのAPIアクセス先エンドポイントを指定します。 省略した場合は環境変数`ANNOFAB_ENDPOINT`の値を利用します。\
                              環境変数も指定されていない場合、デフォルトのエンドポイント（https://annofab.com）を利用します
            project_id: 対象プロジェクト
            en_name: 　英語名称
            default_ignore: deprecated。Annofabの標準プラグインを利用したプロジェクトでは指定しても無視されます。 \
                            このラベルがついた領域を、デフォルトでは他のアノテーションから除外するかどうか。 Trueであれば除外します。
            segment_type: "SEMANTIC" or "INSTANCE" を指定する。
                          "SEMANTIC"の場合、このラベルのインスタンスは唯一つとなる。
                          "INSTANCE"の場合複数のインスタンスを作成可能となる
            layer: このラベルのレイヤーを指定する。 同じレイヤーのラベルは、頂点を共有することが出来ない。
                   また、大きな値のレイヤーが優先して表示される。
                   指定しない場合は 100
            label_id: 追加・更新するラベルのid。指定しない場合はuuidが設定される。
            ja_name: 日本語名称。指定しない場合はen_nameと同じ名称が設定される。
            color: ラベルの表示色。 "(R,G,B)"形式の文字列 R/G/Bは、それぞれ0〜255の整数値で指定する。\
                                        指定しない場合はランダムに設定される。

        Returns:

        """
        if not validate_annofab_credential(annofab_id, annofab_pass):
            return
        assert annofab_id is not None and annofab_pass is not None
        # 数値に変換可能な場合は型がintに変わるので、strに明示的に変換する。
        label_id = str(label_id)

        if segment_type not in (segment_type_semantic, segment_type_instance):
            raise RuntimeError(
                f"segment_typeの値は、{segment_type_semantic} もしくは {segment_type_instance} でなければなりませんが、 {segment_type} でした"
            )
        safe_segment_type = cast(Literal["SEMANTIC", "INSTANCE"], segment_type)
        if layer < 0:
            raise RuntimeError(f"layerは、0以上の整数である必要がありますが、{layer} でした")

        client_loader = ClientLoader(annofab_id, annofab_pass, annofab_endpoint)
        with client_loader.open_api() as api:
            labels = ProjectApi(api).put_segment_label(
                project_id,
                en_name,
                default_ignore,
                segment_kind=safe_segment_type,
                layer=layer,
                label_id=label_id,
                ja_name=ja_name,
                color=color,
            )
            labels_json = Label.schema().dumps(labels, many=True, ensure_ascii=False, indent=2)
            logger.info("Label(=%s) を作成・更新しました", label_id)
            logger.info(labels_json)

    @staticmethod
    def set_whole_annotation_area(
        project_id: str,
        annofab_id: Optional[str] = env_annofab_user_id,
        annofab_pass: Optional[str] = env_annofab_password,
        annofab_endpoint: Optional[str] = env_annofab_endpoint,
    ) -> None:
        """
        対象プロジェクトのアノテーション範囲を、「全体」に設定します。
        すでにアノテーション範囲が設定されていた場合、上書きされます。

        Args:
            annofab_id: AnnofabのユーザID。指定が無い場合は環境変数`ANNOFAB_USER_ID`の値を採用する
            annofab_pass: Annofabのパスワード。指定が無い場合は環境変数`ANNOFAB_PASSWORD`の値を採用する
            annofab_endpoint: AnnofabのAPIアクセス先エンドポイントを指定します。 省略した場合は環境変数`ANNOFAB_ENDPOINT`の値を利用します。\
                              環境変数も指定されていない場合、デフォルトのエンドポイント（https://annofab.com）を利用します
            project_id: 対象プロジェクト

        Returns:

        """
        if not validate_annofab_credential(annofab_id, annofab_pass):
            return

        assert annofab_id is not None and annofab_pass is not None
        client_loader = ClientLoader(annofab_id, annofab_pass, annofab_endpoint)
        with client_loader.open_api() as api:
            new_meta = ProjectApi(api).set_annotation_area(project_id, WholeAnnotationArea())
            logger.info("メタデータを更新しました。")
            logger.info(new_meta.to_json(ensure_ascii=False, indent=2))

    @staticmethod
    def set_sphere_annotation_area(
        project_id: str,
        radius: float,
        annofab_id: Optional[str] = env_annofab_user_id,
        annofab_pass: Optional[str] = env_annofab_password,
        annofab_endpoint: Optional[str] = env_annofab_endpoint,
    ) -> None:
        """
        対象プロジェクトのアノテーション範囲を、「球形」に設定します。
        すでにアノテーション範囲が設定されていた場合、上書きされます。

        Args:
            annofab_id: AnnofabのユーザID。指定が無い場合は環境変数`ANNOFAB_USER_ID`の値を採用する
            annofab_pass: Annofabのパスワード。指定が無い場合は環境変数`ANNOFAB_PASSWORD`の値を採用する
            annofab_endpoint: AnnofabのAPIアクセス先エンドポイントを指定します。 省略した場合は環境変数`ANNOFAB_ENDPOINT`の値を利用します。\
                              環境変数も指定されていない場合、デフォルトのエンドポイント（https://annofab.com）を利用します
            project_id: 対象プロジェクト
            radius: アノテーション範囲の半径

        Returns:

        """
        if not validate_annofab_credential(annofab_id, annofab_pass):
            return

        assert annofab_id is not None and annofab_pass is not None
        client_loader = ClientLoader(annofab_id, annofab_pass, annofab_endpoint)
        with client_loader.open_api() as api:
            new_meta = ProjectApi(api).set_annotation_area(project_id, SphereAnnotationArea(area_radius=str(radius)))
            logger.info("メタデータを更新しました。")
            logger.info(new_meta.to_json(ensure_ascii=False, indent=2))

    @staticmethod
    def set_rect_annotation_area(
        project_id: str,
        x: Tuple[float, float],
        y: Tuple[float, float],
        annofab_id: Optional[str] = env_annofab_user_id,
        annofab_pass: Optional[str] = env_annofab_password,
        annofab_endpoint: Optional[str] = env_annofab_endpoint,
    ) -> None:
        """
        対象プロジェクトのアノテーション範囲を、「矩形」に設定します。
        すでにアノテーション範囲が設定されていた場合、上書きされます。

        Args:
            annofab_id: AnnofabのユーザID。指定が無い場合は環境変数`ANNOFAB_USER_ID`の値を採用する
            annofab_pass: Annofabのパスワード。指定が無い場合は環境変数`ANNOFAB_PASSWORD`の値を採用する
            annofab_endpoint: AnnofabのAPIアクセス先エンドポイントを指定します。 省略した場合は環境変数`ANNOFAB_ENDPOINT`の値を利用します。\
                              環境変数も指定されていない場合、デフォルトのエンドポイント（https://annofab.com）を利用します
            project_id: 対象プロジェクト
            x: アノテーション範囲のx座標の範囲
            y: アノテーション範囲のy座標の範囲

        Returns:

        """
        if not validate_annofab_credential(annofab_id, annofab_pass):
            return

        assert annofab_id is not None and annofab_pass is not None
        client_loader = ClientLoader(annofab_id, annofab_pass, annofab_endpoint)

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
    def remove_preset_cuboid_size(
        project_id: str,
        key_name: str,
        annofab_id: Optional[str] = env_annofab_user_id,
        annofab_pass: Optional[str] = env_annofab_password,
        annofab_endpoint: Optional[str] = env_annofab_endpoint,
    ) -> None:
        """
        対象のプロジェクトからcuboidの規定サイズを削除します。

        Args:
            annofab_id: AnnofabのユーザID。指定が無い場合は環境変数`ANNOFAB_USER_ID`の値を採用する
            annofab_pass: Annofabのパスワード。指定が無い場合は環境変数`ANNOFAB_PASSWORD`の値を採用する
            annofab_endpoint: AnnofabのAPIアクセス先エンドポイントを指定します。 省略した場合は環境変数`ANNOFAB_ENDPOINT`の値を利用します。\
                              環境変数も指定されていない場合、デフォルトのエンドポイント（https://annofab.com）を利用します
            project_id: 対象プロジェクト
            key_name: 削除する規定サイズの名前(英数字)。
                      `presetCuboidSize{Key_name}`というキーのメタデータが削除される(Key_nameはkey_nameの頭文字を大文字にしたもの)

        Returns:

        """
        if not validate_annofab_credential(annofab_id, annofab_pass):
            return

        assert key_name.isalnum()
        assert annofab_id is not None and annofab_pass is not None
        client_loader = ClientLoader(annofab_id, annofab_pass, annofab_endpoint)

        with client_loader.open_api() as api:
            new_meta = ProjectApi(api).remove_preset_cuboid_size(project_id, key_name)
            logger.info("メタデータを更新しました。")
            logger.info(new_meta.to_json(ensure_ascii=False, indent=2))

    @staticmethod
    def add_preset_cuboid_size(
        project_id: str,
        key_name: str,
        ja_name: str,
        en_name: str,
        width: float,
        height: float,
        depth: float,
        order: int,
        annofab_id: Optional[str] = env_annofab_user_id,
        annofab_pass: Optional[str] = env_annofab_password,
        annofab_endpoint: Optional[str] = env_annofab_endpoint,
    ) -> None:
        """
        対象のプロジェクトにcuboidの規定サイズを追加・更新します。

        Args:
            annofab_id: AnnofabのユーザID。指定が無い場合は環境変数`ANNOFAB_USER_ID`の値を採用する
            annofab_pass: Annofabのパスワード。指定が無い場合は環境変数`ANNOFAB_PASSWORD`の値を採用する
            annofab_endpoint: AnnofabのAPIアクセス先エンドポイントを指定します。 省略した場合は環境変数`ANNOFAB_ENDPOINT`の値を利用します。\
                              環境変数も指定されていない場合、デフォルトのエンドポイント（https://annofab.com）を利用します
            project_id: 対象プロジェクト
            key_name: 追加・更新する規定サイズの名前(英数字)。
                      `presetCuboidSize{Key_name}`というメタデータ・キーに対して規定サイズが設定される（Key_nameはkey_nameの頭文字を大文字にしたもの）
            ja_name: 日本語名称
            en_name: 英語名称
            width: 追加・更新する規定サイズの幅（Cuboidのlocal axisにおけるY軸方向の長さ）
            height: 追加・更新する規定サイズの高さ（Cuboidのlocal axisにおけるZ軸方向の長さ）
            depth: 追加・更新する規定サイズの奥行（Cuboidのlocal axisにおけるX軸方向の長さ）
            order: エディタ上での表示順を決めるのに使用される整数（昇順で並べられる）

        Returns:

        """
        if not validate_annofab_credential(annofab_id, annofab_pass):
            return

        assert key_name.isalnum()
        assert annofab_id is not None and annofab_pass is not None
        client_loader = ClientLoader(annofab_id, annofab_pass, annofab_endpoint)

        with client_loader.open_api() as api:
            new_meta = ProjectApi(api).add_preset_cuboid_size(
                project_id, key_name, ja_name, en_name, width, height, depth, order
            )
            logger.info("メタデータを更新しました。")
            logger.info(new_meta.to_json(ensure_ascii=False, indent=2))

    @staticmethod
    def upload_kitti_data(
        project_id: str,
        kitti_dir: str,
        skip: int = 0,
        size: int = 10,
        input_data_id_prefix: str = "",
        sensor_height: Optional[float] = None,
        parallelism: Optional[int] = None,
        force: bool = False,
        annofab_id: Optional[str] = env_annofab_user_id,
        annofab_pass: Optional[str] = env_annofab_password,
        annofab_endpoint: Optional[str] = env_annofab_endpoint,
    ) -> None:
        """
        kitti 3d detection形式のファイル群を3dpc-editorに登録します。
        Args:
            annofab_id: AnnofabのユーザID。指定が無い場合は環境変数`ANNOFAB_USER_ID`の値を採用する
            annofab_pass: Annofabのパスワード。指定が無い場合は環境変数`ANNOFAB_PASSWORD`の値を採用する
            annofab_endpoint: AnnofabのAPIアクセス先エンドポイントを指定します。 省略した場合は環境変数`ANNOFAB_ENDPOINT`の値を利用します。\
                              環境変数も指定されていない場合、デフォルトのエンドポイント（https://annofab.com）を利用します
            project_id: 登録先のプロジェクトid
            kitti_dir: 登録データの配置ディレクトリへのパス。 このディレクトリに "velodyne" / "image_2" / "calib" の3ディレクトリが存在することを期待している
            skip: 見つけたデータの先頭何件をスキップするか
            size: 最大何件のinput_dataを登録するか
            input_data_id_prefix: input_data_idの先頭に付与する文字列
            sensor_height: 点群のセンサ(velodyne)の設置高。単位は点群の単位系（=kittiであれば[m]）
                           3dpc-editorは、この値を元に地面の高さを仮定する。 指定が無い場合はkittiのvelodyneの設置高を採用する
            parallelism: 非同期実行の最大数。 指定しない場合上限を設定しない。実行環境におけるデフォルトのThreadPoolExecutorの最大スレッド数を超える値を与えても意味がない。
            force: 入力データと補助データを上書きしてアップロードするかどうか。
        Returns:

        """
        if not validate_annofab_credential(annofab_id, annofab_pass):
            return

        assert annofab_id is not None and annofab_pass is not None
        asyncio.run(
            ProjectCommand._upload_kitti_data_async(
                project_id,
                kitti_dir,
                annofab_endpoint,
                skip,
                size,
                input_data_id_prefix,
                sensor_height,
                parallelism,
                force,
                annofab_id,
                annofab_pass,
            )
        )

    @staticmethod
    async def _upload_kitti_data_async(
        project_id: str,
        kitti_dir: str,
        annofab_endpoint: Optional[str],
        skip: int,
        size: int,
        input_data_id_prefix: str,
        sensor_height: Optional[float],
        parallelism: Optional[int],
        force: bool,
        annofab_id: str,
        annofab_pass: str,
    ) -> None:
        project = project_id

        kitti_dir_path = Path(kitti_dir)
        loader = FilePathsLoader(kitti_dir_path, kitti_dir_path, kitti_dir_path)
        pathss = loader.load(None)[skip : (skip + size)]
        client_loader = ClientLoader(annofab_id, annofab_pass, annofab_endpoint)
        sem_opt = asyncio.Semaphore(parallelism) if parallelism is not None else None

        async def run_without_sem(paths: FilePaths) -> Tuple[str, List[SupplementaryData]]:
            return await upload_async(
                input_data_id_prefix,
                uploader,
                paths,
                [],
                camera_horizontal_fov=CameraHorizontalFovKind.CALIB,
                fallback_horizontal_fov=None,
                sensor_height=sensor_height,
            )

        async def run_with_sem(paths: FilePaths, sem: asyncio.Semaphore) -> Tuple[str, List[SupplementaryData]]:
            async with sem:
                return await run_without_sem(paths)

        async def run(paths: FilePaths) -> Tuple[str, List[SupplementaryData]]:
            if sem_opt is None:
                return await run_without_sem(paths)
            else:
                return await run_with_sem(paths, sem_opt)

        with client_loader.open_api() as api:
            uploader = AnnofabStorageUploader(api, project, force=force)

            # fmt: off
            tasks = [
                run(paths)
                for paths in pathss
            ]
            uploaded: List[Tuple[str, int]] = [
                (input_id, len(supps))
                for input_id, supps in await asyncio.gather(*tasks)
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
        camera_horizontal_fov: Literal["calib", "settings"] = "settings",
        sensor_height: Optional[float] = None,
        frame_per_task: Optional[int] = None,
        upload_kind: str = UploadKind.CREATE_ANNOTATION.value,
        parallelism: Optional[int] = None,
        force: bool = False,
        annofab_id: Optional[str] = env_annofab_user_id,
        annofab_pass: Optional[str] = env_annofab_password,
        annofab_endpoint: Optional[str] = env_annofab_endpoint,
    ) -> None:
        """
        Annofab点群形式（KITTIベース）のファイル群をAnnofabにアップロードします

        Args:
            annofab_id: AnnofabのユーザID。指定が無い場合は環境変数`ANNOFAB_USER_ID`の値を採用する
            annofab_pass: Annofabのパスワード。指定が無い場合は環境変数`ANNOFAB_PASSWORD`の値を採用する
            annofab_endpoint: AnnofabのAPIアクセス先エンドポイントを指定します。 省略した場合は環境変数`ANNOFAB_ENDPOINT`の値を利用します。\
                              環境変数も指定されていない場合、デフォルトのエンドポイント（https://annofab.com）を利用します
            project_id: 登録先のプロジェクトid
            scene_path: scene.metaファイルのファイルパス or scene.metaファイルの存在するディレクトリパス or kitti形式ディレクトリ
            input_data_id_prefix: アップロードするデータのinput_data_idにつけるprefix
            task_id_prefix: 生成するtaskのidにつけるprefix
            camera_horizontal_fov: 補助画像カメラの視野角の取得方法の指定。 省略した場合"settings" //
                                   settings => 対象の画像にcamera_view_settingが存在していればその値を利用し、無ければ"calib"と同様 //
                                   calib => 対象の画像にキャリブレーションデータが存在すればそこから計算し、なければ90ととする
            sensor_height: velodyneのセンサ設置高。 velodyne座標系上で -sensor_height 辺りに地面が存在すると認識する。
                           省略した場合、kittiのセンサ高(1.73)を採用する
            frame_per_task: タスクを作る場合、１タスク辺り何個のinput_dataを登録するか。 省略した場合 シーン単位でタスクを作成
            upload_kind: 処理の種類　省略した場合 "annotation" //
                         data => 入力データと補助データの登録のみを行う //
                         task => 上記に加えて、タスクの生成を行う //
                         annotation => 上記に加えて、アノテーションの登録を行う
            parallelism: 非同期実行の最大数。 指定しない場合上限を設定しない。実行環境におけるデフォルトのThreadPoolExecutorの最大スレッド数を超える値を与えても意味がない。
            force: 入力データと補助データを上書きしてアップロードするかどうか。

        Returns:

        """
        if not validate_annofab_credential(annofab_id, annofab_pass):
            return

        enum_upload_kind = _decode_enum(UploadKind, upload_kind)
        if not validate_task_id_prefix(task_id_prefix, enum_upload_kind):
            return

        assert annofab_id is not None and annofab_pass is not None
        client_loader = ClientLoader(annofab_id, annofab_pass, annofab_endpoint)
        with client_loader.open_api() as api:
            scene_uploader = SceneUploader(
                api, AnnofabStorageUploader(api, project=project_id, force=force), parallelism
            )
            uploader_input = SceneUploaderInput(
                project_id=project_id,
                input_data_id_prefix=input_data_id_prefix,
                frame_per_task=frame_per_task,
                camera_horizontal_fov=_decode_enum(CameraHorizontalFovKind, camera_horizontal_fov),
                sensor_height=sensor_height,
                task_id_prefix=task_id_prefix,
                kind=enum_upload_kind,
            )
            scene_uploader.upload_from_path(Path(scene_path), uploader_input)

    @staticmethod
    def upload_scene_to_s3(
        project_id: str,
        scene_path: str,
        s3_path: str,
        input_data_id_prefix: str = "",
        task_id_prefix: str = "",
        camera_horizontal_fov: Literal["calib", "settings"] = "settings",
        sensor_height: Optional[float] = None,
        frame_per_task: Optional[int] = None,
        upload_kind: str = UploadKind.CREATE_ANNOTATION.value,
        parallelism: Optional[int] = None,
        force: bool = False,
        annofab_id: Optional[str] = env_annofab_user_id,
        annofab_pass: Optional[str] = env_annofab_password,
        annofab_endpoint: Optional[str] = env_annofab_endpoint,
    ) -> None:
        """
        Annofab点群形式（KITTIベース）のファイル群をAWS S3にアップロードした上で、3dpc-editorに登録します。

        Args:
            s3_path: 登録先のS3パス（ex: "{bucket}/{key}"）
            project_id: 登録先のプロジェクトid
            scene_path: scene.metaファイルのファイルパス or scene.metaファイルの存在するディレクトリパス or kitti形式ディレクトリ
            input_data_id_prefix: アップロードするデータのinput_data_idにつけるprefix
            task_id_prefix: 生成するtaskのidにつけるprefix
            camera_horizontal_fov: 補助画像カメラの視野角の取得方法の指定。 省略した場合"settings" //
                                   settings => 対象の画像にcamera_view_settingが存在していればその値を利用し、無ければ"calib"と同様 //
                                   calib => 対象の画像にキャリブレーションデータが存在すればそこから計算し、なければ90[degree]ととする
            sensor_height: velodyneのセンサ設置高。 velodyne座標系上で -sensor_height 辺りに地面が存在すると認識する。
                           省略した場合、kittiのセンサ高(1.73)を採用する
            frame_per_task: タスクを作る場合、１タスク辺り何個のinput_dataを登録するか。 省略した場合 シーン単位でタスクを作成
            upload_kind: 処理の種類　省略した場合 "annotation" //
                         data => 入力データと補助データの登録のみを行う //
                         task => 上記に加えて、タスクの生成を行う //
                         annotation => 上記に加えて、アノテーションの登録を行う
            parallelism: 非同期実行の最大数。 指定しない場合上限を設定しない。実行環境におけるデフォルトのThreadPoolExecutorの最大スレッド数を超える値を与えても意味がない。
            force: 入力データと補助データを上書きしてアップロードするかどうか。
            annofab_id: AnnofabのユーザID。指定が無い場合は環境変数`ANNOFAB_USER_ID`の値を採用する
            annofab_pass: Annofabのパスワード。指定が無い場合は環境変数`ANNOFAB_PASSWORD`の値を採用する
            annofab_endpoint: AnnofabのAPIアクセス先エンドポイントを指定します。 省略した場合は環境変数`ANNOFAB_ENDPOINT`の値を利用します。\
                              環境変数も指定されていない場合、デフォルトのエンドポイント（https://annofab.com）を利用します
        """
        if not validate_annofab_credential(annofab_id, annofab_pass):
            return
        assert annofab_id is not None and annofab_pass is not None
        if not validate_aws_credentail():
            return

        enum_upload_kind = _decode_enum(UploadKind, upload_kind)
        if not validate_task_id_prefix(task_id_prefix, enum_upload_kind):
            return

        client_loader = ClientLoader(annofab_id, annofab_pass, annofab_endpoint)
        with client_loader.open_api() as api:
            uploader = SceneUploader(
                api, S3Uploader(api, project=project_id, force=force, s3_path=s3_path), parallelism
            )
            uploader_input = SceneUploaderInput(
                project_id=project_id,
                input_data_id_prefix=input_data_id_prefix,
                frame_per_task=frame_per_task,
                camera_horizontal_fov=_decode_enum(CameraHorizontalFovKind, camera_horizontal_fov),
                sensor_height=sensor_height,
                task_id_prefix=task_id_prefix,
                kind=enum_upload_kind,
            )
            uploader.upload_from_path(Path(scene_path), uploader_input)


class LocalCommand:
    """ローカルファイルシステムに対する処理を行います"""

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
        input_data_id_prefix: str = "",
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
            input_data_id_prefix: input_data_idの先頭に付与する文字列
            sensor_height: 点群のセンサ(velodyne)の設置高。単位は点群の単位系（=kittiであれば[m]）
                           3dpc-editorは、この値を元に地面の高さを仮定する。 指定が無い場合はkittiのvelodyneの設置高を採用する
        Returns:
        """
        kitti_dir_path = Path(kitti_dir)
        output_dir_path = Path(output_dir)
        loader = FilePathsLoader(kitti_dir_path, kitti_dir_path, kitti_dir_path)
        pathss = loader.load(None)[skip : (skip + size)]

        inputs = [
            create_kitti_files(
                input_data_id_prefix, output_dir_path, paths, CameraHorizontalFovKind.CALIB, None, sensor_height
            )
            for paths in pathss
        ]

        LocalCommand._write_all_files_json(inputs, output_dir_path)

    @staticmethod
    def make_scene(
        scene_path: str,
        output_dir: str,
        input_data_id_prefix: str = "",
        camera_horizontal_fov: Literal["calib", "settings"] = "settings",
        sensor_height: Optional[float] = None,
    ) -> None:
        """
        Annofab点群形式（KITTIベース）のファイル群を3dpc-editorに登録可能なファイル群に変換します。
        annofabのプライベートストレージを利用する場合にこのコマンドを利用します。
        Args:
            scene_path: scene.metaファイルのファイルパス or scene.metaファイルの存在するディレクトリパス or kitti形式ディレクトリ
            output_dir: 出力先ディレクトリ。
            input_data_id_prefix: input_data_idの先頭に付与する文字列
            camera_horizontal_fov: 補助画像カメラの視野角の取得方法の指定。 省略した場合"settings" //
                                   settings => 対象の画像にcamera_view_settingが存在していればその値を利用し、無ければ"calib"と同様 //
                                   calib => 対象の画像にキャリブレーションデータが存在すればそこから計算し、なければ90[degree]ととする
            sensor_height: 点群のセンサ(velodyne)の設置高。単位は点群の単位系（=kittiであれば[m]）
                           3dpc-editorは、この値を元に地面の高さを仮定する。 指定が無い場合はkittiのvelodyneの設置高を採用する
        Returns:
        """
        output_dir_path = Path(output_dir)
        loader = ScenePathsLoader(Path(scene_path))
        pathss = loader.load()

        inputs = [
            create_kitti_files(
                input_data_id_prefix,
                output_dir_path,
                paths,
                camera_horizontal_fov=_decode_enum(CameraHorizontalFovKind, camera_horizontal_fov),
                fallback_horizontal_fov=None,
                sensor_height=sensor_height,
            )
            for paths in pathss
        ]

        LocalCommand._write_all_files_json(inputs, output_dir_path)


class Command:
    """root command"""

    def __init__(self):
        self.project = ProjectCommand()
        self.local = LocalCommand()

    @staticmethod
    def version():
        """ツールのバージョンを出力します。"""
        print(f"annofab-3dpc-editor-cli {__version__}")


def main():
    fire.Fire(Command)


if __name__ == "__main__":
    main()

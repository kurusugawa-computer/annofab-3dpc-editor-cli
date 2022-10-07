### データの投入（KITTI 3D object detection形式）

`project upload_kitti_data`により、
[KITTI形式(KITTI 3D object detetection)](../kitti_3d_object_detection.md)
の形式を持つファイル群をAnnoFabへ登録できます。

#### ヘルプ

```
$ anno3d project upload_kitti_data --help | cat
INFO: Showing help with the command 'anno3d project upload_kitti_data -- --help | cat
NAME
    anno3d project upload_kitti_data - kitti 3d detection形式のファイル群を3dpc-editorに登録します。

SYNOPSIS
    anno3d project upload_kitti_data PROJECT_ID KITTI_DIR <flags>

DESCRIPTION
    kitti 3d detection形式のファイル群を3dpc-editorに登録します。

POSITIONAL ARGUMENTS
    PROJECT_ID
        登録先のプロジェクトid
    KITTI_DIR
        登録データの配置ディレクトリへのパス。 このディレクトリに "velodyne" / "image_2" / "calib" の3ディレクトリが存在することを期待している

FLAGS
    --skip=SKIP
        見つけたデータの先頭何件をスキップするか
    --size=SIZE
        最大何件のinput_dataを登録するか
    --input_data_id_prefix=INPUT_DATA_ID_PREFIX
        input_data_idの先頭に付与する文字列
    --camera_horizontal_fov=CAMERA_HORIZONTAL_FOV
        カメラのhorizontal FOVの角度[degree] 指定が無い場合はcalibデータから計算する。 calibデータも無い場合はkittiのカメラ仕様を採用する。
    --sensor_height=SENSOR_HEIGHT
        点群のセンサ(velodyne)の設置高。単位は点群の単位系（=kittiであれば[m]） 3dpc-editorは、この値を元に地面の高さを仮定する。 指定が無い場合はkittiのvelodyneの設置高を採用する
    --parallelism=PARALLELISM
        非同期実行の最大数。 指定しない場合上限を設定しない。実行環境におけるデフォルトのThreadPoolExecutorの最大スレッド数を超える値を与えても意味がない。
    --force=FORCE
        入力データと補助データを上書きしてアップロードするかどうか。
    --annofab_id=ANNOFAB_ID
        AnnoFabのユーザID。指定が無い場合は環境変数`ANNOFAB_USER_ID`の値を採用する
    --annofab_pass=ANNOFAB_PASS
        AnnoFabのパスワード。指定が無い場合は環境変数`ANNOFAB_PASSWORD`の値を採用する

NOTES
    You can also use flags syntax for POSITIONAL ARGUMENTS
```


#### コマンド例

```
anno3d project upload_kitti_data \
  --annofab_id ${ANNO_ID} \
  --annofab_pass ${ANNO_PASS} \
  --project_id ${ANNO_PRJ} \
  --kitti_dir "path/to/kitti3d/dir" \
  --skip 0 \
  --size 30 \
  --camera_horizontal_fov 56  \
  --sensor_height 0 \
  --force
```

### make_scene

Annofab点群形式（KITTIベース）のデータを元に出力する場合は、`anno3d local make_scene`コマンドを利用してください。

#### ヘルプ

```
$ anno3d local make_scene -- --help | cat
NAME
    app.py local make_scene - Annofab点群形式（KITTIベース）のファイル群を3dpc-editorに登録可能なファイル群に変換します。 annofabのプライベートストレージを利用する場合にこのコマンドを利用します。

SYNOPSIS
    app.py local make_scene SCENE_PATH OUTPUT_DIR <flags>

DESCRIPTION
    Annofab点群形式（KITTIベース）のファイル群を3dpc-editorに登録可能なファイル群に変換します。 annofabのプライベートストレージを利用する場合にこのコマンドを利用します。

POSITIONAL ARGUMENTS
    SCENE_PATH
        scene.metaファイルのファイルパス or scene.metaファイルの存在するディレクトリパス or kitti形式ディレクトリ
    OUTPUT_DIR
        出力先ディレクトリ。

FLAGS
    --input_data_id_prefix=INPUT_DATA_ID_PREFIX
        input_data_idの先頭に付与する文字列
    --camera_horizontal_fov=CAMERA_HORIZONTAL_FOV
        補助画像カメラの視野角の取得方法の指定。 省略した場合"settings" // settings => 対象の画像にcamera_view_settingが存在していればその値を利用し、無ければ"calib"と同様 // calib => 対象の画像にキャリブレーションデータが存在すればそこから計算し、なければ90[degree]ととする
    --sensor_height=SENSOR_HEIGHT
        点群のセンサ(velodyne)の設置高。単位は点群の単位系（=kittiであれば[m]） 3dpc-editorは、この値を元に地面の高さを仮定する。 指定が無い場合はkittiのvelodyneの設置高を採用する

NOTES
    You can also use flags syntax for POSITIONAL ARGUMENTS

```

#### コマンド例

```
$ anno3d local make_scene \
  --scene_path "/path/to/scene.meta" \
  --output_dir "./output" \
  --input_data_id_prefix "prefix" \
  --camera_horizontal_fov "settings" \
  --sensor_height 0
```

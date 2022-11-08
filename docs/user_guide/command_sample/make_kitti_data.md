# make_kitti_data

プライベートストレージなどを使用する場合に、KITTI形式のデータを元に、Annofabに投入可能なデータ群を作る。

## ヘルプ

```
$ anno3d local make_kitti_data -- --help | cat
NAME
    app.py local make_kitti_data - kitti 3d detection形式のファイル群を3dpc-editorに登録可能なファイル群に変換します。 annofabのプライベートストレージを利用する場合にこのコマンドを利用します。

SYNOPSIS
    app.py local make_kitti_data KITTI_DIR OUTPUT_DIR <flags>

DESCRIPTION
    kitti 3d detection形式のファイル群を3dpc-editorに登録可能なファイル群に変換します。 annofabのプライベートストレージを利用する場合にこのコマンドを利用します。

POSITIONAL ARGUMENTS
    KITTI_DIR
        登録データの配置ディレクトリへのパス。 このディレクトリに "velodyne" / "image_2" / "calib" の3ディレクトリが存在することを期待している
    OUTPUT_DIR
        出力先ディレクトリ。

FLAGS
    --skip=SKIP
        見つけたデータの先頭何件をスキップするか
    --size=SIZE
        最大何件のinput_dataを登録するか
    --input_data_id_prefix=INPUT_DATA_ID_PREFIX
        input_data_idの先頭に付与する文字列
    --sensor_height=SENSOR_HEIGHT
        点群のセンサ(velodyne)の設置高。単位は点群の単位系（=kittiであれば[m]） 3dpc-editorは、この値を元に地面の高さを仮定する。 指定が無い場合はkittiのvelodyneの設置高を採用する

NOTES
    You can also use flags syntax for POSITIONAL ARGUMENTS

```

## コマンド例

```
$ anno3d local make_kitti_data \
 --kitti_dir "path/to/kitti3d/dir" \
 --output_dir "./output" \
 --size 30 \
 --input_data_id_prefix "prefix" \
 --camera_horizontal_fov 56
```
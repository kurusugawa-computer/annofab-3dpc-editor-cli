## コマンドサンプル

* 環境変数`ANNO_ID`にAnnoFabのIdが設定されているものとします。
* 環境変数`ANNO_PASS`にAnnoFabのパスワードが設定されているものとします。
* 環境変数`ANNO_PRJ`にAnnoFabの対象プロジェクトIdが設定されているものとします。

### プラグインプロジェクトの生成

#### ヘルプ

```
$ anno3d project create --help | cat
INFO: Showing help with the command 'anno3d project create -- --help'.

NAME
    anno3d project create - 新しいカスタムプロジェクトを生成します。

SYNOPSIS
    anno3d project create PROJECT_ID ORGANIZATION_NAME PLUGIN_ID <flags>

DESCRIPTION
    新しいカスタムプロジェクトを生成します。

POSITIONAL ARGUMENTS
    PROJECT_ID
        作成するprojectのid
    ORGANIZATION_NAME
        projectを所属させる組織の名前
    PLUGIN_ID
        このプロジェクトで使用する、組織に登録されているプラグインのid。

FLAGS
    --title=TITLE
        projectのタイトル。　省略した場合 project_id と同様
    --overview=OVERVIEW
        projectの概要。 省略した場合 project_id と同様
    --annofab_id=ANNOFAB_ID
        AnnoFabのユーザID。指定が無い場合は環境変数`ANNOFAB_USER_ID`の値を採用する
    --annofab_pass=ANNOFAB_PASS
        AnnoFabのパスワード。指定が無い場合は環境変数`ANNOFAB_PASSWORD`の値を採用する

NOTES
    You can also use flags syntax for POSITIONAL ARGUMENTS

```


#### コマンド例

```
anno3d project create  --annofab_id ${ANNO_ID} --annofab_pass ${ANNO_PASS} --project_id ${ANNO_PRJ} --organization_name "3dpc-editor-devel" --plugin_id "ace7bf49-aefb-4db2-96ad-805496bd40aa"
```


### アノテーション範囲の設定

#### ヘルプ

```
$ anno3d project set_whole_annotation_area --help | cat
INFO: Showing help with the command 'anno3d project set_whole_annotation_area -- --help'.

NAME
    anno3d project set_whole_annotation_area - 対象プロジェクトのアノテーション範囲を、「全体」に設定します。 すでにアノテーション範囲が設定されていた場合、上書きされます。

SYNOPSIS
    anno3d project set_whole_annotation_area PROJECT_ID <flags>

DESCRIPTION
    対象プロジェクトのアノテーション範囲を、「全体」に設定します。 すでにアノテーション範囲が設定されていた場合、上書きされます。

POSITIONAL ARGUMENTS
    PROJECT_ID
        対象プロジェクト

FLAGS
    --annofab_id=ANNOFAB_ID
        AnnoFabのユーザID。指定が無い場合は環境変数`ANNOFAB_USER_ID`の値を採用する
    --annofab_pass=ANNOFAB_PASS
        AnnoFabのパスワード。指定が無い場合は環境変数`ANNOFAB_PASSWORD`の値を採用する

NOTES
    You can also use flags syntax for POSITIONAL ARGUMENTS

```

```
$ anno3d project set_sphere_annotation_area --help | cat
INFO: Showing help with the command 'anno3d project set_sphere_annotation_area -- --help'.

NAME
    anno3d project set_sphere_annotation_area - 対象プロジェクトのアノテーション範囲を、「球形」に設定します。 すでにアノテーション範囲が設定されていた場合、上書きされます。

SYNOPSIS
    anno3d project set_sphere_annotation_area PROJECT_ID RADIUS <flags>

DESCRIPTION
    対象プロジェクトのアノテーション範囲を、「球形」に設定します。 すでにアノテーション範囲が設定されていた場合、上書きされます。

POSITIONAL ARGUMENTS
    PROJECT_ID
        対象プロジェクト
    RADIUS
        アノテーション範囲の半径

FLAGS
    --annofab_id=ANNOFAB_ID
        AnnoFabのユーザID。指定が無い場合は環境変数`ANNOFAB_USER_ID`の値を採用する
    --annofab_pass=ANNOFAB_PASS
        AnnoFabのパスワード。指定が無い場合は環境変数`ANNOFAB_PASSWORD`の値を採用する

NOTES
    You can also use flags syntax for POSITIONAL ARGUMENTS

```

```
$ anno3d project set_rect_annotation_area --help | cat
INFO: Showing help with the command 'anno3d project set_rect_annotation_area -- --help'.

NAME
    anno3d project set_rect_annotation_area - 対象プロジェクトのアノテーション範囲を、「矩形」に設定します。 すでにアノテーション範囲が設定されていた場合、上書きされます。

SYNOPSIS
    anno3d project set_rect_annotation_area PROJECT_ID X Y <flags>

DESCRIPTION
    対象プロジェクトのアノテーション範囲を、「矩形」に設定します。 すでにアノテーション範囲が設定されていた場合、上書きされます。

POSITIONAL ARGUMENTS
    PROJECT_ID
        対象プロジェクト
    X
        アノテーション範囲のx座標の範囲
    Y
        アノテーション範囲のy座標の範囲

FLAGS
    --annofab_id=ANNOFAB_ID
        AnnoFabのユーザID。指定が無い場合は環境変数`ANNOFAB_USER_ID`の値を採用する
    --annofab_pass=ANNOFAB_PASS
        AnnoFabのパスワード。指定が無い場合は環境変数`ANNOFAB_PASSWORD`の値を採用する

NOTES
    You can also use flags syntax for POSITIONAL ARGUMENTS
```

#### コマンド例

##### アノテーション範囲を「全体」に設定

```
anno3d project set_whole_annotation_area \
  --annofab_id ${ANNO_ID} \
  --annofab_pass ${ANNO_PASS} \
  --project_id ${ANNO_PRJ}
```

##### アノテーション範囲を「半径10」に設定

```
anno3d project set_sphere_annotation_area \
  --annofab_id ${ANNO_ID} \
  --annofab_pass ${ANNO_PASS} \
  --project_id ${ANNO_PRJ} \
  --radius 10.0
```

##### アノテーション範囲を「-10 < x < 20, -5 < y < 10の矩形」に設定

```
anno3d project set_rect_annotation_area \
  --annofab_id ${ANNO_ID} \
  --annofab_pass ${ANNO_PASS} \
  --project_id ${ANNO_PRJ} \
  --x "(-10.0, 20.0)" \
  --y "(-5.0, 10.0)"
```

### Cuboidの規定サイズの設定

#### ヘルプ

```
$ anno3d project add_preset_cuboid_size --help | cat
INFO: Showing help with the command 'anno3d project add_preset_cuboid_size -- --help'.

NAME
    anno3d project add_preset_cuboid_size - 対象のプロジェクトにcuboidの規定サイズを追加・更新します。

SYNOPSIS
    anno3d project add_preset_cuboid_size PROJECT_ID KEY_NAME JA_NAME EN_NAME WIDTH HEIGHT DEPTH ORDER <flags>

DESCRIPTION
    対象のプロジェクトにcuboidの規定サイズを追加・更新します。

POSITIONAL ARGUMENTS
    PROJECT_ID
        対象プロジェクト
    KEY_NAME
        追加・更新する規定サイズの名前(英数字)。 `presetCuboidSize{Key_name}`というメタデータ・キーに対して規定サイズが設定される（Key_nameはkey_nameの頭文字を大文字にしたもの）
    JA_NAME
        日本語名称
    EN_NAME
        英語名称
    WIDTH
        追加・更新する規定サイズの幅（Cuboidのlocal axisにおけるY軸方向の長さ）
    HEIGHT
        追加・更新する規定サイズの高さ（Cuboidのlocal axisにおけるZ軸方向の長さ）
    DEPTH
        追加・更新する規定サイズの奥行（Cuboidのlocal axisにおけるX軸方向の長さ）
    ORDER
        エディタ上での表示順を決めるのに使用される整数（昇順で並べられる）

FLAGS
    --annofab_id=ANNOFAB_ID
        AnnoFabのユーザID。指定が無い場合は環境変数`ANNOFAB_USER_ID`の値を採用する
    --annofab_pass=ANNOFAB_PASS
        AnnoFabのパスワード。指定が無い場合は環境変数`ANNOFAB_PASSWORD`の値を採用する

NOTES
    You can also use flags syntax for POSITIONAL ARGUMENTS
```

```
$ anno3d project remove_preset_cuboid_size --help | cat
INFO: Showing help with the command 'anno3d project remove_preset_cuboid_size -- --help'.

NAME
    anno3d project remove_preset_cuboid_size - 対象のプロジェクトからcuboidの規定サイズを削除します。

SYNOPSIS
    anno3d project remove_preset_cuboid_size PROJECT_ID KEY_NAME <flags>

DESCRIPTION
    対象のプロジェクトからcuboidの規定サイズを削除します。

POSITIONAL ARGUMENTS
    PROJECT_ID
        対象プロジェクト
    KEY_NAME
        削除する規定サイズの名前(英数字)。 `presetCuboidSize{Key_name}`というキーのメタデータが削除される(Key_nameはkey_nameの頭文字を大文字にしたもの)

FLAGS
    --annofab_id=ANNOFAB_ID
        AnnoFabのユーザID。指定が無い場合は環境変数`ANNOFAB_USER_ID`の値を採用する
    --annofab_pass=ANNOFAB_PASS
        AnnoFabのパスワード。指定が無い場合は環境変数`ANNOFAB_PASSWORD`の値を採用する

NOTES
    You can also use flags syntax for POSITIONAL ARGUMENTS
```

#### コマンド例

##### Cuboidの規定サイズを追加・更新

```
$ anno3d project add_preset_cuboid_size \
    --annofab_id ${ANNO_ID} \
    --annofab_pass ${ANNO_PASS} \
    --project_id ${ANNO_PRJ} \
    --key_name test1 \
    --ja_name テスト１ \
    --en_name Test1 \
    --width 10 \
    --height 11 \
    --depth 12 \
    --order 1
```

##### Cuboidの規定サイズを削除

```
$ anno3d project remove_preset_cuboid_size \
    --annofab_id ${ANNO_ID} \
    --annofab_pass ${ANNO_PASS} \
    --project_id ${ANNO_PRJ} \
    --key_name test1 
```

### ラベルの設定 

#### ヘルプ

```
$ anno3d project put_cuboid_label --help | cat
INFO: Showing help with the command 'anno3d project put_cuboid_label -- --help'.

NAME
    anno3d project put_cuboid_label - 対象のプロジェクトにcuboidのlabelを追加・更新します。

SYNOPSIS
    anno3d project put_cuboid_label PROJECT_ID LABEL_ID JA_NAME EN_NAME COLOR <flags>

DESCRIPTION
    対象のプロジェクトにcuboidのlabelを追加・更新します。

POSITIONAL ARGUMENTS
    PROJECT_ID
        対象プロジェクト
    LABEL_ID
        追加・更新するラベルのid
    JA_NAME
        日本語名称
    EN_NAME
        英語名称
    COLOR
        ラベルの表示色。 "(R,G,B)"形式の文字列 R/G/Bは、それぞれ0〜255の整数値で指定する

FLAGS
    --annofab_id=ANNOFAB_ID
        AnnoFabのユーザID。指定が無い場合は環境変数`ANNOFAB_USER_ID`の値を採用する
    --annofab_pass=ANNOFAB_PASS
        AnnoFabのパスワード。指定が無い場合は環境変数`ANNOFAB_PASSWORD`の値を採用する

NOTES
    You can also use flags syntax for POSITIONAL ARGUMENTS
```

```
$ anno3d project put_segment_label --help | cat
INFO: Showing help with the command 'app.py project put_segment_label -- --help'.

NAME
    app.py project put_segment_label - 対象のプロジェクトにsegmentのlabelを追加・更新します。

SYNOPSIS
    app.py project put_segment_label PROJECT_ID LABEL_ID JA_NAME EN_NAME COLOR DEFAULT_IGNORE SEGMENT_TYPE <flags>

DESCRIPTION
    対象のプロジェクトにsegmentのlabelを追加・更新します。

POSITIONAL ARGUMENTS
    PROJECT_ID
        対象プロジェクト
    LABEL_ID
        追加・更新するラベルのid
    JA_NAME
        日本語名称
    EN_NAME
        英語名称
    COLOR
        ラベルの表示色。 "(R,G,B)"形式の文字列 R/G/Bは、それぞれ0〜255の整数値で指定する
    DEFAULT_IGNORE
        このラベルがついた領域を、デフォルトでは他のアノテーションから除外するかどうか。 Trueであれば除外する
    SEGMENT_TYPE
        "SEMANTIC" or "INSTANCE" を指定する。 "SEMANTIC"の場合、このラベルのインスタンスは唯一つとなる。 "INSTANCE"の場合複数のインスタンスを作成可能となる

FLAGS
    --layer=LAYER
        このラベルのレイヤーを指定する。 同じレイヤーのラベルは、頂点を共有することが出来ない。 また、大きな値のレイヤーが優先して表示される。 指定しない場合は 100
    --annofab_id=ANNOFAB_ID
        AnnoFabのユーザID。指定が無い場合は環境変数`ANNOFAB_USER_ID`の値を採用する
    --annofab_pass=ANNOFAB_PASS
        AnnoFabのパスワード。指定が無い場合は環境変数`ANNOFAB_PASSWORD`の値を採用する

NOTES
    You can also use flags syntax for POSITIONAL ARGUMENTS
```

#### コマンド例

```
# バウンディングボックスのラベルを追加
anno3d project put_cuboid_label \
  --annofab_id ${ANNO_ID} \
  --annofab_pass ${ANNO_PASS} \
  --project_id ${ANNO_PRJ}\
  --label_id "car" \
  --ja_name "車" \
  --en_name "car" \
  --color "(255, 0, 0)"
anno3d project put_cuboid_label \
  --annofab_id ${ANNO_ID} \
  --annofab_pass ${ANNO_PASS} \
  --project_id ${ANNO_PRJ} \
  --label_id "human" \
  --ja_name "人" \
  --en_name "human" \
  --color "(0, 255, 0)"

# セマンティックセグメンテーションのラベルを追加
# defaultで無視属性が有効
anno3d project put_segment_label \
  --annofab_id ${ANNO_ID} \
  --annofab_pass ${ANNO_PASS} \
  --project_id ${ANNO_PRJ} \
  --label_id "road" \
  --ja_name "道" \
  --en_name "road" \
  --color "(238, 130, 238)" \
  --default_ignore True \
  --segment_type SEMANTIC

# defaultで無視属性が無効
anno3d project put_segment_label \
  --annofab_id ${ANNO_ID} \
  --annofab_pass ${ANNO_PASS} \
  --project_id ${ANNO_PRJ} \
  --label_id "wall" \
  --ja_name "壁" \
  --en_name "wall" \
  --color "(0, 182, 110)" \
  --default_ignore False \
  --segment_type SEMANTIC

# インスタンスセグメンテーションのラベルを追加
anno3d project put_segment_label \
  --annofab_id ${ANNO_ID} \
  --annofab_pass ${ANNO_PASS} \
  --project_id ${ANNO_PRJ} \
  --label_id "car" \
  --ja_name "車(seg)" \
  --en_name "car-seg" \
  --color "(255, 0, 0)" \
  --default_ignore False \
  --segment_type INSTANCE

```

### データの投入（KITTI 3D object detection形式）

`project upload_kitti_data`により、
[KITTI形式(KITTI 3D object detetection)](kitti_3d_object_detection.md)
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

### データの投入（拡張KITTI形式）

`project upload_scene` により、[拡張KITTI形式](kitti_extension.md)の形式をもつ
ファイル群をAnnoFabへ登録できます。
あわせて `--upload_kind` を指定することで、タスク作成やアノテーション登録も同時に行うことができます。


#### ヘルプ

```
$ anno3d project upload_scene -- --help | cat
NAME
    app.py project upload_scene - 拡張kitti形式のファイル群をAnnoFabにアップロードします

SYNOPSIS
    app.py project upload_scene PROJECT_ID SCENE_PATH <flags>

DESCRIPTION
    拡張kitti形式のファイル群をAnnoFabにアップロードします

POSITIONAL ARGUMENTS
    PROJECT_ID
        登録先のプロジェクトid
    SCENE_PATH
        scene.metaファイルのファイルパス or scene.metaファイルの存在するディレクトリパス or kitti形式ディレクトリ

FLAGS
    --input_data_id_prefix=INPUT_DATA_ID_PREFIX
        アップロードするデータのinput_data_idにつけるprefix
    --task_id_prefix=TASK_ID_PREFIX
        生成するtaskのidにつけるprefix
    --camera_horizontal_fov=CAMERA_HORIZONTAL_FOV
        補助画像カメラの視野角の取得方法の指定。 省略した場合"settings" // settings => 対象の画像にcamera_view_settingが存在していればその値を利用し、無ければ"calib"と同様 // calib => 対象の画像にキャリブレーションデータが存在すればそこから計算し、なければ90ととする
    --sensor_height=SENSOR_HEIGHT
        velodyneのセンサ設置高。 velodyne座標系上で -sensor_height 辺りに地面が存在すると認識する。 省略した場合、kittiのセンサ高(1.73)を採用する
    --frame_per_task=FRAME_PER_TASK
        タスクを作る場合、１タスク辺り何個のinput_dataを登録するか。 省略した場合 シーン単位でタスクを作成
    --upload_kind=UPLOAD_KIND
        処理の種類　省略した場合 "annotation" // data => 入力データと補助データの登録のみを行う // task => 上記に加えて、タスクの生成を行う // annotation => 上記に加えて、アノテーションの登録を行う
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
anno3d project upload_scene \
  --annofab_id ${ANNO_ID} \
  --annofab_pass ${ANNO_PASS} \
  --project_id ${ANNO_PRJ} \
  --frame_per_task 4 \
  --camera_horizontal_fov "calib" \
  --input_data_id_prefix scene1-1 \
  --task_id_prefix scene1-task-1- \
  --sensor_height 0 \
  --upload_kind annotation \
  --scene_path /path/to/scene.meta \
  --force
```

### データの投入（S3プライベートストレージ）

`project upload_scene_to_s3` により、[拡張KITTI形式](kitti_extension.md)の形式をもつ
ファイル群を、AWS S3にアップロードした上でAnnoFabへ登録できます。

事前にAWSの認証情報を設定しておく必要があります。[boto3 : Credentials](https://boto3.amazonaws.com/v1/documentation/api/latest/guide/credentials.html) を参考にしてください。


#### ヘルプ

```
$ anno3d project upload_scene_to_s3 -- --help | cat
NAME
    app.py project upload_scene_to_s3 - 拡張kitti形式のファイル群をAWS S3にアップロードした上で、3dpc-editorに登録します。

SYNOPSIS
    app.py project upload_scene_to_s3 PROJECT_ID SCENE_PATH S3_PATH <flags>

DESCRIPTION
    拡張kitti形式のファイル群をAWS S3にアップロードした上で、3dpc-editorに登録します。

POSITIONAL ARGUMENTS
    PROJECT_ID
        登録先のプロジェクトid
    SCENE_PATH
        scene.metaファイルのファイルパス or scene.metaファイルの存在するディレクトリパス or kitti形式ディレクトリ
    S3_PATH
        登録先のS3パス（ex: "{bucket}/{key}"）

FLAGS
    --input_data_id_prefix=INPUT_DATA_ID_PREFIX
        アップロードするデータのinput_data_idにつけるprefix
    --task_id_prefix=TASK_ID_PREFIX
        生成するtaskのidにつけるprefix
    --camera_horizontal_fov=CAMERA_HORIZONTAL_FOV
        補助画像カメラの視野角の取得方法の指定。 省略した場合"settings" // settings => 対象の画像にcamera_view_settingが存在していればその値を利用し、無ければ"calib"と同様 // calib => 対象の画像にキャリブレーションデータが存在すればそこから計算し、なければ90[degree]ととする
    --sensor_height=SENSOR_HEIGHT
        velodyneのセンサ設置高。 velodyne座標系上で -sensor_height 辺りに地面が存在すると認識する。 省略した場合、kittiのセンサ高(1.73)を採用する
    --frame_per_task=FRAME_PER_TASK
        タスクを作る場合、１タスク辺り何個のinput_dataを登録するか。 省略した場合 シーン単位でタスクを作成
    --upload_kind=UPLOAD_KIND
        処理の種類　省略した場合 "annotation" // data => 入力データと補助データの登録のみを行う // task => 上記に加えて、タスクの生成を行う // annotation => 上記に加えて、アノテーションの登録を行う
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
anno3d project upload_scene_to_s3 \
  --annofab_id ${ANNO_ID} \
  --annofab_pass ${ANNO_PASS} \
  --project_id ${ANNO_PRJ} \
  --frame_per_task 4 \
  --camera_horizontal_fov "settings" \
  --s3_path "my-bucket/foo/bar" \
  --input_data_id_prefix scene1-1 \
  --task_id_prefix scene1-task-1- \
  --sensor_height 0 \
  --upload_kind annotation \
  --scene_path /path/to/scene.meta \
  --force
```


### make_kitti_data

プライベートストレージなどを使用する場合に、KITTI形式のデータを元に、AnnoFabに投入可能なデータ群を作る。

#### ヘルプ

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

#### コマンド例

```
$ anno3d local make_kitti_data \
 --kitti_dir "path/to/kitti3d/dir" \
 --output_dir "./output" \
 --size 30 \
 --input_data_id_prefix "prefix" \
 --camera_horizontal_fov 56
```

### make_scene

拡張KITTI形式のデータを元に出力する場合は、`anno3d local make_scene`コマンドを利用してください。

#### ヘルプ

```
$ anno3d local make_scene -- --help | cat
NAME
    app.py local make_scene - 拡張kitti形式のファイル群を3dpc-editorに登録可能なファイル群に変換します。 annofabのプライベートストレージを利用する場合にこのコマンドを利用します。

SYNOPSIS
    app.py local make_scene SCENE_PATH OUTPUT_DIR <flags>

DESCRIPTION
    拡張kitti形式のファイル群を3dpc-editorに登録可能なファイル群に変換します。 annofabのプライベートストレージを利用する場合にこのコマンドを利用します。

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


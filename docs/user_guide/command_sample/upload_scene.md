### データの投入（Annofab点群形式（KITTIベース））

`project upload_scene` により、[Annofab点群形式（KITTIベース）](annofab_point_cloud_format.md)のファイル群をAnnoFabへ登録できます。
あわせて `--upload_kind` を指定することで、タスク作成やアノテーション登録も同時に行うことができます。


#### ヘルプ

```
$ anno3d project upload_scene -- --help | cat
NAME
    app.py project upload_scene - Annofab点群形式（KITTIベース）のファイル群をAnnoFabにアップロードします

SYNOPSIS
    app.py project upload_scene PROJECT_ID SCENE_PATH <flags>

DESCRIPTION
    Annofab点群形式（KITTIベース）のファイル群をAnnoFabにアップロードします

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

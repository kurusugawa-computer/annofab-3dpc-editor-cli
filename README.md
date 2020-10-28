# annofab-3dpc-editor-cli

## 開発環境

 * poetry
     * Poetry version 1.0.5
 * python 3.8
 
 
### 開発環境初期化

poetryのインストール手順は、このファイル下部の`poetryのインストール手順`を参照

```
poetry install
```

----

## コマンドサンプル

* `alias popy='poetry run python'`が設定されているものとします。
* 環境変数`ANNO_ID`にAnnoFabのIdが設定されているものとします。
* 環境変数`ANNO_PASS`にAnnoFabのパスワードが設定されているものとします。
* 環境変数`ANNO_PRJ`にAnnoFabの対象プロジェクトIdが設定されているものとします。

### プラグインプロジェクトの生成

```
popy app.py project create  --annofab_id ${ANNO_ID} --annofab_pass ${ANNO_PASS} --project_id ${ANNO_PRJ} --organization_name "3dpc-editor-devel" --plugin_id "ace7bf49-aefb-4db2-96ad-805496bd40aa"
```

### ラベルの設定 

2020/09/01 現在、3dpc-editorは、セグメンテーション結果のAnnoFabへの保存に対応していないため、`put_segment_label`を利用すると、保存時にエラーとなります。

```
popy app.py project put_cuboid_label \
  --annofab_id ${ANNO_ID} \
  --annofab_pass ${ANNO_PASS} \
  --project_id ${ANNO_PRJ}\
  --label_id "car" \
  --ja_name "車" \
  --en_name "car" \
  --color "(255, 0, 0)"
popy app.py project put_cuboid_label \
  --annofab_id ${ANNO_ID} \
  --annofab_pass ${ANNO_PASS} \
  --project_id ${ANNO_PRJ} \
  --label_id "human" \
  --ja_name "人" \
  --en_name "human" \
  --color "(0, 255, 0)"

popy app.py project put_segment_label \
  --annofab_id ${ANNO_ID} \
  --annofab_pass ${ANNO_PASS} \
  --project_id ${ANNO_PRJ} \
  --label_id "road" \
  --ja_name "道" \
  --en_name "road" \
  --color "(238, 130, 238)" \
  --default_ignore True
popy app.py project put_segment_label \
  --annofab_id ${ANNO_ID} \
  --annofab_pass ${ANNO_PASS} \
  --project_id ${ANNO_PRJ} \
  --label_id "wall" \
  --ja_name "壁" \
  --en_name "wall" \
  --color "(0, 182, 110)" \
  --default_ignore False
```

### データの投入（KITTI 3D object detection形式）

`project upload_kitti_data`により、
[KITTI 3D object detetection](http://www.cvlibs.net/datasets/kitti/eval_object.php?obj_benchmark=3d)
の形式を持つファイル群をAnnoFabへ登録できます。

```
popy app.py project upload_kitti_data \
  --annofab_id ${ANNO_ID} \
  --annofab_pass ${ANNO_PASS} \
  --project_id "3dpc-editor-trial" \
  --kitti_dir "path/to/kitti3d/dir" \
  --skip 0 \
  --size 30 \
  --camera_horizontal_fov 56  \
  --sensor_height 0
```

### データの投入（拡張KITTI形式）

`project upload_scene` により、[拡張KITTI形式（社内ページへの参照）](https://kurusugawa.jp/confluence/pages/viewpage.action?pageId=1123123957)の形式をもつ
ファイル群をAnnoFabへ登録できます。
あわせて `--upload_kind` を指定することで、タスク作成やアノテーション登録も同時に行うことができます。

TODO データ形式の正式な置き場ができたら、URLを書き換える

#### ヘルプ

```
INFO: Showing help with the command 'app.py project upload_scene -- --help'.

NAME
    app.py project upload_scene - 拡張kitti形式のファイル群をAnnoFabにアップロードします

SYNOPSIS
    app.py project upload_scene ANNOFAB_ID ANNOFAB_PASS PROJECT_ID SCENE_PATH <flags>

DESCRIPTION
    拡張kitti形式のファイル群をAnnoFabにアップロードします

POSITIONAL ARGUMENTS
    ANNOFAB_ID
    ANNOFAB_PASS
    PROJECT_ID
        登録先のプロジェクトid
    SCENE_PATH
        scene.metaファイルのファイルパス or scene.metaファイルの存在するディレクトリパス or kitti形式ディレクトリ

FLAGS
    --input_data_id_prefix=INPUT_DATA_ID_PREFIX
        アップロードするデータのinput_data_idにつけるprefix
    --task_id_prefix=TASK_ID_PREFIX
        生成するtaskのidにつけるprefix
    --sensor_height=SENSOR_HEIGHT
        velodyneのセンサ設置高。 velodyne座標系上で -sensor_height 辺りに地面が存在すると認識する。 省略した場合、kittiのセンサ高(1.73)を採用する
    --frame_per_task=FRAME_PER_TASK
        タスクを作る場合、１タスク辺り何個のinput_dataを登録するか。 省略した場合 10
    --upload_kind=UPLOAD_KIND
        処理の種類　省略した場合 "annotation" // data => 入力データと補助データの登録のみを行う // task => 上記に加えて、タスクの生成を行う // annotation => 上記に加えて、アノテーションの登録を行う

NOTES
    You can also use flags syntax for POSITIONAL ARGUMENTS
```

#### コマンド例

```
popy app.py project upload_scene \
  --annofab_id ${ANNO_ID} \
  --annofab_pass ${ANNO_PASS} \
  --project_id ${ANNO_PRJ} \
  --frame_per_task 4 \
  --input_data_id_prefix scene1-1 \
  --task_id_prefix scene1-task-1- \
  --sensor_height 0 \
  --upload_kind annotation \
  --scene_path /path/to/scene.meta
```

### 投入データのローカルファイルシステムへの生成

プライベートストレージなどを使用する場合に、kitti 3d detectionのデータを元に、AnnoFabに投入可能なデータ群を作る

```
popy app.py local make_kitti_data --kitti_dir "path/to/kitti3d/dir" --output_dir "./output" --size 30 --input_id_prefix "prefix" --camera_horizontal_fov 56
```

----


## poetryのインストール手順


poetryのインストール手順一例を以下に示す  
2020/05/21 ubuntu 18.04 にて確認

### pyenv

システムにpython 3.8を直接インストールして使うなら`pyenv`は要らない

```
sudo apt-get update

sudo apt-get install build-essential libssl-dev zlib1g-dev libbz2-dev \
libreadline-dev libsqlite3-dev wget curl llvm libncurses5-dev libncursesw5-dev \
xz-utils tk-dev libffi-dev liblzma-dev python-openssl git
```

```
curl https://pyenv.run | bash
``` 

コンソールに、以下のような設定すべき内容が出力されるので`.bashrc`などに設定

```
export PATH="/home/vagrant/.pyenv/bin:$PATH"
eval "$(pyenv init -)"
eval "$(pyenv virtualenv-init -)"
```

```
pyenv install 3.8.3
pyenv global 3.8.3
```

### pipx

直接 poetry をインストールするなら要らない

```
python -m pip install --user pipx
python -m pipx ensurepath
```

completionを効かせたいときは、`pipx completions` の実行結果に従って設定する

```
$ pipx completions

Add the appropriate command to your shell's config file
so that it is run on startup. You will likely have to restart
or re-login for the autocompletion to start working.

bash:
    eval "$(register-python-argcomplete pipx)"

zsh:
    To activate completions for zsh you need to have
    bashcompinit enabled in zsh:

    autoload -U bashcompinit
    bashcompinit

    Afterwards you can enable completion for pipx:

    eval "$(register-python-argcomplete pipx)"

tcsh:
    eval `register-python-argcomplete --shell tcsh pipx`

fish:
    register-python-argcomplete --shell fish pipx | .
```

### poetry

```
pipx install poetry
poetry completions bash | sudo tee /etc/bash_completion.d/poetry.bash-completion
```
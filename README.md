# annofab-3dpc-editor-cli

## 開発環境

 * poetry
     * Poetry version 1.0.5
 * python 3.8
 
 
### 開発環境初期化

```
poetry install
```

----

poetryのインストール手順一例を以下に示す

#### poetryのインストール

2020/05/21 ubuntu 18.04 にて確認

##### pyenv

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

##### pipx

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

##### poetry

```
pipx install poetry
poetry completions bash | sudo tee /etc/bash_completion.d/poetry.bash-completion
```


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

### データの投入

kitti 3d detectionのデータのAnnoFabへの登録

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

### 投入データのローカルファイルシステムへの生成

プライベートストレージなどを使用する場合に、kitti 3d detectionのデータを元に、AnnoFabに投入可能なデータ群を作る

```
popy app.py local make_kitti_data --kitti_dir "path/to/kitti3d/dir" --output_dir "./output" --size 30 --input_id_prefix "prefix" --camera_horizontal_fov 56
```
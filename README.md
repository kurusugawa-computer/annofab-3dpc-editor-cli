# annofab-3dpc-editor-cli
Annofabの3次元プロジェクトを操作するためのCLIです。

[![Build Status](https://app.travis-ci.com/kurusugawa-computer/annofab-3dpc-editor-cli.svg?branch=master)](https://app.travis-ci.com/kurusugawa-computer/annofab-3dpc-editor-cli)
[![PyPI version](https://badge.fury.io/py/annofab-3dpc-editor-cli.svg)](https://badge.fury.io/py/annofab-3dpc-editor-cli)
[![Python Versions](https://img.shields.io/pypi/pyversions/annofab-3dpc-editor-cli.svg)](https://pypi.org/project/annofab-3dpc-editor-cli)
[![Documentation Status](https://readthedocs.org/projects/annofab-3dpc-editor-cli/badge/?version=latest)](https://annofab-3dpc-editor-cli.readthedocs.io/ja/latest/?badge=latest)



## Install

```
$ pip install annofab-3dpc-editor-cli
```

## コマンドサンプル
https://annofab-3dpc-editor-cli.readthedocs.io/ja/latest/user_guide/command_sample.html 参照


### バージョンの確認方法

```
$ anno3d version
annofab-3dpc-editor-cli 0.2.2a1
```

--------------
## 開発環境

 * poetry
     * Poetry version 1.8.3
 * python 3.12
 
 
### 開発環境初期化

poetryのインストール手順は、このファイル下部の`poetryのインストール手順`を参照

```
poetry install
```



## poetryのインストール手順


poetryのインストール手順一例を以下に示す  
2020/05/21 ubuntu 18.04 にて確認


### pyenv

システムにpython 3.12を直接インストールして使うなら`pyenv`は要らない

#### 前提ライブラリなどのインストール

<details>
<summary>ubuntu 22.04の場合</summary>

```
sudo apt-get update


sudo apt-get install make build-essential libssl-dev zlib1g-dev \
libbz2-dev libreadline-dev libsqlite3-dev wget curl llvm \
libncursesw5-dev xz-utils tk-dev libxml2-dev libxmlsec1-dev libffi-dev liblzma-dev python3-openssl
```

</details>


<details>
<summary>ubuntu 18.04の場合</summary>

```
sudo apt-get update

sudo apt-get install build-essential libssl-dev zlib1g-dev libbz2-dev \
libreadline-dev libsqlite3-dev wget curl llvm libncurses5-dev libncursesw5-dev \
xz-utils tk-dev libffi-dev liblzma-dev python-openssl git
```

</details>


#### pyenvとpythonのインストール

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
pyenv install 3.12.4
pyenv global 3.12.4
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

## PyPIへの公開
[GitHubのReleases](https://github.com/kurusugawa-computer/annofab-3dpc-editor-cli/releases)からリリースを作成してください。
GitHub Actionsにより自動でPyPIに公開されます。
バージョン情報は、`poetry build`時に[poetry-dynamic-versioning](https://github.com/mtkennerly/poetry-dynamic-versioning)によって、Gitのバージョンタグから生成されます。

手動でPyPIに公開する場合は、以下のコマンドを実行してください。

```
# VSCode Dev Containersでは、`/usr/local/lib/python3.12/dist-packages/`にインストールしようとするため、`sudo`で実行する必要があります。
$ sudo poetry self add "poetry-dynamic-versioning[plugin]@1.4.0"
$ make publish
```



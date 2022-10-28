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
annofab-3dpc-editor-cli 0.1.10a1
```

--------------
## 開発環境

 * poetry
     * Poetry version 1.0.5
 * python 3.8
 
 
### 開発環境初期化

poetryのインストール手順は、このファイル下部の`poetryのインストール手順`を参照

```
poetry install
```



## poetryのインストール手順


poetryのインストール手順一例を以下に示す  
2020/05/21 ubuntu 18.04 にて確認

ローカルの環境に以下の手順でインストールする以外に，
python 3.8 および poetry の導入がなされた `docker/Dockerfile` を用いても良い．

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

## PyPIへの公開

```
$ make publish
```



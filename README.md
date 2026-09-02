# annofab-3dpc-editor-cli

Annofabの3次元プロジェクトを操作するためのCLIです。

[![Build Status](https://app.travis-ci.com/kurusugawa-computer/annofab-3dpc-editor-cli.svg?branch=master)](https://app.travis-ci.com/kurusugawa-computer/annofab-3dpc-editor-cli)
[![PyPI version](https://badge.fury.io/py/annofab-3dpc-editor-cli.svg)](https://badge.fury.io/py/annofab-3dpc-editor-cli)
[![Python Versions](https://img.shields.io/pypi/pyversions/annofab-3dpc-editor-cli.svg)](https://pypi.org/project/annofab-3dpc-editor-cli)
[![Documentation Status](https://readthedocs.org/projects/annofab-3dpc-editor-cli/badge/?version=latest)](https://annofab-3dpc-editor-cli.readthedocs.io/ja/latest/?badge=latest)

## Install

```bash
pip install annofab-3dpc-editor-cli
```

## コマンドサンプル

https://annofab-3dpc-editor-cli.readthedocs.io/ja/latest/user_guide/command_sample.html を参照してください。

### バージョンの確認方法

```bash
anno3d version
# annofab-3dpc-editor-cli 0.2.2a1
```

## 開発環境

- uv
- Python 3.12（開発環境）

### 開発環境初期化

uvをインストールしてから、依存関係と開発用の仮想環境を作成します。

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"
uv sync
```

`uv sync` は `linter`、`test`、`documentation`、`dev-only` の各依存グループを含めて同期します。特定のグループだけを使う場合は、たとえば `uv sync --only-group test` を実行してください。

コマンドは `uv run` 経由で実行できます。

```bash
uv run anno3d version
make lint
make test
```

## PyPIへの公開

[GitHub Releases](https://github.com/kurusugawa-computer/annofab-3dpc-editor-cli/releases) からリリースを作成してください。GitHub Actionsにより自動でPyPIへ公開されます。

バージョン情報は、ビルド時に [uv-dynamic-versioning](https://github.com/ninoseki/uv-dynamic-versioning) がGitのバージョンタグから生成します。

手動で公開する場合は、以下を実行してください。

```bash
uv build
uv publish --token "$PYPI_TOKEN"
```

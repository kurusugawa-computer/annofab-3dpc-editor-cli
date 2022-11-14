# プラグインプロジェクトの生成

## ヘルプ

```
$ anno3d project create --help | cat
INFO: Showing help with the command 'anno3d project create -- --help'.

NAME
    anno3d project create - 新しい三次元エディタプロジェクトを生成します。

SYNOPSIS
    anno3d project create TITLE ORGANIZATION_NAME <flags>

DESCRIPTION
    新しい三次元エディタプロジェクトを生成します。

POSITIONAL ARGUMENTS
    TITLE
        projectのタイトル
    ORGANIZATION_NAME
        projectを所属させる組織の名前

FLAGS
    --project_id=PROJECT_ID
        作成するprojectのid。省略した場合自動的にuuidが設定されます。
    --plugin_id=PLUGIN_ID
        このプロジェクトで使用する、組織に登録されている三次元エディタプラグインのid。 省略時は標準プラグインを利用します
    --specs_plugin_id=SPECS_PLUGIN_ID
        このプロジェクトで使用する、組織に登録されている仕様拡張プラグインのid。 省略時は標準プラグインを利用します
    --overview=OVERVIEW
        projectの概要
    --annofab_id=ANNOFAB_ID
        AnnofabのユーザID。指定が無い場合は環境変数`ANNOFAB_USER_ID`の値を採用する
    --annofab_pass=ANNOFAB_PASS
        Annofabのパスワード。指定が無い場合は環境変数`ANNOFAB_PASSWORD`の値を採用する
    --annofab_endpoint=ANNOFAB_ENDPOINT
        AnnofabのAPIアクセス先エンドポイントを指定します。 省略した場合は環境変数`ANNOFAB_ENDPOINT`の値を利用します。                              環境変数も指定されていない場合、デフォルトのエンドポイント（https://annofab.com）を利用します

NOTES
    You can also use flags syntax for POSITIONAL ARGUMENTS

```


## コマンド例

```
anno3d project create  --annofab_id ${ANNO_ID} --annofab_pass ${ANNO_PASS} --title "test_project" --organization_name "3dpc-editor-devel"
```

### プラグインプロジェクトの生成

#### ヘルプ

```
$ anno3d project create --help | cat
INFO: Showing help with the command 'anno3d project create -- --help'.

NAME
    anno3d project create - 新しいカスタムプロジェクトを生成します。

SYNOPSIS
    anno3d project create TITLE ORGANIZATION_NAME PLUGIN_ID <flags>

DESCRIPTION
    新しいカスタムプロジェクトを生成します。

POSITIONAL ARGUMENTS
    TITLE
        projectのタイトル
    ORGANIZATION_NAME
        projectを所属させる組織の名前
    PLUGIN_ID
        このプロジェクトで使用する、組織に登録されているプラグインのid。

FLAGS
    --project_id=PROJECT_ID
        作成するprojectのid。省略した場合自動的にuuidが設定されます。
    --overview=OVERVIEW
        projectの概要。
    --annofab_id=ANNOFAB_ID
        AnnoFabのユーザID。指定が無い場合は環境変数`ANNOFAB_USER_ID`の値を採用する
    --annofab_pass=ANNOFAB_PASS
        AnnoFabのパスワード。指定が無い場合は環境変数`ANNOFAB_PASSWORD`の値を採用する
    --annofab_endpoint=ANNOFAB_ENDPOINT
        AnnofabのAPIアクセス先エンドポイントを指定します。 省略した場合は環境変数`ANNOFAB_ENDPOINT`の値を利用します。                              環境変数も指定されていない場合、デフォルトのエンドポイント（https://annofab.com）を利用します

NOTES
    You can also use flags syntax for POSITIONAL ARGUMENTS

```


#### コマンド例

```
anno3d project create  --annofab_id ${ANNO_ID} --annofab_pass ${ANNO_PASS} --title "test_project" --organization_name "3dpc-editor-devel" --plugin_id "ace7bf49-aefb-4db2-96ad-805496bd40aa"
```

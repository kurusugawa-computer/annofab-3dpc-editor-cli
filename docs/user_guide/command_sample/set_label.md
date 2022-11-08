# ラベルの設定 

## ヘルプ

```
$ anno3d project put_cuboid_label --help | cat
INFO: Showing help with the command 'anno3d project put_cuboid_label -- --help'.

NAME
    anno3d project put_cuboid_label - 対象のプロジェクトにcuboidのlabelを追加・更新します。

SYNOPSIS
    anno3d project put_cuboid_label PROJECT_ID EN_NAME <flags>

DESCRIPTION
    対象のプロジェクトにcuboidのlabelを追加・更新します。

POSITIONAL ARGUMENTS
    PROJECT_ID
        対象プロジェクト
    EN_NAME
        英語名称

FLAGS
    --label_id=LABEL_ID
        追加・更新するラベルのid。指定しない場合はuuidが設定される。
    --ja_name=JA_NAME
        日本語名称。指定しない場合はen_nameと同じ名称が設定される。
    --color=COLOR
        ラベルの表示色。 "(R,G,B)"形式の文字列 R/G/Bは、それぞれ0〜255の整数値で指定する。指定しない場合はランダムに設定される。
    --annofab_id=ANNOFAB_ID
        AnnofabのユーザID。指定が無い場合は環境変数`ANNOFAB_USER_ID`の値を採用する
    --annofab_pass=ANNOFAB_PASS
        Annofabのパスワード。指定が無い場合は環境変数`ANNOFAB_PASSWORD`の値を採用する
    --annofab_endpoint=ANNOFAB_ENDPOINT
        AnnofabのAPIアクセス先エンドポイントを指定します。 省略した場合は環境変数`ANNOFAB_ENDPOINT`の値を利用します。 環境変数も指定されていない場合、デフォルトのエンドポイント（https://annofab.com）を利用します

NOTES
    You can also use flags syntax for POSITIONAL ARGUMENTS
```

```
$ anno3d project put_segment_label --help | cat
INFO: Showing help with the command 'app.py project put_segment_label -- --help'.

NAME
    anno3d project put_segment_label - 対象のプロジェクトにsegmentのlabelを追加・更新します。

SYNOPSIS
    anno3d project put_segment_label PROJECT_ID EN_NAME DEFAULT_IGNORE SEGMENT_TYPE <flags>

DESCRIPTION
    対象のプロジェクトにsegmentのlabelを追加・更新します。

POSITIONAL ARGUMENTS
    PROJECT_ID
        対象プロジェクト
    EN_NAME
        英語名称
    DEFAULT_IGNORE
        このラベルがついた領域を、デフォルトでは他のアノテーションから除外するかどうか。 Trueであれば除外する
    SEGMENT_TYPE
        "SEMANTIC" or "INSTANCE" を指定する。 "SEMANTIC"の場合、このラベルのインスタンスは唯一つとなる。 "INSTANCE"の場合複数のインスタンスを作成可能となる

FLAGS
    --layer=LAYER
        このラベルのレイヤーを指定する。 同じレイヤーのラベルは、頂点を共有することが出来ない。 また、大きな値のレイヤーが優先して表示される。 指定しない場合は 100
    --label_id=LABEL_ID
        追加・更新するラベルのid。指定しない場合はuuidが設定される。
    --ja_name=JA_NAME
        日本語名称。指定しない場合はen_nameと同じ名称が設定される。
    --color=COLOR
        ラベルの表示色。 "(R,G,B)"形式の文字列 R/G/Bは、それぞれ0〜255の整数値で指定する。指定しない場合はランダムに設定される。
    --annofab_id=ANNOFAB_ID
        AnnofabのユーザID。指定が無い場合は環境変数`ANNOFAB_USER_ID`の値を採用する
    --annofab_pass=ANNOFAB_PASS
        Annofabのパスワード。指定が無い場合は環境変数`ANNOFAB_PASSWORD`の値を採用する
    --annofab_endpoint=ANNOFAB_ENDPOINT
        AnnofabのAPIアクセス先エンドポイントを指定します。 省略した場合は環境変数`ANNOFAB_ENDPOINT`の値を利用します。環境変数も指定されていない場合、デフォルトのエンドポイント（https://annofab.com）を利用します

NOTES
    You can also use flags syntax for POSITIONAL ARGUMENTS
```

## コマンド例

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

# アノテーション範囲の設定

## ヘルプ

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
        AnnofabのユーザID。指定が無い場合は環境変数`ANNOFAB_USER_ID`の値を採用する
    --annofab_pass=ANNOFAB_PASS
        Annofabのパスワード。指定が無い場合は環境変数`ANNOFAB_PASSWORD`の値を採用する

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
        AnnofabのユーザID。指定が無い場合は環境変数`ANNOFAB_USER_ID`の値を採用する
    --annofab_pass=ANNOFAB_PASS
        Annofabのパスワード。指定が無い場合は環境変数`ANNOFAB_PASSWORD`の値を採用する

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
        AnnofabのユーザID。指定が無い場合は環境変数`ANNOFAB_USER_ID`の値を採用する
    --annofab_pass=ANNOFAB_PASS
        Annofabのパスワード。指定が無い場合は環境変数`ANNOFAB_PASSWORD`の値を採用する

NOTES
    You can also use flags syntax for POSITIONAL ARGUMENTS
```


## コマンド例

### アノテーション範囲を「全体」に設定

```
anno3d project set_whole_annotation_area \
  --annofab_id ${ANNO_ID} \
  --annofab_pass ${ANNO_PASS} \
  --project_id ${ANNO_PRJ}
```

### アノテーション範囲を「半径10」に設定

```
anno3d project set_sphere_annotation_area \
  --annofab_id ${ANNO_ID} \
  --annofab_pass ${ANNO_PASS} \
  --project_id ${ANNO_PRJ} \
  --radius 10.0
```

### アノテーション範囲を「-10 < x < 20, -5 < y < 10の矩形」に設定

```
anno3d project set_rect_annotation_area \
  --annofab_id ${ANNO_ID} \
  --annofab_pass ${ANNO_PASS} \
  --project_id ${ANNO_PRJ} \
  --x "(-10.0, 20.0)" \
  --y "(-5.0, 10.0)"
```

# Cuboidの規定サイズの設定

## ヘルプ

```
$ anno3d project add_preset_cuboid_size --help | cat
INFO: Showing help with the command 'anno3d project add_preset_cuboid_size -- --help'.

NAME
    anno3d project add_preset_cuboid_size - 対象のプロジェクトにcuboidの規定サイズを追加・更新します。

SYNOPSIS
    anno3d project add_preset_cuboid_size PROJECT_ID KEY_NAME JA_NAME EN_NAME WIDTH HEIGHT DEPTH ORDER <flags>

DESCRIPTION
    対象のプロジェクトにcuboidの規定サイズを追加・更新します。

POSITIONAL ARGUMENTS
    PROJECT_ID
        対象プロジェクト
    KEY_NAME
        追加・更新する規定サイズの名前(英数字)。 `presetCuboidSize{Key_name}`というメタデータ・キーに対して規定サイズが設定される（Key_nameはkey_nameの頭文字を大文字にしたもの）
    JA_NAME
        日本語名称
    EN_NAME
        英語名称
    WIDTH
        追加・更新する規定サイズの幅（Cuboidのlocal axisにおけるY軸方向の長さ）
    HEIGHT
        追加・更新する規定サイズの高さ（Cuboidのlocal axisにおけるZ軸方向の長さ）
    DEPTH
        追加・更新する規定サイズの奥行（Cuboidのlocal axisにおけるX軸方向の長さ）
    ORDER
        エディタ上での表示順を決めるのに使用される整数（昇順で並べられる）

FLAGS
    --annofab_id=ANNOFAB_ID
        AnnofabのユーザID。指定が無い場合は環境変数`ANNOFAB_USER_ID`の値を採用する
    --annofab_pass=ANNOFAB_PASS
        Annofabのパスワード。指定が無い場合は環境変数`ANNOFAB_PASSWORD`の値を採用する

NOTES
    You can also use flags syntax for POSITIONAL ARGUMENTS
```

```
$ anno3d project remove_preset_cuboid_size --help | cat
INFO: Showing help with the command 'anno3d project remove_preset_cuboid_size -- --help'.

NAME
    anno3d project remove_preset_cuboid_size - 対象のプロジェクトからcuboidの規定サイズを削除します。

SYNOPSIS
    anno3d project remove_preset_cuboid_size PROJECT_ID KEY_NAME <flags>

DESCRIPTION
    対象のプロジェクトからcuboidの規定サイズを削除します。

POSITIONAL ARGUMENTS
    PROJECT_ID
        対象プロジェクト
    KEY_NAME
        削除する規定サイズの名前(英数字)。 `presetCuboidSize{Key_name}`というキーのメタデータが削除される(Key_nameはkey_nameの頭文字を大文字にしたもの)

FLAGS
    --annofab_id=ANNOFAB_ID
        AnnofabのユーザID。指定が無い場合は環境変数`ANNOFAB_USER_ID`の値を採用する
    --annofab_pass=ANNOFAB_PASS
        Annofabのパスワード。指定が無い場合は環境変数`ANNOFAB_PASSWORD`の値を採用する

NOTES
    You can also use flags syntax for POSITIONAL ARGUMENTS
```

## コマンド例

### Cuboidの規定サイズを追加・更新

```
$ anno3d project add_preset_cuboid_size \
    --annofab_id ${ANNO_ID} \
    --annofab_pass ${ANNO_PASS} \
    --project_id ${ANNO_PRJ} \
    --key_name test1 \
    --ja_name テスト１ \
    --en_name Test1 \
    --width 10 \
    --height 11 \
    --depth 12 \
    --order 1
```

### Cuboidの規定サイズを削除

```
$ anno3d project remove_preset_cuboid_size \
    --annofab_id ${ANNO_ID} \
    --annofab_pass ${ANNO_PASS} \
    --project_id ${ANNO_PRJ} \
    --key_name test1 
```


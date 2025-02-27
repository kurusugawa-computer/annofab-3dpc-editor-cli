from dataclasses import dataclass

lang_ja = "ja-JP"
lang_en = "en-US"

segment_type_semantic = "SEMANTIC"
segment_type_instance = "INSTANCE"


@dataclass
class IgnoreAdditionalDef:
    id: str
    ja_name: str
    en_name: str
    default: bool


default_ignore_additional = IgnoreAdditionalDef("__3dpc-editor-default-ignore", "無視", "ignore", True)
default_non_ignore_additional = IgnoreAdditionalDef("__3dpc-editor-non-default-ignore", "無視", "ignore", False)

# Annofabで定義されている標準三次元エディタプラグインのID（dev / production共通）
builtin_3d_editor_plugin_id = "bdc16348-107e-4fbc-af4a-e482bc84a60f"

# Annofabで定義されている標準三次元エディタ用拡張仕様プラグインのID（dev / production共通）
builtin_3d_extended_specs_plugin_id = "703ababa-96ac-4920-8afb-d4f2bddac7e3"

# Annofabで定義されているプロジェクト追加データ種別 ProjectExtraData3d のID（dev / production共通）
project_extra_data_3d_kind_id = "5039f9d9-208d-42a2-9ff2-790faaf4ceed"

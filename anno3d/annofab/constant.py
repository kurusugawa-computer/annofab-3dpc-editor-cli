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

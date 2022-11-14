import copy
from dataclasses import replace
from typing import Dict, Optional

from annofabapi.dataclass.annotation_specs import LabelV3

from anno3d.annofab.specifiers.label_specifiers import AnnotationType, LabelSpecifiers
from anno3d.model.label import SegmentLabelInfo


class MetadataLabelSpecifiers(LabelSpecifiers):
    """
    拡張仕様プラグイン適用前の、Metadataにラベルの情報を埋め込んでいる仕様のための LabelSpecifiers実装
    以下のコードで表現されるメタデータを編集する機能をLabelSpecifiersに注入する

    @camelcase
    @dataclass(frozen=True)
    class CuboidLabelMetadata(DataClassJsonMixin):
        ""
        LabelV3.metadataに3d-editor用情報を埋め込む場合に利用する型
        互換性用に残してある型なので、拡張しないこと
        Cuboid用
        ""

        type: str = "CUBOID"


    @camelcase
    @dataclass(frozen=True)
    class SegmentLabelMetadata(DataClassJsonMixin):
        ""
        LabelV3.metadataに3d-editor用情報を埋め込む場合に利用する型
        互換性用に残してある型なので、拡張しないこと
        Segment用
        Args:
            ignore: ignore設定に利用するAdditionalDataのid
            layer: レイヤーを表す数値文字列
            segment_kind: "SEMANTIC" | "INSTANCE"
            type: "SEGMENT" 固定
        ""

        ignore: str
        layer: str = "100"
        segment_kind: str = "SEMANTIC"
        type: str = "SEGMENT"
        version: str = "1"
    """

    def __init__(self):
        super().__init__()

    @staticmethod
    def extended_specs_plugin_version() -> Optional[str]:
        return None

    def _get_metadata(self, label: LabelV3) -> Dict[str, str]:
        return self.metadata.get(label)

    def _zoom_in_segment_info(self, label: LabelV3) -> SegmentLabelInfo:
        default = SegmentLabelInfo()
        meta = self._get_metadata(label)
        ignore = meta.get("ignore", default.ignore)
        layer = int(meta.get("layer", str(default.layer)))
        return SegmentLabelInfo(ignore=ignore, layer=layer)

    def _zoom_out_segment_info(self, label: LabelV3, info: SegmentLabelInfo) -> LabelV3:
        meta = self._get_metadata(label)
        result = copy.deepcopy(meta)

        if info.ignore is None:
            result.pop("ignore", None)
        else:
            result["ignore"] = info.ignore

        result["layer"] = str(info.layer)
        return replace(label, metadata=result)

    def _zoom_in_annotation_type(self, label: LabelV3) -> AnnotationType:
        meta = self._get_metadata(label)
        label_type = meta.get("type", None)
        if label_type == "SEGMENT":
            seg_kind = meta.get("segmentKind", None)
            if seg_kind == "SEMANTIC":
                return "user_semantic_segment"
            elif seg_kind == "INSTANCE":
                return "user_instance_segment"
            else:
                raise RuntimeError(f'label.metadata["segmentKind"]が想定外の値(={label_type})です。')
        else:
            # "type"が無い場合は、Cuboidしかなかった最初期の仕様のはず
            return "user_bounding_box"

    def _zoom_out_annotation_type(self, label: LabelV3, anno_type: AnnotationType) -> LabelV3:
        def init_segment_result(base: Dict[str, str]) -> Dict[str, str]:
            init = copy.deepcopy(base)
            init["version"] = "1"
            init["type"] = "SEGMENT"
            return init

        meta = self._get_metadata(label)
        if anno_type == "user_bounding_box":
            return replace(label, metadata={"type": "CUBOID"})
        elif anno_type == "user_semantic_segment":
            result = init_segment_result(meta)
            result["segmentKind"] = "SEMANTIC"
            return replace(label, metadata=result)
        elif anno_type == "user_instance_segment":
            result = init_segment_result(meta)
            result["segmentKind"] = "INSTANCE"
            return replace(label, metadata=result)
        else:
            raise RuntimeError(f"anno_typeが想定外の値(={anno_type})です。")

    def _zoom_in_ignore(self, label: LabelV3) -> Optional[str]:
        meta = self._get_metadata(label)
        return meta.get("ignore", None)

    def _zoom_out_ignore(self, label: LabelV3, ignore: Optional[str]) -> LabelV3:
        meta = self._get_metadata(label)
        result = copy.deepcopy(meta)
        if ignore is None:
            result.pop("ignore", None)
        else:
            result["ignore"] = ignore

        return replace(label, metadata=result)

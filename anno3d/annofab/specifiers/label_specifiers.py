import copy
from dataclasses import replace
from typing import Callable, Dict, Literal, Optional, cast

from annofabapi.dataclass.annotation_specs import Color, LabelV3

from anno3d.annofab.specifiers.utils import GenList
from anno3d.model.label import SegmentLabelInfo
from anno3d.util.modifier import DataSpecifier

zero_color = Color(0, 0, 0)


AnnotationType = Literal["user_bounding_box", "user_semantic_segment", "user_instance_segment"]


class LabelSpecifiers:
    label = DataSpecifier.identity(LabelV3)
    color = label.zoom(
        lambda label: label.color if label.color is not None else zero_color,
        lambda label, color: replace(label, color=color),
    )

    metadata: DataSpecifier[LabelV3, Dict[str, str]] = label.zoom(
        lambda label: label.metadata if label.metadata is not None else {},
        lambda label, metadata: replace(label, metadata=metadata),
    )

    """
    仕様拡張プラグイン前との互換性のため、以下の表現のメタデータを生成する定義群
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

    @staticmethod
    def zoom_in_segment_info(meta: Dict[str, str]) -> SegmentLabelInfo:
        return SegmentLabelInfo(ignore=meta["ignore"], layer=int(meta["layer"]))

    @staticmethod
    def zoom_out_segment_info(meta: Dict[str, str], info: SegmentLabelInfo) -> Dict[str, str]:
        result = copy.deepcopy(meta)

        if info.ignore is None:
            result.pop("ignore", None)
        else:
            result["ignore"] = info.ignore

        result["layer"] = str(info.layer)
        return result

    @staticmethod
    def zoom_in_segment_kind(meta: Dict[str, str]) -> Literal["SEMANTIC", "INSTANCE"]:
        return cast(Literal["SEMANTIC", "INSTANCE"], meta["segmentKind"])

    @staticmethod
    def zoom_out_segment_kind(meta: Dict[str, str], kind: Literal["SEMANTIC", "INSTANCE"]) -> Dict[str, str]:
        result = copy.deepcopy(meta)
        result["segmentKind"] = kind
        return result

    @staticmethod
    def zoom_in_annotation_type(meta: Dict[str, str]) -> AnnotationType:
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

    @staticmethod
    def zoom_out_annotation_type(meta: Dict[str, str], anno_type: AnnotationType) -> Dict[str, str]:
        def init_segment_result(base: Dict[str, str]) -> Dict[str, str]:
            init = copy.deepcopy(base)
            init["version"] = "1"
            init["type"] = "SEGMENT"
            return init

        if anno_type == "user_bounding_box":
            return {"type": "CUBOID"}
        elif anno_type == "user_semantic_segment":
            result = init_segment_result(meta)
            result["segmentKind"] = "SEMANTIC"
            return result
        elif anno_type == "user_instance_segment":
            result = init_segment_result(meta)
            result["segmentKind"] = "INSTANCE"
            return result
        else:
            raise RuntimeError(f"anno_typeが想定外の値(={anno_type})です。")

    @staticmethod
    def zoom_in_ignore(meta: Dict[str, str]) -> Optional[str]:
        return meta.get("ignore", None)

    @staticmethod
    def zoom_out_ignore(meta: Dict[str, str], ignore: Optional[str]) -> Dict[str, str]:
        result = copy.deepcopy(meta)
        if ignore is None:
            result.pop("ignore", None)
        else:
            result["ignore"] = ignore

        return result

    annotation_type = metadata.zoom(zoom_in_annotation_type, zoom_out_annotation_type)
    segment_kind = metadata.zoom(zoom_in_segment_kind, zoom_out_segment_kind)
    ignore = metadata.zoom(zoom_in_ignore, zoom_out_ignore)
    segment_info: DataSpecifier[LabelV3, SegmentLabelInfo] = metadata.zoom(zoom_in_segment_info, zoom_out_segment_info)

    layer = segment_info.zoom(lambda meta: meta.layer, lambda meta, layer: replace(meta, layer=layer))

    additionals = label.zoom(
        lambda label: label.additional_data_definitions if label.additional_data_definitions is not None else [],
        lambda label, additionals: replace(label, additional_data_definitions=additionals),
    )

    @classmethod
    def additional(cls, additional_id: str) -> DataSpecifier[LabelV3, Optional[str]]:
        predicate: Callable[[str], bool] = lambda additional: additional == additional_id
        return cls.additionals.zoom(GenList.gen_zoom_in(predicate), GenList.gen_zoom_out(predicate))

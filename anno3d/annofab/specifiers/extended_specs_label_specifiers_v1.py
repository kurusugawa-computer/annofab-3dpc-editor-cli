from dataclasses import replace
from typing import Optional, cast

from annofabapi.dataclass.annotation_specs import LabelV3

from anno3d.annofab.model import CuboidFieldValues, SegmentFieldValues
from anno3d.annofab.specifiers.label_specifiers import AnnotationType, LabelSpecifiers
from anno3d.model.label import SegmentLabelInfo


class ExtendedSpecsLabelSpecifiersV1(LabelSpecifiers):
    """拡張仕様プラグイン利用のアノテーション仕様向けLabelSpecifiers プラグインVersion 1.0.1用"""

    def __init__(self):
        super().__init__()

        def zoom_in_segment_field_values(label: LabelV3) -> Optional[SegmentFieldValues]:
            try:
                return SegmentFieldValues.from_dict(label.field_values)
            except:  # noqa: E722  pylint: disable=bare-except
                return None

        def zoom_out_segment_field_values(label: LabelV3, values: Optional[SegmentFieldValues]) -> LabelV3:
            if values is not None:
                return replace(
                    # encode_jsonがTrueの時、Valueを全てJsonに直接変換可能な型に変換しようとする
                    label,
                    field_values=values.to_dict(encode_json=True),
                )
            else:
                return label

        self._segment_field_values = self.label.zoom(zoom_in_segment_field_values, zoom_out_segment_field_values)

        def zoom_in_cuboid_field_values(label: LabelV3) -> Optional[CuboidFieldValues]:
            try:
                return CuboidFieldValues.from_dict(label.field_values)
            except:  # noqa: E722  pylint: disable=bare-except
                return None

        def zoom_out_cuboid_field_values(label: LabelV3, values: Optional[CuboidFieldValues]) -> LabelV3:
            if values is not None:
                return replace(
                    # encode_jsonがTrueの時、Valueを全てJsonに直接変換可能な型に変換しようとする
                    label,
                    field_values=values.to_dict(encode_json=True),
                )
            else:
                return label

        self._cuboid_field_values = self.label.zoom(
            zoom_in_cuboid_field_values,
            zoom_out_cuboid_field_values,
        )

    @staticmethod
    def extended_specs_plugin_version() -> Optional[str]:
        return "1.0.1"

    def _zoom_in_segment_info(self, label: LabelV3) -> SegmentLabelInfo:
        field_values = self._segment_field_values.get(label)
        default = SegmentLabelInfo()
        layer = field_values.layer.value if field_values is not None else default.layer
        return SegmentLabelInfo(layer=layer, ignore=None)

    def _zoom_out_segment_info(self, label: LabelV3, info: SegmentLabelInfo) -> LabelV3:
        values = SegmentFieldValues.from_values(info.layer)
        return self._segment_field_values.set(values)(label)

    def _zoom_in_annotation_type(self, label: LabelV3) -> AnnotationType:
        return cast(AnnotationType, label.annotation_type)

    def _zoom_out_annotation_type(self, label: LabelV3, anno_type: AnnotationType) -> LabelV3:
        return replace(label, annotation_type=anno_type)

    def _zoom_in_ignore(self, label: LabelV3) -> Optional[str]:
        # ignoreは廃止された
        return None

    def _zoom_out_ignore(self, label: LabelV3, ignore: Optional[str]) -> LabelV3:
        # ignoreは廃止された
        return label

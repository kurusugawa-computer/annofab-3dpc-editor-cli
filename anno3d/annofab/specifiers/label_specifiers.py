from abc import ABC, abstractmethod
from dataclasses import replace
from typing import Callable, Dict, List, Literal, Optional, TypeVar

from annofabapi.dataclass.annotation_specs import Color, LabelV3

from anno3d.annofab.specifiers.utils import GenList
from anno3d.model.label import SegmentLabelInfo
from anno3d.util.modifier import DataSpecifier

zero_color = Color(0, 0, 0)


AnnotationType = Literal["user_bounding_box", "user_semantic_segment", "user_instance_segment"]
SegmentKind = Literal["SEMANTIC", "INSTANCE"]
T = TypeVar("T")
LabelSpecifier = DataSpecifier[LabelV3, T]


class LabelSpecifiers(ABC):
    def __init__(self):
        super().__init__()
        self._label = DataSpecifier.identity(LabelV3)
        self._color = self.label.zoom(
            lambda label: label.color if label.color is not None else zero_color,
            lambda label, color: replace(label, color=color),
        )
        self._additionals = self._label.zoom(
            lambda label: label.additional_data_definitions if label.additional_data_definitions is not None else [],
            lambda label, additionals: replace(label, additional_data_definitions=additionals),
        )
        self._metadata = self._label.zoom(
            lambda label: label.metadata if label.metadata is not None else {},
            lambda label, metadata: replace(label, metadata=metadata),
        )

        self._annotation_type = self._label.zoom(self._zoom_in_annotation_type, self._zoom_out_annotation_type)
        self._ignore = self._label.zoom(self._zoom_in_ignore, self._zoom_out_ignore)
        self._segment_info = self._label.zoom(self._zoom_in_segment_info, self._zoom_out_segment_info)
        self._layer = self._segment_info.zoom(lambda meta: meta.layer, lambda meta, layer: replace(meta, layer=layer))

    # ==============================
    # abstract method群　ここから
    # ==============================

    @staticmethod
    @abstractmethod
    def extended_specs_plugin_version() -> Optional[str]:
        """
        このLabelSpecifiersが対応している拡張仕様プラグインバージョン
        拡張仕様プラグイン前の仕様に対応している場合None
        """

    @abstractmethod
    def _zoom_in_segment_info(self, label: LabelV3) -> SegmentLabelInfo:
        pass

    @abstractmethod
    def _zoom_out_segment_info(self, label: LabelV3, info: SegmentLabelInfo) -> LabelV3:
        pass

    @abstractmethod
    def _zoom_in_annotation_type(self, label: LabelV3) -> AnnotationType:
        pass

    @abstractmethod
    def _zoom_out_annotation_type(self, label: LabelV3, anno_type: AnnotationType) -> LabelV3:
        pass

    @abstractmethod
    def _zoom_in_ignore(self, label: LabelV3) -> Optional[str]:
        pass

    @abstractmethod
    def _zoom_out_ignore(self, label: LabelV3, ignore: Optional[str]) -> LabelV3:
        pass

    # ==============================
    # abstract method群　ここまで
    # ==============================

    @property
    def label(self) -> LabelSpecifier[LabelV3]:
        return self._label

    @property
    def color(self) -> LabelSpecifier[Color]:
        return self._color

    @property
    def metadata(self) -> LabelSpecifier[Dict[str, str]]:
        return self._metadata

    @property
    def additionals(self) -> LabelSpecifier[List[str]]:
        return self._additionals

    def additional(self, additional_id: str) -> DataSpecifier[LabelV3, Optional[str]]:
        predicate: Callable[[str], bool] = lambda additional: additional == additional_id
        return self.additionals.zoom(GenList.gen_zoom_in(predicate), GenList.gen_zoom_out(predicate))

    @property
    def annotation_type(self) -> LabelSpecifier[AnnotationType]:
        return self._annotation_type

    @property
    def ignore(self) -> LabelSpecifier[Optional[str]]:
        return self._ignore

    @property
    def segment_info(self) -> LabelSpecifier[SegmentLabelInfo]:
        return self._segment_info

    @property
    def layer(self) -> LabelSpecifier[int]:
        return self._layer

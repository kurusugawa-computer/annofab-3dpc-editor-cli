from dataclasses import replace
from typing import Callable, Dict, List, Optional, TypeVar

from annofabapi.dataclass.annotation_specs import AdditionalDataDefinitionV2, AnnotationSpecsV3, LabelV3

from anno3d.annofab.specifiers.utils import GenList
from anno3d.model.project_specs_meta import decode_project_meta, encode_project_meta
from anno3d.util.modifier import DataSpecifier

A = TypeVar("A")
AS = AnnotationSpecsV3


class ProjectSpecifiers:
    annotation = DataSpecifier.identity(AnnotationSpecsV3)

    class Labels:
        @staticmethod
        def zoom_in(anno: AS) -> List[LabelV3]:
            return anno.labels if anno.labels is not None else []

        @staticmethod
        def zoom_out(anno: AS, labels: List[LabelV3]) -> AS:
            return replace(anno, labels=labels)

    labels: DataSpecifier[AS, List[LabelV3]] = annotation.zoom(Labels.zoom_in, Labels.zoom_out)

    @classmethod
    def label(cls, label_id: str) -> DataSpecifier[AS, Optional[LabelV3]]:
        predicate: Callable[[LabelV3], bool] = lambda l: l.label_id == label_id
        return cls.labels.zoom(GenList.gen_zoom_in(predicate), GenList.gen_zoom_out(predicate))

    class Additionals:
        @staticmethod
        def zoom_in(anno: AS) -> List[AdditionalDataDefinitionV2]:
            return anno.additionals if anno.additionals is not None else []

        @staticmethod
        def zoom_out(anno: AS, additionals: List[AdditionalDataDefinitionV2]) -> AS:
            return replace(anno, additionals=additionals)

    additionals = annotation.zoom(Additionals.zoom_in, Additionals.zoom_out)

    @classmethod
    def additional(cls, additional_id: str) -> DataSpecifier[AS, Optional[AdditionalDataDefinitionV2]]:
        predicate: Callable[[AdditionalDataDefinitionV2], bool] = (
            lambda additionals: additionals.additional_data_definition_id == additional_id
        )

        return cls.additionals.zoom(GenList.gen_zoom_in(predicate), GenList.gen_zoom_out(predicate))

    metadata_dict: DataSpecifier[AS, Dict[str, str]] = annotation.zoom(
        lambda specs: specs.metadata if specs.metadata is not None else {},
        lambda specs, meta: replace(specs, metadata=meta),
    )

    metadata = metadata_dict.bimap(decode_project_meta, encode_project_meta)

    annotation_area = metadata.zoom(lambda m: m.annotation_area, lambda m, area: replace(m, annotation_area=area))

    preset_cuboid_sizes = metadata.zoom(
        lambda m: m.preset_cuboid_sizes, lambda m, cuboids: replace(m, preset_cuboid_sizes=cuboids)
    )

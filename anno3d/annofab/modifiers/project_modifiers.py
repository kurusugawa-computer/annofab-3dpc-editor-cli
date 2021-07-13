from dataclasses import replace
from typing import Callable, List, Optional, TypeVar

import more_itertools
from annofabapi.dataclass.annotation_specs import AdditionalDataDefinitionV2, AnnotationSpecsV2, LabelV2

from anno3d.util.modifier import DataSpecifier

A = TypeVar("A")
AS = AnnotationSpecsV2


class ProjectSpecifiers:
    annotation = DataSpecifier.identity(AnnotationSpecsV2)

    class GenList:
        @staticmethod
        def gen_zoom_in(pred: Callable[[A], bool]) -> Callable[[List[A]], Optional[A]]:
            return lambda l: more_itertools.first_true(l, pred=pred)

        @staticmethod
        def gen_zoom_out(pred: Callable[[A], bool]) -> Callable[[List[A], Optional[A]], List[A]]:
            def zoom_out(a_list: List[A], a: Optional[A]) -> List[A]:
                index, _ = more_itertools.first_true(
                    enumerate(a_list), pred=lambda ie: pred(ie[1]), default=(None, None)
                )
                if index is None:
                    if a is None:
                        pass
                    else:
                        a_list.append(a)
                else:
                    if a is None:
                        a_list.pop(index)
                    else:
                        a_list[index] = a

                return a_list

            return zoom_out

    class Labels:
        @staticmethod
        def zoom_in(anno: AS) -> List[LabelV2]:
            return anno.labels if anno.labels is not None else []

        @staticmethod
        def zoom_out(anno: AS, labels: List[LabelV2]) -> AS:
            return replace(anno, labels=labels)

    labels: DataSpecifier[AS, List[LabelV2]] = annotation.zoom(Labels.zoom_in, Labels.zoom_out)

    @classmethod
    def label(cls, label_id: str) -> DataSpecifier[AS, Optional[LabelV2]]:
        predicate: Callable[[LabelV2], bool] = lambda l: l.label_id == label_id
        return cls.labels.zoom(cls.GenList.gen_zoom_in(predicate), cls.GenList.gen_zoom_out(predicate))

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
        predicate: Callable[
            [AdditionalDataDefinitionV2], bool
        ] = lambda additionals: additionals.additional_data_definition_id == additional_id

        return cls.additionals.zoom(cls.GenList.gen_zoom_in(predicate), cls.GenList.gen_zoom_out(predicate))

    metadata_dict = annotation.zoom(
        lambda specs: specs.metadata if specs.metadata is not None else {},
        lambda specs, meta: replace(specs, metadata=meta),
    )


class ProjectModifiers:
    pass

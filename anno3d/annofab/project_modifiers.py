from dataclasses import replace
from typing import List, Optional

import more_itertools
from annofabapi.dataclass.annotation_specs import AnnotationSpecsV2, LabelV2

from anno3d.util.modifier import DataSpecifier

AS = AnnotationSpecsV2


class ProjectSpecifiers:
    annotation = DataSpecifier.identity(AnnotationSpecsV2)

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
        def zoom_in(labels: List[LabelV2]) -> Optional[LabelV2]:
            return more_itertools.first_true(labels, pred=lambda l: l.label_id == label_id)

        def zoom_out(labels: List[LabelV2], label: Optional[LabelV2]) -> List[LabelV2]:
            index, _ = more_itertools.first_true(
                enumerate(labels), pred=lambda ie: ie[1].label_id == label_id, default=(None, None)
            )
            if index is None:
                if label is None:
                    pass
                else:
                    labels.append(label)
            else:
                if label is None:
                    labels.pop(index)
                else:
                    labels[index] = label

            return labels

        return cls.labels.zoom(zoom_in, zoom_out)

    # def label_color(self, label_id: str):

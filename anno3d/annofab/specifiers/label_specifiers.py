from dataclasses import replace
from typing import Callable, Optional

from annofabapi.dataclass.annotation_specs import Color, LabelV2

from anno3d.annofab.specifiers.utils import GenList
from anno3d.util.modifier import DataSpecifier

zero_color = Color(0, 0, 0)


class LabelSpecifiers:
    label = DataSpecifier.identity(LabelV2)
    color = label.zoom(
        lambda label: label.color if label.color is not None else zero_color,
        lambda label, color: replace(label, color=color),
    )

    additionals = label.zoom(
        lambda label: label.additional_data_definitions if label.additional_data_definitions is not None else [],
        lambda label, additionals: replace(label, additional_data_definitions=additionals),
    )

    @classmethod
    def additional(cls, additional_id: str) -> DataSpecifier[LabelV2, Optional[str]]:
        predicate: Callable[[str], bool] = lambda additional: additional == additional_id
        return cls.additionals.zoom(GenList.gen_zoom_in(predicate), GenList.gen_zoom_out(predicate))

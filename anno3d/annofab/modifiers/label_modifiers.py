from dataclasses import replace

from annofabapi.dataclass.annotation_specs import Color, LabelV2

from anno3d.util.modifier import DataSpecifier

zero_color = Color(0, 0, 0)


class LabelSpecifiers:
    label = DataSpecifier.identity(LabelV2)
    color = label.zoom(
        lambda label: label.color if label.color is not None else zero_color,
        lambda label, color: replace(label, color=color),
    )

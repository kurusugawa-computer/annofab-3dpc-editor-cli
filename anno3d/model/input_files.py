from dataclasses import dataclass
from typing import List

from dataclasses_json import DataClassJsonMixin


@dataclass(frozen=True)
class SupplementaryBody(DataClassJsonMixin):
    supplementary_data_name: str
    supplementary_data_path: str
    supplementary_data_type: str = "custom"
    supplementary_data_number: int = 0


@dataclass(frozen=True)
class Supplementary(DataClassJsonMixin):
    id: str
    body: SupplementaryBody


@dataclass(frozen=True)
class InputDataBody(DataClassJsonMixin):
    input_data_name: str
    input_data_path: str


@dataclass(frozen=True)
class InputData(DataClassJsonMixin):
    id: str
    body: InputDataBody
    supplementary_list: List[Supplementary]

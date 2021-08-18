from dataclasses import dataclass
from typing import Type, TypeVar

from dataclasses_json import DataClassJsonMixin, LetterCase, config

A = TypeVar("A", bound=DataClassJsonMixin)


def camelcase(cls: Type[A]) -> Type[A]:
    cls.dataclass_json_config = config(letter_case=LetterCase.CAMEL)["dataclasses_json"]  # type: ignore

    # 受け取ったクラスはそのまま返す
    return cls


@camelcase
@dataclass(frozen=True)
class Vector3(DataClassJsonMixin):
    x: float
    y: float
    z: float

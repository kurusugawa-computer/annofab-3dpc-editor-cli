from abc import abstractmethod
from typing import Generic, Optional, TypeVar

A = TypeVar("A")


class ValueProvider(Generic[A]):
    value_name: str

    def __init__(self, name: str):
        self.value_name = name

    def value(self) -> A:
        v = self.value_opt()
        if v is None:
            raise RuntimeError(f"{self.value_name}を取得できませんでした")
        return v

    def or_else(self, that: "ValueProvider[A]") -> "ValueProvider[A]":
        return OrElseValueProvider(self, that)

    @abstractmethod
    def value_opt(self) -> Optional[A]:
        ...


class OrElseValueProvider(ValueProvider[A]):
    _left: ValueProvider[A]
    _right: ValueProvider[A]

    def __init__(self, left: ValueProvider[A], right: ValueProvider[A]):
        super().__init__(left.value_name)
        self._left = left
        self._right = right

    def value_opt(self) -> Optional[A]:
        left_value = self._left.value_opt()
        if left_value is not None:
            return left_value

        return self._right.value_opt()


class NoneValueProvider(ValueProvider[A]):
    def __init__(self, name: str):
        super().__init__(name)

    def value_opt(self) -> Optional[A]:
        return None


class ConstValueProvider(ValueProvider[A]):
    _value: A

    def __init__(self, name: str, value: A):
        super().__init__(name)
        self._value = value

    def value_opt(self) -> Optional[A]:
        return self._value

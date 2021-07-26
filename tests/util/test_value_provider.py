from typing import TypeVar

from anno3d.util.value_provider import ConstValueProvider, NoneValueProvider, ValueProvider

A = TypeVar("A")


def test_OrElseProviderのleftがNoneの時rightの値が返ること():
    def test(provider: ValueProvider[A]) -> None:
        result = NoneValueProvider[A]("test").or_else(provider).value()
        assert result == provider.value()

    test(ConstValueProvider("test", "hoge"))
    test(ConstValueProvider("test", 12))
    test(ConstValueProvider("test", True))


def test_OrElseProviderのleftがNoneで無い時leftの値が返ること():
    def test(provider: ValueProvider[A]) -> None:
        result = provider.or_else(NoneValueProvider[A]("test")).value()
        assert result == provider.value()

    test(ConstValueProvider("test", "hoge"))
    test(ConstValueProvider("test", 12))
    test(ConstValueProvider("test", True))

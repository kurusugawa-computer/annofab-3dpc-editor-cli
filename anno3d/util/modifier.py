from typing import Callable, Generic, Protocol, Type, TypeVar

A = TypeVar("A")
B = TypeVar("B")
C = TypeVar("C")
D = TypeVar("D")


class DataSpecifier(Protocol[A, B]):
    """
    データの変更場所の定義を行う構造です
    最終的に生成するのはA型の変換関数でです。
    この型はAから辿ることの可能なB型の値を変更しようとしていることを表します。

    """

    def zoom(self, zoom_in: Callable[[B], C], zoom_out: Callable[[B, C], B]) -> "DataSpecifier[A, C]":
        ...

    def and_then(self, that: "DataSpecifier[B, C]") -> "DataSpecifier[A, C]":
        ...

    def mod(self, f: Callable[[B], B]) -> "DataModifier[A]":
        ...

    @staticmethod
    def identity(_: Type[A]) -> "DataSpecifier[A, A]":
        return IdentityDataSpecifier()


class ZoomedDataSpecifier(Generic[A, B, C], DataSpecifier[A, C]):
    _underlying: DataSpecifier[A, B]

    # CallableのFieldを宣言すると、mypyがメソッドとして扱扱うらしく、第一引数が消えた型になる。
    # ので、書きたいけど書いてない
    # _zoom_in: Callable[[B], C]
    # _zoom_out: Callable[[B, C], B]

    def __init__(self, underlying: DataSpecifier[A, B], zoom_in: Callable[[B], C], zoom_out: Callable[[B, C], B]):
        self._underlying = underlying
        self._zoom_in = zoom_in
        self._zoom_out = zoom_out

    def zoom(self, zoom_in: Callable[[C], D], zoom_out: Callable[[C, D], C]) -> "DataSpecifier[A, D]":
        return ZoomedDataSpecifier(self, zoom_in, zoom_out)

    def and_then(self, that: "DataSpecifier[C, D]") -> "DataSpecifier[A, D]":
        return AndThenDataSpecifier(self, that)

    def mod(self, f: Callable[[C], C]) -> "DataModifier[A]":
        def underlying_mod(b: B) -> B:
            zoom_in: Callable[[B], C] = self._zoom_in
            zoom_out = self._zoom_out
            new_c = f(zoom_in(b))
            return zoom_out(b, new_c)

        return self._underlying.mod(underlying_mod)


class AndThenDataSpecifier(Generic[A, B, C], DataSpecifier[A, C]):
    _left: DataSpecifier[A, B]
    _right: DataSpecifier[B, C]

    def __init__(self, left: DataSpecifier[A, B], right: DataSpecifier[B, C]):
        self._left = left
        self._right = right

    def zoom(self, zoom_in: Callable[[C], D], zoom_out: Callable[[C, D], C]) -> "DataSpecifier[A, D]":
        return AndThenDataSpecifier(self._left, self._right.zoom(zoom_in, zoom_out))

    def and_then(self, that: "DataSpecifier[C, D]") -> "DataSpecifier[A, D]":
        return AndThenDataSpecifier(self, that)

    def mod(self, f: Callable[[C], C]) -> "DataModifier[A]":
        def mod_b(b: B) -> B:
            return self._right.mod(f)(b)

        return self._left.mod(mod_b)


class IdentityDataSpecifier(DataSpecifier[A, A]):
    def zoom(self, zoom_in: Callable[[A], C], zoom_out: Callable[[A, C], A]) -> "DataSpecifier[A, C]":
        return ZoomedDataSpecifier(self, zoom_in, zoom_out)

    def and_then(self, that: "DataSpecifier[A, B]") -> "DataSpecifier[A, B]":
        return that

    def mod(self, f: Callable[[A], A]) -> "DataModifier[A]":
        return DataModifier(f)


class DataModifier(Generic[A]):
    """
    DataSpecifierから生成されるA型の変換関数を表します。
    """

    # _mod: Callable[[A], A]

    def __init__(self, mod: Callable[[A], A]):
        self._mod = mod

    def compose(self, that: "DataModifier[A]") -> "DataModifier[A]":
        return DataModifier(lambda a: self(that(a)))

    def and_then(self, that: "DataModifier[A]") -> "DataModifier[A]":
        return that.compose(self)

    def __call__(self, a: A) -> A:
        mod = self._mod
        return mod(a)

from dataclasses import dataclass, replace

from anno3d.util.modifier import DataSpecifier


@dataclass
class Child:
    s: str
    b: bool


@dataclass
class Parent:
    s: str
    i: int
    f: float
    c: Child


def test_単純な一部の値の変換が可能であること():
    base = Child("str", True)
    child = DataSpecifier.identity(Child)
    s_spec = child.zoom(lambda c: c.s, lambda c, s: replace(c, s=s))
    b_spec = child.zoom(lambda c: c.b, lambda c, b: replace(c, b=b))

    replaced1 = s_spec.mod(lambda s: s + s)(base)
    replaced2 = b_spec.mod(lambda b: not b)(base)

    assert replaced1 == Child("strstr", True)
    assert replaced2 == Child("str", False)


def test_Modifierはand_thenによって結合可能であること():
    base = Child("str", True)
    child = DataSpecifier.identity(Child)
    s_spec = child.zoom(lambda c: c.s, lambda c, s: replace(c, s=s))
    b_spec = child.zoom(lambda c: c.b, lambda c, b: replace(c, b=b))

    mod_s = s_spec.mod(lambda s: s + s)
    mod_b = b_spec.mod(lambda b: not b)
    replaced = mod_s.and_then(mod_b)(base)

    assert replaced == Child("strstr", False)


def test_2回zoomして変更が可能であること():
    base = Parent("str1", 1, 1.5, Child("str2", False))
    spec = (
        DataSpecifier.identity(Parent)
        .zoom(lambda p: p.c, lambda p, c: replace(p, c=c))
        .zoom(lambda c: c.s, lambda c, s: replace(c, s=s))
    )
    replaced = spec.mod(lambda _: "hoge")(base)

    assert replaced == Parent("str1", 1, 1.5, Child("hoge", False))


def test_別の階層を変更するModifierを結合できること():
    base = Parent("str1", 1, 1.5, Child("str2", False))
    spec_s = (
        DataSpecifier.identity(Parent)
        .zoom(lambda p: p.c, lambda p, c: replace(p, c=c))
        .zoom(lambda c: c.s, lambda c, s: replace(c, s=s))
    )
    spec_f = DataSpecifier.identity(Parent).zoom(lambda p: p.f, lambda p, f: replace(p, f=f))

    mod_s = spec_s.mod(lambda s: s + s)
    mod_f = spec_f.mod(lambda f: f * 2)
    replaced = mod_s.compose(mod_f)(base)

    assert replaced == Parent("str1", 1, 3.0, Child("str2str2", False))


def test_specifierのand_thenでspecifierの結合が出来ること():
    base = Parent("str1", 1, 1.5, Child("str2", False))
    spec_pc = DataSpecifier.identity(Parent).zoom(lambda p: p.c, lambda p, c: replace(p, c=c))
    spec_cs = DataSpecifier.identity(Child).zoom(lambda c: c.s, lambda c, s: replace(c, s=s))
    spec_pcs = spec_pc.and_then(spec_cs)

    replaced = spec_pcs.mod(lambda s: s + "hogege")(base)

    assert replaced == Parent("str1", 1, 1.5, Child("str2hogege", False))


def test_bimapによる値の変換が出来ること():
    def map_f(s: str) -> int:
        return int(s)

    def comap(i: int) -> str:
        return str(i)

    def mod(s: int) -> int:
        return s + 10

    # identity
    id_base = "2"
    id_mapped = DataSpecifier.identity(str).bimap(map_f, comap)
    id_replaced = id_mapped.mod(mod)(id_base)
    assert id_replaced == "12"

    base = Parent("str1", 1, 1.5, Child("2", False))

    # zoom
    zoom_mapped = (
        DataSpecifier.identity(Parent)
        .zoom(lambda p: p.c, lambda p, c: replace(p, c=c))
        .zoom(lambda c: c.s, lambda c, s: replace(c, s=s))
        .bimap(map_f, comap)
    )
    zoom_replaced = zoom_mapped.mod(mod)(base)
    assert zoom_replaced == Parent("str1", 1, 1.5, Child("12", False))

    # and_then
    spec_pc = DataSpecifier.identity(Parent).zoom(lambda p: p.c, lambda p, c: replace(p, c=c))
    spec_cs = DataSpecifier.identity(Child).zoom(lambda c: c.s, lambda c, s: replace(c, s=s))
    and_then_mapped = spec_pc.and_then(spec_cs).bimap(map_f, comap)
    and_then_replaced = and_then_mapped.mod(mod)(base)
    assert and_then_replaced == Parent("str1", 1, 1.5, Child("12", False))


def test_setによる値の設定が出来ること():
    # identity
    id_base = "2"
    id_spec = DataSpecifier.identity(str)
    id_replaced = id_spec.set("hoge")(id_base)
    assert id_replaced == "hoge"

    base = Parent("str1", 1, 1.5, Child("2", False))

    # zoom
    zoom_spec = (
        DataSpecifier.identity(Parent)
        .zoom(lambda p: p.c, lambda p, c: replace(p, c=c))
        .zoom(lambda c: c.s, lambda c, s: replace(c, s=s))
    )
    zoom_replaced = zoom_spec.set("fuga")(base)
    assert zoom_replaced == Parent("str1", 1, 1.5, Child("fuga", False))

    # and_then
    spec_pc = DataSpecifier.identity(Parent).zoom(lambda p: p.c, lambda p, c: replace(p, c=c))
    spec_cs = DataSpecifier.identity(Child).zoom(lambda c: c.s, lambda c, s: replace(c, s=s))
    and_then_spec = spec_pc.and_then(spec_cs)
    and_then_replaced = and_then_spec.set("piyo")(base)
    assert and_then_replaced == Parent("str1", 1, 1.5, Child("piyo", False))


def test_getによる値の取得が出来ること():
    # identity
    id_base = "2"
    id_spec = DataSpecifier.identity(str)
    assert id_spec.get(id_base) == "2"

    base = Parent("str1", 1, 1.5, Child("2", False))

    # zoom
    zoom_spec = (
        DataSpecifier.identity(Parent)
        .zoom(lambda p: p.c, lambda p, c: replace(p, c=c))
        .zoom(lambda c: c.s, lambda c, s: replace(c, s=s))
    )
    assert zoom_spec.get(base) == "2"

    # and_then
    spec_pc = DataSpecifier.identity(Parent).zoom(lambda p: p.c, lambda p, c: replace(p, c=c))
    spec_cs = DataSpecifier.identity(Child).zoom(lambda c: c.s, lambda c, s: replace(c, s=s))
    and_then_spec = spec_pc.and_then(spec_cs)
    assert and_then_spec.get(base) == "2"

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

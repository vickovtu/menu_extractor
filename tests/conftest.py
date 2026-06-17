import pytest

from menu_extractor.geometry import Line, Section, SubGroup, Word

# Maps role kind → (fontname, size) — matches what classify.word_role recognises.
ROLE_FONTS = {
    "header": ("IsidoraSans-Black", 16.0),
    "name": ("IsidoraSans-Bold", 10.0),
    "item": ("IsidoraSans-Medium", 10.0),
    "desc": ("IsidoraSans-Medium", 8.0),
    "price": ("BETRegular", 8.0),
}


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    for item in items:
        parent = item.path.parent.name
        if parent == "unit":
            item.add_marker(pytest.mark.unit)
        elif parent == "integration":
            item.add_marker(pytest.mark.integration)


@pytest.fixture
def make_word():
    """Generic Word factory; override any field by keyword."""

    def _factory(
        text: str = "x",
        *,
        x0: float = 0.0,
        x1: float = 10.0,
        top: float = 0.0,
        size: float = 10.0,
        fontname: str = "IsidoraSans-Bold",
    ) -> Word:
        return Word(text=text, x0=x0, x1=x1, top=top, bottom=top + size, size=size, fontname=fontname)

    return _factory


@pytest.fixture
def role_word(make_word):
    """Word with the fontname/size that classify.word_role recognises as the given role."""

    def _factory(text: str, role: str, *, x0: float = 0.0, top: float = 0.0) -> Word:
        fontname, size = ROLE_FONTS[role]
        return make_word(text=text, x0=x0, x1=x0 + 10, top=top, size=size, fontname=fontname)

    return _factory


@pytest.fixture
def role_line(role_word):
    """Line whose words share a single role, laid out sequentially from x0."""

    def _factory(role: str, *texts: str, x0: float = 0.0, top: float = 0.0, price: str | None = None) -> Line:
        words = [role_word(t, role, x0=x0 + i * 12, top=top) for i, t in enumerate(texts)]
        return Line(words=words, price_token=price)

    return _factory


@pytest.fixture
def make_section():
    """Section with one SubGroup wrapping the given lines."""

    def _factory(header: str, *lines: Line, sub_header: str | None = None) -> Section:
        return Section(header=header, sub_groups=[SubGroup(lines=list(lines), sub_header=sub_header)])

    return _factory

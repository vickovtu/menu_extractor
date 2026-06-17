import pytest

from menu_extractor.classify import Role, word_role


@pytest.mark.parametrize(
    ("fontname", "size", "expected"),
    [
        ("IsidoraSans-Black", 16.0, Role.HEADER),
        ("IsidoraSans-Bold", 10.0, Role.NAME),
        ("BETRegular", 8.0, Role.PRICE),
        ("IsidoraSans-Medium", 10.0, Role.ITEM),
        ("IsidoraSans-Medium", 8.0, Role.DESC),  # Medium below ITEM_SIZE_THRESHOLD = 9.0
        ("UnknownFont", 10.0, Role.DESC),  # fallthrough
        ("IsidoraSans-Bold", 6.0, Role.DROP),  # below MIN_KEEP_SIZE
    ],
)
def test_word_role(make_word, fontname: str, size: float, expected: Role):
    assert word_role(make_word(fontname=fontname, size=size)) is expected

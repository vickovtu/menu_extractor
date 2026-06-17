from enum import StrEnum

from menu_extractor.geometry import Word

# Font name encodes role more reliably than casing (headers and sauce names are both upper-case):
#   IsidoraSans-Black  -> section header     ("BURGERS")
#   IsidoraSans-Bold   -> dish name          ("ALL AMERICAN BURGER")
#   BETRegular         -> price              ("$17", "$X")
#   IsidoraSans-Medium -> body; size ~10 = standalone item (sauce/rub), size ~8 = description
ITEM_SIZE_THRESHOLD = 9.0
MIN_KEEP_SIZE = 7.5


class Role(StrEnum):
    HEADER = "header"
    NAME = "name"
    ITEM = "item"
    PRICE = "price"
    DESC = "desc"
    DROP = "drop"


def word_role(word: Word) -> Role:
    font = word.fontname
    if word.size < MIN_KEEP_SIZE:
        return Role.DROP
    if "BET" in font:
        return Role.PRICE
    if "Black" in font:
        return Role.HEADER
    if "Bold" in font:
        return Role.NAME
    if "Medium" in font:
        return Role.ITEM if word.size >= ITEM_SIZE_THRESHOLD else Role.DESC
    return Role.DESC

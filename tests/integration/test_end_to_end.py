from pathlib import Path

import pytest

from menu_extractor.extract import extract_menu

PDF = Path(__file__).resolve().parents[2] / "data" / "espn_bet.pdf"


@pytest.fixture(scope="module")
def items():
    if not PDF.is_file():
        pytest.skip(f"sample PDF not present: {PDF}")
    return extract_menu(PDF)


def _by_name(items, name):
    return next(item for item in items if item.dish_name == name)


def test_success_example_item(items):
    burger = _by_name(items, "ALL AMERICAN BURGER")
    assert burger.category == "BURGERS"
    assert burger.price == 17.0
    assert burger.price_text == "$17"
    assert burger.description == ("7 oz. steakburger, choice of cheese, lettuce, tomato, onion, pickles, brioche bun")


def test_multiline_description_is_merged(items):
    bbq = _by_name(items, "BBQ BACON BURGER")
    assert bbq.description.endswith("brioche bun")
    assert "\n" not in bbq.description


def test_unpriced_items_have_null_price(items):
    sauce = _by_name(items, "GARLIC PARMESAN")
    assert sauce.price is None
    assert sauce.price_text is None


def test_placeholder_price_is_preserved_as_text(items):
    cocktail = _by_name(items, "DILLINOIS")
    assert cocktail.price is None
    assert cocktail.price_text == "$X"


def test_all_target_food_sections_present(items):
    categories = {item.category for item in items}
    for expected in ["LEADING OFF", "SLIDER TOWERS", "BURGERS", "MAIN EVENT", "SIDES", "OVERTIME"]:
        assert expected in categories


def test_dish_ids_unique_and_sequential(items):
    ids = [item.dish_id for item in items]
    assert ids == [f"{number:03d}" for number in range(1, len(items) + 1)]


def test_wings_block_sub_headers_are_folded_into_dish_name(items):
    chicken_dishes = {item.dish_name: item for item in items if item.category == "AIN'T NO THING BUT A CHICKEN..."}
    assert "JUMBO CHICKEN WINGS · 12 WINGS" in chicken_dishes
    assert "BREADED CHICKEN TENDERS · 3 WINGS" in chicken_dishes
    assert "JUMBO CHICKEN WINGS" not in chicken_dishes
    assert "BREADED CHICKEN TENDERS" not in chicken_dishes


def test_signature_sauces_holds_no_chicken_items(items):
    sauces = [item.dish_name for item in items if item.category == "SIGNATURE SAUCES"]
    assert not any("CHICKEN" in name for name in sauces)
    assert not any("TENDERS" in name for name in sauces)

from menu_extractor.geometry import Line, Section, SubGroup
from menu_extractor.parse import MenuBuilder


def test_basic_dish_with_price_and_merged_description(make_section, role_line):
    sec = make_section(
        "BURGERS",
        role_line("name", "ALL", "AMERICAN", "BURGER", price="$17"),
        role_line("desc", "7", "oz.", "steakburger,"),
        role_line("desc", "choice", "of", "cheese"),
    )
    (item,) = MenuBuilder.build([sec])
    assert item.category == "BURGERS"
    assert item.dish_name == "ALL AMERICAN BURGER"
    assert item.price == 17.0
    assert item.price_text == "$17"
    assert item.description == "7 oz. steakburger, choice of cheese"
    assert item.dish_id == "001"


def test_section_note_before_first_dish_is_skipped(make_section, role_line):
    sec = make_section(
        "SLIDER TOWERS",
        role_line("desc", "served", "with", "sidewinder", "fries"),  # section note
        role_line("name", "HOT", "DOG", "TOWER", price="$18"),
        role_line("desc", "four", "mini", "hotdogs"),
    )
    (item,) = MenuBuilder.build([sec])
    assert item.dish_name == "HOT DOG TOWER"
    assert item.description == "four mini hotdogs"


def test_placeholder_and_missing_prices(make_section, role_line):
    flight_sec = make_section("FLIGHTS", role_line("name", "4", "WINGS", "&", "4", "SAUCES", price="$X"))
    sauce_sec = make_section("SIGNATURE SAUCES", role_line("item", "GARLIC", "PARMESAN"))
    flight, sauce = MenuBuilder.build([flight_sec, sauce_sec])
    assert (flight.price, flight.price_text) == (None, "$X")
    assert (sauce.price, sauce.price_text) == (None, None)
    assert sauce.category == "SIGNATURE SAUCES"


def test_dish_ids_are_sequential_and_zero_padded(make_section, role_line):
    sec = make_section(
        "SIDES",
        role_line("name", "COLESLAW", price="$4"),
        role_line("name", "ONION", "PETALS", price="$8"),
    )
    items = MenuBuilder.build([sec])
    assert [i.dish_id for i in items] == ["001", "002"]


def test_sub_header_is_folded_into_dish_name(role_line):
    sec = Section(
        header="AIN'T NO THING BUT A CHICKEN...",
        sub_groups=[
            SubGroup(
                sub_header="JUMBO CHICKEN WINGS",
                lines=[
                    role_line("name", "6", "WINGS", price="$12"),
                    role_line("name", "12", "WINGS", price="$19"),
                ],
            )
        ],
    )
    items = MenuBuilder.build([sec])
    assert [i.dish_name for i in items] == ["JUMBO CHICKEN WINGS · 6 WINGS", "JUMBO CHICKEN WINGS · 12 WINGS"]
    assert [i.price for i in items] == [12.0, 19.0]


def test_empty_sub_group_yields_no_items():
    sec = Section(header="EMPTY", sub_groups=[SubGroup(lines=[])])
    assert MenuBuilder.build([sec]) == []


def test_empty_line_is_skipped():
    assert MenuBuilder.build([Section(header="X", sub_groups=[SubGroup(lines=[Line(words=[])])])]) == []

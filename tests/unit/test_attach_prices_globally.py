from menu_extractor.geometry import Section, SubGroup
from menu_extractor.layout import _attach_prices_globally


def test_assigns_price_to_closest_left_line_on_row(role_line, role_word):
    left = role_line("name", "LEFT", x0=10, top=100)
    right = role_line("name", "RIGHT", x0=200, top=100)
    sections = [Section(header="X", sub_groups=[SubGroup(lines=[left]), SubGroup(lines=[right])])]
    _attach_prices_globally(sections, [role_word("$12", "price", x0=120, top=100)], line_tolerance=4.0)
    assert left.price_token == "$12"
    assert right.price_token is None


def test_picks_correct_line_when_two_sub_columns_have_their_own_prices(role_line, role_word, make_section):
    left = role_line("name", "SIDEWINDER FRIES", x0=10, top=100)
    right = role_line("name", "CRISPY BRUSSELS", x0=200, top=100)
    sections = [make_section("X", left, right)]
    prices = [role_word("$8", "price", x0=150, top=100), role_word("$6", "price", x0=300, top=100)]
    _attach_prices_globally(sections, prices, line_tolerance=4.0)
    assert left.price_token == "$8"
    assert right.price_token == "$6"


def test_drops_price_with_no_line_on_row(role_line, role_word, make_section):
    line = role_line("name", "ELSEWHERE", x0=10, top=50)
    sections = [make_section("X", line)]
    _attach_prices_globally(sections, [role_word("$5", "price", x0=100, top=999)], line_tolerance=4.0)
    assert line.price_token is None

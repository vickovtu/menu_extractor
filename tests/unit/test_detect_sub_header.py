from menu_extractor.layout import _detect_sub_header


def test_promotes_first_unpriced_name_followed_by_priced(role_line):
    lines = [
        role_line("name", "JUMBO", "CHICKEN", "WINGS", top=0),  # no price → candidate
        role_line("name", "6", "WINGS", top=10, price="$12"),
        role_line("name", "12", "WINGS", top=20, price="$19"),
    ]
    sub_header, remaining = _detect_sub_header(lines)
    assert sub_header == "JUMBO CHICKEN WINGS"
    assert [line.price_token for line in remaining] == ["$12", "$19"]


def test_skips_when_first_name_has_price(role_line):
    lines = [
        role_line("name", "4", "WINGS", "&", "4", "SAUCES", top=0, price="$X"),
        role_line("name", "8", "WINGS", "&", "8", "SAUCES", top=10, price="$X"),
    ]
    sub_header, remaining = _detect_sub_header(lines)
    assert sub_header is None
    assert remaining is lines


def test_skips_when_subsequent_name_is_unpriced(role_line):
    lines = [
        role_line("name", "BACON", "BOURBON", "GHOST", top=0),
        role_line("name", "VAMPIRE", "SLAYER", top=10),
        role_line("name", "SIGNATURE", "RUBS", top=20),
    ]
    sub_header, remaining = _detect_sub_header(lines)
    assert sub_header is None
    assert remaining is lines


def test_skips_when_only_one_name_line(role_line):
    lines = [role_line("name", "LONELY", "DISH", top=0, price="$10")]
    sub_header, remaining = _detect_sub_header(lines)
    assert sub_header is None
    assert remaining is lines

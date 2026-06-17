from menu_extractor.normalize import clean_text, parse_price


def test_parse_price_numeric():
    assert parse_price("$17") == (17.0, "$17")
    assert parse_price("$ 7") == (7.0, "$7")
    assert parse_price("$12.50") == (12.5, "$12.50")


def test_parse_price_placeholder():
    assert parse_price("$X") == (None, "$X")
    assert parse_price("$x") == (None, "$X")


def test_parse_price_missing():
    assert parse_price("") == (None, None)
    assert parse_price("no price here") == (None, None)


def test_clean_text_collapses_whitespace_and_quotes():
    assert clean_text("  ALL   AMERICAN\nBURGER ") == "ALL AMERICAN BURGER"
    assert clean_text("“ALL IN” SIDEWINDERS") == '"ALL IN" SIDEWINDERS'
    assert clean_text("DOUBLE–FRIED") == "DOUBLE-FRIED"

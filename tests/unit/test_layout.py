from menu_extractor.layout import (
    _gather_header_lines,
    _group_words_into_lines,
    _split_at_whitespace_gutter,
    _split_at_x,
    _split_into_columns,
    compute_thresholds,
)


def test_compute_thresholds_scales_with_median_font_size(make_word):
    t = compute_thresholds([make_word(str(i), x0=0, x1=1, size=10.0) for i in range(5)])
    assert t.min_vertical_gutter == 18.0
    assert t.min_horizontal_gutter == 9.0
    assert t.line_tolerance == 4.0


def test_compute_thresholds_falls_back_for_empty_input():
    t = compute_thresholds([])
    assert (t.min_vertical_gutter, t.min_horizontal_gutter, t.line_tolerance) == (18.0, 9.0, 4.0)


def test_split_at_x_partitions_words_by_centre(make_word):
    words = [make_word("L", x0=0, x1=10), make_word("R", x0=50, x1=60)]
    strips = _split_at_x(words, [30.0])
    assert [w.text for w in strips[0]] == ["L"]
    assert [w.text for w in strips[1]] == ["R"]


def test_split_at_whitespace_gutter_finds_two_columns(make_word):
    t = compute_thresholds([make_word("x", x0=0, x1=1, size=10.0)])
    words = [
        make_word("L1", x0=0, x1=10),
        make_word("L2", x0=0, x1=10, top=20),
        make_word("R1", x0=100, x1=110),
        make_word("R2", x0=100, x1=110, top=20),
    ]
    assert len(_split_at_whitespace_gutter(words, t)) == 2


def test_split_at_whitespace_gutter_keeps_one_strip_when_no_gap(make_word):
    t = compute_thresholds([make_word("x", x0=0, x1=1, size=10.0)])
    words = [make_word("a", x0=0, x1=10), make_word("b", x0=12, x1=22), make_word("c", x0=24, x1=34)]
    assert len(_split_at_whitespace_gutter(words, t)) == 1


def test_split_at_whitespace_gutter_single_word(make_word):
    t = compute_thresholds([make_word("x", x0=0, x1=1, size=10.0)])
    only = [make_word("only", x0=0, x1=10)]
    assert _split_at_whitespace_gutter(only, t) == [only]


def test_group_words_into_lines_groups_by_baseline(make_word):
    words = [
        make_word("a", x0=0, x1=5, top=0.0),
        make_word("b", x0=10, x1=15, top=0.5),  # within tolerance → same line
        make_word("c", x0=0, x1=5, top=20.0),  # new line
    ]
    lines = _group_words_into_lines(words, line_tolerance=4.0)
    assert len(lines) == 2
    assert [w.text for w in lines[0].words] == ["a", "b"]
    assert [w.text for w in lines[1].words] == ["c"]


def test_split_into_columns_returns_single_column_when_no_dividers(make_word):
    words = [make_word("a", x0=0, x1=10), make_word("b", x0=100, x1=110)]
    columns = _split_into_columns(words, vlines=[], page_height=1000.0)
    assert len(columns) == 1
    assert {w.text for w in columns[0]} == {"a", "b"}


def test_gather_header_lines_returns_empty_when_no_headers(make_word):
    words = [make_word("a", x0=0, x1=10), make_word("b", x0=0, x1=10, top=20)]
    assert _gather_header_lines(words, line_tolerance=4.0) == []

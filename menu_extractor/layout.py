import statistics
from itertools import pairwise

import pdfplumber

from menu_extractor.classify import Role, word_role
from menu_extractor.geometry import Line, Section, SubGroup, Thresholds, Word
from menu_extractor.normalize import clean_text

# Multipliers applied to the median word font-size on the page to derive layout
# thresholds. Reverse-engineered for typography where body is ~10pt:
#   - 1.8 * body type for column gutters (wider than any inter-word space)
#   - 0.9 * body type for block separators between stacked groups
#   - 0.4 * body type for baseline jitter inside a single line
VERTICAL_GUTTER_MULT = 1.8
HORIZONTAL_GUTTER_MULT = 0.9
LINE_TOLERANCE_MULT = 0.4

# Fallback used only when a page is empty (no words to take a median over).
DEFAULT_MEDIAN_SIZE = 10.0

# A vertical line counts as a "page-level" column divider when it spans this much
# of its column's height (otherwise it's an intra-section sub-column divider).
PAGE_DIVIDER_HEIGHT_RATIO = 0.6

# Lines whose endpoints are within this many points of each other count as
# axis-aligned (vertical or horizontal). Absorbs minor PDF jitter.
LINE_AXIS_TOLERANCE = 0.5


def parse_page_layout(page: pdfplumber.page.Page) -> list[Section]:
    """Page → ordered Sections.

    Top-down: page splits at full-height vlines into columns, each column splits
    at HEADER-font lines into sections, each section splits at intra-section
    vlines (or the widest whitespace gutter) into sub-groups, then prices are
    re-attached and sub-headers detected. Sections with no dishes are dropped.
    """
    words = _extract_words(page)
    if not words:
        return []
    thresholds = compute_thresholds(words)
    page_lines = page.lines or []
    vlines = [line for line in page_lines if abs(line["x0"] - line["x1"]) < LINE_AXIS_TOLERANCE]

    # Separate prices from layout content so a price sitting in the gutter
    # between sub-columns doesn't get filed into the wrong strip during the
    # geometric split. Re-attach prices once all lines exist.
    content_words = [word for word in words if word_role(word) is not Role.PRICE]
    price_words = [word for word in words if word_role(word) is Role.PRICE]

    columns = _split_into_columns(content_words, vlines, page.height)
    sections: list[Section] = []
    for col_words in columns:
        sections.extend(_sections_in_column(col_words, vlines, thresholds))
    _attach_prices_globally(sections, price_words, thresholds.line_tolerance)
    _detect_sub_headers_in_sections(sections)
    return sections


def compute_thresholds(words: list[Word]) -> Thresholds:
    median_size = statistics.median(word.size for word in words) if words else DEFAULT_MEDIAN_SIZE
    return Thresholds(
        min_vertical_gutter=median_size * VERTICAL_GUTTER_MULT,
        min_horizontal_gutter=median_size * HORIZONTAL_GUTTER_MULT,
        line_tolerance=median_size * LINE_TOLERANCE_MULT,
    )


def _extract_words(page: pdfplumber.page.Page) -> list[Word]:
    raw_words = page.extract_words(extra_attrs=["size", "fontname"], use_text_flow=False)
    return [
        Word(
            text=raw_word["text"],
            x0=float(raw_word["x0"]),
            x1=float(raw_word["x1"]),
            top=float(raw_word["top"]),
            bottom=float(raw_word["bottom"]),
            size=float(raw_word.get("size", 0.0)),
            fontname=str(raw_word.get("fontname", "")),
        )
        for raw_word in raw_words
    ]


def _split_into_columns(words: list[Word], vlines: list[dict], page_height: float) -> list[list[Word]]:
    page_dividers = sorted(
        line["x0"] for line in vlines if (line["bottom"] - line["top"]) >= page_height * PAGE_DIVIDER_HEIGHT_RATIO
    )
    if not page_dividers:
        return [_drop_words(words)]

    boundaries = [-float("inf"), *page_dividers, float("inf")]
    columns: list[list[Word]] = []
    for left, right in pairwise(boundaries):
        column_words = [word for word in words if left <= word.cx < right]
        if column_words:
            columns.append(_drop_words(column_words))
    return columns


def _drop_words(words: list[Word]) -> list[Word]:
    return [word for word in words if word_role(word) is not Role.DROP]


def _sections_in_column(col_words: list[Word], all_vlines: list[dict], thresholds: Thresholds) -> list[Section]:
    header_lines = _gather_header_lines(col_words, thresholds.line_tolerance)
    if not header_lines:
        return []

    col_left = min(word.x0 for word in col_words)
    col_right = max(word.x1 for word in col_words)
    sections: list[Section] = []
    for index, (top, _x0, text, words_in_header) in enumerate(header_lines):
        next_top = header_lines[index + 1][0] if index + 1 < len(header_lines) else float("inf")
        header_set = set(words_in_header)
        body = [word for word in col_words if top < word.top < next_top and word not in header_set]
        sub_groups = _build_sub_groups(body, all_vlines, top, next_top, col_left, col_right, thresholds)
        if sub_groups and any(sub_group.lines for sub_group in sub_groups):
            sections.append(Section(header=clean_text(text), sub_groups=sub_groups))
    return sections


def _gather_header_lines(words: list[Word], line_tolerance: float) -> list[tuple[float, float, str, tuple[Word, ...]]]:
    headers = [word for word in words if word_role(word) is Role.HEADER]
    if not headers:
        return []
    headers.sort(key=lambda word: (word.top, word.x0))
    rows: list[list[Word]] = []
    for word in headers:
        if rows and abs(word.top - rows[-1][0].top) <= line_tolerance:
            rows[-1].append(word)
        else:
            rows.append([word])
    result = []
    for row in rows:
        row.sort(key=lambda word: word.x0)
        text = " ".join(word.text for word in row)
        result.append((row[0].top, row[0].x0, text, tuple(row)))
    return result


def _build_sub_groups(
    body: list[Word],
    all_vlines: list[dict],
    section_top: float,
    section_bottom: float,
    col_left: float,
    col_right: float,
    thresholds: Thresholds,
) -> list[SubGroup]:
    if not body:
        return []
    # Prefer explicit vertical lines inside the section's y-range *and* the
    # column's x-range (a vline from the neighbouring column would otherwise
    # leak across and silently collapse this section into one strip).
    sub_dividers = sorted(
        line["x0"]
        for line in all_vlines
        if line["top"] >= section_top - thresholds.line_tolerance
        and line["bottom"] <= section_bottom + thresholds.line_tolerance
        and abs(line["x0"] - line["x1"]) < LINE_AXIS_TOLERANCE
        and col_left <= line["x0"] <= col_right
    )

    strips: list[list[Word]] = []
    if sub_dividers:
        strips = _split_at_x(body, sub_dividers)
    # If no vline was usable, or the split didn't produce at least two strips,
    # fall back to whitespace-gutter detection (e.g. SIGNATURE SAUCES / SIDES).
    if len(strips) < 2:
        strips = _split_at_whitespace_gutter(body, thresholds)
    sub_groups: list[SubGroup] = []
    for strip in strips:
        lines = _group_words_into_lines(strip, thresholds.line_tolerance)
        if lines:
            sub_groups.append(SubGroup(lines=lines))
    return sub_groups


def _split_at_x(words: list[Word], dividers: list[float]) -> list[list[Word]]:
    boundaries = [-float("inf"), *dividers, float("inf")]
    strips: list[list[Word]] = []
    for left, right in pairwise(boundaries):
        strip = [word for word in words if left <= word.cx < right]
        if strip:
            strips.append(strip)
    return strips


def _split_at_whitespace_gutter(words: list[Word], thresholds: Thresholds) -> list[list[Word]]:
    """If no explicit divider, split at the widest x-gutter that exceeds the
    column-gutter threshold (whitespace-only fallback for sections like
    SIGNATURE SAUCES where sub-columns aren't drawn as lines)."""
    if len(words) < 2:
        return [words]
    intervals = sorted((word.x0, word.x1) for word in words)
    best_width, best_pos = 0.0, 0.0
    covered_end = intervals[0][1]
    for start, end in intervals[1:]:
        if start > covered_end:
            width = start - covered_end
            if width > best_width:
                best_width, best_pos = width, (covered_end + start) / 2
        covered_end = max(covered_end, end)
    if best_width < thresholds.min_vertical_gutter:
        return [words]
    return _split_at_x(words, [best_pos])


def _group_words_into_lines(words: list[Word], line_tolerance: float) -> list[Line]:
    lines: list[Line] = []
    for word in sorted(words, key=lambda word: (word.top, word.x0)):
        if lines and abs(word.top - lines[-1].words[0].top) <= line_tolerance:
            lines[-1].words.append(word)
        else:
            lines.append(Line(words=[word]))
    for line in lines:
        line.words.sort(key=lambda word: word.x0)
    return lines


def _attach_prices_globally(sections: list[Section], prices: list[Word], line_tolerance: float) -> None:
    """For each price, find the line across the whole page on its row whose
    leftmost word sits closest to (but left of) the price's centre. Done at
    page level — not per sub-group — because a price often sits inside the
    gutter between two sub-columns and would otherwise be filed into the wrong
    strip during geometric splitting."""
    all_lines = [
        line for section in sections for sub_group in section.sub_groups for line in sub_group.lines if line.words
    ]
    for price in prices:
        best: Line | None = None
        best_x0 = -float("inf")
        for line in all_lines:
            if abs(line.top - price.top) <= line_tolerance and line.x0 < price.cx and line.x0 > best_x0:
                best, best_x0 = line, line.x0
        if best is not None:
            best.price_token = f"{best.price_token} {price.text}".strip() if best.price_token else price.text


def _detect_sub_headers_in_sections(sections: list[Section]) -> None:
    """Now that prices are attached, look at each sub-group: if its first NAME
    line is unpriced and the rest carry prices, promote that line to sub_header."""
    for section in sections:
        for sub_group in section.sub_groups:
            sub_header, remaining = _detect_sub_header(sub_group.lines)
            sub_group.sub_header = sub_header
            sub_group.lines = remaining


def _detect_sub_header(lines: list[Line]) -> tuple[str | None, list[Line]]:
    """Promote the first NAME-only line to a sub-header iff it has no price and
    every subsequent NAME line carries one (the JUMBO CHICKEN WINGS pattern)."""
    name_indices = [index for index, line in enumerate(lines) if _is_name_line(line)]
    if len(name_indices) < 2:
        return None, lines
    first_index = name_indices[0]
    first_line = lines[first_index]
    if first_line.price_token is not None:
        return None, lines
    if not all(lines[index].price_token is not None for index in name_indices[1:]):
        return None, lines
    sub_header_text = clean_text(
        " ".join(word.text for word in first_line.words if word_role(word) in (Role.NAME, Role.ITEM))
    )
    remaining = [line for index, line in enumerate(lines) if index != first_index]
    return sub_header_text, remaining


def _is_name_line(line: Line) -> bool:
    return any(word_role(word) in (Role.NAME, Role.ITEM) for word in line.words)

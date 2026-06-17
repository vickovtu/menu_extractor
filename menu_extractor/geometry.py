from dataclasses import dataclass


@dataclass(frozen=True)
class Word:
    text: str
    x0: float
    x1: float
    top: float
    bottom: float
    size: float
    fontname: str

    @property
    def cx(self) -> float:
        return (self.x0 + self.x1) / 2


@dataclass
class Line:
    words: list[Word]
    price_token: str | None = None

    @property
    def top(self) -> float:
        return min(word.top for word in self.words)

    @property
    def x0(self) -> float:
        return min(word.x0 for word in self.words)


@dataclass(frozen=True)
class Thresholds:
    min_vertical_gutter: float
    min_horizontal_gutter: float
    line_tolerance: float


@dataclass
class SubGroup:
    """One vertical strip inside a section. `sub_header` is set when the strip
    starts with an unpriced NAME followed by priced NAMEs (e.g. JUMBO CHICKEN
    WINGS over its tiers) — it gets folded into each dish_name."""

    lines: list[Line]
    sub_header: str | None = None


@dataclass
class Section:
    header: str
    sub_groups: list[SubGroup]

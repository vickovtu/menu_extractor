from itertools import count

from menu_extractor.classify import Role, word_role
from menu_extractor.geometry import Line, Section
from menu_extractor.models import DraftItem, MenuItem
from menu_extractor.normalize import clean_text, parse_price


class MenuBuilder:
    """Assembles MenuItems from the hierarchical layout output. Category and
    sub-header come from the layout (Section / SubGroup); the builder only
    walks dish lines and merges multi-line descriptions."""

    @classmethod
    def build(cls, sections: list[Section]) -> list[MenuItem]:
        builder = cls()
        for section in sections:
            builder.feed_section(section)
        return builder.finish()

    def __init__(self) -> None:
        self.items: list[MenuItem] = []
        self._dish_ids = count(1)
        self._current: DraftItem | None = None
        self._category: str | None = None
        self._sub_header: str | None = None
        self._seen_name_in_subgroup = False

    def feed_section(self, section: Section) -> None:
        self._category = section.header
        for sub_group in section.sub_groups:
            self._sub_header = sub_group.sub_header
            self._seen_name_in_subgroup = False
            for line in sub_group.lines:
                self._feed_line(line)
            self._flush()

    def finish(self) -> list[MenuItem]:
        self._flush()
        return self.items

    def _feed_line(self, line: Line) -> None:
        roles = {word_role(word) for word in line.words}
        if not roles:
            return

        if roles & {Role.NAME, Role.ITEM}:
            name = _text_for_roles(line, Role.NAME, Role.ITEM)
            if self._sub_header:
                name = f"{self._sub_header} · {name}"
            self._start_item(name, line.price_token)
            return

        # Body text before any dish in a sub-group is a section note
        # (e.g. "served with choice of side"), not a dish description.
        if Role.DESC in roles and self._current is not None and self._seen_name_in_subgroup:
            self._current.description.append(_text_for_roles(line, Role.DESC))

    def _start_item(self, name: str, price_token: str | None) -> None:
        self._flush()
        amount, raw = parse_price(price_token or "")
        self._current = DraftItem(
            category=self._category or "UNCATEGORIZED",
            dish_name=name,
            price=amount,
            price_text=raw,
        )
        self._seen_name_in_subgroup = True

    def _flush(self) -> None:
        if self._current is None:
            return
        self.items.append(
            MenuItem(
                category=self._current.category,
                dish_name=self._current.dish_name,
                price=self._current.price,
                price_text=self._current.price_text,
                description=" ".join(self._current.description) or None,
                dish_id=f"{next(self._dish_ids):03d}",
            )
        )
        self._current = None


def _text_for_roles(line: Line, *roles: Role) -> str:
    tokens = [word.text for word in line.words if word_role(word) in roles]
    return clean_text(" ".join(tokens))

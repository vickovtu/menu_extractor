from dataclasses import dataclass, field

from pydantic import BaseModel, ConfigDict, field_validator


class MenuItem(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    category: str
    dish_name: str
    price: float | None = None
    price_text: str | None = None
    description: str | None = None
    dish_id: str

    @field_validator("description")
    @classmethod
    def empty_description_is_none(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None


@dataclass
class DraftItem:
    category: str
    dish_name: str
    price: float | None
    price_text: str | None
    description: list[str] = field(default_factory=list)

from pathlib import Path

import pdfplumber

from menu_extractor.exceptions import MenuExtractionError
from menu_extractor.geometry import Section
from menu_extractor.layout import parse_page_layout
from menu_extractor.models import MenuItem
from menu_extractor.parse import MenuBuilder


def extract_menu(pdf_path: str | Path) -> list[MenuItem]:
    path = Path(pdf_path)
    sections: list[Section] = []
    try:
        with pdfplumber.open(str(path)) as pdf:
            for page in pdf.pages:
                sections.extend(parse_page_layout(page))
    except (FileNotFoundError, PermissionError) as exc:
        raise MenuExtractionError(f"Cannot read PDF {path}: {exc}") from exc
    except Exception as exc:
        raise MenuExtractionError(f"Failed to parse PDF {path}: {exc}") from exc
    return MenuBuilder.build(sections)

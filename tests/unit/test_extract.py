from pathlib import Path

import pytest

from menu_extractor.exceptions import MenuExtractionError
from menu_extractor.extract import extract_menu


def test_missing_pdf_raises_menu_extraction_error(tmp_path: Path):
    with pytest.raises(MenuExtractionError, match="Cannot read PDF"):
        extract_menu(tmp_path / "does-not-exist.pdf")


def test_non_pdf_input_raises_menu_extraction_error(tmp_path: Path):
    fake = tmp_path / "fake.pdf"
    fake.write_text("This is not a PDF", encoding="utf-8")
    with pytest.raises(MenuExtractionError, match="Failed to parse PDF"):
        extract_menu(fake)

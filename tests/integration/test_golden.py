import json
from pathlib import Path

import pytest

from menu_extractor.extract import extract_menu

ROOT = Path(__file__).resolve().parents[2]
PDF = ROOT / "data" / "espn_bet.pdf"
GOLDEN = ROOT / "tests" / "fixtures" / "menu.golden.json"


@pytest.fixture(scope="module")
def golden() -> list[dict]:
    return json.loads(GOLDEN.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def extracted() -> list[dict]:
    if not PDF.is_file():
        pytest.skip(f"sample PDF not present: {PDF}")
    return [item.model_dump() for item in extract_menu(PDF)]


def test_item_count_matches_golden(extracted, golden):
    assert len(extracted) == len(golden)


def test_full_payload_matches_golden(extracted, golden):
    # On failure, inspect the diff and either fix the regression or regenerate
    # with `make update-golden` when the change is expected.
    assert extracted == golden

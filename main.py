import argparse
import json
import logging
import sys
from collections import Counter
from pathlib import Path

from menu_extractor.exceptions import MenuExtractionError
from menu_extractor.extract import extract_menu

logger = logging.getLogger(__name__)


def main(argv: list[str] | None = None) -> int:
    # Bare format keeps human-facing CLI output clean — no timestamps or level prefixes.
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    parser = argparse.ArgumentParser(description="Extract menu dishes from a PDF into JSON.")
    parser.add_argument("pdf", type=Path, help="Path to the menu PDF")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("output/menu.json"),
        help="Where to write the JSON (default: output/menu.json)",
    )
    args = parser.parse_args(argv)

    if not args.pdf.is_file():
        parser.error(f"PDF not found: {args.pdf}")

    try:
        items = extract_menu(args.pdf)
    except MenuExtractionError as exc:
        parser.error(str(exc))
    payload = [item.model_dump() for item in items]

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    by_category = Counter(item.category for item in items)
    logger.info("Extracted %d items across %d sections -> %s", len(items), len(by_category), args.output)
    for category, count in by_category.items():
        logger.info("  %3d  %s", count, category)
    return 0


if __name__ == "__main__":
    sys.exit(main())

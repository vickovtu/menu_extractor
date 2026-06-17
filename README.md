# menu-extractor

Extracts dishes from a two-column restaurant-menu PDF and emits normalized JSON.

```json
{
  "category": "BURGERS",
  "dish_name": "ALL AMERICAN BURGER",
  "price": 17.0,
  "price_text": "$17",
  "description": "7 oz. steakburger, choice of cheese, lettuce, tomato, onion, pickles, brioche bun",
  "dish_id": "041"
}
```

## Why

A naive `pdfplumber.extract_text()` reads the page across both columns and interleaves them. This extractor reads the page **structurally** — using the PDF's own vector lines as column/section dividers and the embedded font stack to classify each word's role — so the output preserves the visual hierarchy of the menu.

Key properties:

- **Pure deterministic Python** — no OCR, no LLM, no external API. Reproducible byte-for-byte across runs.
- **Honest price model** — `price` (numeric) and `price_text` (raw token) are separate fields, so a `$X` placeholder is distinguishable from an unpriced item:

  | Case                     | `price` | `price_text` |
  |--------------------------|---------|--------------|
  | Normal price (`$17`)     | `17.0`  | `"$17"`      |
  | Placeholder (`$X`)       | `null`  | `"$X"`       |
  | No price (e.g. a sauce)  | `null`  | `null`       |

- **Sub-header folding** — parent labels like *JUMBO CHICKEN WINGS* above tier rows (`6 / 12 / 18 WINGS`) get folded into each tier's `dish_name` as `"JUMBO CHICKEN WINGS · 12 WINGS"`.
- **Test-first** — unit + integration + a golden-fixture deep-equality test, with a 95% coverage gate.

## Getting started

Requires Python 3.12+ and [uv](https://docs.astral.sh/uv/).

```bash
make install                                       # uv sync --extra dev
make run                                           # writes output/menu.json
# or directly:
uv run python main.py data/espn_bet.pdf -o output/menu.json
```

Output goes to `output/menu.json` by default. Override with `-o`.

### Make targets

| Target              | What it does                                       |
|---------------------|----------------------------------------------------|
| `make install`      | Install runtime + dev deps via `uv sync`           |
| `make run`          | Extract from `data/espn_bet.pdf` to `output/menu.json` |
| `make test`         | Run all tests (unit + integration)                 |
| `make test-unit`    | Run unit tests only (fast, no PDF needed)          |
| `make test-integration` | Run integration tests only                     |
| `make coverage`     | Run tests with coverage, fail under 95%            |
| `make lint`         | Ruff lint                                          |
| `make fix`          | Ruff lint --fix + format                           |
| `make check`        | Lint + format-check (CI gate)                      |
| `make update-golden`| Regenerate `tests/fixtures/menu.golden.json`       |
| `make clean`        | Remove caches and coverage artefacts               |

## How it works

The menu is a **digital PDF with a real text layer** (no OCR needed). Reading it correctly is two problems:

1. **Words, not text.** Each word is read with its coordinates and font via `pdfplumber`. The font name encodes the role unambiguously — casing alone fails because section headers *and* sauce names are upper-case:
   - `IsidoraSans-Black` → section header
   - `IsidoraSans-Bold` → dish name
   - `BETRegular` → price token
   - `IsidoraSans-Medium` → body text (size ~10 = standalone item like a sauce; size ~8 = description)

2. **Line-driven hierarchical layout.** The PDF embeds a structural skeleton — a page-spanning vertical line, paired horizontal lines around section headers, and shorter vertical lines inside sub-columned blocks. The parser walks it top-down:

   **page → main columns (vlines) → sections (HEADER lines) → sub-groups (intra-section vlines, or whitespace gutter as fallback) → dish lines**

3. **Sub-header folding.** Inside a sub-group, if the first NAME-font line has no price but every subsequent one carries one, the unpriced label is treated as a sub-header and folded into each tier's `dish_name`.

4. **Global price re-attachment.** Right-aligned prices often sit in the gutter between sub-columns. Each price is matched against every line on the page after the layout is built — closest line on the same row, starting left of the price wins.

5. **Assembly.** A state machine walks each section's dish lines, merging multi-line descriptions and skipping section notes (e.g. *"served with choice of side"*) that appear before the first dish.

## Project structure

```
menu-extractor/
├── main.py                          # CLI entry-point
├── menu_extractor/
│   ├── geometry.py                  # Word / Line / Section / SubGroup / Thresholds
│   ├── classify.py                  # font signature → Role
│   ├── normalize.py                 # NFKC, smart-quote cleanup, price parsing
│   ├── models.py                    # MenuItem (pydantic) + DraftItem
│   ├── layout.py                    # PDF page → ordered list[Section]
│   ├── parse.py                     # MenuBuilder: Section → MenuItem
│   └── extract.py                   # PDF → list[MenuItem]
├── tests/
│   ├── conftest.py                  # shared pytest fixtures + auto-tagging
│   ├── unit/                        # pure-function tests
│   ├── integration/                 # end-to-end + golden comparison
│   └── fixtures/menu.golden.json
├── data/espn_bet.pdf                # sample input
├── output/menu.json                 # generated
├── pyproject.toml
└── Makefile
```

## Scope and limitations

The role-classification rules are **tuned to this PDF's font stack** (`IsidoraSans-*` / `BETRegular`, 14pt / 16pt headers, paired-line section brackets). The layout helpers scale with the page's median word font-size, so segmentation would adapt to other typography, but `menu_extractor/classify.py` would need re-tuning to recognise the right fonts for a different menu.

## See also

- [`AI_USAGE.md`](AI_USAGE.md) — reflection on AI tool usage during development, assumptions, and known gaps (as required by the task brief).
- [`tests/fixtures/menu.golden.json`](tests/fixtures/menu.golden.json) — the byte-for-byte expected output for the sample PDF.

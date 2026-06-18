# menu-extractor

A small script that reads a two-column restaurant-menu PDF and writes out one
normalized JSON record per dish.

```json
{
  "category": "LEADING OFF",
  "dish_name": "JUMBO GERMAN PRETZEL",
  "price": 16.0,
  "price_text": "$16",
  "description": "caramelized onion dip, queso blanco, house-made honey mustard",
  "dish_id": "001"
}
```

On the sample PDF (`data/espn_bet.pdf`) it produces 105 items across 17 sections.

## What the assignment asked for, and where it's handled

| Requirement | Where / how |
|---|---|
| Extract dishes from the target sections (`LEADING OFF`, `BURGERS`, …) | Sections come from the PDF's header-font lines — see `layout.py` |
| Merge multi-line descriptions | `MenuBuilder` in `parse.py` walks dish lines and appends following body lines |
| Handle missing prices and `$X` placeholders | `price` / `price_text` split in `normalize.py` — see [Prices](#prices) |
| Normalize fields (whitespace, smart quotes, format) | `clean_text` in `normalize.py` (NFKC + quote folding + whitespace collapse) |
| Python 3.12+, reproducible | Pure-Python, deterministic; `make install` / `make run` below |
| Output JSON file | Written to `output/menu.json` (override with `-o`) |

## How to run

Requires Python 3.12+ and [uv](https://docs.astral.sh/uv/).

```bash
make install                                       # uv sync --extra dev
make run                                            # writes output/menu.json
# or directly:
uv run python main.py data/espn_bet.pdf -o output/menu.json
```

Other useful targets: `make test` (all tests), `make check` (lint + format check),
`make coverage` (tests with a 95% gate), `make update-golden` (regenerate the fixture).

## How it works

The PDF has a real text layer, so there's no OCR. The hard part is that
`pdfplumber.extract_text()` reads straight across both columns and interleaves
them, so I read the page structurally instead.

1. **Words, not text.** Each word is read with its coordinates and font name.
   The font tells us a word's role more reliably than casing does — section
   headers *and* sauce names are both upper-case, so casing alone can't tell
   them apart:
   - `IsidoraSans-Black` → section header
   - `IsidoraSans-Bold` → dish name
   - `BETRegular` → price token
   - `IsidoraSans-Medium` → body (≈10pt is a standalone item like a sauce, ≈8pt is a description)

2. **Layout from the page's own lines.** The PDF draws a page-spanning vertical
   rule between the two columns, and shorter vertical rules inside multi-column
   blocks. The parser walks them top-down:

   `page → columns (full-height vlines) → sections (header lines) → sub-groups (intra-section vlines, or the widest whitespace gutter as a fallback) → dish lines`

3. **Sub-header folding.** When a sub-group starts with an unpriced label and
   every line after it is priced — e.g. `JUMBO CHICKEN WINGS` over its `6 / 12 / 18`
   tiers — the label is folded into each dish name as `JUMBO CHICKEN WINGS · 12 WINGS`.

4. **Price re-attachment.** Right-aligned prices often sit in the gutter between
   sub-columns, so I match each price to the nearest line on its row across the
   whole page, rather than per sub-group.

5. **Assembly.** `MenuBuilder` walks each section's lines, merging multi-line
   descriptions and skipping section notes (e.g. "served with choice of side")
   that appear before the first dish.

## Prices

`price` (numeric) and `price_text` (the raw token) are separate fields so the
three cases stay distinguishable:

| Case | `price` | `price_text` | Example |
|---|---|---|---|
| Normal price | `16.0` | `"$16"` | `JUMBO GERMAN PRETZEL` |
| Placeholder | `null` | `"$X"` | `4 WINGS & 4 SAUCES` |
| No price | `null` | `null` | a sauce like `GARLIC PARMESAN` |

## Project structure

```
menu-extractor/
├── main.py                          # CLI entry-point
├── menu_extractor/
│   ├── geometry.py                  # Word / Line / Section / SubGroup / SectionBounds / Thresholds
│   ├── classify.py                  # font signature → Role
│   ├── normalize.py                 # NFKC, quote cleanup, price parsing
│   ├── models.py                    # MenuItem (pydantic) + DraftItem
│   ├── layout.py                    # PDF page → ordered list[Section]
│   ├── parse.py                     # MenuBuilder: Section → MenuItem
│   └── extract.py                   # PDF → list[MenuItem]
├── tests/
│   ├── unit/                        # pure-function tests
│   ├── integration/                 # end-to-end + golden comparison
│   └── fixtures/menu.golden.json
├── data/espn_bet.pdf                # sample input
└── output/menu.json                 # generated
```

## Limitations

The role classification is tuned to this PDF's font stack (`IsidoraSans-*` /
`BETRegular`, 14–16pt headers, paired-line section brackets). The layout
helpers scale with the page's median word size, so the *segmentation* would
adapt to other typography, but `classify.py` would need re-tuning to recognise
the right fonts for a different menu. `dish_id` is a sequential counter over the
output, not an identifier carried in the PDF.

## AI usage

- **Tool.** I used AI as a coding agent to draft implementation and test code
  while I selected the approach, tuned the heuristics, reviewed the output, and
  verified behavior with tests.
- **Division of labour.** I decided the module layout (geometry / classify /
  normalize / layout / parse), the font-based classification approach, and the
  `price` vs `price_text` model; the agent filled in the code and I corrected
  naming, thresholds, and structure as it went.
- **What I tuned by hand.** The layout thresholds (column-gutter and
  line-tolerance multipliers) and the font signatures in `classify.py` are
  specific to this PDF — I checked them against the actual output rather than
  trusting generated defaults.
- **Verification.** A golden-fixture test pins the full 105-item output, so any
  change that altered extraction would fail the build. I ran a final
  AI-assisted review over the code for readability and dead code.
- **Known gaps.** See [Limitations](#limitations) — `classify.py` is
  font-specific and would need re-tuning for a differently-typeset menu.
- **Note on "no LLM."** The extractor itself uses no LLM or external API at
  runtime — it's deterministic and reproducible. The AI usage above is about how
  I *built* it, not what it does when you run it.


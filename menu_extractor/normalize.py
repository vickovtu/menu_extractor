import re
import unicodedata

REPLACEMENTS = {
    "“": '"',
    "”": '"',
    "‘": "'",
    "’": "'",
    "–": "-",
    "—": "-",
    "…": "...",
    " ": " ",
}

PRICE_RE = re.compile(r"\$\s*(\d+(?:\.\d{1,2})?)")
PLACEHOLDER_RE = re.compile(r"\$\s*[xX]\b")


def clean_text(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)
    for source, replacement in REPLACEMENTS.items():
        text = text.replace(source, replacement)
    return re.sub(r"\s+", " ", text).strip()


def parse_price(text: str) -> tuple[float | None, str | None]:
    if not text:
        return None, None
    match = PRICE_RE.search(text)
    if match:
        raw_token = match.group(0).replace(" ", "")
        return float(match.group(1)), raw_token
    if PLACEHOLDER_RE.search(text):
        return None, "$X"
    return None, None

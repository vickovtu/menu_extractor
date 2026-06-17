PDF ?= data/espn_bet.pdf
OUT ?= output/menu.json
SOURCES = main.py menu_extractor tests

.PHONY: help install lint format fix check test test-unit test-integration coverage coverage-html run update-golden clean all

help:
	@echo "Targets:"
	@echo "  install   Install runtime + dev dependencies via uv"
	@echo "  lint      Run ruff lint checks"
	@echo "  format    Run ruff formatter"
	@echo "  fix       Run ruff with --fix, then format"
	@echo "  check     lint + format --check (no writes) — CI-style gate"
	@echo "  test      Run all tests"
	@echo "  test-unit         Run unit tests only (fast, no PDF needed)"
	@echo "  test-integration  Run integration tests only (loads $(PDF))"
	@echo "  coverage          Run tests with coverage report (terminal)"
	@echo "  coverage-html     Run tests with coverage and open HTML report"
	@echo "  run       Extract from \$$PDF (default: $(PDF)) to \$$OUT (default: $(OUT))"
	@echo "  update-golden  Re-extract from $(PDF) and overwrite tests/fixtures/menu.golden.json"
	@echo "  clean     Remove caches and build artefacts"
	@echo "  all       lint + test"

install:
	uv sync --extra dev

lint:
	uv run ruff check $(SOURCES)

format:
	uv run ruff format $(SOURCES)

fix:
	uv run ruff check --fix $(SOURCES)
	uv run ruff format $(SOURCES)

check:
	uv run ruff check $(SOURCES)
	uv run ruff format --check $(SOURCES)

test:
	uv run pytest

test-unit:
	uv run pytest tests/unit

test-integration:
	uv run pytest tests/integration

coverage:
	uv run pytest --cov --cov-report=term-missing

coverage-html:
	uv run pytest --cov --cov-report=html
	@echo "HTML report: htmlcov/index.html"

run:
	uv run python main.py $(PDF) -o $(OUT)

update-golden:
	uv run python main.py $(PDF) -o tests/fixtures/menu.golden.json

clean:
	rm -rf .pytest_cache .ruff_cache .coverage htmlcov
	find . -type d -name __pycache__ -prune -exec rm -rf {} +

all: lint test

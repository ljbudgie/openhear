# OpenHear developer convenience targets.
#
# These are thin wrappers around the same commands CI runs, so that a
# contributor can reproduce the CI checks locally with `make ci`.

PYTHON ?= python
PIP ?= pip

.PHONY: help install install-dev lint format test coverage build clean ci

help:
	@echo "Available targets:"
	@echo "  install      Install runtime dependencies + the package (editable)."
	@echo "  install-dev  Install dev dependencies (ruff, pytest, build, ...)."
	@echo "  lint         Run ruff check and ruff format --check."
	@echo "  format       Run ruff format and ruff check --fix."
	@echo "  test         Run the unit-test suite."
	@echo "  coverage     Run tests with coverage reporting."
	@echo "  build        Build sdist + wheel into ./dist."
	@echo "  clean        Remove build/test artefacts."
	@echo "  ci           Run lint + tests (what CI runs)."

install:
	$(PIP) install -e .

install-dev:
	$(PIP) install -e ".[dev]"
	$(PIP) install ruff pytest-cov build pre-commit

lint:
	ruff check .
	ruff format --check .

format:
	ruff format .
	ruff check --fix .

test:
	pytest -q

coverage:
	pytest -q --cov --cov-report=term --cov-report=xml

build:
	$(PYTHON) -m build

clean:
	rm -rf build dist *.egg-info .pytest_cache .ruff_cache .mypy_cache htmlcov coverage.xml .coverage

ci: lint test

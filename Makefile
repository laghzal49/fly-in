.PHONY: install run debug clean lint lint-strict lint-deps help

DEFAULT_MAP := maps/challenger/01_the_impossible_dream.txt
MAP ?= $(if $(map),$(map),$(DEFAULT_MAP))
PYTHON ?= .venv/bin/python
PIP ?= .venv/bin/pip

help:
	@echo "Fly-in: Drone Routing System"
	@echo "Available targets:"
	@echo "  install        - Create venv and install dependencies"
	@echo "  run [map=FILE] - Run simulation"
	@echo "  debug [map=FILE] - Run in debug mode with pdb"
	@echo "  clean          - Remove temporary files and caches"
	@echo "  lint           - Run flake8 and mypy checks"
	@echo "  lint-strict    - Run strict mypy checks"
	@echo "  help           - Show this help message"
	@echo ""
	@echo "Examples:"
	@echo "  make run"
	@echo "  make run map=maps/easy/02_simple_fork.txt"
	@echo "  make debug map=maps/medium/01_dead_end_trap.txt"

install:
	python3 -m venv .venv
	$(PIP) install --upgrade pip


run:
	$(PYTHON) main.py $(MAP)

debug:
	$(PYTHON) -m pdb main.py $(MAP)

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*~" -delete

lint-deps:
	$(PIP) install flake8 mypy

lint: lint-deps
	$(PYTHON) -m flake8 .
	$(PYTHON) -m mypy . --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs

lint-strict: lint-deps
	$(PYTHON) -m flake8 .
	$(PYTHON) -m mypy . --strict

.PHONY: install run debug clean lint lint-strict help

MAP ?= maps/challenger/01_the_impossible_dream.txt

help:
	@echo "Fly-in: Drone Routing System"
	@echo "Available targets:"
	@echo "  install        - Install project dependencies"
	@echo "  run [map=FILE] - Run simulation (default: maps/easy/01_linear_path.txt)"
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
	pip install --upgrade pip
	pip install webcolors

run:
	python3 main.py $(MAP)

debug:
	python3 -m pdb main.py $(MAP)

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*~" -delete

lint:
	flake8 .
	mypy . --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs

lint-strict:
	flake8 .
	mypy . --strict

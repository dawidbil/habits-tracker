.DEFAULT_GOAL := default
.PHONY: default install lint test upgrade build clean run help

default: install lint test

install:
	uv sync --all-extras --dev

lint:
	uv run python devtools/lint.py

test:
	uv run pytest

upgrade:
	uv sync --upgrade

build:
	uv build

clean:
	-rm -rf dist/ *.egg-info/ .pytest_cache/ .venv/
	-find . -type d -name "__pycache__" -exec rm -rf {} +
	-find . -type d -name ".ruff_cache" -exec rm -rf {} +

run:
	uv run habits

help:
	@echo "Habits Tracker - Makefile targets:"
	@echo "  make install   - Install dependencies with uv"
	@echo "  make lint      - Run code quality checks"
	@echo "  make test      - Run test suite"
	@echo "  make upgrade   - Upgrade dependencies"
	@echo "  make build     - Build distribution package"
	@echo "  make clean     - Clean build artifacts and caches"
	@echo "  make run       - Run the CLI tool"
	@echo "  make help      - Show this help message"

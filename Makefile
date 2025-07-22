SHELL := /bin/bash

.PHONY: help install lint format test build clean

help:
	@echo "Commands:"
	@echo "  install   - Install dependencies"
	@echo "  lint      - Run linters"
	@echo "  format    - Format code"
	@echo "  test      - Run tests"
	@echo "  build     - Build package"
	@echo "  clean     - Clean up build artifacts"

install:
	pip install -e .[dev]

lint:
	ruff check .
	black --check .
	isort --check .
	mypy src/

format:
	ruff --fix .
	black .
	isort .

test:
	pytest --cov=olla_cli --cov-report=term-missing

build:
	python -m build

clean:
	rm -rf dist build .tox .pytest_cache .mypy_cache *.egg-info

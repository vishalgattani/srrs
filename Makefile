# Makefile — local CI simulation for srrs
PYTHON = /Users/vishalgattani/opt/anaconda3/envs/conda_vault/bin/python
PYTEST = $(PYTHON) -m pytest

.PHONY: build install test ci clean

## Build the wheel
build:
	$(PYTHON) -m build --wheel --outdir dist/

## Install wheel + dev deps
install: build
	$(PYTHON) -m pip install dist/srrs-*.whl pytest pytest-cov -q

## Run full test suite with coverage
test:
	$(PYTEST) tests/ -v --tb=short --cov=python --cov-report=term-missing

## Run tests for a single config (usage: make test-config CONFIG=CHO)
test-config:
	$(PYTEST) tests/test_$(CONFIG).py -v --tb=short --cov=python --cov-report=term-missing

## Simulate full CI: build → install → test
ci: build install test

## Remove build artifacts
clean:
	rm -rf dist/ build/ srrs.egg-info/ .coverage htmlcov/ .pytest_cache/

# Makefile for Protein Disorder Classifier API
# Implements Iterative Loss Function Methodology for Code Quality
#
# Usage:
#   make check-all    - Run all quality checks (recommended before commit)
#   make lint         - Run all linters
#   make test         - Run test suite
#   make fix          - Auto-fix formatting issues
#   make help         - Show this help message

.PHONY: help check-all lint test fix clean fix-black fix-isort lint-black lint-isort lint-flake8 lint-pylint lint-mypy lint-bandit install
.DEFAULT_GOAL := help

# Colors for output
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[0;33m
NC := \033[0m # No Color

# Python settings
PYTHON := python3
PIP := pip3
API_DIR := api

help: ## Show this help message
	@echo "${GREEN}Protein Disorder Classifier - Development Commands${NC}"
	@echo ""
	@echo "${YELLOW}Quality Checks (Iterative Loss Function Methodology):${NC}"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  ${GREEN}%-20s${NC} %s\n", $$1, $$2}'
	@echo ""
	@echo "${YELLOW}Methodology: Run check-all before committing to ensure error_count = 0${NC}"

check-all: lint test ## Run ALL quality checks (use before committing)
	@echo "${GREEN}✅ All quality checks passed! Error count: 0${NC}"

lint: lint-black lint-isort lint-flake8 lint-pylint lint-mypy lint-bandit ## Run all linters
	@echo "${GREEN}✅ All linters passed!${NC}"

lint-black: ## Check code formatting with Black
	@echo "${YELLOW}Running Black formatter check...${NC}"
	@black --check --diff . || (echo "${RED}❌ Black formatting failed${NC}" && exit 1)
	@echo "${GREEN}✅ Black check passed${NC}"

lint-isort: ## Check import ordering with isort
	@echo "${YELLOW}Running isort import checker...${NC}"
	@isort --check-only --diff . || (echo "${RED}❌ isort check failed${NC}" && exit 1)
	@echo "${GREEN}✅ isort check passed${NC}"

lint-flake8: ## Check code style with Flake8
	@echo "${YELLOW}Running Flake8 linter...${NC}"
	@flake8 --count --show-source --statistics . || (echo "${RED}❌ Flake8 failed${NC}" && exit 1)
	@echo "${GREEN}✅ Flake8 passed${NC}"

lint-pylint: ## Check code quality with Pylint
	@echo "${YELLOW}Running Pylint...${NC}"
	@if [ -d "$(API_DIR)" ]; then \
		pylint $(API_DIR)/ || (echo "${RED}❌ Pylint failed${NC}" && exit 1); \
	fi
	@find . -maxdepth 1 -name "*.py" -type f | xargs -r pylint || (echo "${RED}❌ Pylint failed${NC}" && exit 1)
	@echo "${GREEN}✅ Pylint passed${NC}"

lint-mypy: ## Check type hints with mypy
	@echo "${YELLOW}Running mypy type checker...${NC}"
	@if [ -d "$(API_DIR)" ]; then \
		mypy $(API_DIR)/ || (echo "${RED}❌ mypy failed${NC}" && exit 1); \
	fi
	@find . -maxdepth 1 -name "*.py" -type f | xargs -r mypy || (echo "${RED}❌ mypy failed${NC}" && exit 1)
	@echo "${GREEN}✅ mypy passed${NC}"

lint-bandit: ## Run security checks with Bandit
	@echo "${YELLOW}Running Bandit security scanner...${NC}"
	@bandit -r . --configfile pyproject.toml || (echo "${RED}❌ Bandit security scan failed${NC}" && exit 1)
	@echo "${GREEN}✅ Bandit security scan passed${NC}"

test: ## Run test suite with coverage
	@echo "${YELLOW}Running test suite...${NC}"
	@pytest tests/ --cov=. --cov-report=xml --cov-report=term --cov-report=html || (echo "${RED}❌ Tests failed${NC}" && exit 1)
	@echo "${GREEN}✅ Tests passed${NC}"

fix: fix-black fix-isort ## Auto-fix formatting issues
	@echo "${GREEN}✅ Auto-fixes applied${NC}"

fix-black: ## Auto-fix code formatting with Black
	@echo "${YELLOW}Running Black formatter (fixing)...${NC}"
	@black .
	@echo "${GREEN}✅ Black formatting applied${NC}"

fix-isort: ## Auto-fix import ordering with isort
	@echo "${YELLOW}Running isort (fixing)...${NC}"
	@isort .
	@echo "${GREEN}✅ isort fixes applied${NC}"

clean: ## Clean up cache and temporary files
	@echo "${YELLOW}Cleaning up...${NC}"
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name '*.pyc' -delete
	@echo "${GREEN}✅ Cleanup complete${NC}"

install: ## Install development dependencies
	@echo "${YELLOW}Installing dependencies...${NC}"
	@$(PIP) install -r requirements.txt
	@echo "${GREEN}✅ Dependencies installed${NC}"

# Makefile for Protein Disorder Classifier API
# Implements Iterative Loss Function Methodology for Code Quality
#
# Usage:
#   make check-all    - Run all quality checks (recommended before commit)
#   make lint         - Run all linters
#   make test         - Run test suite
#   make fix          - Auto-fix formatting issues
#   make help         - Show this help message

.PHONY: help check-all lint test fix clean fix-black fix-isort lint-black lint-isort lint-flake8 lint-pylint lint-mypy lint-bandit lint-markdown install
.DEFAULT_GOAL := help

# Colors for output
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[0;33m
NC := \033[0m # No Color

# Python settings
PYTHON := python3
PIP := pip3
API_DIR := .

help: ## Show this help message
	@echo "${GREEN}Protein Disorder Classifier - Development Commands${NC}"
	@echo ""
	@echo "${YELLOW}Quality Checks (Iterative Loss Function Methodology):${NC}"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  ${GREEN}%-20s${NC} %s\n", $$1, $$2}'
	@echo ""
	@echo "${YELLOW}Methodology: Run check-all before committing to ensure error_count = 0${NC}"

check-all: lint test ## Run ALL quality checks (use before committing)
	@echo "${GREEN}✅ All quality checks passed!${NC}"

lint: lint-black lint-isort lint-flake8 lint-pylint lint-mypy lint-bandit lint-markdown ## Run all linters
	@echo "${GREEN}✅ All linters passed!${NC}"

lint-black: ## Check code formatting with Black
	@echo "${YELLOW}Running Black formatter check...${NC}"
	@black --check --diff . || (echo "${RED}❌ Black formatting failed${NC}" && exit 1)
	@echo "${GREEN}✅ Black check passed${NC}"

lint-isort: ## Check import ordering with isort
	@echo "${YELLOW}Running isort import checker...${NC}"
	@if [ -f "api/.isort.cfg" ]; then \
		isort --settings-file=api/.isort.cfg --check-only --diff . || (echo "${RED}❌ isort check failed${NC}" && exit 1); \
	else \
		isort --check-only --diff . || (echo "${RED}❌ isort check failed${NC}" && exit 1); \
	fi
	@echo "${GREEN}✅ isort check passed${NC}"

lint-flake8: ## Check code style with Flake8
	@echo "${YELLOW}Running Flake8 linter...${NC}"
	@flake8 --count --show-source --statistics . || (echo "${RED}❌ Flake8 failed${NC}" && exit 1)
	@echo "${GREEN}✅ Flake8 passed${NC}"

lint-pylint: ## Check code quality with Pylint
	@echo "${YELLOW}Running Pylint...${NC}"
	@if [ -d "api" ] && [ -f "api/.pylintrc" ]; then \
		pylint --rcfile=api/.pylintrc api/ || (echo "${RED}❌ Pylint failed${NC}" && exit 1); \
	else \
		pylint $(API_DIR)/ || (echo "${RED}❌ Pylint failed${NC}" && exit 1); \
	fi
	@find . -maxdepth 1 -name "*.py" -type f | xargs -r pylint || (echo "${RED}❌ Pylint failed${NC}" && exit 1)
	@echo "${GREEN}✅ Pylint passed${NC}"

lint-mypy: ## Check type hints with mypy
	@echo "${YELLOW}Running mypy type checker...${NC}"
	@if [ -d "api" ] && [ -f "api/mypy.ini" ]; then \
		mypy --config-file=api/mypy.ini api/ || (echo "${RED}❌ mypy failed${NC}" && exit 1); \
	else \
		mypy $(API_DIR)/ || (echo "${RED}❌ mypy failed${NC}" && exit 1); \
	fi
	@find . -maxdepth 1 -name "*.py" -type f | xargs -r mypy || (echo "${RED}❌ mypy failed${NC}" && exit 1)
	@echo "${GREEN}✅ mypy passed${NC}"

lint-bandit: ## Run security checks with Bandit
	@echo "${YELLOW}Running Bandit security scanner...${NC}"
	@if [ -f "pyproject.toml" ]; then \
		bandit -r . --configfile pyproject.toml || (echo "${RED}❌ Bandit security scan failed${NC}" && exit 1); \
	else \
		bandit -r . --exclude ./tests,./venv,./env,./.venv || (echo "${RED}❌ Bandit security scan failed${NC}" && exit 1); \
	fi
	@echo "${GREEN}✅ Bandit security scan passed${NC}"

lint-markdown: ## Check markdown files with markdownlint
	@echo "${YELLOW}Running markdownlint...${NC}"
	@if command -v markdownlint >/dev/null 2>&1; then \
		markdownlint '**/*.md' --ignore node_modules --ignore __pycache__ --ignore '*.egg-info' --ignore venv --ignore .venv --ignore env --ignore ENV --ignore build --ignore dist --ignore .pytest_cache --ignore .mypy_cache --ignore .tox --ignore .nox --ignore .ipynb_checkpoints --config .markdownlint.json || (echo "${RED}❌ markdownlint failed${NC}" && exit 1); \
	else \
		echo "${YELLOW}⚠️  markdownlint not installed - skipping markdown checks${NC}"; \
		echo "${YELLOW}   Install with: npm install -g markdownlint-cli${NC}"; \
	fi
	@echo "${GREEN}✅ markdownlint passed${NC}"

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

# Terraform targets
.PHONY: terraform-check terraform-fmt terraform-init terraform-validate terraform-plan

terraform-check: terraform-fmt terraform-init terraform-validate terraform-plan ## Run all Terraform checks (format, init, validate, plan)
	@echo "${GREEN}✅ All Terraform checks passed!${NC}"

terraform-fmt: ## Check Terraform formatting
	@echo "${YELLOW}Checking Terraform formatting...${NC}"
	@terraform fmt -check -recursive terraform/ || (echo "${RED}❌ Terraform formatting check failed${NC}" && echo "${YELLOW}Run 'terraform fmt -recursive terraform/' to fix${NC}" && exit 1)
	@echo "${GREEN}✅ Terraform formatting check passed${NC}"

terraform-init: ## Initialize Terraform
	@echo "${YELLOW}Initializing Terraform...${NC}"
	@terraform -chdir=terraform init -backend=false || (echo "${RED}❌ Terraform init failed${NC}" && exit 1)
	@echo "${GREEN}✅ Terraform initialized${NC}"

terraform-validate: terraform-init ## Validate Terraform configuration
	@echo "${YELLOW}Validating Terraform configuration...${NC}"
	@terraform -chdir=terraform validate || (echo "${RED}❌ Terraform validation failed${NC}" && exit 1)
	@echo "${GREEN}✅ Terraform validation passed${NC}"

terraform-plan: terraform-init ## Run Terraform plan (requires tfvars)
	@echo "${YELLOW}Running Terraform plan...${NC}"
	@if [ ! -f terraform/terraform.tfvars ]; then \
		echo "${YELLOW}⚠️  terraform.tfvars not found, creating from example...${NC}"; \
		cp terraform/terraform.tfvars.example terraform/terraform.tfvars; \
		echo "${YELLOW}⚠️  Please edit terraform/terraform.tfvars with your AWS account ID${NC}"; \
	fi
	@terraform -chdir=terraform plan || (echo "${RED}❌ Terraform plan failed${NC}" && exit 1)
	@echo "${GREEN}✅ Terraform plan completed${NC}"

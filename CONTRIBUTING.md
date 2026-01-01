# Contributing to Protein Disorder Classification API

Thank you for contributing to the Protein Disorder Classification API! This document provides guidelines and instructions for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Code Style and Standards](#code-style-and-standards)
- [Testing](#testing)
- [Pull Request Process](#pull-request-process)
- [Quality Gates](#quality-gates)

## Code of Conduct

This project follows a professional code of conduct. Please be respectful, collaborative, and constructive in all interactions.

## Getting Started

### Prerequisites

- Python 3.10, 3.11, or 3.12
- pip package manager
- Git

### Initial Setup

1. **Clone the repository:**

   ```bash
   git clone https://github.com/kmesiab/concept-model-protein-classifier.git
   cd concept-model-protein-classifier
   ```

2. **Create a virtual environment:**

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

4. **Install development tools:**

   ```bash
   pip install black flake8 pylint mypy isort pytest pytest-cov
   ```

## Development Workflow

1. **Create a feature branch:**

   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** following the code style guidelines below

3. **Run formatting and linting:**

   ```bash
   # Format code with Black
   black .
   
   # Sort imports with isort
   isort .
   
   # Check linting with Flake8
   flake8 .
   
   # Run Pylint
   pylint data_download.py
   
   # Check types with MyPy
   mypy data_download.py
   ```

4. **Run tests:**

   ```bash
   pytest tests/ -v --cov=. --cov-report=term
   ```

5. **Commit your changes:**

   ```bash
   git add .
   git commit -m "feat: add new feature"
   ```

## Code Style and Standards

### Formatting

- **Line length:** Maximum 100 characters
- **Code formatter:** Black (enforced)
- **Import sorting:** isort with Black profile
- **Type hints:** Required for all function signatures

### Linting Standards

All code must pass:

- **Black:** 100% compliance with Black formatting
- **Flake8:** No errors or warnings (max complexity: 10)
- **Pylint:** Score ≥ 9.0/10
- **MyPy:** Type checking enabled with strict equality checks

### Code Quality

- Write clear, self-documenting code
- Add docstrings for all public functions and classes
- Use type hints for function parameters and return values
- Keep functions focused and single-purpose
- Maximum cyclomatic complexity: 10

### Naming Conventions

- **Functions/variables:** `snake_case`
- **Classes:** `PascalCase`
- **Constants:** `UPPER_SNAKE_CASE`
- **Private methods:** `_leading_underscore`

## Testing

### Test Coverage Requirements

- **Minimum coverage:** 80% overall
- **Unit tests:** Required for all new functions
- **Integration tests:** Required for API endpoints
- **Async tests:** Use pytest-asyncio for async functions

### Writing Tests

1. **Location:** Place tests in the `tests/` directory
2. **Naming:** Test files should be named `test_*.py`
3. **Structure:** Use pytest fixtures for setup/teardown
4. **Assertions:** Use clear, descriptive assertions

### Running Tests

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=. --cov-report=term --cov-report=html

# Run specific test file
pytest tests/test_data_download.py -v

# Run tests matching a pattern
pytest tests/ -k "test_download"
```

### Test Example

```python
import pytest
from data_download import split_fasta

class TestSplitFasta:
    def test_basic_parsing(self):
        # Arrange
        ...
        
        # Act
        result = split_fasta(temp_file)
        
        # Assert
        assert len(result) == 2
```

## Pull Request Process

### Before Submitting

1. ✅ All tests pass locally
2. ✅ Code coverage ≥ 80%
3. ✅ All linting checks pass (Black, Flake8, Pylint, MyPy, isort)
4. ✅ Documentation updated (if applicable)
5. ✅ Commit messages follow conventional commits format

### Conventional Commit Format

Use the following prefixes for commit messages:

- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `style:` - Code style changes (formatting, etc.)
- `refactor:` - Code refactoring
- `test:` - Adding or updating tests
- `chore:` - Maintenance tasks

Example:

```text
feat: add protein sequence validation

- Implement amino acid validation
- Add comprehensive tests
- Update documentation
```

### PR Description Template

When creating a PR, use the template provided in `.github/PULL_REQUEST_TEMPLATE.md`

### Review Process

1. **Automated Checks:** CI/CD pipeline will run all quality gates
2. **Code Review:** At least one approval required from maintainers
3. **Testing:** All CI checks must pass (green ✅)
4. **Coverage:** Coverage report must show ≥80%

## Quality Gates

All PRs must pass the following quality gates before merging:

| Check | Tool | Threshold |
|-------|------|-----------|
| Code formatting | Black | 100% compliance |
| Linting | Flake8, Pylint | No errors |
| Type checking | MyPy | No errors |
| Test coverage | pytest-cov | ≥80% |
| Security | Bandit | No HIGH/CRITICAL |
| Dependencies | Safety, pip-audit | No known vulnerabilities |
| Secret scanning | TruffleHog | No verified secrets |

## Security

### Secret Scanning

All code changes are automatically scanned for accidentally committed secrets using TruffleHog:

- **Automated Scanning:** Runs on every push, PR, and weekly schedule
- **Full History Scan:** Checks entire git history, not just new commits
- **Blocking:** PRs with detected secrets will be blocked from merging

**Before Committing:**

```bash
# Install TruffleHog locally (optional but recommended)
pip install trufflehog

# Scan your changes before committing
trufflehog filesystem . --config=.trufflehog.yaml --only-verified
```

**If Secrets Are Detected:**

1. **DO NOT** push the commit
2. **Immediately revoke** the exposed credential
3. **Remove from git history:**

   ```bash
   # For the most recent commit
   git reset --soft HEAD~1
   # Edit files to remove secrets
   # Recommit without the secrets
   
   # For older commits, use git filter-repo or BFG Repo-Cleaner
   ```

4. **Use environment variables** or secrets management tools
5. **Regenerate credentials** and store securely

**False Positives:**

If TruffleHog flags a false positive:

1. Verify it's truly a false positive (not a real secret)
2. Add to `.trufflehog.yaml` with clear justification
3. Document why it's safe in the PR description

### General Security Practices

- **Never commit secrets** (API keys, passwords, tokens)
- **Use environment variables** for configuration
- **Run security scans** before committing
- **Report vulnerabilities** via GitHub Security Advisories

## Questions or Issues?

- **Bug reports:** Open an issue on GitHub
- **Feature requests:** Open an issue with the "enhancement" label
- **Questions:** Use GitHub Discussions

---

Thank you for contributing! 🚀

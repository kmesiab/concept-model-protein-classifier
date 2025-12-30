# CI/CD Pipeline Documentation

This document provides comprehensive documentation for the CI/CD pipeline implemented for the Protein Disorder Classification API.

## Table of Contents

- [Overview](#overview)
- [Workflows](#workflows)
- [Configuration Files](#configuration-files)
- [Quality Gates](#quality-gates)
- [Branch Protection](#branch-protection)
- [Troubleshooting](#troubleshooting)

## Overview

The CI/CD pipeline ensures code quality, security, and reliability through automated testing and validation on every commit and pull request.

### Pipeline Architecture

```
┌─────────────┐
│   Push/PR   │
└──────┬──────┘
       │
       ├─────────────┬─────────────┬─────────────┐
       │             │             │             │
   ┌───▼────┐   ┌───▼────┐   ┌───▼────┐   ┌───▼────┐
   │  Lint  │   │  Test  │   │Security│   │ Docker │
   └───┬────┘   └───┬────┘   └───┬────┘   └───┬────┘
       │             │             │             │
       └─────────────┴─────────────┴─────────────┘
                      │
                 ┌────▼────┐
                 │  Merge  │
                 └────┬────┘
                      │
                 ┌────▼────┐
                 │ Deploy  │
                 └─────────┘
```

## Workflows

### 1. Code Quality Workflow (`lint.yml`)

**Triggers:**
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop`

**Jobs:**
- Runs on Ubuntu latest
- Tests Python 3.10, 3.11, and 3.12 (matrix)
- Executes 5 linting tools in sequence

**Steps:**
1. **Checkout Code** - Uses `actions/checkout@v4`
2. **Setup Python** - Uses `actions/setup-python@v5`
3. **Cache Dependencies** - Caches pip packages for faster builds
4. **Install Dependencies** - Installs linting tools and project dependencies
5. **Black Check** - Validates code formatting
6. **Flake8** - Checks code style and complexity
7. **Pylint** - Advanced static code analysis
8. **MyPy** - Type checking with strict mode
9. **isort** - Validates import sorting

**Failure Handling:**
- Any linting failure stops the workflow
- Clear error messages with file locations
- Suggests fixes when possible

**Example Run:**
```bash
# Local equivalent
black --check --diff --color .
flake8 . --count --show-source --statistics
pylint data_download.py
mypy data_download.py
isort --check-only --diff --color .
```

### 2. Testing Workflow (`test.yml`)

**Triggers:**
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop`

**Jobs:**
- Runs on Ubuntu latest
- Matrix testing: Python 3.10, 3.11, 3.12
- fail-fast disabled for complete test coverage

**Steps:**
1. **Checkout Code**
2. **Setup Python** - For each matrix version
3. **Cache Dependencies**
4. **Install Dependencies** - pytest, pytest-cov, pytest-asyncio, coverage
5. **Run Tests with Coverage** - Generates XML and HTML reports
6. **Upload to Codecov** - Uploads coverage data (requires `CODECOV_TOKEN`)
7. **Enforce Coverage Threshold** - Fails if <80%
8. **Upload HTML Report** - Artifacts available for download

**Coverage Requirements:**
- Overall: ≥80%
- Branch coverage: Tracked
- Missing lines: Reported

**Example Run:**
```bash
# Local equivalent
pytest tests/ -v --cov=. --cov-report=xml --cov-report=term --cov-report=html
coverage report --fail-under=80
```

### 3. Security Workflow (`security.yml`)

**Triggers:**
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop`
- Scheduled: Weekly on Mondays at 9 AM UTC

**Jobs:**
Single job with 4 security scanners

**Steps:**
1. **Checkout Code**
2. **Setup Python 3.11**
3. **Cache Dependencies**
4. **Install Security Tools** - bandit, safety, pip-audit
5. **Bandit Scan** - Python code security analysis
   - Generates JSON and text reports
   - Excludes tests and virtual environments
6. **Safety Check** - Dependency vulnerability scanning
   - Checks against known CVE database
   - Generates JSON report
7. **pip-audit** - Additional dependency auditing
   - Comprehensive vulnerability database
8. **Trivy Scan** - Filesystem vulnerability scanning
   - SARIF format for GitHub Security tab
   - Table output for human review
   - Checks for CRITICAL, HIGH, and MEDIUM severity

**Security Reports:**
- Uploaded as artifacts for each run
- SARIF results sent to GitHub Security tab
- Summary posted to workflow summary

**Example Run:**
```bash
# Local equivalent
bandit -r . --exclude ./tests,./venv
safety check
pip-audit
```

## Configuration Files

### `pyproject.toml`

Centralizes configuration for multiple tools:

**Black Configuration:**
```toml
[tool.black]
line-length = 100
target-version = ['py310', 'py311', 'py312']
```

**isort Configuration:**
```toml
[tool.isort]
profile = "black"
line_length = 100
```

**MyPy Configuration:**
```toml
[tool.mypy]
python_version = "3.10"
warn_return_any = true
disallow_untyped_defs = false
ignore_missing_imports = true
```

**pytest Configuration:**
```toml
[tool.pytest.ini_options]
minversion = "7.0"
testpaths = ["tests"]
```

**Coverage Configuration:**
```toml
[tool.coverage.report]
fail_under = 80
```

### `.flake8`

Flake8-specific configuration:
```ini
[flake8]
max-line-length = 100
max-complexity = 10
exclude = .git, __pycache__, build, dist
```

### `pylintrc`

Pylint configuration (extensive):
- Disabled checks: C0111 (missing-docstring), C0103 (invalid-name)
- Max line length: 100
- Max complexity: Configured per category

## Quality Gates

All PRs must pass these gates before merging:

| Gate | Tool | Threshold | Failure Action |
|------|------|-----------|----------------|
| Formatting | Black | 100% | ❌ Block merge |
| Style | Flake8 | 0 errors | ❌ Block merge |
| Analysis | Pylint | Score ≥9.0 | ❌ Block merge |
| Types | MyPy | 0 errors | ❌ Block merge |
| Imports | isort | 100% | ❌ Block merge |
| Tests | pytest | All pass | ❌ Block merge |
| Coverage | pytest-cov | ≥80% | ❌ Block merge |
| Security | Bandit | No CRITICAL/HIGH | ⚠️ Review required |
| Dependencies | Safety | No CVEs | ⚠️ Review required |
| Vulnerabilities | Trivy | No CRITICAL | ⚠️ Review required |

## Branch Protection

### Recommended Settings for `main`

```yaml
Required status checks:
  - Code Quality (Python 3.10)
  - Code Quality (Python 3.11)
  - Code Quality (Python 3.12)
  - Tests (Python 3.10)
  - Tests (Python 3.11)
  - Tests (Python 3.12)
  - Security

Require branches to be up to date: true
Require pull request reviews: 1
Require linear history: true
Include administrators: true
```

## Troubleshooting

### Common Issues

#### 1. Black Formatting Failures

**Problem:** `would reformat X files`

**Solution:**
```bash
black .
git add .
git commit -m "style: apply black formatting"
```

#### 2. Coverage Below Threshold

**Problem:** `Coverage report --fail-under=80`

**Solution:**
- Add more tests for uncovered code
- Check coverage report: `htmlcov/index.html`
- Focus on critical paths first

#### 3. MyPy Type Errors

**Problem:** `error: Need type annotation`

**Solution:**
```python
# Before
def func(param):
    return param

# After
def func(param: str) -> str:
    return param
```

#### 4. Pylint Score Too Low

**Problem:** `Your code has been rated at X/10`

**Solution:**
- Fix reported issues
- Or disable specific checks (last resort):
```python
# pylint: disable=specific-rule
```

#### 5. Security Vulnerabilities

**Problem:** Bandit/Safety reports vulnerabilities

**Solution:**
- Update dependencies: `pip install --upgrade package-name`
- Check if false positive
- Add exception if necessary (with justification)

### Debugging Workflows

**View workflow runs:**
```bash
gh run list --workflow=lint.yml
gh run view RUN_ID --log
```

**Re-run failed jobs:**
- Use GitHub UI to re-run
- Or push a new commit to trigger

**Check specific job logs:**
1. Go to Actions tab
2. Click on workflow run
3. Click on specific job
4. View detailed logs

## Local Development

Run all checks locally before pushing:

```bash
#!/bin/bash
# run-checks.sh

set -e

echo "🔍 Running Black..."
black --check .

echo "📦 Running isort..."
isort --check-only .

echo "🔎 Running Flake8..."
flake8 .

echo "🔬 Running Pylint..."
pylint data_download.py

echo "🔍 Running MyPy..."
mypy data_download.py

echo "🧪 Running Tests..."
pytest tests/ -v --cov=. --cov-report=term

echo "🔒 Running Security Scans..."
bandit -r . --exclude ./tests

echo "✅ All checks passed!"
```

## Performance

**Typical Run Times:**
- Lint workflow: ~2-3 minutes
- Test workflow: ~3-5 minutes per Python version
- Security workflow: ~4-6 minutes

**Optimization Tips:**
- Caching reduces install time by ~50%
- Matrix jobs run in parallel
- fail-fast disabled for complete feedback

## Future Enhancements

### Phase 2 (Planned)
- Docker build and push workflow
- Performance benchmarking workflow
- Automated dependency updates via Dependabot

### Phase 3 (Future)
- AWS deployment workflow
- Production monitoring integration
- Automated rollback procedures
- Blue-green deployments

---

For questions or issues with the CI/CD pipeline, please open an issue on GitHub.

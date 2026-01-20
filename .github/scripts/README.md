# Security Workflow Scripts

This directory contains helper scripts for the security workflow that ensure
scan failures are visible with PR annotations and clear error messages.

## Scripts

### check-file-exists.sh

Checks if a file exists and emits a GitHub Actions error annotation if not.

**Usage:**

```bash
.github/scripts/check-file-exists.sh <filepath> <description>
```

**Example:**

```bash
.github/scripts/check-file-exists.sh reports/bandit-report.json "Bandit JSON report"
```

**Exit Codes:**

- `0`: File exists
- `1`: File does not exist (emits `::error` annotation)

**Linting:** Passes `shellcheck`

---

### annotate-bandit-findings.py

Parses Bandit JSON report and emits GitHub Actions error annotations for
findings.

**Usage:**

```bash
python3 .github/scripts/annotate-bandit-findings.py <bandit-report.json> [min_severity]
```

**Arguments:**

- `bandit-report.json`: Path to Bandit JSON report
- `min_severity`: Optional. Minimum severity to annotate (HIGH, MEDIUM, or LOW).
  Default: MEDIUM

**Example:**

```bash
python3 .github/scripts/annotate-bandit-findings.py reports/bandit-report.json HIGH
```

**Output:**

Emits GitHub Actions annotations in the format:

```text
::error file=<filename>,line=<line>::[Bandit <severity>] <issue_id>: <message>
```

**Linting:** Passes `black`, `isort`, `flake8`, `pylint`, `mypy`

---

### annotate-pip-audit-findings.py

Parses pip-audit JSON report and emits GitHub Actions error annotations for
vulnerabilities.

**Usage:**

```bash
python3 .github/scripts/annotate-pip-audit-findings.py <pip-audit-report.json>
```

**Arguments:**

- `pip-audit-report.json`: Path to pip-audit JSON report

**Example:**

```bash
python3 .github/scripts/annotate-pip-audit-findings.py reports/pip-audit-report.json
```

**Output:**

Emits GitHub Actions annotations in the format:

```text
::error file=requirements.txt::[pip-audit] <package> <version> - <vuln_id>: <message>
```

**Linting:** Passes `black`, `isort`, `flake8`, `pylint`, `mypy`

---

### annotate-trivy-findings.py

Parses Trivy JSON report and emits GitHub Actions error annotations for
vulnerabilities, misconfigurations, and secrets.

**Usage:**

```bash
python3 .github/scripts/annotate-trivy-findings.py <trivy-report.json> [min_severity]
```

**Arguments:**

- `trivy-report.json`: Path to Trivy JSON report
- `min_severity`: Optional. Minimum severity to annotate (CRITICAL, HIGH, or
  MEDIUM). Default: HIGH

**Example:**

```bash
python3 .github/scripts/annotate-trivy-findings.py trivy-results.json HIGH
```

**Output:**

Emits GitHub Actions annotations for:

- **Vulnerabilities:**
  `::error file=<target>::[Trivy <severity>] <package> - <vuln_id>: <message>`
- **Misconfigurations:**
  `::error file=<target>::[Trivy <severity>] config - <id>: <message>`
- **Secrets:**
  `::error file=<target>,line=<line>::[Trivy CRITICAL] Secret - <rule_id>: <message>`

**Linting:** Passes `black`, `isort`, `flake8`, `pylint`, `mypy`

---

## Workflow Integration

These scripts are integrated into the `.github/workflows/security.yml` workflow:

1. **Scan steps** run security tools (Bandit, pip-audit, Trivy)
2. **Check steps** verify output files exist using `check-file-exists.sh`
3. **Annotate steps** parse reports and emit PR annotations using the Python scripts
4. **Upload steps** upload reports as artifacts

## Error Handling

All scripts follow best practices for error handling:

- **Fail fast:** Scripts exit with non-zero code on errors
- **Clear messages:** Error messages are descriptive and actionable
- **PR annotations:** Use GitHub Actions workflow commands (`::error`) to surface
  issues directly in PR UI
- **Type safety:** Python scripts use type hints and pass mypy strict checks
- **Linter compliance:** All scripts pass appropriate linters

## Development

### Running Linters

**Bash scripts:**

```bash
shellcheck .github/scripts/*.sh
```

**Python scripts:**

```bash
black --check .github/scripts/*.py
isort --check-only .github/scripts/*.py
flake8 .github/scripts/*.py
pylint .github/scripts/*.py
mypy .github/scripts/*.py
```

### Testing

Create sample reports and test the scripts:

```bash
# Test file existence check
.github/scripts/check-file-exists.sh /tmp/test.txt "Test file"

# Test annotation scripts with sample data
python3 .github/scripts/annotate-bandit-findings.py sample-bandit.json HIGH
python3 .github/scripts/annotate-pip-audit-findings.py sample-pip-audit.json
python3 .github/scripts/annotate-trivy-findings.py sample-trivy.json HIGH
```

## References

- [GitHub Actions Workflow Commands](https://docs.github.com/en/actions/using-workflows/workflow-commands-for-github-actions)
- [Bandit Security Tool](https://bandit.readthedocs.io/)
- [pip-audit](https://pypi.org/project/pip-audit/)
- [Trivy Security Scanner](https://aquasecurity.github.io/trivy/)

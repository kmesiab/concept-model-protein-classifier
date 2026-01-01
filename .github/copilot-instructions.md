# Copilot Instructions

## ABSOLUTIST QUALITY PHILOSOPHY (NON-NEGOTIABLE)

**ACCEPT NOTHING LESS THAN PERFECTION. Lives depend on this code.**

This is enterprise-grade bioinformatics software. Any code quality failure is unacceptable and should NEVER be presented to a reviewer. If a PR has not passed ALL GitHub Actions checks, it is NOT ready.

## Workflow (CRITICAL - MANDATORY BEFORE EVERY COMMIT)

### BEFORE ANY COMMIT - VERIFY WITH MAKE CHECK-ALL

1. **Run all quality checks:**
   ```bash
   make check-all  # MUST return exit code 0
   ```

2. **If ANY check fails:**
   ```bash
   make fix        # Auto-fix what can be fixed
   make check-all  # Verify ALL checks pass
   ```

3. **Iterate until perfection:**
   - Fix issue
   - Run `make check-all`
   - If fails, repeat
   - Continue until error_count = 0
   - ONLY THEN commit

### NEVER COMMIT UNTIL:

- ✅ `make check-all` returns exit code 0
- ✅ ALL linters pass with their config files:
  - Black formatting: 0 issues
  - isort: 0 import order issues
  - Flake8: 0 violations
  - Pylint: Score ≥ 9.5/10
  - mypy: 0 type errors
  - Bandit: 0 security issues
  - markdownlint: 0 documentation issues
- ✅ ALL tests pass
- ✅ No linter suppression comments (no `noqa`, `type: ignore`, etc.)
- ✅ GitHub Actions workflows are correctly configured
- ✅ You can PROVE with 100% certainty that GHA will pass

## Iterative Quality Verification Process

After making ANY code change:

1. Run `make check-all` immediately
2. If it fails, fix the issue immediately
3. Run `make check-all` again
4. Repeat steps 2-3 until ALL checks pass
5. Only then is work complete

## Code Style Requirements

- Self-documenting variable names
- Inline comments explain WHY, not WHAT
- Follow existing patterns in codebase
- Type hints on ALL functions
- No suppression of linters - FIX THE CODE PROPERLY
- No shortcuts, no bypasses

## Quality Standards

- **Formatting**: Perfect Black/isort compliance
- **Type Safety**: Complete mypy coverage, no `type: ignore`
- **Security**: Zero Bandit findings
- **Code Quality**: Pylint score ≥ 9.5/10
- **Documentation**: Full markdown compliance
- **Tests**: ≥80% coverage, all passing

## Configuration Files (ALWAYS USE THESE)

The repository has specific configuration files for each tool:
- `api/.pylintrc` - Use with `--rcfile=api/.pylintrc`
- `api/mypy.ini` - Use with `--config-file=api/mypy.ini`
- `api/.isort.cfg` - Use with `--settings-file=api/.isort.cfg`
- `pyproject.toml` - Bandit uses `--configfile pyproject.toml`

GitHub Actions are configured to use these. Your local verification MUST match.

## Failure is Not an Option

If you complete work and commit without ensuring `make check-all` passes, YOU HAVE FAILED. This wastes time, tokens, and reviewer patience. 

Check and recheck your work from multiple angles. NEVER call work complete unless you can PROVE 100% passing GitHub Actions.

See `Makefile` for all quality tools and commands.

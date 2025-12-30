## Description
<!-- Provide a clear and concise description of your changes -->

## Type of Change
<!-- Mark the relevant option with an "x" -->

- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update
- [ ] Performance improvement
- [ ] Code refactoring
- [ ] Security fix

## Related Issue
<!-- Link to the issue this PR addresses -->
Closes #

## Changes Made
<!-- List the specific changes made in this PR -->

- 
- 
- 

## Testing Checklist
<!-- Mark completed items with an "x" -->

- [ ] All new code has unit tests
- [ ] All tests pass locally (`pytest tests/ -v`)
- [ ] Test coverage is ≥80% (`pytest tests/ --cov`)
- [ ] No test files were deleted or modified without justification

## Code Quality Checklist
<!-- Mark completed items with an "x" -->

- [ ] Code follows Black formatting (`black --check .`)
- [ ] Imports are sorted correctly (`isort --check-only .`)
- [ ] Flake8 linting passes (`flake8 .`)
- [ ] Pylint score ≥9.0 (`pylint <files>`)
- [ ] Type hints added and MyPy passes (`mypy <files>`)
- [ ] Code complexity is reasonable (max 10)

## Security Checklist
<!-- Mark completed items with an "x" -->

- [ ] No secrets or credentials in code
- [ ] Bandit security scan passes (`bandit -r .`)
- [ ] No new security vulnerabilities introduced
- [ ] Dependencies are up to date and secure

## Documentation Checklist
<!-- Mark completed items with an "x" -->

- [ ] Docstrings added for new functions/classes
- [ ] README updated (if needed)
- [ ] CONTRIBUTING.md updated (if needed)
- [ ] Type hints documented

## Performance Impact
<!-- Describe any performance implications -->

- [ ] No performance impact
- [ ] Performance improved
- [ ] Performance degraded (explain why below)

**Performance notes:**


## Breaking Changes
<!-- If this is a breaking change, describe what breaks and the migration path -->


## Screenshots
<!-- If applicable, add screenshots to demonstrate changes -->


## Additional Notes
<!-- Add any additional context, implementation details, or concerns -->


## Reviewer Checklist
<!-- For reviewers -->

- [ ] Code follows project conventions
- [ ] Tests are comprehensive
- [ ] Documentation is clear
- [ ] No obvious security issues
- [ ] Performance is acceptable

---

**By submitting this PR, I confirm that:**
- [ ] I have read the [CONTRIBUTING.md](../CONTRIBUTING.md) guidelines
- [ ] My code follows the project's code style
- [ ] I have performed a self-review of my code
- [ ] I have commented my code where necessary
- [ ] My changes generate no new warnings
- [ ] I have added tests that prove my fix/feature works
- [ ] All CI checks pass

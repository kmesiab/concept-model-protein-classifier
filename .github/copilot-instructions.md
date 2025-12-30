# Copilot Instructions

## Workflow (CRITICAL)

Before committing:
```bash
make check-all  # Run ALL quality checks
```

If checks fail:
```bash
make fix        # Auto-fix formatting
make check-all  # Verify fixes
```

**Never commit until `make check-all` passes (error_count = 0).**

## Code Style

- Self-documenting variable names
- Inline comments explain WHY, not WHAT
- Follow existing patterns in codebase
- Type hints on all functions

See `Makefile` for all quality tools.

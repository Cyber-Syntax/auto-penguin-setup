# AGENTS.md

This file provides guidance to agents when working with code in this repository.

## General Guidelines

1. KISS (Keep It Simple, Stupid): Aim for simplicity and clarity. Avoid unnecessary abstractions or metaprogramming.
2. DRY (Don't Repeat Yourself): Reuse code appropriately but avoid over-engineering. Each command handler has single responsibility.
3. Confirm understanding before making changes: If you're unsure about the purpose of a piece of code, ask for clarification rather than making assumptions.
4. **ALWAYS** use `ruff check <filepath>` on each python file you modify to ensure proper formatting and linting.
    - Use `ruff format <filepath>` on each python file you modify to ensure proper formatting.
    - Use `ruff check --fix <filepath>` on each python file you modify to fix any fixable errors.

## Code Style Guidelines

- Never use f-strings in logging statements, instead use `%s` formatting.
- Use only the helpers in `aps/utils/privilege.py` for any privileged operations.
- Always call `ensure_sudo()` once at the start of commands that require privileges (not in helpers).
- Use `run_privileged()` for all commands needing sudo/root.

## Testing Instructions

Critical: Run tests after any change to ensure nothing breaks.

```bash
# Run all tests:
uv run pytest
# Run specific test file:
uv run pytest tests/test_config.py -v
# Run specific test function:
uv run pytest tests/test_config.py::test_function_name -v
# Run with coverage
uv run pytest tests/python/ --cov=aps --cov-report=html
```

## Running the CLI

```bash
# Run CLI
uv run aps --help
```

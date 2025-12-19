# AGENTS.md

This file provides guidance to agents when working with code in this repository.

## General Guidelines

1. KISS (Keep It Simple, Stupid): Aim for simplicity and clarity. Avoid unnecessary abstractions or metaprogramming.
2. DRY (Don't Repeat Yourself): Reuse code appropriately but avoid over-engineering. Each command handler has single responsibility.
3. Confirm understanding before making changes: If you're unsure about the purpose of a piece of code, ask for clarification rather than making assumptions.
4. ALWAYS use `ruff check <filepath>` on each Python file you modify to ensure proper linting and formatting:
    - Use `ruff check --fix <filepath>` to automatically fix any fixable errors.
    - Use `ruff format path/to/file.py` to format a specific file.
    - Use `ruff format path/to/code/` to format all files in `path/to/code` (and any subdirectories).
    - Use `ruff format` to format all files in the current directory.

## Code Style Guidelines

- Never use f-strings in logging statements, instead use `%s` formatting.
- Use only the helpers in `aps/utils/privilege.py` for any privileged operations.
- Always call `ensure_sudo()` once at the start of commands that require privileges (not in helpers).
- Use `run_privileged()` for all commands needing sudo/root.
- Always pass the command and its arguments as a list (e.g., `["ls", "-l"]`) in subprocess calls.

## Testing Instructions

Critical: Run tests after any change to ensure nothing breaks.

```bash
# Run all tests:
uv run pytest
# Run specific test file:
uv run pytest tests/test_config.py
# Run specific test function:
uv run pytest tests/test_config.py::test_function_name
# Run with coverage
uv run pytest tests/python/ --cov=aps.<folder>.<module>
uv run pytest tests/system/test_sudoers.py --cov=aps.system.sudoers
```

## Running the CLI

```bash
# Run CLI
uv run aps --help
```

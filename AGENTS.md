# AGENTS.md

This file provides guidance to agents when working with code in this repository.

## General Guidelines

1. Simple is better than complex.
2. KISS (Keep It Simple, Stupid): Aim for simplicity and clarity. Avoid unnecessary abstractions or metaprogramming.
3. DRY (Don't Repeat Yourself): Reuse code appropriately but avoid over-engineering. Each command handler has single responsibility.
4. Confirm understanding before making changes: If you're unsure about the purpose of a piece of code, ask for clarification rather than making assumptions.
5. **ALWAYS** use `ruff check <filepath>` on each python file you modify to ensure proper formatting and linting.
    - Use `ruff format <filepath>` on each python file you modify to ensure proper formatting.
    - Use `ruff check --fix <filepath>` on each python file you modify to fix any fixable errors.

## Code Style Guidelines

- Never use f-strings in logging statements, instead use `%s` formatting.

## Testing Instructions

Critical: Run tests after any change to ensure nothing breaks.

```bash
# Always activate venv before testing:
source .venv/bin/activate

# Run all tests:
pytest -v -q --strict-markers

# Run specific test file:
pytest tests/test_config.py -v

# Run specific test function:
pytest tests/test_config.py::test_function_name -v
# Run with coverage
pytest tests/python/ --cov=aps --cov-report=html
```

## Development Workflow

### Setup

```bash
# Create virtual environment
uv venv

# Activate environment
source .venv/bin/activate

# Install in development mode
uv pip install -e .
```

### Development Commands

```bash
# Run CLI
python -m aps --help
```

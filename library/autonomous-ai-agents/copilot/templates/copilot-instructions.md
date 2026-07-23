# GitHub Copilot Instructions

This file provides project-specific guidance for GitHub Copilot. It is automatically loaded by Copilot CLI when working in this repository.

## Project Overview

<!-- Beschreibe hier kurz was dieses Projekt ist -->

- **Language:** <!-- z.B. Python, TypeScript, Go -->
- **Framework:** <!-- z.B. FastAPI, React, None -->
- **Build System:** <!-- z.B. uv, npm, cargo -->
- **Test Framework:** <!-- z.B. pytest, jest, go test -->

## Coding Standards

### General
- Write clean, readable code with meaningful variable names
- Add comments for complex logic, not for obvious operations
- Keep functions small and focused (single responsibility)
- Prefer composition over inheritance

### Style
- Follow the existing code style in this project
- Use the project's linter configuration (`.eslintrc`, `pyproject.toml`, etc.)
- Run the formatter before committing (`black .`, `prettier --write`, etc.)

### Error Handling
- Always handle errors explicitly
- Use specific exception types, not generic `Exception`
- Provide meaningful error messages
- Log errors with context (what failed, why, what was the input)

### Testing
- Write tests for new features
- Use descriptive test names: `test_<what>_<condition>_<expected>`
- Test edge cases (empty input, null, boundary values)
- Mock external dependencies (APIs, databases, file system)

## Project Structure

```
<!-- Beschreibe hier die Ordnerstruktur -->

src/          # Source code
tests/        # Test files
docs/         # Documentation
scripts/      # Build/utility scripts
```

## Common Patterns

<!-- Beschreibe hier wiederkehrende Patterns im Projekt -->

### Example: Creating a new module
```python
# 1. Create module in src/<package>/
# 2. Add __init__.py exports
# 3. Create tests in tests/<package>/
# 4. Add to pyproject.toml if needed
```

## What NOT to Do

- Don't add dependencies without checking `pyproject.toml` / `package.json` first
- Don't commit secrets or API keys
- Don't break existing tests
- Don't add TODO comments without a ticket number
- Don't use deprecated APIs

## Git Conventions

- **Commit format:** `type: concise subject` (feat:, fix:, refactor:, docs:, chore:)
- **Branch naming:** `feature/<description>`, `fix/<description>`, `refactor/<description>`
- **PR description:** What changed, why, how to test

## Useful Commands

```bash
# Run tests
pytest tests/ -v

# Run linter
ruff check .

# Run formatter
black .

# Type check
mypy src/
```

## Notes for Copilot

- When generating code, prefer the patterns already used in this project
- If unsure about a dependency, check the existing imports first
- For new features, create tests alongside the implementation
- When refactoring, preserve existing behavior — run tests before and after

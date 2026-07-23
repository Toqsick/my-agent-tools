# GitHub Copilot Instructions — Template

This is a generic template for `.github/copilot-instructions.md`. Copy and customize per project.

## Project Overview

- **Language:** <!-- Python / TypeScript / Go -->
- **Framework:** <!-- FastAPI / React / None -->
- **Build System:** <!-- uv / npm / cargo -->
- **Test Framework:** <!-- pytest / jest / go test -->

## Coding Standards

### General
- Write clean, readable code with meaningful variable names
- Add comments for complex logic, not for obvious operations
- Keep functions small and focused (single responsibility)
- Prefer composition over inheritance

### Style
- Follow the existing code style in this project
- Use the project's linter configuration
- Run the formatter before committing

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
src/          # Source code
tests/        # Test files
docs/         # Documentation
scripts/      # Build/utility scripts
```

## What NOT to Do

- Don't add dependencies without checking existing config first
- Don't commit secrets or API keys
- Don't break existing tests
- Don't add TODO comments without a ticket number
- Don't use deprecated APIs

## Git Conventions

- **Commit format:** `type: concise subject` (feat:, fix:, refactor:, docs:, chore:)
- **Branch naming:** `feature/<description>`, `fix/<description>`

## Useful Commands

```bash
# Run tests
pytest tests/ -v

# Run linter
ruff check .

# Run formatter
black .
```

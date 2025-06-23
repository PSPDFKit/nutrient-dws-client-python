# Claude Development Guide for Nutrient DWS Python Client


## Critical Reference
**ALWAYS** refer to `SPECIFICATION.md` before implementing any features. This document contains the complete design specification for the Nutrient DWS Python Client library.

## Project Overview
Building a Python client library for the Nutrient Document Web Services (DWS) API with two main interfaces:
1. **Direct API**: Static methods on `NutrientClient` for single operations
2. **Builder API**: Fluent, chainable interface for multi-step workflows

## Key Implementation Guidelines

### Architecture
- Main entry point: `NutrientClient` class
- Builder pattern via `client.build()` returns `BuildAPIWrapper`
- Only external dependency: `requests` library
- Use `src` layout for package structure

### API Design Principles
- Direct API methods are snake_case versions of OpenAPI tool names
- All tool-specific parameters are keyword-only arguments
- File inputs accept: str (path), bytes, or file-like objects
- File outputs return bytes by default, or save to path if `output_path` provided

### Error Handling
Custom exceptions hierarchy:
- `NutrientError` (base)
- `AuthenticationError` (401/403)
- `APIError` (other API errors with status_code and response_body)

### Testing & Quality
- Run linting: `ruff check .`
- Run type checking: `mypy src/`
- Run tests: `pytest`
- Format code: `ruff format .`

### Before Committing
Always run the quality checks above to ensure code meets standards.

## Development Workflow
1. Refer to SPECIFICATION.md for requirements
2. Implement features incrementally
3. Write tests alongside implementation
4. Update documentation/docstrings
5. Run quality checks before marking tasks complete
6. Use `gh` cli tool

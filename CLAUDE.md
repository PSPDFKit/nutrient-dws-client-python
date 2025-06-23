# Claude Development Guide for Nutrient DWS Python Client

## Critical Reference
**ALWAYS** refer to `SPECIFICATION.md` before implementing any features. This document contains the complete design specification for the Nutrient DWS Python Client library.

## Project Overview
Building a Python client library for the Nutrient Document Web Services (DWS) API with two main interfaces:
1. **Direct API**: Static methods on `NutrientClient` for single operations
2. **Builder API**: Fluent, chainable interface for multi-step workflows

**Python Version**: Target Python 3.10+ and leverage type hints to their full extent for better developer experience and code quality.

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
6. Use `gh` cli tool for GitHub operations.
7. Always check out a feature branch when beginning work.
8. When sending a PR, always wait for tests to run and if it fails, read the logs to fix it.
9. Use `gh run list` with branch filter to not get confused.

**PR Strategy**: All GitHub PRs are squash merged to maintain clean commit history.

## Implementation Patterns for New Tools

### Build API Pattern (e.g., split_pdf)
Many Nutrient DWS tools use the Build API (`/build` endpoint) rather than dedicated tool endpoints:

```python
# Pattern for Build API tools
instructions = {
    "parts": [{"file": "file", "pages": page_range}],  # or other part config
    "actions": []  # or specific actions for the tool
}

result = self._http_client.post("/build", files=files, json_data=instructions)
```

### Key Learnings from split_pdf Implementation
- **Page Ranges**: Use `{"start": 0, "end": 5}` (0-based, end exclusive) and `{"start": 10}` (to end)
- **Multiple Operations**: Some tools require multiple API calls (one per page range/operation)
- **Error Handling**: API returns 400 with detailed errors when parameters are invalid
- **Testing Strategy**: Focus on integration tests with live API rather than unit test mocking
- **File Handling**: Use `prepare_file_for_upload()` and `save_file_output()` from file_handler module

### Method Template for DirectAPIMixin
```python
def new_tool(
    self,
    input_file: FileInput,
    output_path: Optional[str] = None,
    # tool-specific parameters with proper typing
) -> Optional[bytes]:
    """Tool description following existing docstring patterns."""
    # Use _process_file for simple tools or implement Build API pattern for complex ones
    return self._process_file("tool-name", input_file, output_path, **options)
```

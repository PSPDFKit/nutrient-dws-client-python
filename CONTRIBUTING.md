# Contributing to nutrient-dws

Thank you for your interest in contributing to the nutrient-dws Python client library! This document provides guidelines and instructions for contributing.

## Code of Conduct

By participating in this project, you agree to abide by our Code of Conduct: be respectful, inclusive, and constructive in all interactions.

## How to Contribute

### Reporting Issues

1. Check if the issue already exists in [GitHub Issues](https://github.com/jdrhyne/nutrient-dws-client-python/issues)
2. If not, create a new issue with:
   - Clear, descriptive title
   - Detailed description of the problem
   - Steps to reproduce
   - Expected vs actual behavior
   - Python version and OS
   - Relevant code snippets or error messages

### Suggesting Features

1. Check existing issues and pull requests
2. Open an issue with the "enhancement" label
3. Describe the feature and its use case
4. Explain why it would be valuable

### Contributing Code

#### Setup Development Environment

1. Fork the repository
2. Clone your fork:
   ```bash
   git clone https://github.com/YOUR_USERNAME/nutrient-dws-client-python.git
   cd nutrient-dws-client-python
   ```

3. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

4. Install development dependencies:
   ```bash
   pip install -e ".[dev]"
   pre-commit install
   ```

#### Development Workflow

1. Create a feature branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes following our coding standards

3. Run tests:
   ```bash
   pytest
   ```

4. Run type checking:
   ```bash
   mypy src/
   ```

5. Run linting:
   ```bash
   ruff check src/
   ```

6. Commit your changes:
   ```bash
   git add .
   git commit -m "feat: add new feature"
   ```

   Follow [Conventional Commits](https://www.conventionalcommits.org/):
   - `feat:` New feature
   - `fix:` Bug fix
   - `docs:` Documentation changes
   - `test:` Test changes
   - `refactor:` Code refactoring
   - `chore:` Maintenance tasks

7. Push and create a pull request

### Pull Request Guidelines

1. **Title**: Use conventional commit format
2. **Description**: Include:
   - Summary of changes
   - Related issue numbers
   - Breaking changes (if any)
   - Screenshots (if applicable)
3. **Tests**: Add tests for new features
4. **Documentation**: Update relevant documentation
5. **Code Quality**: Ensure all checks pass

### Coding Standards

- **Style**: Follow PEP 8, enforced by ruff
- **Type Hints**: Use type annotations for all public APIs
- **Docstrings**: Google-style docstrings for all public functions
- **Testing**: Aim for >90% test coverage
- **Error Handling**: Use appropriate exception types

### Testing

- Write unit tests for new functionality
- Include integration tests for API interactions
- Mock external API calls in unit tests
- Use pytest fixtures for common test data

Example test:
```python
def test_new_feature():
    """Test description."""
    client = NutrientClient({'apiKey': 'your_api_key'})
    result = client.new_feature()
    assert result == expected_value
```

### Documentation

- Update docstrings for API changes
- Update README.md if adding new features
- Update CHANGELOG.md following Keep a Changelog format
- Add examples for new functionality

## Release Process

1. Update version in `pyproject.toml`
2. Update CHANGELOG.md
3. Create release notes
4. Tag release: `git tag v0.1.0`
5. Push tags: `git push --tags`

## Questions?

- Open an issue for questions
- Check existing documentation
- Review closed issues and PRs

Thank you for contributing!

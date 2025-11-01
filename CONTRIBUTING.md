# Contributing to SQL Rule Extractor

Thank you for your interest in contributing to SQL Rule Extractor! This document provides guidelines and instructions for contributing.

## Development Setup

1. Fork and clone the repository:
```bash
git clone https://github.com/yourusername/sql-rule-extractor.git
cd sql-rule-extractor
```

2. Run the setup script:
```bash
./setup.sh
```

3. Activate the virtual environment:
```bash
source .venv/bin/activate
```

## Development Workflow

1. Create a new branch for your feature or bugfix:
```bash
git checkout -b feature/your-feature-name
```

2. Make your changes and add tests

3. Run tests to ensure everything works:
```bash
pytest -v
```

4. Run linting:
```bash
ruff check src/ tests/
black src/ tests/
```

5. Commit your changes with a descriptive message:
```bash
git commit -m "Add feature: description of your changes"
```

6. Push to your fork and create a pull request

## Code Style

- Follow PEP 8 guidelines
- Use type hints where appropriate
- Write docstrings for all public functions and classes
- Keep functions focused and concise
- Maximum line length: 100 characters

## Testing Guidelines

### Unit Tests
- Write unit tests for all new functionality
- Test edge cases and error conditions
- Use descriptive test names that explain what is being tested
- Aim for >80% code coverage

### Integration Tests
- Add integration tests for end-to-end workflows
- Test with realistic data samples
- Verify outputs are valid and complete

### Test Structure
```python
class TestYourFeature:
    """Test description."""

    def setup_method(self):
        """Setup test fixtures."""
        # Setup code

    def test_specific_behavior(self):
        """Test that specific behavior works correctly."""
        # Arrange
        # Act
        # Assert
```

## Adding New Features

### Adding a New SQL Dialect

1. Extend `SQLParser` in `src/extractor/sql_parser.py`
2. Add dialect-specific parsing logic
3. Register in `RepositoryIngestor`
4. Add tests for the new dialect

### Adding a New Clustering Method

1. Implement in `RuleClusterer` in `src/extractor/clusterer.py`
2. Add configuration options in `config.yml`
3. Document parameters in README
4. Add tests

### Adding a New LLM Provider

1. Create adapter class in `src/extractor/enricher.py`
2. Implement `LLMAdapter` interface
3. Add configuration support
4. Add environment variable documentation
5. Test with stub for CI

## Documentation

- Update README.md for user-facing changes
- Add docstrings for all new code
- Update configuration examples
- Add usage examples for new features

## Pull Request Process

1. Ensure all tests pass
2. Update documentation as needed
3. Add entry to CHANGELOG (if exists)
4. Request review from maintainers
5. Address review feedback
6. Squash commits if requested

## Reporting Bugs

When reporting bugs, include:
- Python version
- Operating system
- Steps to reproduce
- Expected behavior
- Actual behavior
- Error messages and logs
- Sample code/data if applicable

## Suggesting Enhancements

For feature requests:
- Clearly describe the use case
- Explain why this would be useful
- Provide examples of desired behavior
- Consider backward compatibility

## Code of Conduct

- Be respectful and inclusive
- Welcome newcomers
- Give constructive feedback
- Focus on what is best for the project

## Questions?

- Open an issue for questions
- Check existing issues and documentation first
- Provide context and examples

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

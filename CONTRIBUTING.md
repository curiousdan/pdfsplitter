# Contributing to PDF Chapter Splitter

Thank you for considering contributing to PDF Chapter Splitter! This document provides guidelines and instructions for contributing to this project.

## Code of Conduct

By participating in this project, you agree to maintain a respectful and inclusive environment for everyone.

## Setting Up Development Environment

1. Fork the repository on GitHub
2. Clone your fork locally:
   ```bash
   git clone https://github.com/yourusername/pdfsplitter.git
   cd pdfsplitter
   ```

3. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

4. Install development dependencies:
   ```bash
   pip install uv
   uv pip install -r requirements.txt
   uv pip install -e .[dev]  # Install development dependencies
   ```

## Development Workflow

1. Create a new branch for your feature or bug fix:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes, following the coding standards below
   
3. Add tests for your changes

4. Run the test suite to ensure all tests pass:
   ```bash
   pytest
   ```

5. Format your code and check type hints:
   ```bash
   black src/ tests/
   isort src/ tests/
   mypy src/
   ```

## Coding Standards

This project follows specific coding standards to maintain consistency:

- **Code formatting**: We use Black with a line length of 88 characters
- **Type hints**: All functions must have type hints (mypy is configured with disallow_untyped_defs=true)
- **Documentation**: Use Google-style docstrings for all classes and functions
- **Import ordering**: Use isort with Black profile for consistent imports
- **Variable naming**: Use semantic variable names, including units where applicable (e.g., timeoutSec)
- **Error handling**: Return typed validation objects where appropriate
- **Tests**: Create small, targeted test cases for all functionality

Refer to the [coding_style.md](context/coding_style.md) document for more detailed guidelines.

## Submitting Changes

1. Commit your changes with a clear commit message:
   ```bash
   git commit -m "Add feature: brief description of changes"
   ```

2. Push your branch to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```

3. Open a pull request on GitHub against the main repository
   - Provide a clear title and description
   - Reference any related issues

## Reporting Issues

When reporting issues, please include:

1. A clear, descriptive title
2. Steps to reproduce the issue
3. Expected behavior
4. Actual behavior
5. System information (OS, Python version, etc.)
6. Screenshots if applicable

## Feature Requests

Feature requests are welcome! Please provide:

1. A clear description of the feature
2. The motivation for the feature
3. How you envision it working
4. Any implementation ideas you may have

## Code Review Process

Pull requests will be reviewed by maintainers:
- Code must meet the coding standards
- All tests must pass
- New features must have appropriate tests
- Documentation must be updated as needed

## License

By contributing to this project, you agree that your contributions will be licensed under the project's [MIT License](LICENSE).
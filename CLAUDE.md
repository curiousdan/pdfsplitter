# PDFSPLITTER PROJECT GUIDE

## Build & Test Commands
- Run all tests: `pytest`
- Run single test: `pytest tests/test_file.py::test_function -v`
- Type checking: `mypy src/`
- Format code: `black src/ tests/`
- Sort imports: `isort src/ tests/`

## Code Style
- Black formatting (88 char line length)
- Type hints required (disallow_untyped_defs=true)
- Google-style docstrings for all functions and classes
- Import order: stdlib → third-party → project modules
- Semantic variable names including units (timeoutSec, lengthMm)
- Prefer constants over literals
- Readability over efficiency
- Error handling: Return typed validation objects where appropriate

## Project Structure
- Source code: src/pdfsplitter/
- Tests: tests/ (pytest with pytest-qt and pytest-cov)
- UI components use PyQt6
- PDF handling with PyMuPDF

## Guidelines
- Add TODO/FIXME comments with actions for future improvement
- Create small, targeted test cases
- Be consistent with existing code patterns
- Split implementation from interface when possible
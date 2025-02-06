# PDF Chapter Splitter

A user-friendly tool for splitting PDF files into chapters with preview capabilities.

## Features

- Load and validate PDF files (up to 100MB)
- Display page thumbnails for preview
- Manual page range selection
- Split PDFs into multiple files based on page ranges
- Simple and intuitive GUI interface

## Requirements

- Python 3.10 or higher
- PyQt6 for the GUI interface
- PyMuPDF for PDF processing

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/pdfsplitter.git
cd pdfsplitter
```

2. Create a virtual environment and install dependencies using `uv`:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh  # Install uv if not already installed
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -e ".[dev]"  # Install with development dependencies
```

## Usage

1. Start the application:
```bash
python -m pdfsplitter
```

2. Use the GUI to:
   - Load a PDF file using the "Open" button in the toolbar
   - View page thumbnails in a scrollable grid
   - Select an output directory for split files
   - (Coming soon) Define chapter ranges and extract them

## Development

- Run tests:
```bash
pytest tests/
```

- Format code:
```bash
black src/ tests/
isort src/ tests/
```

- Type checking:
```bash
mypy src/ tests/
```

## Project Structure

```
pdfsplitter/
├── src/
│   └── pdfsplitter/
│       ├── __init__.py      # Package initialization
│       ├── __main__.py      # Application entry point
│       ├── pdf_document.py  # PDF handling functionality
│       └── main_window.py   # GUI implementation
├── tests/                   # Test files
├── pyproject.toml          # Project configuration
└── README.md              # This file
```

## License

MIT License - See LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and ensure they pass
5. Submit a pull request

## Project Status

- [x] Phase 1: Basic PDF Handling
  - PDF loading and validation
  - Thumbnail generation
  - Page extraction functionality
  
- [x] Phase 2: Core GUI Implementation
  - Main window layout
  - Thumbnail preview grid
  - File selection dialog
  - Output directory selection
  
- [ ] Phase 3: Range Management GUI
  - Chapter range input interface
  - Range validation
  - Range list management
  - Split operation integration
  
- [ ] Phase 4: Polish and Error Handling
  - Input validation
  - Error dialogs
  - Progress indicators
  - UI polish
  
- [ ] Future: Automatic chapter detection 
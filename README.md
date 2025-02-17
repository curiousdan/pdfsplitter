# PDF Chapter Splitter

A powerful PDF bookmark management tool with an intuitive user interface.

## Features

- **Bookmark Management**
  - View and edit PDF bookmarks in a tree structure
  - Add new bookmarks via thumbnail right-click
  - Edit and delete existing bookmarks
  - Drag-and-drop reorganization
  - Keyboard shortcuts for common operations

- **Thumbnail Navigation**
  - Efficient thumbnail preview with lazy loading
  - Visual feedback for selected pages
  - Context menu for quick bookmark creation
  - Smooth scrolling and navigation

- **Chapter Detection**
  - Automatic chapter detection
  - Manual chapter range selection
  - Chapter preview and navigation
  - Bookmark-based chapter organization

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/pdfsplitter.git
   cd pdfsplitter
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. Install dependencies using uv:
   ```bash
   pip install uv
   uv pip install -r requirements.txt
   ```

## Usage

1. Launch the application:
   ```bash
   uv run python -m pdfsplitter
   ```

2. Open a PDF file using the "Open PDF..." button in the toolbar.

3. Managing Bookmarks:
   - Right-click on a thumbnail to add a new bookmark
   - Double-click a bookmark to edit its title
   - Press Delete to remove a bookmark
   - Drag and drop bookmarks to reorganize
   - Use arrow keys to expand/collapse bookmark tree

4. Keyboard Shortcuts:
   - F2: Edit selected bookmark
   - Delete: Remove selected bookmark
   - Right Arrow: Expand bookmark
   - Left Arrow: Collapse bookmark

## Development

### Project Structure

```
pdfsplitter/
├── src/
│   └── pdfsplitter/
│       ├── bookmark_manager.py  # Bookmark operations
│       ├── bookmark_tree.py     # Tree widget UI
│       ├── thumbnail_widget.py  # Thumbnail display
│       └── main_window.py       # Main application window
├── tests/                       # Unit and integration tests
├── docs/                        # Documentation
└── requirements.txt            # Project dependencies
```

### Running Tests

```bash
uv run pytest tests/
```

### Code Style

The project follows these coding standards:
- Type hints for all function parameters and returns
- Comprehensive docstrings in Google style
- Logging for important operations
- Unit tests for all functionality

## Performance Considerations

- Lazy loading of thumbnails for better memory usage
- Efficient bookmark tree operations
- Optimized PDF operations using PyMuPDF
- Non-blocking UI during heavy operations

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- PyQt6 for the GUI framework
- PyMuPDF for PDF handling
- pytest for testing infrastructure 
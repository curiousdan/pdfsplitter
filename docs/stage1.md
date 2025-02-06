# PDF Chapter Splitter Design Document (Manual First Approach)

## Current Context
- Currently, users need to manually split PDF books into chapters
- No existing simple solution for preview-based PDF splitting
- Need for a user-friendly tool to handle PDFs
- Starting with manual splitting via GUI, with auto-detection as future enhancement

## Requirements

### Functional Requirements
Phase 1 (Manual):
- Load and validate single PDF files (< 100MB)
- Display page thumbnails for preview
- Allow manual entry of page ranges
- Generate separate PDF files for each range
- Basic error handling and validation

Phase 2 (Future - Automatic):
- Detect chapter boundaries from PDF bookmarks/structure
- Fallback to manual mode if automatic detection fails
- Optional manifest file generation

### Non-Functional Requirements
- User-friendly GUI interface
- Quick preview generation
- Efficient PDF processing
- Clear error messaging
- Minimal setup requirements for users

## Design Decisions

### 1. GUI Framework
Will implement using PyQt6 because:
- Native look and feel on macOS
- Rich widget library for PDF preview
- Good documentation and community support
- Built-in widgets for range input and validation
- Trade-off: Larger dependency size, but worth it for functionality

### 2. PDF Processing Library
Will implement using PyMuPDF (fitz) because:
- Efficient thumbnail generation
- Simple API for page extraction
- Fast performance for large files
- Good documentation
- Trade-off: More complex API than PyPDF2, but more reliable

### 3. Application Architecture
Will implement using Model-View-Controller (MVC) pattern because:
- Clear separation of concerns
- Easier to test components independently
- Facilitates future automatic detection addition
- Common pattern for GUI applications

## Technical Design

### 1. Core Components
````

class PDFDocument:
    """Handles PDF loading, validation, and page operations"""
    def __init__(self, file_path: Path) -> None: ...
    def validate_file(self) -> bool: ...
    def generate_thumbnails(self) -> list[QImage]: ...
    def get_page_count(self) -> int: ...

class PageRange:
    """Represents a user-defined page range"""
    def __init__(self, name: str, start_page: int, end_page: int) -> None: ...
    def validate(self, max_pages: int) -> bool: ...
    def to_dict(self) -> dict[str, Any]: ...

class MainWindow(QMainWindow):
    """Main application window"""
    def __init__(self) -> None: ...
    def show_preview(self, thumbnails: list[QImage]) -> None: ...
    def show_error(self, message: str) -> None: ...
    def add_range(self) -> None: ...
    def remove_range(self) -> None: ...

class PDFSplitter:
    """Handles the actual PDF splitting operations"""
    def split_pdf(self, ranges: list[PageRange], output_dir: Path) -> None: ...
````

### 2. Data Models
````

@dataclass
class SplitConfiguration:
    """Configuration for PDF splitting"""
    input_file: Path
    output_dir: Path
    ranges: list[PageRange]
````

### 3. Integration Points
- File system for PDF I/O
- GUI event system for user interactions
- PDF library for document processing

## Implementation Plan

1. Phase 1: Basic PDF Handling (1 week)
   - Implement PDF loading and validation
   - Basic thumbnail generation
   - Simple page extraction

2. Phase 2: Core GUI Implementation (1 week)
   - Create main window layout
   - Implement thumbnail preview grid
   - Add file selection dialog
   - Implement output directory selection

3. Phase 3: Range Management GUI (1 week)
   - Add range input interface
   - Implement range validation
   - Add range list management
   - Connect split operation

4. Phase 4: Polish and Error Handling (1 week)
   - Add input validation
   - Implement error dialogs
   - Add progress indicators
   - Final UI polish

Future Phases:
- Automatic chapter detection
- Manifest generation
- Enhanced preview features

## Testing Strategy

### Unit Tests
- PDF loading and validation
- Page range validation
- Split operations
- Data model validation

### Integration Tests
- End-to-end manual splitting
- GUI interaction flows
- Error handling scenarios

## Observability

### Logging
- PDF loading and validation
- User-defined ranges
- Split operations
- Error conditions
- User interactions

### Metrics
- Processing time
- Success/failure rates
- Memory usage during processing

## Future Considerations

### Potential Enhancements
- Automatic chapter detection
- Batch processing support
- Configuration saving
- Enhanced preview options
- Manifest file generation

### Known Limitations
- Manual range entry only (initially)
- No automatic detection (initially)
- No sub-chapter handling
- No special character support

## Dependencies

### Runtime Dependencies
- Python 3.10+
- PyQt6
- PyMuPDF
- typing-extensions

### Development Dependencies
- pytest
- pytest-qt
- mypy
- black
- isort

## Security Considerations
- Input validation for PDF files
- Secure file handling
- Memory management for large files

## Rollout Strategy
1. Development of manual splitting features
2. Internal testing with sample PDFs
3. Initial release with manual features
4. Gather user feedback
5. Begin automatic detection development

## References
- PyMuPDF documentation
- PyQt6 documentation
- PDF specification

# PDF Chapter Detection Enhancement Design Document

## Current Context
- PDF Chapter Splitter currently supports manual splitting via GUI
- Users must manually input page ranges for chapters
- Memory issues observed (4-5GB RAM usage)
- No automatic detection capabilities
- No bookmark navigation features
- Well-functioning preview and splitting capabilities exist

## Requirements

### Functional Requirements
- Automatic detection of chapter boundaries from PDF bookmarks
- Display bookmark structure in new panel
- Navigate to bookmark locations in preview
- Pre-fill detected ranges in existing interface
- Support partial detection with manual fallback
- Copy logs feature for debugging
- Memory optimization for preview generation

### Non-Functional Requirements
- Detection process completes in < 2 seconds
- RAM usage < 1GB for 100MB PDF
- Non-intrusive error messaging
- Maintainable pattern detection system
- Comprehensive logging for debugging
- Seamless degradation to manual mode

## Design Decisions

### 1. Bookmark Detection System
Will implement modular pattern-based detection because:
- Allows easy addition of new patterns
- Clear separation of detection logic
- Simple to test individual patterns
- Trade-off: Might miss complex patterns initially

### 2. Memory Management
Will implement preview caching strategy because:
- Current unlimited caching causing memory bloat
- Can limit to visible pages only
- Trade-off: Slightly slower navigation for better memory usage

### 3. Bookmark Panel Integration
Will implement as dockable widget because:
- Consistent with PyQt6 design patterns
- Users can hide/show as needed
- Flexible positioning
- Trade-off: More complex layout management

## Technical Design

### 1. Core Components
```python
class BookmarkDetector:
    """Handles PDF bookmark analysis and chapter detection"""
    def detect_chapters(self, pdf_doc: fitz.Document) -> list[PageRange]: ...
    def analyze_structure(self) -> BookmarkTree: ...

class PatternMatcher(Protocol):
    """Interface for chapter detection patterns"""
    def matches(self, bookmark: BookmarkNode) -> bool: ...
    def extract_range(self, bookmark: BookmarkNode) -> PageRange: ...

class BookmarkPanel(QDockWidget):
    """Displays PDF bookmark structure"""
    def update_bookmarks(self, tree: BookmarkTree) -> None: ...
    def on_bookmark_clicked(self, page: int) -> None: ...

class PreviewCache:
    """Manages memory-efficient preview caching"""
    def get_preview(self, page: int) -> QImage: ...
    def clear_distant_pages(self, current_page: int) -> None: ...
```

### 2. Data Models
```python
@dataclass
class BookmarkNode:
    """Represents a PDF bookmark"""
    title: str
    page: int
    level: int
    children: list[BookmarkNode]

@dataclass
class BookmarkTree:
    """Complete bookmark structure"""
    root: BookmarkNode
    chapter_ranges: list[PageRange]
```

### 3. Integration Points
- PDFDocument class for bookmark extraction
- MainWindow for bookmark panel integration
- Existing preview system for navigation
- Logging system for detection feedback

## Implementation Plan

1. Phase 1: Memory Optimization (1 week)
   - Implement PreviewCache
   - Add page cleanup logic
   - Test memory usage
   - Benchmark performance

2. Phase 2: Bookmark Detection (1 week)
   - Implement BookmarkDetector
   - Add initial pattern matching
   - Add detection logging
   - Unit test coverage

3. Phase 3: UI Enhancement (1 week)
   - Add BookmarkPanel
   - Integrate navigation
   - Add status messages
   - Update progress indicators

4. Phase 4: Integration & Testing (1 week)
   - Connect all components
   - End-to-end testing
   - Performance testing
   - Memory usage verification

## Testing Strategy

### Unit Tests
- Pattern matching logic
- Bookmark tree construction
- Preview cache behavior
- Memory management

### Integration Tests
- End-to-end detection flow
- UI interaction scenarios
- Memory usage scenarios
- Error handling paths

## Observability

### Logging
- Bookmark structure analysis
- Pattern matching decisions
- Memory usage statistics
- Detection success/failure
- User interactions

### Metrics
- Detection success rate
- Memory usage over time
- Processing time
- Cache hit/miss rates

## Future Considerations

### Potential Enhancements
- Additional detection patterns
- Sub-chapter handling
- Custom pattern configuration
- Enhanced bookmark visualization

### Known Limitations
- Simple pattern matching only
- No nested chapter support
- Manual intervention needed for complex structures
- Limited to well-structured PDFs

## Dependencies

### Runtime Dependencies
- PyQt6
- PyMuPDF (fitz)
- typing-extensions

### Development Dependencies
- pytest
- pytest-qt
- pytest-cov
- memory_profiler

## Security Considerations
- Input validation for bookmarks
- Memory limits enforcement
- Resource cleanup

## Rollout Strategy
1. Memory optimization deployment
2. Internal testing with sample PDFs
3. Bookmark detection release
4. UI enhancement deployment
5. Monitoring and feedback collection

## References
- PyMuPDF bookmark documentation
- PyQt6 docking system documentation
- PDF specification for bookmarks

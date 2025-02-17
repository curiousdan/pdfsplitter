# PDF Bookmark Enhancement Design Document

## Current Context
- PDF viewer supports displaying existing bookmarks in expanded view
- No capability to add or modify bookmarks
- Bookmarks are read-only and always expanded
- No ability to save bookmark changes back to PDF
- Well-functioning thumbnail preview and navigation system exists

## Requirements

### Functional Requirements
- Display bookmarks in collapsed tree view by default
- Add new bookmarks via thumbnail right-click
- Edit and delete existing bookmarks (both original and custom)
- Drag-and-drop reorganization of bookmarks
- Save modified bookmarks back to PDF file
- Navigate to bookmarked pages via bookmark click
- Support nested bookmark hierarchies
- Maintain page-order sorting within each level

### Non-Functional Requirements
- Responsive UI during bookmark operations
- Clear visual feedback for selected thumbnails
- Intuitive drag-drop interaction
- Non-blocking PDF modifications
- Graceful error handling for write-protected PDFs
- Clear indication of unsaved changes

## Design Decisions

### 1. Bookmark Storage
Will implement direct PDF bookmark modification because:
- Maintains bookmark data within the PDF file itself
- No need for external storage or sync
- Standard PDF feature supported by most readers
- Trade-off: More complex save operations, but worth it for portability

### 2. Bookmark Organization
Will implement unrestricted drag-drop because:
- Provides maximum flexibility for user organization
- Simplifies implementation by removing validation logic
- Matches user expectation of free-form organization
- Trade-off: Potentially illogical structures, but prioritizes user choice

### 3. UI Interaction Model
Will implement right-click + immediate edit because:
- Reduces number of clicks needed to add bookmarks
- Provides immediate feedback and ability to name
- Matches common UI patterns for tree views
- Trade-off: Less discoverable than button, but more efficient

## Technical Design

### 1. Core Components
```python
class BookmarkManager:
    """Handles bookmark operations and state management"""
    def add_bookmark(self, page: int, title: str, parent: Optional[BookmarkNode] = None) -> BookmarkNode: ...
    def delete_bookmark(self, node: BookmarkNode) -> None: ...
    def move_bookmark(self, node: BookmarkNode, new_parent: Optional[BookmarkNode]) -> None: ...
    def save_to_pdf(self, path: Path) -> None: ...

class BookmarkTreeWidget(QTreeWidget):
    """Custom tree widget for bookmark display and interaction"""
    def enable_drag_drop(self) -> None: ...
    def handle_drop(self, source: QTreeWidgetItem, target: QTreeWidgetItem) -> None: ...
    def start_edit_item(self, item: QTreeWidgetItem) -> None: ...

class ThumbnailWidget(QWidget):
    """Enhanced thumbnail widget with selection support"""
    def set_selected(self, selected: bool) -> None: ...
    def show_context_menu(self, pos: QPoint) -> None: ...
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
    modified: bool = False
    parent: Optional[BookmarkNode] = None

class BookmarkTreeModel:
    """Manages bookmark hierarchy and modifications"""
    root: BookmarkNode
    modified: bool = False
```

### 3. Integration Points
- PDFDocument class for bookmark extraction and saving
- MainWindow for bookmark panel integration
- Existing thumbnail system for selection and navigation
- PyMuPDF for PDF bookmark manipulation

## Implementation Plan

1. Phase 1: Basic Bookmark Management (1 week)
   - Add BookmarkManager class
   - Implement bookmark addition/deletion
   - Add unsaved changes tracking
   - Add save functionality

2. Phase 2: UI Enhancement (1 week)
   - Add thumbnail selection
   - Implement context menu
   - Add immediate edit mode
   - Implement drag-drop support

3. Phase 3: PDF Integration (1 week)
   - Implement PDF bookmark saving
   - Add save/save as dialogs
   - Handle write protection
   - Add error handling

4. Phase 4: Testing & Polish (1 week)
   - Performance optimization
   - UI polish
   - Documentation

## Testing Strategy

### Unit Tests
- BookmarkManager operations
- Tree model modifications
- PDF save/load operations
- Drag-drop logic

### Integration Tests
- End-to-end bookmark workflows
- UI interaction scenarios
- PDF modification scenarios
- Error handling paths

## Observability

### Logging
- Bookmark operations
- Tree modifications
- Save operations
- Error conditions
- User interactions

### Metrics
- Operation success rates
- UI response times
- PDF modification times
- Error frequencies

## Future Considerations

### Potential Enhancements
- Multi-select bookmark operations
- Bookmark search/filter
- Bookmark templates
- Bookmark import/export

### Known Limitations
- No validation of bookmark hierarchy
- No auto-save functionality
- No bookmark style customization
- Limited to PDF internal bookmarks

## Dependencies

### Runtime Dependencies
- PyQt6
- PyMuPDF (fitz)
- typing-extensions

### Development Dependencies
- pytest
- pytest-qt
- pytest-mock
- mypy

## Security Considerations
- PDF write permission validation
- File system access controls
- Input sanitization for bookmark titles

## Rollout Strategy
1. Internal testing with sample PDFs
2. Beta testing with power users
3. Gradual feature enablement
4. Full release
5. Monitor for issues

## References
- PyMuPDF bookmark documentation
- PDF specification for bookmarks
- PyQt6 tree widget documentation

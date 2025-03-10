# Bookmark Drag-Drop Enhancement Design Document

## Current Context
- Bookmark tree supports basic drag-drop UI
- No validation of bookmark hierarchy levels
- Missing visual feedback for nesting
- Inconsistent parent-child relationship updates
- Page order not maintained during moves
- Well-functioning bookmark data model exists

## Requirements

### Functional Requirements
- Validate bookmark level hierarchy during drag-drop
- Maintain page order within each level
- Support nested bookmark structures (H1 → H2 → H3)
- Provide clear visual feedback during drag operations
- Update both UI and data model consistently
- Support undo/redo for drag-drop operations

### Non-Functional Requirements
- Responsive drag-drop feedback (<50ms)
- Clear visual indicators for valid/invalid drops
- Intuitive level nesting visualization
- Graceful error handling for invalid moves
- Comprehensive logging for debugging

## Design Decisions

### 1. Drag-Drop Validation
Will implement real-time validation during drag because:
- Provides immediate feedback to users
- Prevents invalid operations before they occur
- Matches user expectations for drag-drop
- Trade-off: More complex UI code, but worth it for UX

### 2. Visual Feedback System
Will implement custom drop indicator painting because:
- Allows precise control over nesting visualization
- Can show both level and validity
- Supports custom styling per requirement
- Trade-off: More maintenance than default indicators

### 3. Bookmark Level Management
Will implement strict level validation because:
- Maintains consistent document structure
- Prevents invalid hierarchies
- Simplifies bookmark export
- Trade-off: Less flexibility, but ensures valid PDFs

## Technical Design

### 1. Core Components
```python
class BookmarkTreeWidget(QTreeWidget):
    """Enhanced tree widget with validated drag-drop"""
    
    def __init__(self) -> None:
        self.level_validator = BookmarkLevelValidator()
        self.drop_indicator = DropIndicatorPainter()
        
    def dragMoveEvent(self, event: QDragMoveEvent) -> None:
        """Real-time validation during drag"""
        if self.validateDrop(event):
            self.drop_indicator.show(event, valid=True)
            event.accept()
        else:
            self.drop_indicator.show(event, valid=False)
            event.ignore()
            
    def validateDrop(self, event: QDragMoveEvent) -> bool:
        """Validate level hierarchy and page order"""
        
class BookmarkLevelValidator:
    """Validates bookmark level changes"""
    def validate_move(
        self, 
        source: BookmarkNode,
        target: BookmarkNode,
        position: DropPosition
    ) -> ValidationResult: ...

class DropIndicatorPainter:
    """Custom drop indicator visualization"""
    def show(
        self,
        event: QDragMoveEvent,
        valid: bool,
        level_change: Optional[int] = None
    ) -> None: ...
```

### 2. Data Models
```python
@dataclass
class DropPosition:
    """Represents a potential drop location"""
    target: BookmarkNode
    position: Literal["before", "after", "inside"]
    resulting_level: int
    page_order_valid: bool

@dataclass
class ValidationResult:
    """Result of drop validation"""
    valid: bool
    message: str
    level_change: Optional[int] = None
```

### 3. Integration Points
- BookmarkManager for node operations
- MainWindow for status updates
- UndoStack for operation history
- Logging system for debugging

## Implementation Plan

1. Phase 1: Core Validation (1 week)
   - Implement BookmarkLevelValidator
   - Add page order validation
   - Add hierarchy validation
   - Write unit tests for validation logic

2. Phase 2: Visual Enhancement (1 week)
   - Create DropIndicatorPainter
   - Add level change visualization
   - Implement validity feedback
   - Add hover state feedback

3. Phase 3: Data Model Integration (1 week)
   - Update BookmarkNode move operations
   - Add undo/redo support
   - Implement consistent updates
   - Add error handling

4. Phase 4: Testing & Polish (1 week)
   - Add integration tests
   - Performance optimization
   - Add logging
   - Documentation

## Testing Strategy

### Unit Tests
- Level validation logic
- Page order validation
- Drop position calculations
- Visual feedback states

### Integration Tests
- End-to-end drag-drop operations
- Undo/redo functionality
- Error handling scenarios
- Performance benchmarks

## Observability

### Logging
- Drag start/end events
- Validation results
- Move operations
- Error conditions

### Metrics
- Validation time
- UI response time
- Error rates
- Usage patterns

## Future Considerations

### Potential Enhancements
- Multi-item drag-drop
- Custom level rules
- Keyboard-driven moves
- Bookmark templates

### Known Limitations
- Single item moves only
- Fixed level hierarchy
- No cross-window drag-drop
- Limited undo history

## Dependencies

### Runtime Dependencies
- PyQt6
- typing-extensions
- dataclasses

### Development Dependencies
- pytest
- pytest-qt
- pytest-mock
- mypy

## Security Considerations
- Input validation for bookmark titles
- Memory management during drag
- Resource cleanup
- Error recovery

## Rollout Strategy
1. Developer testing with sample PDFs
2. QA testing with edge cases
3. Beta testing with power users
4. Gradual feature enablement
5. Full release with monitoring

## References
- PyQt6 drag-drop documentation
- PDF bookmark specifications
- Qt tree widget examples
- Existing bookmark manager code

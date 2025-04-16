# Bookmark Drag-and-Drop Feature Design

## 1. Problem Statement

The PDF splitter application features a bookmark tree that allows users to reorder bookmarks via drag-and-drop. Currently, the functionality is partially implemented but not working correctly. When a user drags a bookmark, the UI might visually change, but the underlying data model (BookmarkManager) isn't updated, and validation rules aren't properly enforced.

We need to implement a fully functioning drag-and-drop system that properly:
- Processes drop events
- Validates moves against defined rules 
- Provides visual feedback
- Updates the BookmarkManager's data structure
- Ensures the UI reflects the changes

## 2. Component Analysis

From analyzing the existing code, we've identified the following key components:

### 2.1 BookmarkTreeWidget (src/pdfsplitter/bookmark_tree.py)
- Custom QTreeWidget implementation for displaying bookmarks
- Currently has a basic dropEvent implementation, but lacks proper validation and doesn't update the data model correctly
- Has a bookmark_moved signal but only passes source_node and new_parent_node, missing position information

### 2.2 BookmarkLevelValidator (src/pdfsplitter/bookmark_validation.py)
- Responsible for validating bookmark moves
- Validates structure, page order, and level constraints
- Returns ValidationResult objects with validation status, message, and level_change

### 2.3 BookmarkManager (src/pdfsplitter/bookmark_manager.py)
- Manages the bookmark data model
- Has a move_bookmark method that updates the hierarchy, but isn't connected to the drag-drop operation
- Handles saving the updated bookmark structure to PDF files

### 2.4 BookmarkPanel (src/pdfsplitter/bookmark_panel.py)
- Currently uses a standard QTreeWidget instead of the custom BookmarkTreeWidget
- Needs to be updated to use BookmarkTreeWidget and handle bookmark_moved signals

## 3. Design and Implementation Plan

### 3.1 UI Integration
1. Modify BookmarkPanel to use BookmarkTreeWidget instead of QTreeWidget
2. Connect the bookmark_moved signal to a handler in BookmarkPanel
3. Update MainWindow to pass the BookmarkManager to BookmarkPanel

### 3.2 Enhanced Drag-Drop Implementation in BookmarkTreeWidget
1. Refine the dropEvent method to:
   - Get source and target items
   - Determine drop position (BEFORE, AFTER, INSIDE)
   - Get appropriate parent node based on position
   - Validate the move using BookmarkLevelValidator
   - Emit an enhanced bookmark_moved signal with position information
   - Update UI with appropriate visual feedback

2. Enhance the bookmark_moved signal to include:
   - Source node
   - New parent node
   - Drop position (BEFORE, AFTER, INSIDE)
   - Level change information

### 3.3 BookmarkPanel Handler Implementation
1. Implement _handle_bookmark_moved_in_model method to:
   - Calculate the new bookmark level based on position and target
   - Call BookmarkManager.move_bookmark with correct parameters
   - Handle exceptions and provide error feedback
   - Refresh the tree if necessary

### 3.4 BookmarkManager Integration
1. Ensure BookmarkManager.move_bookmark correctly updates:
   - Parent-child relationships
   - Bookmark levels
   - Modified flag

## 4. Detailed Implementation Steps

### Step 1: Modify BookmarkTreeWidget.dropEvent
1. Import necessary types from bookmark_validation
2. Determine drop position (BEFORE, AFTER, INSIDE) from dropIndicatorPosition()
3. Use validation logic from BookmarkLevelValidator
4. Enhance bookmark_moved signal to include drop position and level change
5. Provide visual feedback for successful/failed operations

### Step 2: Update BookmarkPanel to use BookmarkTreeWidget
1. Replace QTreeWidget instantiation with BookmarkTreeWidget
2. Implement _handle_bookmark_moved_in_model to update the data model
3. Connect bookmark_moved signal to the handler

### Step 3: Ensure BookmarkManager.move_bookmark works correctly
1. Verify logic for updating parent-child relationships
2. Confirm that bookmark levels are properly updated
3. Ensure modified flag is set

### Step 4: Add Comprehensive Tests
1. Add tests for BookmarkTreeWidget.dropEvent
2. Add more test cases for BookmarkLevelValidator
3. Add tests for BookmarkPanel's handling of bookmark_moved signals

## 5. Testing Plan

1. Unit Tests:
   - Test BookmarkTreeWidget.dropEvent with various scenarios
   - Test BookmarkLevelValidator with different move operations
   - Test BookmarkPanel._handle_bookmark_moved_in_model

2. Integration Tests:
   - Test the full workflow from drag-drop to model update

3. Manual Testing:
   - Verify drag-drop operations in the UI
   - Check that invalid operations are prevented
   - Confirm that the bookmark structure is saved correctly

## 6. Challenges and Considerations

1. Maintaining UI responsiveness during validation
2. Handling edge cases like dropping onto an empty tree
3. Ensuring a consistent UI state when a move is invalid
4. Calculating the correct new level for bookmarks
5. Supporting undo/redo functionality (future enhancement)

## 7. Future Enhancements

1. Visual indication of valid drop targets
2. Animation for smoother user experience
3. Undo/redo support for bookmark operations
4. Keyboard shortcuts for moving bookmarks 
Task: Implement Bookmark Drag-and-Drop Functionality
1. Context:

Problem: The application features a bookmark tree (BookmarkTreeWidget defined in src/pdfsplitter/bookmark_tree.py) designed to allow users to reorder bookmarks via drag-and-drop. Currently, this feature is non-functional. Dragging might be visually possible, but dropping an item doesn't correctly update the bookmark order, likely due to issues in event handling, validation logic (src/pdfsplitter/bookmark_validation.py), or updating the data model (src/pdfsplitter/bookmark_manager.py). The intended design is described in bookmark_feature.md.

Goal: Implement a fully working drag-and-drop functionality for the BookmarkTreeWidget. This involves correctly processing drop events, validating the move against defined rules, providing visual feedback (optional for now, focus on functionality), updating the BookmarkManager's data structure, and ensuring the UI reflects the changes.

2. Affected Files:

src/pdfsplitter/bookmark_tree.py (Primary UI logic)

src/pdfsplitter/bookmark_validation.py (Validation rules)

src/pdfsplitter/bookmark_manager.py (Data model updates)

src/pdfsplitter/main_window.py (Signal/slot connections)

src/pdfsplitter/bookmark_panel.py (Potential integration point)

tests/test_bookmark_tree.py

tests/test_bookmark_validation.py

tests/test_bookmark_manager.py

3. Important Prerequisite - UI Integration:

The custom BookmarkTreeWidget (which has the drag-drop code) needs to be used in the application's UI. Currently, BookmarkPanel (src/pdfsplitter/bookmark_panel.py) uses a standard QTreeWidget.

Action: Modify BookmarkPanel.__init__ to instantiate and use BookmarkTreeWidget instead of QTreeWidget.

# src/pdfsplitter/bookmark_panel.py
# Add import for the custom widget
from .bookmark_tree import BookmarkTreeWidget
# ... other imports ...

class BookmarkPanel(QDockWidget):
    # ... signals ...
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        # ... super().__init__ ...
        self._init_ui()
        # Add a reference to the bookmark manager if needed for updates
        self.bookmark_manager = None # Initialize, set later

    def _init_ui(self) -> None:
        # ... main_widget, layout ...

        # Replace QTreeWidget with BookmarkTreeWidget
        # self._tree = QTreeWidget() # Old line
        self._tree = BookmarkTreeWidget() # New line

        # Configure the custom tree (remove standard QTreeWidget settings if now defaults in BookmarkTreeWidget)
        # self._tree.setHeaderLabels(["Title", "Page"]) # Maybe set inside BookmarkTreeWidget?
        # self._tree.setColumnWidth(0, 200)
        # self._tree.setToolTip("Drag to reorder bookmarks") # Update tooltip
        # self._tree.setDragEnabled(False) # Remove, should be True in BookmarkTreeWidget
        # self._tree.setAcceptDrops(False) # Remove, should be True in BookmarkTreeWidget
        # self._tree.setSelectionMode(QTreeWidget.SelectionMode.SingleSelection) # Keep or set in custom widget

        # Connect signals from the custom tree
        self._tree.itemClicked.connect(self._on_item_clicked) # Keep for navigation
        # self._tree.itemDoubleClicked.connect(self._on_item_double_clicked) # Keep for editing?
        # Connect the NEW signal for when a move happens in the data model
        self._tree.bookmark_moved.connect(self._handle_bookmark_moved_in_model) # Add this connection

        self._layout.addWidget(self._tree)
        # ... rest of UI setup ...

    # Add a method to set the bookmark manager
    def set_bookmark_manager(self, manager):
         self.bookmark_manager = manager

    # Rename update_bookmarks to reflect it updates from the manager
    def update_tree_from_manager(self) -> None:
        """Updates the tree view based on the current state of the bookmark manager."""
        if self.bookmark_manager:
             self._tree.update_from_manager(self.bookmark_manager.root)
        else:
             self._tree.clear()
        # Update status label etc.

    # Slot to handle the bookmark_moved signal from the tree widget
    def _handle_bookmark_moved_in_model(self, source_node, new_parent_node, position, level_change):
        """Handles the actual data move in the BookmarkManager."""
        if not self.bookmark_manager:
            return

        try:
            # Calculate new level if needed (logic might depend on validator/manager)
            # This might be simplified if move_bookmark handles level calculation
            calculated_new_level = None # Placeholder - determine how level is updated
            if position == DropPosition.INSIDE and new_parent_node:
                 calculated_new_level = BookmarkLevel(new_parent_node.level.value + 1)
            elif new_parent_node: # Moving as sibling
                 calculated_new_level = new_parent_node.level
            else: # Moving to root
                 calculated_new_level = BookmarkLevel.H1

            # Clamp level if necessary (e.g., BookmarkLevel max)
            if calculated_new_level and calculated_new_level.value > max(level.value for level in BookmarkLevel if level != BookmarkLevel.ROOT):
                 # Handle max level constraint if applicable
                 pass


            self.bookmark_manager.move_bookmark(source_node, new_parent_node, new_level=calculated_new_level)

            # Optional: Refresh the specific part of the tree if update_from_manager is too slow
            # For now, rely on the fact that super().dropEvent moved the UI item

            # Mark changes as unsaved (might need signal to MainWindow)
            # self.changes_made.emit() # Example signal

        except Exception as e:
            logger.error(f"Error moving bookmark in manager: {e}")
            QMessageBox.critical(self, "Error", f"Failed to update bookmark structure: {e}")
            # Consider reverting the UI move if the manager update fails
            self.update_tree_from_manager() # Refresh tree to revert UI on error

    # Modify update_bookmarks (or rename) to accept BookmarkManager
    # def update_bookmarks(self, tree: Optional[BookmarkTree]) -> None: # Old
    def display_bookmarks(self, manager) -> None: # New example
         self.set_bookmark_manager(manager)
         self.update_tree_from_manager()
         # Update ranges tree etc.

    # ... rest of BookmarkPanel ...


Update MainWindow: Modify MainWindow to pass the BookmarkManager instance to the BookmarkPanel after a PDF is loaded. Change calls from self.bookmark_panel.update_bookmarks(...) to self.bookmark_panel.display_bookmarks(self.bookmark_manager). Ensure BookmarkManager is created/loaded in MainWindow.

4. Detailed Steps (Code Implementation):

Step 4.1: Refine BookmarkTreeWidget.dropEvent (src/pdfsplitter/bookmark_tree.py)

Implement the logic as outlined in the previous response's Task 3, Step 1.

Key points:

Import BookmarkLevelValidator, DropPosition, QMessageBox, QDropEvent, QPointF, QMimeData.

Get source_item and target_item.

Determine position (BEFORE, AFTER, INSIDE) based on dropIndicatorPosition() and handle dropping onto the background (target_item is None).

Calculate actual_parent_node based on position and target_item.

Instantiate BookmarkLevelValidator.

Call validator.validate_move(source_node, target_node, position).

If valid:

Call event.acceptProposedAction().

Emit self.bookmark_moved.emit(source_node, actual_parent_node, position, validation_result.level_change). Note: Add position and level_change parameters to the signal definition if they aren't there:

# In BookmarkTreeWidget class definition
bookmark_moved = pyqtSignal(BookmarkNode, BookmarkNode, DropPosition, int) # Add DropPosition, int

Call super().dropEvent(event) to let Qt move the QTreeWidgetItem.

Optionally update selection/scroll position.

If invalid:

Show QMessageBox.warning with validation_result.message.

Call event.ignore().

Use try...except for robustness.

Step 4.2: Review/Refactor BookmarkLevelValidator (src/pdfsplitter/bookmark_validation.py)

Read through the validate_move method and its helpers (_validate_structure, _validate_page_order, _validate_levels).

Add comments explaining the logic behind each check.

Simplify (Optional but Recommended): Can the level validation (_validate_levels) be simplified? Does it need to be strictly PyMuPDF compliant, or just prevent obvious issues like level jumps > 1? Discuss if unsure. The current logic for level_change calculation seems complex and might need refinement based on how BookmarkManager.move_bookmark handles level updates.

Ensure validate_move returns a ValidationResult with the correct level_change value when the move is valid, especially for INSIDE moves.

Step 4.3: Connect Signal and Implement Handler (in src/pdfsplitter/bookmark_panel.py)

Ensure the BookmarkTreeWidget instance (self._tree) is used (see Prerequisite step).

Add the _handle_bookmark_moved_in_model slot as shown in the Prerequisite step.

Connect the signal in _init_ui: self._tree.bookmark_moved.connect(self._handle_bookmark_moved_in_model).

Implement the logic inside _handle_bookmark_moved_in_model:

Get the source_node, new_parent_node, position, level_change from the signal arguments.

Call self.bookmark_manager.move_bookmark(...). Decide how to determine the new_level parameter for this call (e.g., based on position, level_change, new_parent_node.level). Add logic to calculate calculated_new_level.

Wrap the call to move_bookmark in try...except.

On success, signal MainWindow to enable the save button.

On error, show a QMessageBox.critical and potentially refresh the tree (self.update_tree_from_manager()) to revert the UI change.

Step 4.4: Ensure BookmarkManager.move_bookmark is Correct (src/pdfsplitter/bookmark_manager.py)

Verify the logic:

Removes node from node.parent.children.

Appends node to actual_parent.children (where actual_parent is new_parent or self.root).

Updates node.parent.

Updates node.level if new_level argument is provided and valid.

Sets self._modified = True.

Consider adding more robust checks (e.g., ensure node is actually removed from the old parent).

Step 4.5: Update Tests

test_bookmark_validation.py: Add more test cases covering different drop positions (BEFORE, AFTER, INSIDE), level changes, page order violations, and structural violations (moving root, moving to descendant).

test_bookmark_tree.py:

Modify test_move_bookmark to use the updated bookmark_moved signal signature.

Mock BookmarkLevelValidator.validate_move to return specific ValidationResult objects (both valid and invalid).

Assert that bookmark_moved is emitted only when validation passes.

Assert that QMessageBox.warning is called when validation fails (you might need to patch QMessageBox).

Assert that super().dropEvent is called only on valid drops.

test_bookmark_manager.py: Add more scenarios to test_move_bookmark, specifically checking the final parent, children list, and level of the moved node after various valid moves.

test_bookmark_panel.py (or test_main_window.py): Add integration tests (mocking lower levels) to verify that a successful drop in the BookmarkTreeWidget triggers the _handle_bookmark_moved_in_model slot, which in turn calls BookmarkManager.move_bookmark with the correct arguments.

5. Verification:

Run the application and load a PDF with bookmarks.

Ensure the bookmark tree is now using BookmarkTreeWidget (e.g., check tooltips or default behavior).

Try dragging and dropping bookmarks:

Reorder siblings at the same level.

Nest a bookmark under another (making it a child).

Un-nest a bookmark (move it to the parent level or root level).

Move bookmarks between different branches.

Verify that moves that should be invalid (e.g., creating level jumps > 1, violating page order if validation enforces it) are prevented, ideally with a warning message.

After a successful move, verify the tree UI updates correctly.

Verify the "Save" action becomes enabled after a successful move.

Save the PDF, reopen it, and confirm the bookmark structure matches the changes made via drag-and-drop.

Run pytest and ensure all tests, especially the new/modified ones, pass.


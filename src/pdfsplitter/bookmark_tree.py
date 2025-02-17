"""
Tree widget for displaying and managing PDF bookmarks with drag-drop support.
"""

import logging
from typing import Optional, Dict, Any
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import (
    QTreeWidget, QTreeWidgetItem, QMenu,
    QInputDialog, QMessageBox
)

from .bookmark_manager import BookmarkNode, BookmarkLevel, BookmarkError

logger = logging.getLogger(__name__)

class BookmarkTreeItem(QTreeWidgetItem):
    """
    Tree widget item representing a bookmark.
    
    This class maintains a reference to the actual BookmarkNode and
    provides methods for updating the display.
    """
    
    def __init__(
        self,
        node: BookmarkNode,
        parent: Optional[QTreeWidgetItem] = None
    ) -> None:
        """
        Initialize the tree item.
        
        Args:
            node: The bookmark node this item represents
            parent: Optional parent tree item
        """
        super().__init__(parent)
        self.node = node
        self.update_display()
        
    def update_display(self) -> None:
        """Update the item's display text."""
        self.setText(0, self.node.title)
        self.setToolTip(0, f"Page {self.node.page}")

class BookmarkTreeWidget(QTreeWidget):
    """
    Tree widget for displaying and managing bookmarks.
    
    This widget provides a tree view of bookmarks with support for:
    - Drag and drop reorganization
    - Context menu operations
    - In-place editing
    """
    
    bookmark_added = pyqtSignal(BookmarkNode)
    bookmark_deleted = pyqtSignal(BookmarkNode)
    bookmark_moved = pyqtSignal(BookmarkNode, BookmarkNode)  # node, new_parent
    bookmark_edited = pyqtSignal(BookmarkNode)
    bookmark_clicked = pyqtSignal(BookmarkNode)
    
    def __init__(self, parent=None) -> None:
        """Initialize the tree widget."""
        super().__init__(parent)
        
        # Configure the tree widget
        self.setHeaderHidden(True)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setDragDropMode(QTreeWidget.DragDropMode.InternalMove)
        self.setSelectionMode(QTreeWidget.SelectionMode.SingleSelection)
        self.setExpandsOnDoubleClick(False)
        
        # Connect signals
        self.itemDoubleClicked.connect(self._handle_double_click)
        self.itemClicked.connect(self._handle_click)
        
        # Create context menu actions
        self._create_actions()
        
    def _create_actions(self) -> None:
        """Create context menu actions."""
        self.edit_action = QAction("Edit...", self)
        self.edit_action.triggered.connect(self._edit_current_item)
        
        self.delete_action = QAction("Delete", self)
        self.delete_action.triggered.connect(self._delete_current_item)
        
    def contextMenuEvent(self, event) -> None:
        """Show context menu for bookmark operations."""
        item = self.itemAt(event.pos())
        if not item:
            return
            
        menu = QMenu(self)
        menu.addAction(self.edit_action)
        menu.addAction(self.delete_action)
        menu.exec(event.globalPos())
        
    def dropEvent(self, event) -> None:
        """Handle bookmark drag-drop events."""
        # Get the source and target items
        source_item = self.currentItem()
        if not source_item:
            event.ignore()
            return
            
        target_item = self.itemAt(event.position().toPoint())
        if target_item is source_item:
            event.ignore()
            return
            
        # Determine drop position
        drop_indicator = self.dropIndicatorPosition()
        
        # Handle different drop positions
        if drop_indicator == QTreeWidget.DropIndicatorPosition.OnItem:
            # Drop as child
            new_parent = target_item
        elif drop_indicator in (
            QTreeWidget.DropIndicatorPosition.AboveItem,
            QTreeWidget.DropIndicatorPosition.BelowItem
        ):
            # Drop as sibling
            new_parent = target_item.parent() if target_item else None
        else:
            # Drop at root level
            new_parent = None
            
        try:
            # Convert tree items to bookmark nodes
            source_node = source_item.node
            new_parent_node = new_parent.node if new_parent else None
            
            # Emit signal for bookmark move
            self.bookmark_moved.emit(source_node, new_parent_node)
            
            # Let the base class handle the UI update
            super().dropEvent(event)
            
        except BookmarkError as e:
            QMessageBox.warning(self, "Cannot Move Bookmark", str(e))
            event.ignore()
            
    def _handle_double_click(self, item: QTreeWidgetItem, column: int) -> None:
        """Handle double-click events for editing."""
        if item and column == 0:
            self._edit_current_item()
            
    def _handle_click(self, item: QTreeWidgetItem, column: int) -> None:
        """Handle click events for navigation."""
        if item and column == 0:
            self.bookmark_clicked.emit(item.node)
            
    def _edit_current_item(self) -> None:
        """Edit the currently selected bookmark."""
        item = self.currentItem()
        if not item:
            return
            
        title, ok = QInputDialog.getText(
            self,
            "Edit Bookmark",
            "Enter new title:",
            text=item.node.title
        )
        
        if ok and title.strip():
            try:
                item.node.title = title.strip()
                item.update_display()
                self.bookmark_edited.emit(item.node)
            except BookmarkError as e:
                QMessageBox.warning(self, "Cannot Edit Bookmark", str(e))
                
    def _delete_current_item(self) -> None:
        """Delete the currently selected bookmark."""
        item = self.currentItem()
        if not item:
            return
            
        reply = QMessageBox.question(
            self,
            "Delete Bookmark",
            f"Delete bookmark '{item.node.title}' and its children?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.bookmark_deleted.emit(item.node)
            self.takeTopLevelItem(self.indexOfTopLevelItem(item))
            
    def update_from_manager(self, root_node: BookmarkNode) -> None:
        """
        Update the tree view from a bookmark manager.
        
        Args:
            root_node: The root bookmark node
        """
        self.clear()
        
        def add_node(node: BookmarkNode, parent_item: Optional[QTreeWidgetItem] = None):
            """Recursively add bookmark nodes to the tree."""
            if node.level == BookmarkLevel.ROOT:
                # Skip the root node itself, but add its children
                for child in node.children:
                    add_node(child)
            else:
                # Create tree item
                item = BookmarkTreeItem(node, parent_item)
                if not parent_item:
                    self.addTopLevelItem(item)
                    
                # Add children recursively
                for child in node.children:
                    add_node(child, item)
                    
        # Add all nodes
        add_node(root_node)
        
        # Expand all items
        self.expandAll() 
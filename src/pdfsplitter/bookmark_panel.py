"""
Bookmark panel for displaying and navigating PDF structure.
"""
import logging
from typing import Optional, List, Callable

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtWidgets import (
    QDockWidget, QWidget, QVBoxLayout, QTreeWidget, QTreeWidgetItem,
    QPushButton, QLabel, QStyle, QSizePolicy
)

from .bookmark_detection import BookmarkNode, BookmarkTree, PageRange

logger = logging.getLogger(__name__)

class BookmarkPanel(QDockWidget):
    """Dockable widget for displaying PDF bookmarks and chapter ranges."""
    
    # Signals
    page_selected = pyqtSignal(int)  # Emitted when a bookmark page is selected
    range_selected = pyqtSignal(int, int, str)  # Emitted when a chapter range is selected
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """Initialize the bookmark panel."""
        super().__init__("Bookmarks", parent)
        self.setAllowedAreas(
            Qt.DockWidgetArea.LeftDockWidgetArea |
            Qt.DockWidgetArea.RightDockWidgetArea
        )
        
        # Create main widget and layout
        self._main_widget = QWidget()
        self._layout = QVBoxLayout(self._main_widget)
        self._layout.setContentsMargins(8, 8, 8, 8)
        self._layout.setSpacing(8)
        
        # Add bookmark tree
        self._tree = QTreeWidget()
        self._tree.setHeaderLabels(["Title", "Page"])
        self._tree.setColumnWidth(0, 200)  # Title column width
        self._tree.itemClicked.connect(self._on_item_clicked)
        self._layout.addWidget(self._tree)
        
        # Add chapter ranges section
        ranges_label = QLabel("Detected Chapters")
        ranges_label.setStyleSheet("font-weight: bold;")
        self._layout.addWidget(ranges_label)
        
        self._ranges_tree = QTreeWidget()
        self._ranges_tree.setHeaderLabels(["Title", "Pages"])
        self._ranges_tree.setColumnWidth(0, 200)
        self._ranges_tree.itemClicked.connect(self._on_range_clicked)
        self._layout.addWidget(self._ranges_tree)
        
        # Add status label
        self._status_label = QLabel()
        self._status_label.setWordWrap(True)
        self._status_label.setSizePolicy(
            QSizePolicy.Policy.Preferred,
            QSizePolicy.Policy.Minimum
        )
        self._layout.addWidget(self._status_label)
        
        # Set main widget
        self.setWidget(self._main_widget)
        
        # Initialize state
        self._current_tree: Optional[BookmarkTree] = None
        self._update_status()
    
    def update_bookmarks(self, tree: Optional[BookmarkTree]) -> None:
        """
        Update the displayed bookmark structure.
        
        Args:
            tree: The bookmark tree to display, or None to clear
        """
        self._current_tree = tree
        self._tree.clear()
        self._ranges_tree.clear()
        
        if tree is None:
            self._update_status("No bookmarks found")
            return
        
        # Add bookmark nodes
        self._add_bookmark_nodes(tree.root, None)
        self._tree.expandAll()
        
        # Add chapter ranges
        self._add_chapter_ranges(tree.chapter_ranges)
        self._ranges_tree.expandAll()
        
        # Update status
        self._update_status(
            f"Found {len(tree.chapter_ranges)} chapters in {self._count_bookmarks(tree.root)} bookmarks"
        )
        
        logger.debug("Updated bookmark panel with %d ranges", len(tree.chapter_ranges))
    
    def _add_bookmark_nodes(
        self,
        node: BookmarkNode,
        parent: Optional[QTreeWidgetItem]
    ) -> None:
        """Add bookmark nodes to the tree widget recursively."""
        if node.title == "root":
            # Skip root node, add its children directly
            for child in node.children:
                self._add_bookmark_nodes(child, None)
            return
        
        # Create item
        item = QTreeWidgetItem(parent or self._tree)
        item.setText(0, node.title)
        item.setText(1, str(node.page + 1))  # Display 1-based page numbers
        item.setData(0, Qt.ItemDataRole.UserRole, node.page)  # Store 0-based page
        
        # Add icon based on level
        if node.level == 0:
            icon = self.style().standardIcon(QStyle.StandardPixmap.SP_FileIcon)
            item.setIcon(0, icon)
        
        # Add children
        for child in node.children:
            self._add_bookmark_nodes(child, item)
    
    def _add_chapter_ranges(self, ranges: List[PageRange]) -> None:
        """Add chapter ranges to the ranges tree."""
        for range_ in ranges:
            item = QTreeWidgetItem(self._ranges_tree)
            item.setText(0, range_.title)
            # Display 1-based page numbers
            item.setText(1, f"{range_.start + 1}-{range_.end + 1}")
            # Store 0-based page numbers
            item.setData(0, Qt.ItemDataRole.UserRole, (range_.start, range_.end))
    
    def _count_bookmarks(self, node: BookmarkNode) -> int:
        """Count total number of bookmarks in tree."""
        count = 0 if node.title == "root" else 1
        for child in node.children:
            count += self._count_bookmarks(child)
        return count
    
    def _update_status(self, message: str = "") -> None:
        """Update the status label."""
        self._status_label.setText(message)
        self._status_label.setVisible(bool(message))
    
    def _on_item_clicked(self, item: QTreeWidgetItem, column: int) -> None:
        """Handle bookmark item click."""
        page = item.data(0, Qt.ItemDataRole.UserRole)
        if page is not None:
            self.page_selected.emit(page)
            logger.debug("Selected bookmark page %d", page + 1)
    
    def _on_range_clicked(self, item: QTreeWidgetItem, column: int) -> None:
        """Handle chapter range item click."""
        range_data = item.data(0, Qt.ItemDataRole.UserRole)
        if isinstance(range_data, tuple):
            start, end = range_data
            title = item.text(0)
            self.range_selected.emit(start, end, title)
            logger.debug(
                "Selected chapter range %s (pages %d-%d)",
                title, start + 1, end + 1
            ) 
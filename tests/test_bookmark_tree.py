"""Unit tests for the bookmark tree widget components."""

import pytest
from PyQt6.QtCore import Qt, QPoint, QPointF, QMimeData
from PyQt6.QtGui import QDropEvent
from PyQt6.QtWidgets import QTreeWidgetItem, QMessageBox

from pdfsplitter.bookmark_tree import BookmarkTreeWidget, BookmarkTreeItem
from pdfsplitter.bookmark_manager import (
    BookmarkNode, BookmarkLevel, BookmarkError
)

@pytest.fixture
def root_node():
    """Create a sample bookmark hierarchy for testing."""
    root = BookmarkNode("", 1, BookmarkLevel.ROOT)
    
    # Add some bookmarks
    ch1 = BookmarkNode("Chapter 1", 1, BookmarkLevel.H1)
    ch2 = BookmarkNode("Chapter 2", 5, BookmarkLevel.H1)
    
    # Add sections to Chapter 1
    sec1 = BookmarkNode("Section 1.1", 2, BookmarkLevel.H2)
    sec2 = BookmarkNode("Section 1.2", 3, BookmarkLevel.H2)
    ch1.children.extend([sec1, sec2])
    
    root.children.extend([ch1, ch2])
    return root

@pytest.fixture
def tree_widget(qtbot):
    """Create a BookmarkTreeWidget instance for testing."""
    widget = BookmarkTreeWidget()
    qtbot.addWidget(widget)
    return widget

def test_bookmark_tree_item_init(root_node):
    """Test BookmarkTreeItem initialization."""
    # Create item for Chapter 1
    node = root_node.children[0]
    item = BookmarkTreeItem(node)
    
    assert item.node is node
    assert item.text(0) == "Chapter 1"
    assert item.toolTip(0) == "Page 1"

def test_bookmark_tree_widget_init(tree_widget):
    """Test BookmarkTreeWidget initialization."""
    # Check initial configuration
    assert tree_widget.isHeaderHidden()
    assert tree_widget.dragEnabled()
    assert tree_widget.acceptDrops()
    assert tree_widget.dragDropMode() == tree_widget.DragDropMode.InternalMove
    assert tree_widget.selectionMode() == tree_widget.SelectionMode.SingleSelection

def test_update_from_manager(tree_widget, root_node):
    """Test updating the tree from a bookmark hierarchy."""
    tree_widget.update_from_manager(root_node)
    
    # Check top level items
    assert tree_widget.topLevelItemCount() == 2
    
    # Check Chapter 1 and its children
    ch1_item = tree_widget.topLevelItem(0)
    assert ch1_item.text(0) == "Chapter 1"
    assert ch1_item.childCount() == 2
    assert ch1_item.child(0).text(0) == "Section 1.1"
    assert ch1_item.child(1).text(0) == "Section 1.2"
    
    # Check Chapter 2
    ch2_item = tree_widget.topLevelItem(1)
    assert ch2_item.text(0) == "Chapter 2"
    assert ch2_item.childCount() == 0

def test_edit_bookmark(qtbot, tree_widget, root_node, monkeypatch):
    """Test editing a bookmark."""
    tree_widget.update_from_manager(root_node)
    
    # Select Chapter 1
    ch1_item = tree_widget.topLevelItem(0)
    tree_widget.setCurrentItem(ch1_item)
    
    # Mock the input dialog
    monkeypatch.setattr(
        "PyQt6.QtWidgets.QInputDialog.getText",
        lambda *args, **kwargs: ("New Chapter Title", True)
    )
    
    # Setup signal spy
    with qtbot.waitSignal(tree_widget.bookmark_edited) as blocker:
        tree_widget._edit_current_item()
    
    # Verify changes
    assert ch1_item.text(0) == "New Chapter Title"
    assert blocker.args[0] is ch1_item.node
    assert ch1_item.node.title == "New Chapter Title"

def test_delete_bookmark(qtbot, tree_widget, root_node, monkeypatch):
    """Test deleting a bookmark."""
    tree_widget.update_from_manager(root_node)
    
    # Select Chapter 1
    ch1_item = tree_widget.topLevelItem(0)
    tree_widget.setCurrentItem(ch1_item)
    
    # Mock the question dialog
    monkeypatch.setattr(
        QMessageBox,
        "question",
        lambda *args, **kwargs: QMessageBox.StandardButton.Yes
    )
    
    # Setup signal spy
    with qtbot.waitSignal(tree_widget.bookmark_deleted) as blocker:
        tree_widget._delete_current_item()
    
    # Verify deletion
    assert tree_widget.topLevelItemCount() == 1
    assert blocker.args[0] is ch1_item.node
    assert tree_widget.topLevelItem(0).text(0) == "Chapter 2"

def test_move_bookmark(qtbot, tree_widget, root_node):
    """Test moving a bookmark via drag and drop."""
    tree_widget.update_from_manager(root_node)
    
    # Get items
    ch1_item = tree_widget.topLevelItem(0)
    sec1_item = ch1_item.child(0)
    ch2_item = tree_widget.topLevelItem(1)
    
    # Setup for drag-drop
    tree_widget.setCurrentItem(sec1_item)
    
    # Simulate drop on Chapter 2
    with qtbot.waitSignal(tree_widget.bookmark_moved) as blocker:
        # Create a proper drop event
        mime_data = QMimeData()
        drop_event = QDropEvent(
            QPointF(0, 0),  # pos
            Qt.DropAction.MoveAction,  # action
            mime_data,  # data
            Qt.MouseButton.NoButton,  # buttons
            Qt.KeyboardModifier.NoModifier  # modifiers
        )
        
        # Set target item
        tree_widget.itemAt = lambda *args: ch2_item
        tree_widget.dropIndicatorPosition = lambda: tree_widget.DropIndicatorPosition.OnItem
        
        # Process drop
        tree_widget.dropEvent(drop_event)
    
    # Verify move
    assert blocker.args[0] is sec1_item.node  # Source node
    assert blocker.args[1] is ch2_item.node  # New parent node

def test_bookmark_navigation(qtbot, tree_widget, root_node):
    """Test bookmark navigation via clicking."""
    tree_widget.update_from_manager(root_node)
    
    # Get Chapter 1
    ch1_item = tree_widget.topLevelItem(0)
    
    # Setup signal spy
    with qtbot.waitSignal(tree_widget.bookmark_clicked) as blocker:
        # Simulate click
        tree_widget.itemClicked.emit(ch1_item, 0)
    
    # Verify navigation
    assert blocker.args[0] is ch1_item.node 
"""
Tests for the bookmark tree widget.
"""
import sys
import pytest
from unittest.mock import MagicMock, patch
from PyQt6.QtWidgets import QApplication, QTreeWidget, QMessageBox
from PyQt6.QtCore import QPoint, QPointF, Qt, QMimeData
from PyQt6.QtGui import QDropEvent

from pdfsplitter.bookmark_tree import BookmarkTreeWidget, BookmarkTreeItem
from pdfsplitter.bookmark_manager import (
    BookmarkNode, BookmarkLevel, BookmarkError
)
from pdfsplitter.bookmark_validation import (
    BookmarkLevelValidator, DropPosition, ValidationResult
)

# Initialize Qt application for tests
app = QApplication.instance()
if not app:
    app = QApplication(sys.argv)

# Set a default timeout for all tests in this file to prevent hanging
@pytest.fixture(autouse=True)
def timeout_for_tests():
    """Add a timeout to all tests in this file."""
    pytest.mark.timeout(10)

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

def create_bookmark_node(title, page, level, parent=None):
    """Create a test bookmark node."""
    node = BookmarkNode(title, page, level)
    if parent:
        parent.children.append(node)
        node.parent = parent
    return node

def create_tree_widget_with_items():
    """Create a tree widget with test bookmark items."""
    tree = BookmarkTreeWidget()
    
    # Create root node
    root = BookmarkNode("", 1, BookmarkLevel.ROOT)
    
    # Create some test nodes
    node1 = create_bookmark_node("Chapter 1", 1, BookmarkLevel.H1, root)
    node2 = create_bookmark_node("Chapter 2", 10, BookmarkLevel.H1, root)
    node2_1 = create_bookmark_node("Section 2.1", 12, BookmarkLevel.H2, node2)
    node2_2 = create_bookmark_node("Section 2.2", 15, BookmarkLevel.H2, node2)
    node3 = create_bookmark_node("Chapter 3", 20, BookmarkLevel.H1, root)
    
    # Add items to tree
    tree.update_from_manager(root)
    
    return tree, root, node1, node2, node2_1, node2_2, node3

class TestBookmarkTreeWidget:
    """Tests for the BookmarkTreeWidget class."""
    
    def test_init(self):
        """Test widget initialization."""
        widget = BookmarkTreeWidget()
        assert widget.dragEnabled()
        assert widget.acceptDrops()
        
    def test_update_from_manager(self):
        """Test updating tree from a bookmark manager."""
        tree, root, *_ = create_tree_widget_with_items()
        
        # Check that items were added
        assert tree.topLevelItemCount() == 3  # 3 chapters at top level
        
        # Check second chapter's children
        chapter2_item = tree.topLevelItem(1)
        assert chapter2_item.text(0) == "Chapter 2"
        assert chapter2_item.childCount() == 2
    
    @pytest.mark.timeout(5)  # Add timeout to prevent hanging
    @patch('pdfsplitter.bookmark_tree.BookmarkLevelValidator')
    def test_drag_drop_valid(self, mock_validator_class):
        """Test drag and drop when validation passes."""
        # Set up mock validator with valid result
        mock_validator = MagicMock()
        mock_validator.validate_move.return_value = ValidationResult(
            valid=True,
            message="Valid move",
            level_change=0
        )
        mock_validator_class.return_value = mock_validator
        
        # Create test tree with items
        tree, root, node1, node2, node2_1, node2_2, node3 = create_tree_widget_with_items()
        
        # Create mock drop event with necessary properties
        mock_event = MagicMock()
        mock_event.position().toPoint.return_value = QPoint(10, 10)
        
        # Find item positions
        chapter1_item = tree.topLevelItem(0)
        chapter2_item = tree.topLevelItem(1)
        
        # Set up for drag-drop
        tree.setCurrentItem(chapter1_item)  # Dragging Chapter 1
        tree.itemAt = MagicMock(return_value=chapter2_item)  # Dropping onto Chapter 2
        
        # Mock the drop indicator position
        tree.dropIndicatorPosition = MagicMock(
            return_value=QTreeWidget.DropIndicatorPosition.OnItem
        )
        
        # Mock the super().dropEvent method to avoid actual UI operations
        with patch.object(QTreeWidget, 'dropEvent') as mock_super_drop:
            # Create a signal spy to check if signal was emitted
            signal_spy = MagicMock()
            tree.bookmark_moved.connect(signal_spy)
            
            # Perform the drop
            tree.dropEvent(mock_event)
            
            # Check validator was called with correct params
            mock_validator.validate_move.assert_called_once()
            
            # Check signal was emitted with correct params
            signal_spy.assert_called_once()
            call_args = signal_spy.call_args[0]
            assert call_args[0] == node1  # Source node
            assert call_args[1] == node2  # Target/new parent node
            assert call_args[2] == DropPosition.INSIDE  # Position
            assert call_args[3] == 0  # Level change
            
            # Check super().dropEvent was called
            mock_super_drop.assert_called_once()
            
            # Check event was accepted
            mock_event.acceptProposedAction.assert_called_once()
    
    @pytest.mark.timeout(5)  # Add timeout to prevent hanging
    @patch('pdfsplitter.bookmark_tree.BookmarkLevelValidator')
    @patch('pdfsplitter.bookmark_tree.QMessageBox')
    def test_drag_drop_invalid(self, mock_messagebox, mock_validator_class):
        """Test drag and drop when validation fails."""
        # Set up mock validator with invalid result
        mock_validator = MagicMock()
        mock_validator.validate_move.return_value = ValidationResult(
            valid=False,
            message="Invalid move - would violate page order",
            level_change=None
        )
        mock_validator_class.return_value = mock_validator
        
        # Create test tree with items
        tree, root, node1, node2, node2_1, node2_2, node3 = create_tree_widget_with_items()
        
        # Create mock drop event
        mock_event = MagicMock()
        mock_event.position().toPoint.return_value = QPoint(10, 10)
        
        # Find item positions
        chapter1_item = tree.topLevelItem(0)
        chapter2_item = tree.topLevelItem(1)
        
        # Set up for drag-drop
        tree.setCurrentItem(chapter1_item)  # Dragging Chapter 1
        tree.itemAt = MagicMock(return_value=chapter2_item)  # Dropping onto Chapter 2
        
        # Mock the drop indicator position
        tree.dropIndicatorPosition = MagicMock(
            return_value=QTreeWidget.DropIndicatorPosition.OnItem
        )
        
        # Create a signal spy to check if signal was emitted
        signal_spy = MagicMock()
        tree.bookmark_moved.connect(signal_spy)
        
        # Perform the drop
        tree.dropEvent(mock_event)
        
        # Check validator was called with correct params
        mock_validator.validate_move.assert_called_once()
        
        # Check signal was NOT emitted
        signal_spy.assert_not_called()
        
        # Check warning was shown
        mock_messagebox.warning.assert_called_once()
        
        # Check event was ignored
        mock_event.ignore.assert_called_once() 
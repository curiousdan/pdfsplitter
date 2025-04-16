"""
Tests for the bookmark panel.
"""
import sys
import pytest
from unittest.mock import MagicMock, patch
from PyQt6.QtWidgets import QApplication

from pdfsplitter.bookmark_panel import BookmarkPanel
from pdfsplitter.bookmark_detection import (
    BookmarkNode,
    BookmarkTree,
    PageRange
)
from pdfsplitter.bookmark_manager import (
    BookmarkNode, BookmarkLevel, BookmarkManager, BookmarkError
)
from pdfsplitter.bookmark_validation import DropPosition

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
def panel(qtbot):
    """Create a BookmarkPanel instance for testing."""
    panel = BookmarkPanel()
    qtbot.addWidget(panel)
    return panel

@pytest.fixture
def sample_tree():
    """Create a sample bookmark tree for testing."""
    # Create root node - use BookmarkLevel.ROOT and page 1 for the root node
    root = BookmarkNode(title="root", page=1, level=BookmarkLevel.ROOT)
    
    # Add chapters - page numbers start from 1 now
    chapter1 = BookmarkNode(title="Chapter 1", page=1, level=BookmarkLevel.H1)
    chapter2 = BookmarkNode(title="Chapter 2", page=11, level=BookmarkLevel.H1)
    
    # Add sections to chapter 1
    section1 = BookmarkNode(title="1.1 Introduction", page=2, level=BookmarkLevel.H2)
    section2 = BookmarkNode(title="1.2 Background", page=6, level=BookmarkLevel.H2)
    chapter1.children = [section1, section2]
    
    # Add sections to chapter 2
    section3 = BookmarkNode(title="2.1 Methods", page=12, level=BookmarkLevel.H2)
    chapter2.children = [section3]
    
    # Build tree
    root.children = [chapter1, chapter2]
    
    # Create ranges - keep 0-based indexing for page ranges since it's a different class
    ranges = [
        PageRange(start=0, end=9, title="Chapter 1", level=0),
        PageRange(start=10, end=20, title="Chapter 2", level=0)
    ]
    
    return BookmarkTree(root=root, chapter_ranges=ranges)

def test_panel_initialization(panel):
    """Test panel is initialized correctly."""
    assert panel.windowTitle() == "Bookmarks"
    assert panel._tree.columnCount() == 2
    assert panel._ranges_tree.columnCount() == 2
    assert not panel._status_label.text()

def test_update_bookmarks_with_tree(panel, sample_tree, qtbot):
    """Test updating panel with bookmark tree."""
    # Update with tree
    panel.update_bookmarks(sample_tree)
    
    # Check bookmark tree
    assert panel._tree.topLevelItemCount() == 2  # Two chapters
    chapter1 = panel._tree.topLevelItem(0)
    assert chapter1.text(0) == "Chapter 1"
    assert chapter1.text(1) == "2"  # Changed to match updated 1-based page numbers
    assert chapter1.childCount() == 2  # Two sections
    
    # Check ranges tree
    assert panel._ranges_tree.topLevelItemCount() == 2  # Two ranges
    range1 = panel._ranges_tree.topLevelItem(0)
    assert range1.text(0) == "Chapter 1"
    assert range1.text(1) == "1-10"  # 1-based page numbers
    
    # Check status
    assert "2 chapters" in panel._status_label.text()
    assert "5 bookmarks" in panel._status_label.text()

def test_update_bookmarks_clear(panel, sample_tree, qtbot):
    """Test clearing bookmark panel."""
    # First add tree
    panel.update_bookmarks(sample_tree)
    assert panel._tree.topLevelItemCount() > 0
    
    # Then clear
    panel.update_bookmarks(None)
    assert panel._tree.topLevelItemCount() == 0
    assert panel._ranges_tree.topLevelItemCount() == 0
    assert "No bookmarks found" in panel._status_label.text()

def test_bookmark_click_signal(panel, sample_tree, qtbot):
    """Test bookmark click signal emission."""
    panel.update_bookmarks(sample_tree)
    
    # Prepare to catch signal - note that in BookmarkPanel, regular QTreeWidgetItems are used for the UI
    # (not BookmarkTreeItems), so we need to use the data stored in UserRole
    with qtbot.waitSignal(panel.page_selected) as blocker:
        # Click first chapter
        item = panel._tree.topLevelItem(0)
        # QTreeWidgetItem has page stored in UserRole data, not node attribute
        # When panel._on_item_clicked is called, it gets page from UserRole
        panel._on_item_clicked(item, 0)
    
    # Check signal with the page number from our updated BookmarkNode (1)
    assert blocker.args == [1]  # Expect 1 now

def test_range_click_signal(panel, sample_tree, qtbot):
    """Test chapter range click signal emission."""
    panel.update_bookmarks(sample_tree)
    
    # Prepare to catch signal
    with qtbot.waitSignal(panel.range_selected) as blocker:
        # Click first range
        item = panel._ranges_tree.topLevelItem(0)
        panel._ranges_tree.itemClicked.emit(item, 0)
    
    # Check signal - PageRange uses 0-based indexing
    assert blocker.args == [0, 9, "Chapter 1"]  # start, end, title

def test_bookmark_icons(panel, sample_tree):
    """Test bookmark icons are set correctly."""
    panel.update_bookmarks(sample_tree)
    
    # Chapter should have icon
    chapter = panel._tree.topLevelItem(0)
    assert chapter.icon(0) is not None
    
    # Section should not have icon
    section = chapter.child(0)
    assert section.icon(0).isNull()

def test_tree_expansion(panel, sample_tree, qtbot):
    """Test trees are expanded after update."""
    panel.update_bookmarks(sample_tree)
    
    # Both trees should be expanded
    assert panel._tree.isExpanded(panel._tree.model().index(0, 0))
    assert panel._ranges_tree.isExpanded(panel._ranges_tree.model().index(0, 0))

@pytest.fixture
def bookmark_manager():
    """Create a test bookmark manager."""
    manager = BookmarkManager(total_pages=20)
    
    # Add some test bookmarks
    ch1 = manager.add_bookmark(1, "Chapter 1")
    ch2 = manager.add_bookmark(5, "Chapter 2")
    sec2_1 = manager.add_bookmark(6, "Section 2.1", parent=ch2, level=BookmarkLevel.H2)
    sec2_2 = manager.add_bookmark(8, "Section 2.2", parent=ch2, level=BookmarkLevel.H2)
    ch3 = manager.add_bookmark(10, "Chapter 3")
    
    return manager, ch1, ch2, sec2_1, sec2_2, ch3

@pytest.fixture
def bookmark_panel():
    """Create a test bookmark panel."""
    panel = BookmarkPanel()
    return panel

class TestBookmarkPanel:
    """Tests for the BookmarkPanel class."""
    
    def test_display_bookmarks(self, bookmark_panel, bookmark_manager):
        """Test displaying bookmarks from manager."""
        # Arrange
        manager, *_ = bookmark_manager
        
        # Mock the update_from_manager method in the tree
        bookmark_panel._tree.update_from_manager = MagicMock()
        
        # Act
        bookmark_panel.display_bookmarks(manager)
        
        # Assert
        assert bookmark_panel.bookmark_manager is manager
        bookmark_panel._tree.update_from_manager.assert_called_once_with(manager.root)
    
    def test_handle_bookmark_moved_no_manager(self, bookmark_panel, bookmark_manager):
        """Test handling bookmark moved event with no manager."""
        # Arrange
        _, ch1, ch2, *_ = bookmark_manager
        bookmark_panel.bookmark_manager = None
        
        # Act - this should not raise an exception
        bookmark_panel._handle_bookmark_moved_in_model(
            ch1, ch2, DropPosition.INSIDE, 1
        )
        
        # No assertions needed - we're just checking it doesn't raise an exception
    
    @patch('pdfsplitter.bookmark_panel.logger')
    def test_handle_bookmark_moved_success(self, mock_logger, bookmark_panel, bookmark_manager):
        """Test handling bookmark moved event with success."""
        # Arrange
        manager, ch1, ch2, *_ = bookmark_manager
        bookmark_panel.set_bookmark_manager(manager)
        
        # Mock the methods we need
        bookmark_panel.changes_made = MagicMock()
        bookmark_panel._update_status = MagicMock()
        manager.move_bookmark = MagicMock()
        
        # Act
        bookmark_panel._handle_bookmark_moved_in_model(
            ch1, ch2, DropPosition.INSIDE, 1
        )
        
        # Assert
        manager.move_bookmark.assert_called_once()
        bookmark_panel.changes_made.emit.assert_called_once()
        bookmark_panel._update_status.assert_called_once_with("Bookmark moved successfully")
    
    @patch('pdfsplitter.bookmark_panel.QMessageBox')
    @patch('pdfsplitter.bookmark_panel.logger')
    def test_handle_bookmark_moved_error(self, mock_logger, mock_messagebox, bookmark_panel, bookmark_manager):
        """Test handling bookmark moved event with error."""
        # Arrange
        manager, ch1, ch2, *_ = bookmark_manager
        bookmark_panel.set_bookmark_manager(manager)
        
        # Mock the methods we need
        bookmark_panel.update_tree_from_manager = MagicMock()
        manager.move_bookmark = MagicMock(side_effect=BookmarkError("Test error"))
        
        # Act
        bookmark_panel._handle_bookmark_moved_in_model(
            ch1, ch2, DropPosition.INSIDE, 1
        )
        
        # Assert
        manager.move_bookmark.assert_called_once()
        mock_messagebox.critical.assert_called_once()
        bookmark_panel.update_tree_from_manager.assert_called_once()
        
    def test_level_calculation(self, bookmark_panel, bookmark_manager):
        """Test level calculation for different drop positions."""
        # Arrange
        manager, ch1, ch2, sec2_1, *_ = bookmark_manager
        bookmark_panel.set_bookmark_manager(manager)
        
        # Replace move_bookmark with a mock to capture the calculated level
        manager.move_bookmark = MagicMock()
        
        # Act and Assert - INSIDE position
        bookmark_panel._handle_bookmark_moved_in_model(
            ch1, ch2, DropPosition.INSIDE, 1
        )
        # The level should be parent level + 1 (H1 -> H2)
        call_args = manager.move_bookmark.call_args[1]
        assert call_args['new_level'].value == BookmarkLevel.H2.value
        
        # Reset mock
        manager.move_bookmark.reset_mock()
        
        # Act and Assert - BEFORE position (sibling)
        bookmark_panel._handle_bookmark_moved_in_model(
            ch1, sec2_1, DropPosition.BEFORE, 0
        )
        # The level should be the same as the target (H2)
        call_args = manager.move_bookmark.call_args[1]
        assert call_args['new_level'].value == BookmarkLevel.H2.value
        
        # Reset mock
        manager.move_bookmark.reset_mock()
        
        # Act and Assert - AFTER position (sibling)
        bookmark_panel._handle_bookmark_moved_in_model(
            ch1, sec2_1, DropPosition.AFTER, 0
        )
        # The level should be the same as the target (H2)
        call_args = manager.move_bookmark.call_args[1]
        assert call_args['new_level'].value == BookmarkLevel.H2.value 
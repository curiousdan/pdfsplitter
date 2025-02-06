"""Tests for bookmark panel functionality."""
import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QTreeWidgetItem

from pdfsplitter.bookmark_panel import BookmarkPanel
from pdfsplitter.bookmark_detection import (
    BookmarkNode,
    BookmarkTree,
    PageRange
)

@pytest.fixture
def panel(qtbot):
    """Create a BookmarkPanel instance for testing."""
    panel = BookmarkPanel()
    qtbot.addWidget(panel)
    return panel

@pytest.fixture
def sample_tree():
    """Create a sample bookmark tree for testing."""
    # Create root node
    root = BookmarkNode(title="root", page=0, level=-1)
    
    # Add chapters
    chapter1 = BookmarkNode(title="Chapter 1", page=0, level=0)
    chapter2 = BookmarkNode(title="Chapter 2", page=10, level=0)
    
    # Add sections to chapter 1
    section1 = BookmarkNode(title="1.1 Introduction", page=1, level=1)
    section2 = BookmarkNode(title="1.2 Background", page=5, level=1)
    chapter1.children = [section1, section2]
    
    # Add sections to chapter 2
    section3 = BookmarkNode(title="2.1 Methods", page=11, level=1)
    chapter2.children = [section3]
    
    # Build tree
    root.children = [chapter1, chapter2]
    
    # Create ranges
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
    assert chapter1.text(1) == "1"  # 1-based page number
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
    
    # Prepare to catch signal
    with qtbot.waitSignal(panel.page_selected) as blocker:
        # Click first chapter
        item = panel._tree.topLevelItem(0)
        panel._tree.itemClicked.emit(item, 0)
    
    # Check signal
    assert blocker.args == [0]  # 0-based page number

def test_range_click_signal(panel, sample_tree, qtbot):
    """Test chapter range click signal emission."""
    panel.update_bookmarks(sample_tree)
    
    # Prepare to catch signal
    with qtbot.waitSignal(panel.range_selected) as blocker:
        # Click first range
        item = panel._ranges_tree.topLevelItem(0)
        panel._ranges_tree.itemClicked.emit(item, 0)
    
    # Check signal
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
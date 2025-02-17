"""Unit tests for the bookmark management functionality."""

import pytest
from pdfsplitter.bookmark_manager import (
    BookmarkManager,
    BookmarkNode,
    BookmarkLevel,
    BookmarkValidationError,
    BookmarkOperationError
)

@pytest.fixture
def manager():
    """Create a BookmarkManager instance for testing."""
    return BookmarkManager(total_pages=10)

def test_bookmark_node_validation():
    """Test that BookmarkNode validates its attributes."""
    # Valid bookmark
    node = BookmarkNode("Test", 1, BookmarkLevel.H1)
    assert node.title == "Test"
    assert node.page == 1
    assert node.level == BookmarkLevel.H1
    assert not node.modified
    assert node.parent is None
    assert node.children == []

    # Invalid title
    with pytest.raises(BookmarkValidationError):
        BookmarkNode("", 1, BookmarkLevel.H1)
    with pytest.raises(BookmarkValidationError):
        BookmarkNode("   ", 1, BookmarkLevel.H1)

    # Invalid page
    with pytest.raises(BookmarkValidationError):
        BookmarkNode("Test", 0, BookmarkLevel.H1)
    with pytest.raises(BookmarkValidationError):
        BookmarkNode("Test", -1, BookmarkLevel.H1)

def test_add_bookmark(manager):
    """Test adding bookmarks with validation."""
    # Add root level bookmark
    b1 = manager.add_bookmark(1, "Chapter 1")
    assert b1.title == "Chapter 1"
    assert b1.page == 1
    assert b1.level == BookmarkLevel.H1
    assert b1.parent is manager.root
    assert manager.modified

    # Add child bookmark
    b2 = manager.add_bookmark(2, "Section 1.1", parent=b1, level=BookmarkLevel.H2)
    assert b2.title == "Section 1.1"
    assert b2.page == 2
    assert b2.level == BookmarkLevel.H2
    assert b2.parent is b1
    assert b2 in b1.children

    # Invalid page number
    with pytest.raises(BookmarkValidationError):
        manager.add_bookmark(11, "Invalid Page")

    # Duplicate title at same level
    with pytest.raises(BookmarkValidationError):
        manager.add_bookmark(3, "Chapter 1")

def test_delete_bookmark(manager):
    """Test deleting bookmarks."""
    # Setup test bookmarks
    b1 = manager.add_bookmark(1, "Chapter 1")
    b2 = manager.add_bookmark(2, "Section 1.1", parent=b1)
    
    # Delete leaf bookmark
    manager.delete_bookmark(b2)
    assert b2 not in b1.children
    
    # Delete bookmark with children
    b3 = manager.add_bookmark(3, "Chapter 2")
    b4 = manager.add_bookmark(4, "Section 2.1", parent=b3)
    manager.delete_bookmark(b3)
    assert b3 not in manager.get_bookmarks()
    
    # Cannot delete root
    with pytest.raises(BookmarkOperationError):
        manager.delete_bookmark(manager.root)

def test_move_bookmark(manager):
    """Test moving bookmarks in the hierarchy."""
    # Setup test bookmarks
    b1 = manager.add_bookmark(1, "Chapter 1")
    b2 = manager.add_bookmark(2, "Section 1.1", parent=b1)
    b3 = manager.add_bookmark(3, "Chapter 2")
    
    # Move to new parent
    manager.move_bookmark(b2, b3)
    assert b2 not in b1.children
    assert b2 in b3.children
    assert b2.parent is b3
    
    # Move to root level
    manager.move_bookmark(b2, None)
    assert b2 in manager.root.children
    assert b2.parent is manager.root
    
    # Cannot move root
    with pytest.raises(BookmarkOperationError):
        manager.move_bookmark(manager.root, b1)
        
    # Cannot move to self
    with pytest.raises(BookmarkOperationError):
        manager.move_bookmark(b1, b1)
        
    # Cannot move to descendant
    b4 = manager.add_bookmark(4, "Section 1.2", parent=b1)
    with pytest.raises(BookmarkOperationError):
        manager.move_bookmark(b1, b4)

def test_bookmark_level_change(manager):
    """Test changing bookmark levels."""
    b1 = manager.add_bookmark(1, "Chapter 1", level=BookmarkLevel.H1)
    assert b1.level == BookmarkLevel.H1
    
    # Change level during move
    manager.move_bookmark(b1, None, new_level=BookmarkLevel.H2)
    assert b1.level == BookmarkLevel.H2

def test_modified_flag(manager):
    """Test that the modified flag is properly tracked."""
    assert not manager.modified
    
    b1 = manager.add_bookmark(1, "Chapter 1")
    assert manager.modified
    
    manager.clear_modified_flag()
    assert not manager.modified
    
    manager.delete_bookmark(b1)
    assert manager.modified

def test_get_bookmarks(manager):
    """Test retrieving all bookmarks."""
    # Empty initially
    assert manager.get_bookmarks() == []
    
    # Add some bookmarks
    b1 = manager.add_bookmark(1, "Chapter 1")
    b2 = manager.add_bookmark(2, "Chapter 2")
    
    bookmarks = manager.get_bookmarks()
    assert len(bookmarks) == 2
    assert b1 in bookmarks
    assert b2 in bookmarks
    
    # Verify we get a copy
    bookmarks.clear()
    assert len(manager.get_bookmarks()) == 2 
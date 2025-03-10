"""
Tests for bookmark validation components.
"""
import pytest
from pdfsplitter.bookmark_validation import (
    BookmarkLevelValidator,
    DropPosition,
    ValidationResult
)
from pdfsplitter.bookmark_manager import BookmarkNode, BookmarkLevel

@pytest.fixture
def validator():
    """Create a BookmarkLevelValidator instance."""
    return BookmarkLevelValidator()

@pytest.fixture
def bookmark_tree():
    """Create a sample bookmark tree for testing."""
    root = BookmarkNode("", 1, BookmarkLevel.ROOT)
    
    # Create chapters (level 1)
    ch1 = BookmarkNode("Chapter 1", 1, BookmarkLevel.H1)
    ch2 = BookmarkNode("Chapter 2", 5, BookmarkLevel.H1)
    ch1.parent = root
    ch2.parent = root
    root.children.extend([ch1, ch2])
    
    # Create sections under Chapter 1 (level 2)
    sec1 = BookmarkNode("Section 1.1", 2, BookmarkLevel.H2)
    sec2 = BookmarkNode("Section 1.2", 3, BookmarkLevel.H2)
    sec1.parent = ch1
    sec2.parent = ch1
    ch1.children.extend([sec1, sec2])
    
    # Create subsection under Section 1.1 (level 3)
    subsec = BookmarkNode("Section 1.1.1", 2, BookmarkLevel.H3)
    subsec.parent = sec1
    sec1.children.append(subsec)
    
    return root

def test_validate_move_root(validator, bookmark_tree):
    """Test that root bookmark cannot be moved."""
    target = bookmark_tree.children[0]
    result = validator.validate_move(bookmark_tree, target, DropPosition.BEFORE)
    assert not result.valid
    assert "root bookmark" in result.message

def test_validate_move_to_self(validator, bookmark_tree):
    """Test that bookmark cannot be moved to itself."""
    source = bookmark_tree.children[0]
    result = validator.validate_move(source, source, DropPosition.BEFORE)
    assert not result.valid
    assert "to itself" in result.message

def test_validate_move_to_descendant(validator, bookmark_tree):
    """Test that bookmark cannot be moved to its descendant."""
    ch1 = bookmark_tree.children[0]
    sec1 = ch1.children[0]
    result = validator.validate_move(ch1, sec1, DropPosition.INSIDE)
    assert not result.valid
    assert "descendant" in result.message

def test_validate_level_increment_rules(validator, bookmark_tree):
    """Test PyMuPDF's level increment rules."""
    ch1 = bookmark_tree.children[0]  # Level 1
    sec1 = ch1.children[0]          # Level 2
    
    # Valid: Moving to level + 1
    result = validator.validate_move(sec1, ch1, DropPosition.INSIDE)
    assert result.valid
    assert result.level_change == 1
    
    # Invalid: Moving to level + 2
    deep_node = BookmarkNode("Deep", 10, BookmarkLevel.H4)  # Use page 10 to avoid page order issues
    result = validator.validate_move(deep_node, sec1, DropPosition.INSIDE)
    assert not result.valid
    assert "can only change by 1" in result.message

def test_validate_adjacent_level_rules(validator, bookmark_tree):
    """Test level rules between adjacent bookmarks."""
    ch1 = bookmark_tree.children[0]
    sec1 = ch1.children[0]
    sec2 = ch1.children[1]
    
    # Create a deeper bookmark with higher page number to avoid page order issues
    deep_node = BookmarkNode("Deep", 10, BookmarkLevel.H4)
    deep_node.parent = sec1
    sec1.children.append(deep_node)
    
    # Invalid: Too big level difference between adjacent bookmarks
    result = validator.validate_move(deep_node, sec1, DropPosition.BEFORE)
    assert not result.valid
    assert "can only change by 1" in result.message
    
    # Valid: Moving between bookmarks of same level
    result = validator.validate_move(sec2, sec1, DropPosition.BEFORE)
    assert result.valid
    assert result.level_change == 0

def test_validate_page_order_inside(validator, bookmark_tree):
    """Test page order validation when moving inside."""
    ch1 = bookmark_tree.children[0]
    sec1 = ch1.children[0]  # Page 2
    
    # Try to move to a chapter with existing bookmark on same page
    new_sec = BookmarkNode("New Section", 2, BookmarkLevel.H2)
    result = validator.validate_page_order(new_sec, ch1, DropPosition.INSIDE)
    assert not result.valid
    assert "same page" in result.message

def test_validate_page_order_between(validator, bookmark_tree):
    """Test page order validation when moving between siblings."""
    ch1 = bookmark_tree.children[0]  # Page 1
    ch2 = bookmark_tree.children[1]  # Page 5
    
    # Create a new chapter with page 3
    ch3 = BookmarkNode("Chapter 3", 3, BookmarkLevel.H1)
    ch3.parent = bookmark_tree
    bookmark_tree.children.append(ch3)
    
    # Valid moves
    result = validator.validate_page_order(ch3, ch2, DropPosition.BEFORE)
    assert result.valid
    
    # Invalid moves
    result = validator.validate_page_order(ch2, ch1, DropPosition.BEFORE)
    assert not result.valid
    assert "page order" in result.message

def test_validate_complex_hierarchy(validator, bookmark_tree):
    """Test validation with a more complex hierarchy."""
    ch1 = bookmark_tree.children[0]
    sec1 = ch1.children[0]
    
    # Create a multi-level structure with increasing page numbers
    level2 = BookmarkNode("Level 2", 10, BookmarkLevel.H2)
    level3 = BookmarkNode("Level 3", 11, BookmarkLevel.H3)
    level4 = BookmarkNode("Level 4", 12, BookmarkLevel.H4)
    
    # Test moving with valid level increments
    result = validator.validate_move(level2, ch1, DropPosition.INSIDE)
    assert result.valid
    assert result.level_change == 1
    
    # Test moving with invalid level increments
    result = validator.validate_move(level4, level2, DropPosition.INSIDE)
    assert not result.valid
    assert "can only change by 1" in result.message 
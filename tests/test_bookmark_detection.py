"""Tests for bookmark detection functionality."""
import pytest
from unittest.mock import Mock, patch

from pdfsplitter.bookmark_detection import (
    BookmarkNode,
    BookmarkTree,
    PageRange,
    BookmarkDetector,
    ChapterTitlePattern
)

@pytest.fixture
def detector():
    """Create a BookmarkDetector instance for testing."""
    return BookmarkDetector()

@pytest.fixture
def sample_bookmark():
    """Create a sample bookmark node for testing."""
    return BookmarkNode(
        title="Chapter 1: Introduction",
        page=0,
        level=0
    )

@pytest.fixture
def mock_doc():
    """Create a mock PDF document for testing."""
    doc = Mock()
    doc.get_toc.return_value = [
        # level, title, page
        [1, "Chapter 1: Introduction", 1],
        [2, "1.1 Background", 2],
        [1, "Chapter 2: Methods", 5],
        [2, "2.1 Approach", 6],
        [1, "Chapter 3: Results", 10]
    ]
    return doc

def test_page_range_validation():
    """Test page range validation."""
    # Valid range
    range1 = PageRange(start=0, end=5, title="Test", level=0)
    assert range1.start == 0
    assert range1.end == 5
    
    # Invalid ranges
    with pytest.raises(ValueError):
        PageRange(start=5, end=0, title="Test", level=0)
    
    with pytest.raises(ValueError):
        PageRange(start=-1, end=5, title="Test", level=0)
    
    with pytest.raises(ValueError):
        PageRange(start=0, end=5, title="Test", level=-1)

def test_chapter_title_pattern_matches(sample_bookmark):
    """Test chapter title pattern matching."""
    pattern = ChapterTitlePattern()
    
    # Test chapter keyword (level 0)
    assert pattern.matches(sample_bookmark)
    
    # Test section keyword (level 0)
    bookmark2 = BookmarkNode(title="Section 2", page=10, level=0)
    assert pattern.matches(bookmark2)
    
    # Test numbered pattern (level 0)
    bookmark3 = BookmarkNode(title="1 Details", page=5, level=0)
    assert pattern.matches(bookmark3)
    
    # Test letter pattern (level 0)
    bookmark4 = BookmarkNode(title="A. Overview", page=3, level=0)
    assert pattern.matches(bookmark4)
    
    # Test non-matching patterns
    assert not pattern.matches(  # Subsection (level > 0)
        BookmarkNode(title="1.2 Details", page=5, level=1)
    )
    assert not pattern.matches(  # No pattern match
        BookmarkNode(title="Introduction", page=0, level=0)
    )
    assert not pattern.matches(  # Subsection number
        BookmarkNode(title="1.1 Overview", page=0, level=0)
    )

def test_chapter_title_pattern_extract_range(sample_bookmark):
    """Test page range extraction from chapter pattern."""
    pattern = ChapterTitlePattern()
    
    # Test with next bookmark
    next_bookmark = BookmarkNode(title="Chapter 2", page=10, level=0)
    range1 = pattern.extract_range(sample_bookmark, next_bookmark)
    assert range1.start == 0
    assert range1.end == 9
    assert range1.title == "Chapter 1: Introduction"
    
    # Test without next bookmark (should use default chunk size)
    range2 = pattern.extract_range(sample_bookmark, None)
    assert range2.start == 0
    assert range2.end == 10  # Default chunk size is 10

def test_bookmark_detector_build_tree(detector, mock_doc):
    """Test building bookmark tree from document."""
    tree = detector._build_tree(mock_doc)
    
    # Check root
    assert tree.title == "root"
    assert tree.level == -1
    assert len(tree.children) == 3  # Three chapters
    
    # Check first chapter
    chapter1 = tree.children[0]
    assert chapter1.title == "Chapter 1: Introduction"
    assert chapter1.page == 0  # 0-based
    assert chapter1.level == 0
    assert len(chapter1.children) == 1  # One subsection
    
    # Check subsection
    subsection = chapter1.children[0]
    assert subsection.title == "1.1 Background"
    assert subsection.page == 1  # 0-based
    assert subsection.level == 1

def test_bookmark_detector_analyze_document(detector, mock_doc):
    """Test complete document analysis."""
    result = detector.analyze_document(mock_doc)
    
    # Check tree structure
    assert isinstance(result, BookmarkTree)
    assert len(result.root.children) == 3
    
    # Check detected ranges (only top-level chapters)
    assert len(result.chapter_ranges) == 3  # Three chapters
    
    # Check first range
    first_range = result.chapter_ranges[0]
    assert first_range.title == "Chapter 1: Introduction"
    assert first_range.start == 0
    assert first_range.end == 3  # Up to next chapter - 1
    
    # Check last range
    last_range = result.chapter_ranges[-1]
    assert last_range.title == "Chapter 3: Results"
    assert last_range.start == 9
    assert last_range.end == 19  # Default chunk size

def test_bookmark_detector_error_handling(detector):
    """Test error handling in bookmark detection."""
    # Mock document that raises error
    doc = Mock()
    doc.get_toc.side_effect = Exception("Failed to get bookmarks")
    
    # Should still return valid tree, just empty
    result = detector.analyze_document(doc)
    assert isinstance(result, BookmarkTree)
    assert len(result.root.children) == 0
    assert len(result.chapter_ranges) == 0

def test_bookmark_detector_add_pattern(detector):
    """Test adding custom pattern matcher."""
    # Create custom pattern
    custom_pattern = Mock()
    custom_pattern.matches.return_value = True
    custom_pattern.extract_range.return_value = PageRange(0, 5, "Test", 0)
    
    # Add pattern
    initial_count = len(detector._patterns)
    detector.add_pattern(custom_pattern)
    assert len(detector._patterns) == initial_count + 1
    
    # Test with mock document
    doc = Mock()
    doc.get_toc.return_value = [[1, "Test", 1]]
    
    result = detector.analyze_document(doc)
    assert len(result.chapter_ranges) == 1
    assert result.chapter_ranges[0].title == "Test" 
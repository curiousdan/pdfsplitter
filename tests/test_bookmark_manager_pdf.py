"""Unit tests for PDF bookmark loading and saving."""

import pytest
from pathlib import Path
import fitz

from pdfsplitter.bookmark_manager import (
    BookmarkManager,
    BookmarkLevel,
    BookmarkError,
    BookmarkSaveError
)

@pytest.fixture
def sample_pdf(tmp_path):
    """Create a sample PDF file for testing."""
    pdf_path = tmp_path / "test.pdf"
    doc = fitz.open()
    
    # Add some pages
    for _ in range(5):
        doc.new_page()
        
    # Add some bookmarks
    # Format: [level, title, page, ...]
    doc.set_toc([
        [1, "Chapter 1", 0],  # Level 1, page 1 (0-based)
        [2, "Section 1.1", 1],  # Level 2, page 2
        [2, "Section 1.2", 2],  # Level 2, page 3
        [1, "Chapter 2", 3],  # Level 1, page 4
    ])
    
    doc.save(str(pdf_path))
    doc.close()
    
    return pdf_path

@pytest.fixture
def invalid_pdf(tmp_path):
    """Create an invalid PDF file for testing."""
    pdf_path = tmp_path / "invalid.pdf"
    pdf_path.write_text("Not a PDF file")
    return pdf_path

def test_load_pdf_bookmarks(sample_pdf):
    """Test loading bookmarks from a PDF file."""
    manager = BookmarkManager.from_pdf(sample_pdf)
    
    # Check total pages
    assert manager.total_pages == 5
    
    # Check loaded bookmarks
    bookmarks = manager.get_bookmarks()
    assert len(bookmarks) == 2  # Two top-level chapters
    
    # Check Chapter 1
    ch1 = bookmarks[0]
    assert ch1.title == "Chapter 1"
    assert ch1.page == 2  # 2-based indexing for Chapter 1
    assert ch1.level == BookmarkLevel.H1
    assert len(ch1.children) == 2
    
    # Check Section 1.1
    sec1 = ch1.children[0]
    assert sec1.title == "Section 1.1"
    assert sec1.page == 2  # Same page as Chapter 1
    
    # Check Section 1.2
    sec2 = ch1.children[1]
    assert sec2.title == "Section 1.2"
    assert sec2.page == 3  # Next page
    
    # Check Chapter 2
    ch2 = bookmarks[1]
    assert ch2.title == "Chapter 2"
    assert ch2.page == 4  # Page 4
    assert ch2.level == BookmarkLevel.H1
    assert len(ch2.children) == 0
    
    # Check modified flag
    assert not manager.modified

def test_load_invalid_pdf(invalid_pdf):
    """Test loading bookmarks from an invalid PDF file."""
    with pytest.raises(BookmarkError) as exc_info:
        BookmarkManager.from_pdf(invalid_pdf)
    assert "Failed to read PDF bookmarks" in str(exc_info.value)

def test_save_pdf_bookmarks(sample_pdf, tmp_path):
    """Test saving bookmarks to a PDF file."""
    # Load initial bookmarks
    manager = BookmarkManager.from_pdf(sample_pdf)
    
    # Add a new bookmark
    manager.add_bookmark(1, "New Chapter", level=BookmarkLevel.H1)
    assert manager.modified
    
    # Save to a new file
    output_path = tmp_path / "output.pdf"
    manager.save_to_pdf(sample_pdf, output_path)
    assert not manager.modified
    
    # Load the saved file and verify bookmarks
    new_manager = BookmarkManager.from_pdf(output_path)
    bookmarks = new_manager.get_bookmarks()
    assert len(bookmarks) == 3
    assert bookmarks[2].title == "New Chapter"

def test_save_pdf_in_place(sample_pdf):
    """Test saving bookmarks back to the source PDF."""
    # Load initial bookmarks
    manager = BookmarkManager.from_pdf(sample_pdf)
    
    # Modify bookmarks
    ch1 = manager.get_bookmarks()[0]
    ch1.title = "Modified Chapter 1"
    manager._modified = True
    
    # Save in place
    manager.save_to_pdf(sample_pdf)
    assert not manager.modified
    
    # Load again and verify changes
    new_manager = BookmarkManager.from_pdf(sample_pdf)
    assert new_manager.get_bookmarks()[0].title == "Modified Chapter 1"

def test_save_to_invalid_path(sample_pdf, tmp_path):
    """Test saving bookmarks to an invalid path."""
    manager = BookmarkManager.from_pdf(sample_pdf)
    
    # Try to save to a non-existent directory
    invalid_path = tmp_path / "nonexistent" / "output.pdf"
    with pytest.raises(BookmarkSaveError) as exc_info:
        manager.save_to_pdf(sample_pdf, invalid_path)
    assert "Failed to save bookmarks" in str(exc_info.value)

def test_bookmark_to_pdf_outline():
    """Test converting BookmarkNode to PDF outline format."""
    # Create a bookmark hierarchy
    from pdfsplitter.bookmark_manager import BookmarkNode
    
    root = BookmarkNode("", 1, BookmarkLevel.ROOT)
    ch1 = BookmarkNode("Chapter 1", 1, BookmarkLevel.H1)
    sec1 = BookmarkNode("Section 1.1", 2, BookmarkLevel.H2)
    ch1.children.append(sec1)
    root.children.append(ch1)
    
    # Convert to outline
    outline = ch1.to_pdf_outline()
    
    # Verify structure
    assert outline[0] == [1, "Chapter 1", 0]  # Level 1, title, page 0 (0-based)
    assert outline[1] == [2, "Section 1.1", 1]  # Level 2, title, page 1 
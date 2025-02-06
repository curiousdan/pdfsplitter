"""
Tests for the PDFDocument class.
"""
from pathlib import Path
import pytest
from PyQt6.QtGui import QImage

from pdfsplitter.pdf_document import PDFDocument, PDFLoadError

@pytest.fixture
def sample_pdf(tmp_path):
    """Create a sample PDF file for testing."""
    import fitz
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)  # A4 size
    page.insert_text((72, 72), "Test PDF")
    pdf_path = tmp_path / "test.pdf"
    doc.save(str(pdf_path))
    doc.close()
    return pdf_path

@pytest.fixture
def large_pdf(tmp_path):
    """Create a large PDF file for testing size validation."""
    pdf_path = tmp_path / "large.pdf"
    # Create a file larger than MAX_FILE_SIZE
    with open(pdf_path, 'wb') as f:
        f.seek(PDFDocument.MAX_FILE_SIZE + 1)
        f.write(b'\0')
    return pdf_path

def test_load_valid_pdf(sample_pdf):
    """Test loading a valid PDF file."""
    doc = PDFDocument(sample_pdf)
    assert doc.get_page_count() == 1

def test_load_nonexistent_pdf():
    """Test loading a non-existent PDF file."""
    with pytest.raises(PDFLoadError, match="File not found"):
        PDFDocument(Path("nonexistent.pdf"))

def test_load_non_pdf_file(tmp_path):
    """Test loading a non-PDF file."""
    text_file = tmp_path / "test.txt"
    text_file.write_text("Not a PDF")
    with pytest.raises(PDFLoadError, match="Not a PDF file"):
        PDFDocument(text_file)

def test_load_large_pdf(large_pdf):
    """Test loading a PDF file that exceeds size limit."""
    with pytest.raises(PDFLoadError, match="File too large"):
        PDFDocument(large_pdf)

def test_generate_thumbnails(sample_pdf):
    """Test thumbnail generation."""
    doc = PDFDocument(sample_pdf)
    thumbnails = doc.generate_thumbnails()
    assert len(thumbnails) == 1
    assert isinstance(thumbnails[0], QImage)
    assert thumbnails[0].width() == 200
    assert thumbnails[0].height() == 300

def test_extract_pages(sample_pdf, tmp_path):
    """Test page extraction."""
    doc = PDFDocument(sample_pdf)
    output_path = tmp_path / "output.pdf"
    doc.extract_pages(0, 0, output_path)
    assert output_path.exists()
    
    # Verify extracted PDF
    extracted_doc = PDFDocument(output_path)
    assert extracted_doc.get_page_count() == 1

def test_extract_pages_invalid_range(sample_pdf, tmp_path):
    """Test page extraction with invalid page range."""
    doc = PDFDocument(sample_pdf)
    output_path = tmp_path / "output.pdf"
    
    with pytest.raises(ValueError, match="Invalid start page"):
        doc.extract_pages(-1, 0, output_path)
    
    with pytest.raises(ValueError, match="Invalid end page"):
        doc.extract_pages(0, 1, output_path)
    
    with pytest.raises(ValueError, match="Start page .* greater than end page"):
        doc.extract_pages(1, 0, output_path) 
"""
Shared test fixtures.
"""
import pytest

from pdfsplitter.pdf_document import PDFDocument

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
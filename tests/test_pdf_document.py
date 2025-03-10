"""
Tests for the PDFDocument class.

MIT License

Copyright (c) 2025 Daniel Park

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
"""
from pathlib import Path
import pytest
from PyQt6.QtGui import QImage
from unittest.mock import Mock, patch, MagicMock, call
from PyQt6.QtCore import QSize, Qt, QBuffer

from pdfsplitter.pdf_document import PDFDocument, PDFLoadError, PreviewGenerator, PreviewConfig

@pytest.fixture
def sample_pdf(tmp_path):
    """Create a sample PDF file for testing."""
    import fitz
    doc = fitz.open()
    # Create 5 pages
    for i in range(5):
        page = doc.new_page(width=595, height=842)  # A4 size
        page.insert_text((72, 72), f"Page {i+1}")
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

@pytest.fixture
def mock_doc():
    """Create a mock PDF document."""
    doc = Mock()
    doc.__len__ = Mock(return_value=10)  # 10 pages
    
    # Mock page with pixmap
    page = Mock()
    pixmap = Mock()
    pixmap.samples = bytes([0] * (100 * 100 * 3))  # RGB data
    pixmap.width = 100
    pixmap.height = 100
    pixmap.stride = 300  # 3 bytes per pixel
    page.get_pixmap.return_value = pixmap
    
    # Make all pages return the same mock page
    doc.__getitem__ = Mock(return_value=page)
    
    return doc

@pytest.fixture
def mock_pdf_path(tmp_path):
    """Create a mock PDF file."""
    pdf_path = tmp_path / "test.pdf"
    # Create a minimal valid PDF file
    with open(pdf_path, 'wb') as f:
        f.write(b"%PDF-1.4\n")
        f.write(b"1 0 obj\n<</Type/Catalog/Pages 2 0 R>>\nendobj\n")
        f.write(b"2 0 obj\n<</Type/Pages/Kids[3 0 R]/Count 1>>\nendobj\n")
        f.write(b"3 0 obj\n<</Type/Page/Parent 2 0 R/MediaBox[0 0 595 842]>>\nendobj\n")
        f.write(b"xref\n0 4\n0000000000 65535 f\n0000000010 00000 n\n0000000056 00000 n\n0000000111 00000 n\n")
        f.write(b"trailer\n<</Size 4/Root 1 0 R>>\nstartxref\n183\n%%EOF\n")
    return pdf_path

def test_load_valid_pdf(sample_pdf):
    """Test loading a valid PDF file."""
    doc = PDFDocument(sample_pdf)
    assert doc.get_page_count() == 5

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
    assert len(thumbnails) == 5
    assert isinstance(thumbnails[0], QImage)
    
    # Check that aspect ratio is preserved within tolerance
    original_width = 595  # A4 width in points
    original_height = 842  # A4 height in points
    original_aspect = original_height / original_width
    
    for thumb in thumbnails:
        thumb_aspect = thumb.height() / thumb.width()
        
        # Allow 1% tolerance in aspect ratio
        assert abs(thumb_aspect - original_aspect) / original_aspect < 0.01
        
        # Allow ±2 pixels variation in width
        target_width = 200
        assert abs(thumb.width() - target_width) <= 2

def test_extract_pages(sample_pdf, tmp_path):
    """Test page extraction."""
    doc = PDFDocument(sample_pdf)
    output_path = tmp_path / "output.pdf"
    doc.extract_pages(0, 0, output_path)
    assert output_path.exists()
    
    # Verify extracted PDF
    extracted_doc = PDFDocument(output_path)
    assert extracted_doc.get_page_count() == 5

def test_extract_pages_invalid_range(sample_pdf, tmp_path):
    """Test page extraction with invalid page range."""
    doc = PDFDocument(sample_pdf)
    output_path = tmp_path / "output.pdf"
    
    with pytest.raises(ValueError, match="Invalid start page"):
        doc.extract_pages(-1, 0, output_path)
    
    with pytest.raises(ValueError, match="Invalid end page"):
        doc.extract_pages(0, 6, output_path)
    
    with pytest.raises(ValueError, match="Start page .* greater than end page"):
        doc.extract_pages(1, 0, output_path)

def test_preview_generator_initialization(mock_doc):
    """Test preview generator initialization."""
    generator = PreviewGenerator(mock_doc)
    assert generator.doc == mock_doc

def test_preview_generation_basic(mock_doc):
    """Test basic preview generation."""
    generator = PreviewGenerator(mock_doc)
    preview = generator.generate_preview(0, (100, 100))
    
    assert isinstance(preview, QImage)
    assert preview.width() == 100
    assert preview.height() == 100

def test_preview_generation_grayscale(mock_doc):
    """Test grayscale preview generation."""
    generator = PreviewGenerator(mock_doc)
    preview = generator.generate_preview(0, (100, 100), grayscale=True)
    
    assert isinstance(preview, QImage)
    assert preview.format() == QImage.Format.Format_Grayscale8

def test_preview_generation_compression(mock_doc):
    """Test preview generation with compression."""
    page = mock_doc[0]
    pixmap = page.get_pixmap.return_value
    pixmap.samples = bytes([0] * (200 * 200 * 3))
    pixmap.width = 200
    pixmap.height = 200
    pixmap.stride = 200 * 3
    
    generator = PreviewGenerator(mock_doc)
    preview = generator.generate_preview(0, (200, 200), quality=25)
    
    # Verify we get a valid image back
    assert isinstance(preview, QImage)
    assert not preview.isNull()
    assert preview.width() > 0
    assert preview.height() > 0

def test_preview_generation_layer_error(mock_doc):
    """Test handling of layer configuration error."""
    page = mock_doc[0]
    # First call raises error, second succeeds
    page.get_pixmap.side_effect = [
        RuntimeError("No default Layer config"),
        page.get_pixmap.return_value
    ]
    
    generator = PreviewGenerator(mock_doc)
    preview = generator.generate_preview(0, (100, 100))
    
    assert isinstance(preview, QImage)
    # Should have retried with no_layers=True
    assert page.get_pixmap.call_count == 2
    assert page.get_pixmap.call_args_list[1].kwargs["no_layers"] == True

def test_preview_generation_other_error(mock_doc):
    """Test handling of other errors."""
    page = mock_doc[0]
    page.get_pixmap.side_effect = RuntimeError("Some other error")
    
    generator = PreviewGenerator(mock_doc)
    with pytest.raises(RuntimeError, match="Some other error"):
        generator.generate_preview(0, (100, 100))

def test_pdf_document_initialization(mock_pdf_path):
    """Test PDF document initialization."""
    doc = PDFDocument(mock_pdf_path)
    assert doc.file_path == mock_pdf_path
    assert doc._preview_cache is not None
    assert doc._preview_generator is not None

def test_pdf_document_invalid_file(tmp_path):
    """Test handling of invalid PDF file."""
    invalid_path = tmp_path / "invalid.pdf"
    with pytest.raises(PDFLoadError, match="File not found"):
        PDFDocument(invalid_path)

def test_pdf_document_preview_generation(mock_pdf_path):
    """Test PDF document preview generation."""
    with patch("pdfsplitter.pdf_document.fitz.open") as mock_open:
        # Set up mock document
        mock_doc = Mock()
        mock_doc.__len__ = Mock(return_value=10)
        mock_doc.__getitem__ = Mock(return_value=Mock())
        mock_open.return_value = mock_doc
        
        # Create a real QImage for caching tests
        mock_image = QImage(10, 10, QImage.Format.Format_RGB888)
        
        # Set up preview generator mock
        with patch("pdfsplitter.pdf_document.PreviewGenerator") as mock_generator:
            generator_instance = Mock()
            generator_instance.generate_preview.return_value = mock_image
            mock_generator.return_value = generator_instance
            
            doc = PDFDocument(mock_pdf_path)
            
            # Test configuration for different types of previews
            # Test thumbnail generation
            doc.generate_preview(0, is_thumbnail=True)
            doc._preview_cache.clear()  # Clear cache for next test
            
            # Test full preview generation
            doc.generate_preview(0, is_thumbnail=False)
            doc._preview_cache.clear()  # Clear cache for next test
            
            # Test custom size
            custom_size = (400, 600)
            doc.generate_preview(0, size=custom_size)
            doc._preview_cache.clear()  # Clear cache for next test
            
            # Verify all calls were made with correct configurations
            expected_calls = [
                call(0, PreviewConfig.THUMBNAIL_SIZE,
                     dpi=PreviewConfig.THUMBNAIL_DPI,
                     grayscale=PreviewConfig.USE_GRAYSCALE,
                     quality=PreviewConfig.JPEG_QUALITY),
                call(0, PreviewConfig.PREVIEW_SIZE,
                     dpi=PreviewConfig.PREVIEW_DPI,
                     grayscale=False,
                     quality=PreviewConfig.JPEG_QUALITY),
                call(0, custom_size,
                     dpi=PreviewConfig.PREVIEW_DPI,
                     grayscale=False,
                     quality=PreviewConfig.JPEG_QUALITY)
            ]
            generator_instance.generate_preview.assert_has_calls(expected_calls)
            
            # Test caching behavior in isolation
            doc._preview_cache.clear()  # Start with clean cache
            
            # First call should generate preview
            preview1 = doc.generate_preview(0)
            initial_call_count = generator_instance.generate_preview.call_count
            
            # Second call should return cached version
            preview2 = doc.generate_preview(0)
            assert generator_instance.generate_preview.call_count == initial_call_count  # No additional calls
            assert preview1 is preview2  # Should be same object from cache

def test_pdf_document_preview_validation(mock_pdf_path):
    """Test preview generation input validation."""
    with patch("pdfsplitter.pdf_document.fitz.open") as mock_open:
        mock_doc = Mock()
        mock_doc.__len__ = Mock(return_value=10)
        mock_open.return_value = mock_doc
        
        doc = PDFDocument(mock_pdf_path)
        
        # Test invalid page numbers
        with pytest.raises(ValueError, match="Invalid page number"):
            doc.generate_preview(-1)
        
        with pytest.raises(ValueError, match="Invalid page number"):
            doc.generate_preview(6)  # Beyond last page

def test_pdf_document_preview_error_handling(mock_pdf_path):
    """Test preview generation error handling."""
    with patch("pdfsplitter.pdf_document.fitz.open") as mock_open:
        mock_doc = Mock()
        mock_doc.__len__ = Mock(return_value=10)
        mock_open.return_value = mock_doc
        
        with patch("pdfsplitter.pdf_document.PreviewGenerator") as mock_generator:
            generator_instance = Mock()
            generator_instance.generate_preview.side_effect = RuntimeError("Preview generation failed")
            mock_generator.return_value = generator_instance
            
            doc = PDFDocument(mock_pdf_path)
            
            # Should wrap third-party errors in PDFLoadError
            with pytest.raises(PDFLoadError, match="Failed to generate preview for page"):
                doc.generate_preview(0)

def test_bookmark_ordering(sample_pdf):
    """Test that bookmarks are added in correct page order."""
    doc = PDFDocument(sample_pdf)
    
    # Add bookmarks in non-sequential order
    doc.add_bookmark("Chapter 5", 4)  # Page 5
    doc.add_bookmark("Chapter 1", 0)  # Page 1
    doc.add_bookmark("Chapter 3", 2)  # Page 3
    
    # Get the TOC and verify order
    toc = doc.doc.get_toc()
    
    # Filter top-level bookmarks and their pages
    top_level = [(title, page) for level, title, page in toc if level == 1]
    
    # Verify order by page number (TOC uses 1-based page numbers)
    assert top_level == [
        ("Chapter 1", 1),  # Page 1
        ("Chapter 3", 3),  # Page 3
        ("Chapter 5", 5),  # Page 5
    ], "Bookmarks should be ordered by page number"
    
    # Add a bookmark between existing ones
    doc.add_bookmark("Chapter 2", 1)  # Page 2
    
    # Get updated TOC and verify order
    toc = doc.doc.get_toc()
    top_level = [(title, page) for level, title, page in toc if level == 1]
    
    # Verify the new bookmark is inserted in the correct position (TOC uses 1-based page numbers)
    assert top_level == [
        ("Chapter 1", 1),  # Page 1
        ("Chapter 2", 2),  # Page 2
        ("Chapter 3", 3),  # Page 3
        ("Chapter 5", 5),  # Page 5
    ], "New bookmark should be inserted in correct page order" 
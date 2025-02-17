"""Integration and performance tests for the PDF Chapter Splitter."""
import time
import pytest
import psutil
import logging
from pathlib import Path
from unittest.mock import Mock, patch
from PyQt6.QtWidgets import QApplication
from PyQt6.QtTest import QTest
from PyQt6.QtCore import Qt, QThread

from pdfsplitter.main_window import MainWindow
from pdfsplitter.pdf_document import PDFDocument
from pdfsplitter.preview_cache import MemoryPressure
pytestmark = pytest.mark.skip(reason="Integration tests temporarily disabled")

# Increase timeouts for CI environments
LOAD_TIMEOUT = 5000  # 5 seconds
OPERATION_TIMEOUT = 2000  # 2 seconds

@pytest.fixture
def large_sample_pdf(tmp_path):
    """Create a large sample PDF for performance testing."""
    import fitz
    doc = fitz.open()
    for i in range(100):  # 100 pages
        page = doc.new_page(width=595, height=842)  # A4 size
        page.insert_text((72, 72), f"Page {i+1}")
        # Add some content to make it more realistic
        for j in range(10):
            page.insert_text(
                (72, 144 + j*20),
                "Lorem ipsum dolor sit amet, consectetur adipiscing elit."
            )
    pdf_path = tmp_path / "large_test.pdf"
    doc.save(str(pdf_path))
    doc.close()
    return pdf_path

@pytest.fixture
def app(qtbot):
    """Create QApplication instance."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app

@pytest.fixture
def main_window(app, qtbot):
    """Create MainWindow instance."""
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()
    return window

def test_end_to_end_workflow(main_window, large_sample_pdf, qtbot):
    """Test complete workflow from loading PDF to splitting chapters."""
    # 1. Load PDF
    with patch('PyQt6.QtWidgets.QFileDialog.getOpenFileName') as mock_dialog:
        mock_dialog.return_value = (str(large_sample_pdf), "PDF Files (*.pdf)")
        main_window._select_file()
    
    # Wait for thumbnails to generate
    qtbot.wait(LOAD_TIMEOUT)
    
    # 2. Verify PDF loaded
    assert main_window.pdf_doc is not None
    assert main_window.pdf_doc.get_page_count() == 100
    
    # 3. Add chapter ranges
    range_widget = main_window.range_widget
    
    # Add first chapter
    qtbot.keyClicks(range_widget.name_edit, "Chapter 1")
    range_widget.start_page.setValue(1)
    range_widget.end_page.setValue(10)
    qtbot.mouseClick(range_widget.add_button, Qt.MouseButton.LeftButton)
    
    # Add second chapter
    qtbot.keyClicks(range_widget.name_edit, "Chapter 2")
    range_widget.start_page.setValue(11)
    range_widget.end_page.setValue(20)
    qtbot.mouseClick(range_widget.add_button, Qt.MouseButton.LeftButton)
    
    # 4. Verify ranges added
    assert len(range_widget.ranges) == 2
    assert range_widget.range_list.count() == 2
    
    # 5. Split PDF
    output_dir = large_sample_pdf.parent
    with qtbot.waitSignal(range_widget.ranges_updated, timeout=OPERATION_TIMEOUT):
        qtbot.mouseClick(range_widget.split_button, Qt.MouseButton.LeftButton)
    
    # Wait for file operations to complete
    qtbot.wait(OPERATION_TIMEOUT)
    
    # 6. Verify output files
    assert (output_dir / "Chapter 1.pdf").exists()
    assert (output_dir / "Chapter 2.pdf").exists()
    
    # 7. Verify split files
    chapter1 = PDFDocument(output_dir / "Chapter 1.pdf")
    assert chapter1.get_page_count() == 10
    
    chapter2 = PDFDocument(output_dir / "Chapter 2.pdf")
    assert chapter2.get_page_count() == 10

def test_performance_preview_generation(large_sample_pdf):
    """Test performance of preview generation."""
    doc = PDFDocument(large_sample_pdf)
    
    # Measure time for first preview (cold start)
    start_time = time.time()
    preview1 = doc.generate_preview(0)
    cold_time = time.time() - start_time
    
    # Measure time for cached preview
    start_time = time.time()
    preview2 = doc.generate_preview(0)
    cache_time = time.time() - start_time
    
    # Verify performance
    assert cold_time < 2.0  # Cold generation should be under 2 seconds
    assert cache_time < 0.1  # Cached access should be under 100ms
    assert preview1 is preview2  # Should be same cached object

def test_memory_usage(large_sample_pdf):
    """Test memory usage during operations."""
    process = psutil.Process()
    initial_memory = process.memory_info().rss / 1024 / 1024  # MB
    
    doc = PDFDocument(large_sample_pdf)
    
    # Generate several previews
    for i in range(10):
        doc.generate_preview(i)
        
        # Check memory after each preview
        current_memory = process.memory_info().rss / 1024 / 1024
        memory_increase = current_memory - initial_memory
        
        # Memory should not increase more than 200MB per preview
        assert memory_increase < 200, f"Memory usage increased by {memory_increase}MB"
    
    # Clear cache
    doc._preview_cache.clear()
    
    # Force garbage collection
    import gc
    gc.collect()
    
    # Verify memory released (allow for some overhead)
    final_memory = process.memory_info().rss / 1024 / 1024
    assert (final_memory - initial_memory) < 100  # Should release most memory

def test_bookmark_detection_performance(large_sample_pdf):
    """Test performance of bookmark detection."""
    doc = PDFDocument(large_sample_pdf)
    
    # Measure time for bookmark analysis
    start_time = time.time()
    tree = doc.get_bookmark_tree()
    detection_time = time.time() - start_time
    
    # Verify performance
    assert detection_time < 1.0  # Should complete in under 1 second

def test_concurrent_operations(main_window, large_sample_pdf, qtbot):
    """Test handling of concurrent operations."""
    # Load PDF
    with patch('PyQt6.QtWidgets.QFileDialog.getOpenFileName') as mock_dialog:
        mock_dialog.return_value = (str(large_sample_pdf), "PDF Files (*.pdf)")
        main_window._select_file()
    
    # Wait for initial load
    qtbot.wait(LOAD_TIMEOUT)
    
    # Simulate rapid preview requests
    for i in range(5):
        main_window.pdf_doc.generate_preview(i)
        # Minimal wait to simulate rapid clicks
        qtbot.wait(50)
    
    # Verify no crashes or memory issues
    current_memory = psutil.Process().memory_info().rss / 1024 / 1024
    assert current_memory < 1024  # Should stay under 1GB

def test_memory_pressure_handling(large_sample_pdf):
    """Test handling of memory pressure situations."""
    doc = PDFDocument(large_sample_pdf)
    cache = doc._preview_cache
    
    # Mock high memory pressure
    with patch('pdfsplitter.preview_cache.MemoryPressure.get_pressure_level', return_value="high"):
        # Generate previews under pressure
        for i in range(5):
            doc.generate_preview(i)
            
            # Verify cache size is limited
            cache_size = len(cache._cache)
            assert cache_size <= cache._initial_size // 2
            
    # Return to normal pressure
    with patch('pdfsplitter.preview_cache.MemoryPressure.get_pressure_level', return_value="low"):
        # Generate more previews
        for i in range(5, 10):
            doc.generate_preview(i)
            
            # Verify cache can grow again
            cache_size = len(cache._cache)
            assert cache_size <= cache._initial_size * 2 
"""
Tests for the range management components.
"""
import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QMessageBox, QPushButton, QDialog, QFileDialog
from pathlib import Path
from PyQt6.QtTest import QTest
from typing import List, Tuple
import logging
from unittest.mock import Mock

from pdfsplitter.pdf_document import PDFDocument
from pdfsplitter.range_management import RangeManagementWidget

logger = logging.getLogger(__name__)

@pytest.fixture
def mock_dialog(monkeypatch):
    """Mock dialog to prevent popups during tests."""
    class MockDialog:
        def __init__(self, *args, **kwargs):
            pass
        def exec(self):
            return QDialog.DialogCode.Accepted
        def run_operation(self, worker):
            worker.operation(lambda value, message: None)
    
    monkeypatch.setattr("pdfsplitter.range_management.ProgressDialog", MockDialog)
    monkeypatch.setattr("pdfsplitter.main_window.ProgressDialog", MockDialog)
    monkeypatch.setattr(QMessageBox, "question", lambda *args: QMessageBox.StandardButton.Yes)
    monkeypatch.setattr(QMessageBox, "information", lambda *args: None)
    monkeypatch.setattr(QMessageBox, "critical", lambda *args: None)

@pytest.fixture
def mock_file_dialog(monkeypatch):
    """Mock file dialog to prevent popups during tests."""
    def mock_get_existing_directory(*args, **kwargs):
        return str(Path.home() / "test_output")
    
    monkeypatch.setattr("PyQt6.QtWidgets.QFileDialog.getExistingDirectory", mock_get_existing_directory)

@pytest.fixture
def range_widget(qtbot, mock_dialog, mock_file_dialog):
    """Create a RangeManagementWidget instance for testing."""
    widget = RangeManagementWidget()
    qtbot.addWidget(widget)
    return widget

def test_range_widget_initial_state(range_widget):
    """Test the initial state of the range management widget."""
    assert not range_widget.isEnabled()  # Should be disabled without PDF
    assert not range_widget.split_button.isEnabled()  # Split button should be disabled

def test_pdf_loading(range_widget, sample_pdf):
    """Test widget state after loading a PDF."""
    pdf_doc = PDFDocument(sample_pdf)
    range_widget.set_pdf_document(pdf_doc)
    
    assert range_widget.isEnabled()  # Widget should be enabled with PDF
    assert not range_widget.split_button.isEnabled()  # Split button should still be disabled until explicitly enabled

def test_split_button_state(range_widget, sample_pdf):
    """Test split button state management."""
    pdf_doc = PDFDocument(sample_pdf)
    range_widget.set_pdf_document(pdf_doc)
    
    # Initially disabled
    assert not range_widget.split_button.isEnabled()
    
    # Enable via the method
    range_widget.set_split_enabled(True)
    assert range_widget.split_button.isEnabled()
    
    # Disable via the method
    range_widget.set_split_enabled(False)
    assert not range_widget.split_button.isEnabled()

def test_split_pdf_operation(range_widget, qtbot, sample_pdf, tmp_path, monkeypatch):
    """Test PDF splitting operation with provided ranges."""
    pdf_doc = PDFDocument(sample_pdf)
    
    # Create a mock extract_pages method that creates empty files
    def mock_extract_pages(self, start, end, output_path, progress_callback=None):
        # Create an empty file at the output path
        output_path.touch()
        if progress_callback:
            progress_callback(100, "Complete!")
    
    # Apply mock
    monkeypatch.setattr(PDFDocument, "extract_pages", mock_extract_pages)
    
    # Set PDF document to widget
    range_widget.set_pdf_document(pdf_doc)
    
    # Create sample ranges
    sample_ranges = [
        ("Chapter 1", 0, 0),  # 0-based indices
        ("Chapter 2", 1, 1)
    ]
    
    # Enable the split button
    range_widget.set_split_enabled(True)
    
    # Create a test output directory
    test_output = tmp_path / "test_output"
    test_output.mkdir(exist_ok=True)
    
    # Mock the file dialog to return our test directory
    def mock_get_dir(*args, **kwargs):
        return str(test_output)
    
    monkeypatch.setattr(QFileDialog, "getExistingDirectory", mock_get_dir)
    
    # Mock the WorkerThread and ProgressDialog
    class MockWorker:
        def __init__(self):
            self.operation = None
            self.finished = Mock()
        
        def start(self):
            # Directly call the operation with a mock progress callback
            if self.operation:
                self.operation(lambda value, message: None)
    
    class MockDialog:
        def __init__(self, *args, **kwargs):
            pass
        
        def run_operation(self, worker):
            worker.start()
            worker.finished.emit()
    
    # Apply mocks
    monkeypatch.setattr("pdfsplitter.range_management.WorkerThread", MockWorker)
    monkeypatch.setattr("pdfsplitter.range_management.ProgressDialog", MockDialog)
    
    # Call the split method directly with the sample ranges
    range_widget._split_pdf(sample_ranges)
    
    # Verify the output files exist
    for name, _, _ in sample_ranges:
        output_path = test_output / f"{name}.pdf"
        assert output_path.exists(), f"Expected output file {output_path} does not exist" 
"""
Tests for the range management components.
"""
import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QMessageBox, QPushButton, QDialog
from pathlib import Path
from PyQt6.QtTest import QTest, QSignalSpy
import logging

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
def range_widget(qtbot, mock_dialog):
    """Create a RangeManagementWidget instance for testing."""
    widget = RangeManagementWidget()
    qtbot.addWidget(widget)
    return widget

def test_range_widget_initial_state(range_widget):
    """Test the initial state of the range management widget."""
    assert not range_widget.isEnabled()  # Should be disabled without PDF
    assert len(range_widget.ranges) == 0
    assert range_widget.range_list.count() == 0

def test_pdf_loading(range_widget, sample_pdf):
    """Test widget state after loading a PDF."""
    pdf_doc = PDFDocument(sample_pdf)
    range_widget.set_pdf_document(pdf_doc)
    
    assert range_widget.isEnabled()
    assert range_widget.start_page.value() == 1
    assert range_widget.end_page.value() == pdf_doc.get_page_count()
    assert not range_widget.add_button.isEnabled()  # No name entered

def test_add_valid_range(range_widget, qtbot, sample_pdf):
    """Test adding a valid chapter range."""
    pdf_doc = PDFDocument(sample_pdf)
    range_widget.set_pdf_document(pdf_doc)
    
    # Add a range
    range_widget.name_edit.setText("Chapter 1")
    range_widget.start_page.setValue(1)
    range_widget.end_page.setValue(1)
    QTest.qWait(100)
    
    assert range_widget.add_button.isEnabled()
    
    # Click add button
    qtbot.mouseClick(range_widget.add_button, Qt.MouseButton.LeftButton)
    
    # Verify the range was added
    assert len(range_widget.ranges) == 1
    assert range_widget.range_list.count() == 1
    name, start, end = range_widget.ranges[0]
    assert name == "Chapter 1"
    assert start == 0  # 0-based
    assert end == 0    # 0-based

def test_business_rules(range_widget, qtbot, sample_pdf):
    """Test business rule enforcement."""
    pdf_doc = PDFDocument(sample_pdf)
    range_widget.set_pdf_document(pdf_doc)
    
    # Test initial state (empty name)
    assert not range_widget.validate_input(), "Empty name should be invalid"
    assert not range_widget.add_button.isEnabled()
    
    # Test valid input
    range_widget.name_edit.setText("Chapter 1")
    range_widget.start_page.setValue(1)
    range_widget.end_page.setValue(1)
    QTest.qWait(100)  # Allow for event processing
    assert range_widget.validate_input(), "Valid input should pass validation"
    assert range_widget.add_button.isEnabled()
    
    # Add the range
    qtbot.mouseClick(range_widget.add_button, Qt.MouseButton.LeftButton)
    assert len(range_widget.ranges) == 1, "Range should be added"
    
    # Test duplicate name rejection
    range_widget.name_edit.setText("Chapter 1")
    range_widget.start_page.setValue(2)
    range_widget.end_page.setValue(2)
    QTest.qWait(100)  # Allow for event processing
    assert not range_widget.validate_input(), "Duplicate name should fail validation"
    assert not range_widget.add_button.isEnabled()
    
    # Test unique name acceptance
    range_widget.name_edit.setText("Chapter 2")
    range_widget.start_page.setValue(2)  # Ensure start page is set
    range_widget.end_page.setValue(2)    # Ensure end page is set
    QTest.qWait(100)  # Allow for event processing
    assert range_widget.validate_input(), "Unique name should pass validation"
    assert range_widget.add_button.isEnabled()

def test_range_removal(range_widget, qtbot, sample_pdf):
    """Test removing a chapter range."""
    pdf_doc = PDFDocument(sample_pdf)
    range_widget.set_pdf_document(pdf_doc)
    
    # Add a range
    range_widget.name_edit.setText("Chapter 1")
    range_widget.start_page.setValue(1)
    range_widget.end_page.setValue(1)
    QTest.qWait(100)
    qtbot.mouseClick(range_widget.add_button, Qt.MouseButton.LeftButton)
    
    # Select and remove the range
    range_widget.range_list.setCurrentRow(0)
    assert range_widget.remove_button.isEnabled()
    qtbot.mouseClick(range_widget.remove_button, Qt.MouseButton.LeftButton)
    
    # Verify the range was removed
    assert len(range_widget.ranges) == 0
    assert range_widget.range_list.count() == 0
    assert not range_widget.remove_button.isEnabled()
    assert not range_widget.split_button.isEnabled()

def test_split_button_state(range_widget, qtbot, sample_pdf):
    """Test split button state management."""
    pdf_doc = PDFDocument(sample_pdf)
    range_widget.set_pdf_document(pdf_doc)
    
    assert not range_widget.split_button.isEnabled()  # No ranges
    
    # Add a range
    range_widget.name_edit.setText("Chapter 1")
    range_widget.start_page.setValue(1)
    range_widget.end_page.setValue(1)
    QTest.qWait(100)
    qtbot.mouseClick(range_widget.add_button, Qt.MouseButton.LeftButton)
    
    assert range_widget.split_button.isEnabled()  # Has ranges
    
    # Remove the range
    range_widget.range_list.setCurrentRow(0)
    qtbot.mouseClick(range_widget.remove_button, Qt.MouseButton.LeftButton)
    
    assert not range_widget.split_button.isEnabled()  # No ranges again

def test_split_pdf_operation(range_widget, qtbot, sample_pdf, tmp_path):
    """Test PDF splitting operation."""
    pdf_doc = PDFDocument(sample_pdf)
    range_widget.set_pdf_document(pdf_doc)
    
    # Add a range
    range_widget.name_edit.setText("Chapter 1")
    range_widget.start_page.setValue(1)
    range_widget.end_page.setValue(1)
    QTest.qWait(100)
    qtbot.mouseClick(range_widget.add_button, Qt.MouseButton.LeftButton)
    
    # Split the PDF
    qtbot.mouseClick(range_widget.split_button, Qt.MouseButton.LeftButton)
    
    # Verify the output file exists
    output_path = Path(str(sample_pdf)).parent / "Chapter 1.pdf"
    assert output_path.exists()
    
    # Verify ranges are cleared after split
    assert len(range_widget.ranges) == 0
    assert range_widget.range_list.count() == 0
    assert not range_widget.split_button.isEnabled() 
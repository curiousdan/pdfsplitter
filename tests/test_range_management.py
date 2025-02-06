"""
Tests for the range management components.
"""
import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QMessageBox, QPushButton
from pathlib import Path

from pdfsplitter.pdf_document import PDFDocument
from pdfsplitter.range_management import ChapterRange, RangeManagementWidget

def test_chapter_range_validation():
    """Test chapter range validation."""
    # Valid range
    chapter = ChapterRange("Chapter 1", 0, 5)
    valid, _ = chapter.validate(10)
    assert valid
    
    # Empty name
    chapter = ChapterRange("", 0, 5)
    valid, error = chapter.validate(10)
    assert not valid
    assert "name cannot be empty" in error
    
    # Start page out of range
    chapter = ChapterRange("Chapter 1", -1, 5)
    valid, error = chapter.validate(10)
    assert not valid
    assert "Start page must be between" in error
    
    # End page out of range
    chapter = ChapterRange("Chapter 1", 0, 10)
    valid, error = chapter.validate(10)
    assert not valid
    assert "End page must be between" in error
    
    # Start > End
    chapter = ChapterRange("Chapter 1", 5, 3)
    valid, error = chapter.validate(10)
    assert not valid
    assert "Start page cannot be greater than end page" in error

def test_chapter_range_string_representation():
    """Test string representation of chapter ranges."""
    chapter = ChapterRange("Chapter 1", 0, 5)
    assert str(chapter) == "Chapter 1: Pages 1-6"  # Note: 1-based page numbers in display

@pytest.fixture
def range_widget(qtbot):
    """Create a RangeManagementWidget instance for testing."""
    widget = RangeManagementWidget()
    qtbot.addWidget(widget)
    return widget

def test_range_widget_initial_state(range_widget):
    """Test the initial state of the range management widget."""
    assert not range_widget.isEnabled()  # Should be disabled without PDF
    assert len(range_widget.ranges) == 0
    assert range_widget.range_list.count() == 0

def test_add_range(range_widget, qtbot, sample_pdf):
    """Test adding a chapter range."""
    # Set up the widget with a PDF
    pdf_doc = PDFDocument(sample_pdf)
    range_widget.set_pdf_document(pdf_doc)
    assert range_widget.isEnabled()
    
    # Add a range
    range_widget.name_edit.setText("Chapter 1")
    range_widget.start_page.setValue(1)
    range_widget.end_page.setValue(1)
    
    add_button = range_widget.findChild(QPushButton, "addRangeButton")
    qtbot.mouseClick(add_button, Qt.MouseButton.LeftButton)
    
    # Verify the range was added
    assert len(range_widget.ranges) == 1
    assert range_widget.range_list.count() == 1
    assert range_widget.ranges[0].name == "Chapter 1"
    assert range_widget.ranges[0].start_page == 0  # 0-based
    assert range_widget.ranges[0].end_page == 0    # 0-based

def test_remove_range(range_widget, qtbot, sample_pdf):
    """Test removing a chapter range."""
    # Set up the widget with a PDF and add a range
    pdf_doc = PDFDocument(sample_pdf)
    range_widget.set_pdf_document(pdf_doc)
    range_widget.name_edit.setText("Chapter 1")
    range_widget.start_page.setValue(1)
    range_widget.end_page.setValue(1)
    
    add_button = range_widget.findChild(QPushButton, "addRangeButton")
    qtbot.mouseClick(add_button, Qt.MouseButton.LeftButton)
    
    # Select and remove the range
    range_widget.range_list.setCurrentRow(0)
    remove_button = range_widget.findChild(QPushButton, "removeRangeButton")
    qtbot.mouseClick(remove_button, Qt.MouseButton.LeftButton)
    
    # Verify the range was removed
    assert len(range_widget.ranges) == 0
    assert range_widget.range_list.count() == 0

def test_split_pdf(range_widget, qtbot, sample_pdf, tmp_path):
    """Test splitting a PDF into chapters."""
    # Set up the widget with a PDF
    pdf_doc = PDFDocument(sample_pdf)
    range_widget.set_pdf_document(pdf_doc)
    
    # Add a range
    range_widget.name_edit.setText("Chapter 1")
    range_widget.start_page.setValue(1)
    range_widget.end_page.setValue(1)
    
    add_button = range_widget.findChild(QPushButton, "addRangeButton")
    qtbot.mouseClick(add_button, Qt.MouseButton.LeftButton)
    
    # Split the PDF
    split_button = range_widget.findChild(QPushButton, "splitPdfButton")
    qtbot.mouseClick(split_button, Qt.MouseButton.LeftButton)
    
    # Verify the output file exists
    output_path = Path(str(sample_pdf)).parent / "Chapter 1.pdf"
    assert output_path.exists()

def test_invalid_range(range_widget, qtbot, sample_pdf, monkeypatch):
    """Test adding an invalid range."""
    # Set up the widget with a PDF
    pdf_doc = PDFDocument(sample_pdf)
    range_widget.set_pdf_document(pdf_doc)
    
    # Mock the warning dialog
    warning_shown = False
    def mock_warning(*args, **kwargs):
        nonlocal warning_shown
        warning_shown = True
    monkeypatch.setattr(QMessageBox, "warning", mock_warning)
    
    # Try to add an invalid range (empty name)
    range_widget.name_edit.setText("")  # Empty name
    range_widget.start_page.setValue(1)
    range_widget.end_page.setValue(1)
    
    add_button = range_widget.findChild(QPushButton, "addRangeButton")
    qtbot.mouseClick(add_button, Qt.MouseButton.LeftButton)
    
    # Verify the range was not added and warning was shown
    assert warning_shown
    assert len(range_widget.ranges) == 0
    assert range_widget.range_list.count() == 0 
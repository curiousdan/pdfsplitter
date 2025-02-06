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
from tests.test_utils import (
    MockRangeWidget,
    MockSpinBox,
    ValidationState,
    create_mock_validator,
    assert_validation_state,
    assert_range_state
)

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

@pytest.fixture
def mock_widget():
    """Create a mock range management widget."""
    return MockRangeWidget()

@pytest.fixture
def mock_spinbox():
    """Create a mock spinbox."""
    return MockSpinBox()

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

def test_widget_initialization(mock_widget):
    """Test widget initialization."""
    assert mock_widget.validation_state.is_valid is False
    assert not mock_widget.ranges

def test_validation_change_signal(mock_widget):
    """Test validation change signal."""
    # Setup signal tracking
    validation_states = []
    mock_widget.validation_changed.connect(lambda state: validation_states.append(state))
    
    # Test validation changes
    mock_widget.simulate_validation_change(True)
    assert validation_states == [True]
    
    mock_widget.simulate_validation_change(False, "Error", ["name"])
    assert validation_states == [True, False]
    
    # Verify final state
    expected_state = ValidationState(False, "Error", ["name"])
    assert_validation_state(mock_widget, expected_state)

def test_range_addition(mock_widget):
    """Test range addition."""
    # Setup signal tracking
    added_ranges = []
    mock_widget.range_added.connect(lambda name, start, end: 
        added_ranges.append((name, start, end)))
    
    # Add ranges
    mock_widget.simulate_range_added("Chapter 1", 1, 10)
    mock_widget.simulate_range_added("Chapter 2", 11, 20)
    
    # Verify signals
    assert added_ranges == [
        ("Chapter 1", 1, 10),
        ("Chapter 2", 11, 20)
    ]
    
    # Verify state
    expected_ranges = [
        ("Chapter 1", 1, 10),
        ("Chapter 2", 11, 20)
    ]
    assert_range_state(mock_widget, expected_ranges)

def test_range_removal(mock_widget):
    """Test range removal."""
    # Setup initial ranges
    mock_widget.simulate_range_added("Chapter 1", 1, 10)
    mock_widget.simulate_range_added("Chapter 2", 11, 20)
    mock_widget.simulate_range_added("Chapter 3", 21, 30)
    
    # Setup signal tracking
    removed_indices = []
    mock_widget.range_removed.connect(lambda idx: removed_indices.append(idx))
    
    # Remove ranges
    mock_widget.simulate_range_removed(1)  # Remove Chapter 2
    assert removed_indices == [1]
    
    expected_ranges = [
        ("Chapter 1", 1, 10),
        ("Chapter 3", 21, 30)
    ]
    assert_range_state(mock_widget, expected_ranges)
    
    # Remove another range
    mock_widget.simulate_range_removed(0)  # Remove Chapter 1
    assert removed_indices == [1, 0]
    
    expected_ranges = [
        ("Chapter 3", 21, 30)
    ]
    assert_range_state(mock_widget, expected_ranges)

def test_spinbox_behavior(mock_spinbox):
    """Test spinbox behavior."""
    # Test initial state
    assert mock_spinbox.value() == 0
    assert not mock_spinbox.error_state
    assert mock_spinbox.error_message == ""
    
    # Test value changes
    values_changed = []
    mock_spinbox.value_changed.connect(lambda v: values_changed.append(v))
    
    mock_spinbox.setValue(50)
    assert mock_spinbox.value() == 50
    assert values_changed == [50]
    
    # Test bounds
    mock_spinbox.setMinimum(20)
    assert mock_spinbox.value() == 50  # Unchanged
    
    mock_spinbox.setValue(10)  # Below minimum
    assert mock_spinbox.value() == 20  # Clamped to minimum
    assert values_changed == [50, 20]
    
    mock_spinbox.setMaximum(40)
    assert mock_spinbox.value() == 20  # Unchanged
    
    mock_spinbox.setValue(60)  # Above maximum
    assert mock_spinbox.value() == 40  # Clamped to maximum
    assert values_changed == [50, 20, 40]

def test_validation_with_mock_validator(mock_widget):
    """Test validation using mock validator."""
    validator = create_mock_validator(
        name_valid=False,
        range_valid=True,
        name_error="Invalid name",
        range_error=""
    )
    
    # Simulate validation
    mock_widget.validate_input.return_value = False
    mock_widget.simulate_validation_change(
        False,
        "Invalid name",
        ["name"]
    )
    
    # Verify validation state
    expected_state = ValidationState(
        is_valid=False,
        error_message="Invalid name",
        error_fields=["name"]
    )
    assert_validation_state(mock_widget, expected_state)
    
    # Test with valid input
    validator = create_mock_validator(
        name_valid=True,
        range_valid=True
    )
    
    mock_widget.validate_input.return_value = True
    mock_widget.simulate_validation_change(True)
    
    expected_state = ValidationState(is_valid=True)
    assert_validation_state(mock_widget, expected_state)

def test_error_state_propagation(mock_widget):
    """Test error state propagation."""
    # Set error state
    mock_widget.simulate_validation_change(
        False,
        "Multiple errors",
        ["name", "start", "end"]
    )
    
    # Verify error state was set
    mock_widget.set_error_state.assert_called_once()
    
    # Verify validation state
    expected_state = ValidationState(
        is_valid=False,
        error_message="Multiple errors",
        error_fields=["name", "start", "end"]
    )
    assert_validation_state(mock_widget, expected_state)

def test_range_validation_integration(mock_widget):
    """Test range validation integration."""
    # Setup mock validator
    validator = create_mock_validator()
    
    # Test valid range addition
    mock_widget.validate_input.return_value = True
    mock_widget.simulate_range_added("Chapter 1", 1, 10)
    
    # Verify range was added
    expected_ranges = [("Chapter 1", 1, 10)]
    assert_range_state(mock_widget, expected_ranges)
    
    # Test invalid range addition
    mock_widget.validate_input.return_value = False
    mock_widget.simulate_validation_change(
        False,
        "Invalid range",
        ["start", "end"]
    )
    
    # Verify range was not added
    assert_range_state(mock_widget, expected_ranges)  # Still only one range
    
    # Verify error state
    expected_state = ValidationState(
        is_valid=False,
        error_message="Invalid range",
        error_fields=["start", "end"]
    )
    assert_validation_state(mock_widget, expected_state) 
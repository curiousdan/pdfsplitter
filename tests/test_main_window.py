"""
Tests for the main window and GUI components.
"""
import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QMessageBox, QToolBar

from pdfsplitter.main_window import MainWindow

@pytest.fixture
def main_window(qtbot):
    """Create a MainWindow instance for testing."""
    window = MainWindow()
    qtbot.addWidget(window)
    return window

def test_window_title(main_window):
    """Test the initial window title."""
    assert main_window.windowTitle() == "PDF Chapter Splitter"

def test_window_size(main_window):
    """Test the minimum window size."""
    assert main_window.minimumWidth() == 1000
    assert main_window.minimumHeight() == 700

def test_toolbar_creation(main_window):
    """Test that the toolbar is created correctly."""
    toolbar = main_window.findChild(QToolBar)
    assert toolbar is not None
    assert not toolbar.isMovable()
    
    # Check actions
    actions = toolbar.actions()
    assert len(actions) == 1
    assert actions[0].text() == "Open PDF..."

def test_open_pdf_dialog_cancel(main_window, qtbot, monkeypatch):
    """Test canceling the open PDF dialog."""
    # Mock the file dialog to return an empty string (cancel)
    monkeypatch.setattr(
        "PyQt6.QtWidgets.QFileDialog.getOpenFileName",
        lambda *args, **kwargs: ("", "")
    )
    
    # Click the Open PDF action
    main_window.open_action.trigger()
    
    # Verify that no PDF is loaded
    assert main_window.pdf_doc is None

def test_open_invalid_pdf(main_window, qtbot, monkeypatch, tmp_path):
    """Test opening an invalid PDF file."""
    # Create an invalid PDF file
    invalid_pdf = tmp_path / "invalid.pdf"
    invalid_pdf.write_text("Not a PDF file")
    
    # Mock the file dialog to return our invalid PDF
    monkeypatch.setattr(
        "PyQt6.QtWidgets.QFileDialog.getOpenFileName",
        lambda *args, **kwargs: (str(invalid_pdf), "")
    )
    
    # Mock the error dialog
    error_shown = False
    def mock_critical(*args, **kwargs):
        nonlocal error_shown
        error_shown = True
    monkeypatch.setattr(QMessageBox, "critical", mock_critical)
    
    # Try to open the invalid PDF
    main_window.open_action.trigger()
    
    # Verify error handling
    assert error_shown
    assert main_window.pdf_doc is None

def test_close_without_pdf(main_window, qtbot):
    """Test closing the window without a loaded PDF."""
    # Should close without confirmation
    assert main_window.close()

def test_close_with_pdf(main_window, qtbot, monkeypatch, sample_pdf):
    """Test closing the window with a loaded PDF."""
    # Load a PDF
    main_window.pdf_doc = sample_pdf
    
    # Mock the question dialog to return "No"
    monkeypatch.setattr(
        QMessageBox,
        "question",
        lambda *args, **kwargs: QMessageBox.StandardButton.No
    )
    
    # Try to close - should be prevented
    assert not main_window.close()
    
    # Mock the question dialog to return "Yes"
    monkeypatch.setattr(
        QMessageBox,
        "question",
        lambda *args, **kwargs: QMessageBox.StandardButton.Yes
    )
    
    # Try to close again - should succeed
    assert main_window.close() 
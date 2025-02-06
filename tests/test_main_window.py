"""
Tests for the main window and GUI components.
"""
import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QFileDialog, QMessageBox, QPushButton, QToolBar

from pdfsplitter.main_window import MainWindow, ThumbnailViewer

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
    assert main_window.minimumWidth() == 800
    assert main_window.minimumHeight() == 600

def test_thumbnail_viewer_creation(main_window):
    """Test that the thumbnail viewer is created correctly."""
    assert isinstance(main_window.thumbnail_viewer, ThumbnailViewer)
    assert main_window.thumbnail_viewer.minimumWidth() == 600
    assert main_window.thumbnail_viewer.minimumHeight() == 400
    assert main_window.thumbnail_viewer.objectName() == "thumbnailViewer"

def test_output_directory_initial_state(main_window):
    """Test the initial state of output directory selection."""
    assert main_window.output_dir is None
    assert main_window.output_dir_label.text() == "Output Directory: Not selected"

def test_open_pdf_dialog_cancel(main_window, qtbot, monkeypatch):
    """Test canceling the open PDF dialog."""
    # Mock the file dialog to return an empty string (cancel)
    monkeypatch.setattr(
        QFileDialog,
        "getOpenFileName",
        lambda *args, **kwargs: ("", "")
    )
    
    # Click the Open PDF action
    toolbar = main_window.findChild(QToolBar, "mainToolbar")
    for action in toolbar.actions():
        if action.objectName() == "openPdfAction":
            action.trigger()
            break
    
    # Verify that no PDF is loaded
    assert main_window.pdf_doc is None

def test_select_output_directory(main_window, qtbot, monkeypatch, tmp_path):
    """Test selecting an output directory."""
    # Mock the directory dialog
    monkeypatch.setattr(
        QFileDialog,
        "getExistingDirectory",
        lambda *args, **kwargs: str(tmp_path)
    )
    
    # Find and click the select directory button
    button = main_window.findChild(QPushButton, "selectOutputDirButton")
    qtbot.mouseClick(button, Qt.MouseButton.LeftButton)
    
    # Verify the output directory is set
    assert main_window.output_dir == tmp_path
    assert main_window.output_dir_label.text() == f"Output Directory: {tmp_path}"

def test_open_invalid_pdf(main_window, qtbot, monkeypatch, tmp_path):
    """Test opening an invalid PDF file."""
    # Create an invalid PDF file
    invalid_pdf = tmp_path / "invalid.pdf"
    invalid_pdf.write_text("Not a PDF file")
    
    # Mock the file dialog to return our invalid PDF
    monkeypatch.setattr(
        QFileDialog,
        "getOpenFileName",
        lambda *args, **kwargs: (str(invalid_pdf), "")
    )
    
    # Mock the error dialog
    error_shown = False
    def mock_critical(*args, **kwargs):
        nonlocal error_shown
        error_shown = True
    monkeypatch.setattr(QMessageBox, "critical", mock_critical)
    
    # Try to open the invalid PDF
    toolbar = main_window.findChild(QToolBar, "mainToolbar")
    for action in toolbar.actions():
        if action.objectName() == "openPdfAction":
            action.trigger()
            break
    
    # Verify error handling
    assert error_shown
    assert main_window.pdf_doc is None 
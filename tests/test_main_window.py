"""
Tests for the main window and GUI components.
"""
import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QMessageBox, QToolBar
from pathlib import Path
from PyQt6.QtGui import QCloseEvent

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
    assert len(actions) == 3  # Open PDF, Save, and Show Bookmarks actions
    assert actions[0].text() == "Open PDF..."
    assert actions[1].text() == "Save"
    assert actions[2].text() == "Show Bookmarks"
    
    # Verify bookmark action properties
    bookmark_action = actions[2]
    assert bookmark_action.isCheckable()
    assert bookmark_action.isChecked()  # Should be checked by default

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
    
    # Mock the PDFDocument constructor to raise an error
    error_msg = "Invalid PDF file format"
    def mock_pdf_init(self, path):
        self.file_path = Path(path)
        from pdfsplitter.pdf_document import PDFLoadError
        raise PDFLoadError(error_msg)
    
    from pdfsplitter.pdf_document import PDFDocument
    original_init = PDFDocument.__init__
    monkeypatch.setattr(PDFDocument, "__init__", mock_pdf_init)
    
    # Mock the error dialog
    error_shown = False
    def mock_critical(*args, **kwargs):
        nonlocal error_shown
        error_shown = True
    monkeypatch.setattr(QMessageBox, "critical", mock_critical)
    
    try:
        # Try to open the invalid PDF
        main_window.open_action.trigger()
        
        # Verify error handling
        assert error_shown
        assert main_window.pdf_doc is None
    finally:
        # Restore original
        monkeypatch.setattr(PDFDocument, "__init__", original_init)

def test_close_without_pdf(main_window, qtbot):
    """Test closing the window without a loaded PDF."""
    # Should close without confirmation
    assert main_window.close()

def test_close_with_pdf(main_window, qtbot, monkeypatch):
    """Test closing the window with a loaded PDF."""
    # Mock a PDF document with unsaved changes
    class MockPDFDocument:
        def __init__(self):
            self._unsaved_changes = True
        
        def has_unsaved_changes(self):
            return self._unsaved_changes
            
        def save_changes(self):
            self._unsaved_changes = False
    
    # Create and set the mock PDF
    mock_pdf = MockPDFDocument()
    main_window.pdf_doc = mock_pdf
    
    # Mock the range_widget to also report unsaved changes
    main_window.range_widget.has_unsaved_changes = lambda: False
    
    # Mock the question dialog to return Cancel
    def mock_question(*args, **kwargs):
        return QMessageBox.StandardButton.Cancel
    
    monkeypatch.setattr(QMessageBox, "question", mock_question)
    
    # Direct test of closeEvent - we need to bypass the normal close() method
    close_event = QCloseEvent()
    
    # First test - should be prevented (event accepted flag should be False)
    main_window.closeEvent(close_event)
    assert close_event.isAccepted() is False  # Event should not be accepted
    
    # Now mock the dialog to return Discard (to avoid the save path)
    def mock_question_discard(*args, **kwargs):
        return QMessageBox.StandardButton.Discard
    
    monkeypatch.setattr(QMessageBox, "question", mock_question_discard)
    
    # Create a new event and test again - should be accepted
    close_event_2 = QCloseEvent()
    main_window.closeEvent(close_event_2)
    assert close_event_2.isAccepted() is True  # Event should be accepted

def test_trigger_split_no_pdf(main_window, qtbot, monkeypatch):
    """Test triggering split without a PDF loaded."""
    # Mock the warning dialog
    warning_shown = False
    def mock_warning(*args, **kwargs):
        nonlocal warning_shown
        warning_shown = True
    monkeypatch.setattr(QMessageBox, "warning", mock_warning)
    
    # Trigger split
    main_window._trigger_split()
    
    # Verify warning was shown
    assert warning_shown

def test_get_chapter_ranges_no_pdf(main_window):
    """Test getting chapter ranges without a PDF loaded."""
    # No PDF loaded
    assert main_window._get_chapter_ranges_from_bookmarks() == []

def test_get_chapter_ranges_no_bookmarks(main_window, monkeypatch):
    """Test getting chapter ranges with no bookmarks."""
    # Mock PDF document with no bookmarks
    class MockPDF:
        def get_bookmark_tree(self):
            return None
        
        def has_unsaved_changes(self):
            return False
    
    main_window.pdf_doc = MockPDF()
    
    # Should return empty list
    assert main_window._get_chapter_ranges_from_bookmarks() == []

def test_get_chapter_ranges_with_bookmarks(main_window):
    """Test getting chapter ranges with bookmarks."""
    from pdfsplitter.bookmark_detection import BookmarkTree, PageRange
    
    # Create mock bookmark tree with chapter ranges
    class MockPageRange:
        def __init__(self, title, start, end):
            self.title = title
            self.start = start
            self.end = end
    
    class MockBookmarkTree:
        def __init__(self):
            self.chapter_ranges = [
                MockPageRange("Chapter 1", 0, 9),
                MockPageRange("Chapter 2", 10, 19)
            ]
    
    class MockPDF:
        def get_bookmark_tree(self):
            return MockBookmarkTree()
            
        def has_unsaved_changes(self):
            return False
    
    main_window.pdf_doc = MockPDF()
    
    # Get chapter ranges
    ranges = main_window._get_chapter_ranges_from_bookmarks()
    
    # Verify ranges
    assert len(ranges) == 2
    assert ranges[0] == ("Chapter 1", 0, 9)
    assert ranges[1] == ("Chapter 2", 10, 19)

def test_trigger_split_no_ranges(main_window, qtbot, monkeypatch):
    """Test triggering split with no chapter ranges."""
    # Mock PDF document with no bookmarks
    class MockPDF:
        def get_bookmark_tree(self):
            return None
            
        def has_unsaved_changes(self):
            return False
    
    main_window.pdf_doc = MockPDF()
    
    # Mock the warning dialog
    warning_shown = False
    def mock_warning(*args, **kwargs):
        nonlocal warning_shown
        warning_shown = True
    monkeypatch.setattr(QMessageBox, "warning", mock_warning)
    
    # Trigger split
    main_window._trigger_split()
    
    # Verify warning was shown
    assert warning_shown

def test_trigger_split_with_ranges(main_window, qtbot, monkeypatch):
    """Test triggering split with chapter ranges."""
    from pdfsplitter.bookmark_detection import BookmarkTree, PageRange
    
    # Create mock bookmark tree with chapter ranges
    class MockPageRange:
        def __init__(self, title, start, end):
            self.title = title
            self.start = start
            self.end = end
    
    class MockBookmarkTree:
        def __init__(self):
            self.chapter_ranges = [
                MockPageRange("Chapter 1", 0, 9),
                MockPageRange("Chapter 2", 10, 19)
            ]
    
    class MockPDF:
        def get_bookmark_tree(self):
            return MockBookmarkTree()
            
        def has_unsaved_changes(self):
            return False
    
    main_window.pdf_doc = MockPDF()
    
    # Mock the range widget's split method
    split_called = False
    ranges_passed = None
    def mock_split_pdf(ranges):
        nonlocal split_called, ranges_passed
        split_called = True
        ranges_passed = ranges
    
    main_window.range_widget._split_pdf = mock_split_pdf
    
    # Trigger split
    main_window._trigger_split()
    
    # Verify split was called with correct ranges
    assert split_called
    assert len(ranges_passed) == 2
    assert ranges_passed[0] == ("Chapter 1", 0, 9)
    assert ranges_passed[1] == ("Chapter 2", 10, 19) 
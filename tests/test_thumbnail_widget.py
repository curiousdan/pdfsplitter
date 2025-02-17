"""Unit tests for the thumbnail widget components."""

import pytest
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QImage, QContextMenuEvent
from PyQt6.QtWidgets import QFrame

from pdfsplitter.thumbnail_widget import ThumbnailLabel, ThumbnailWidget
from pdfsplitter.pdf_document import PDFDocument

class MockPDFDocument:
    """Mock PDFDocument for testing."""
    def __init__(self, num_pages: int = 3):
        self.num_pages = num_pages
        self.preview_calls = []

    def get_page_count(self) -> int:
        """Return the number of pages."""
        return self.num_pages

    def generate_preview(self, page_num: int, size: tuple[int, int], is_thumbnail: bool = False) -> QImage:
        """Mock preview generation."""
        self.preview_calls.append((page_num, size, is_thumbnail))
        return QImage(size[0], size[1], QImage.Format.Format_RGB32)

@pytest.fixture
def sample_image():
    """Create a sample QImage for testing."""
    return QImage(200, 300, QImage.Format.Format_RGB32)

@pytest.fixture
def thumbnail_label(qtbot, sample_image):
    """Create a ThumbnailLabel instance for testing."""
    label = ThumbnailLabel(1, sample_image)
    qtbot.addWidget(label)
    return label

@pytest.fixture
def thumbnail_widget(qtbot):
    """Create a ThumbnailWidget instance for testing."""
    widget = ThumbnailWidget()
    qtbot.addWidget(widget)
    return widget

@pytest.fixture
def mock_pdf():
    """Create a mock PDF document."""
    return MockPDFDocument()

def test_thumbnail_label_init(thumbnail_label):
    """Test ThumbnailLabel initialization."""
    assert thumbnail_label.page_number == 1
    assert not thumbnail_label.selected
    assert thumbnail_label.minimumSize().width() == 200
    assert thumbnail_label.minimumSize().height() == 300
    assert thumbnail_label.frameStyle() == QFrame.Shape.Box

def test_thumbnail_label_selection(thumbnail_label):
    """Test ThumbnailLabel selection state changes."""
    # Initial state
    assert not thumbnail_label.selected
    assert thumbnail_label.lineWidth() == 1
    
    # Select
    thumbnail_label.set_selected(True)
    assert thumbnail_label.selected
    assert thumbnail_label.lineWidth() == 2
    
    # Deselect
    thumbnail_label.set_selected(False)
    assert not thumbnail_label.selected
    assert thumbnail_label.lineWidth() == 1

def test_thumbnail_label_click(qtbot, thumbnail_label):
    """Test ThumbnailLabel click handling."""
    # Setup signal spy
    with qtbot.waitSignal(thumbnail_label.clicked) as blocker:
        # Simulate left click
        qtbot.mouseClick(thumbnail_label, Qt.MouseButton.LeftButton)
    
    # Verify signal
    assert blocker.args == [1]  # Page number

def test_thumbnail_label_context_menu(qtbot, thumbnail_label):
    """Test ThumbnailLabel context menu handling."""
    # Setup signal spy
    with qtbot.waitSignal(thumbnail_label.context_menu_requested) as blocker:
        # Create and post a context menu event
        pos = QPoint(10, 10)
        event = QContextMenuEvent(
            QContextMenuEvent.Reason.Mouse,
            pos,
            thumbnail_label.mapToGlobal(pos)
        )
        thumbnail_label.contextMenuEvent(event)
    
    # Verify signal
    assert blocker.args[0] == 1  # Page number
    assert isinstance(blocker.args[1], QPoint)  # Menu position

def test_thumbnail_widget_init(thumbnail_widget):
    """Test ThumbnailWidget initialization."""
    assert thumbnail_widget.thumbnails == []
    assert thumbnail_widget.selected_page is None
    assert thumbnail_widget._context_menu_handler is None
    assert thumbnail_widget._pdf_doc is None

def test_thumbnail_widget_set_pdf_document(qtbot, thumbnail_widget, mock_pdf):
    """Test setting PDF document in the widget."""
    # Set PDF document
    thumbnail_widget.set_pdf_document(mock_pdf)
    
    # Verify thumbnails
    assert len(thumbnail_widget.thumbnails) == 3
    for i, thumbnail in enumerate(thumbnail_widget.thumbnails, start=1):
        assert isinstance(thumbnail, ThumbnailLabel)
        assert thumbnail.page_number == i

def test_thumbnail_widget_selection(qtbot, thumbnail_widget, mock_pdf):
    """Test thumbnail selection in the widget."""
    # Set PDF document
    thumbnail_widget.set_pdf_document(mock_pdf)
    
    # Select page
    with qtbot.waitSignal(thumbnail_widget.page_selected):
        thumbnail_widget.thumbnails[0].clicked.emit(1)
    
    assert thumbnail_widget.selected_page == 1
    assert thumbnail_widget.thumbnails[0].selected
    assert not thumbnail_widget.thumbnails[1].selected
    
    # Change selection
    with qtbot.waitSignal(thumbnail_widget.page_selected):
        thumbnail_widget.thumbnails[1].clicked.emit(2)
    
    assert thumbnail_widget.selected_page == 2
    assert not thumbnail_widget.thumbnails[0].selected
    assert thumbnail_widget.thumbnails[1].selected

def test_thumbnail_widget_context_menu(qtbot, thumbnail_widget, mock_pdf):
    """Test context menu handling in the widget."""
    # Set PDF document
    thumbnail_widget.set_pdf_document(mock_pdf)
    
    # Setup context menu handler
    menu_called = False
    def handler(page: int, pos: QPoint):
        nonlocal menu_called
        menu_called = True
        assert page == 1
        assert isinstance(pos, QPoint)
    
    thumbnail_widget.set_context_menu_handler(handler)
    
    # Trigger context menu
    pos = QPoint(10, 10)
    thumbnail_widget.thumbnails[0].context_menu_requested.emit(1, pos)
    
    assert menu_called

def test_thumbnail_widget_clear(qtbot, thumbnail_widget, mock_pdf):
    """Test clearing thumbnails from the widget."""
    # Set PDF document
    thumbnail_widget.set_pdf_document(mock_pdf)
    assert len(thumbnail_widget.thumbnails) == 3
    
    # Select a page
    thumbnail_widget.set_selected_page(1)
    assert thumbnail_widget.selected_page == 1
    
    # Clear thumbnails
    thumbnail_widget.clear()
    assert thumbnail_widget.thumbnails == []
    assert thumbnail_widget.selected_page is None
    assert thumbnail_widget.content_layout.count() == 0

def test_thumbnail_widget_lazy_loading(qtbot, thumbnail_widget, mock_pdf):
    """Test lazy loading of thumbnails."""
    # Set PDF document
    thumbnail_widget.set_pdf_document(mock_pdf)
    
    # Initially, no thumbnails should be loaded since viewport is empty
    assert len(mock_pdf.preview_calls) == 0
    
    # Simulate viewport showing first two thumbnails
    thumbnail_widget._visible_range = (0, 1)
    thumbnail_widget._load_visible_thumbnails()
    
    # Should have loaded first two thumbnails
    assert len(mock_pdf.preview_calls) == 2
    assert all(call[2] for call in mock_pdf.preview_calls)  # All should be thumbnails
    assert all(0 <= call[0] <= 1 for call in mock_pdf.preview_calls)  # Pages 0-1
    
    # Clear preview calls to test further loading
    mock_pdf.preview_calls.clear()
    
    # Simulate scrolling to show last thumbnail
    thumbnail_widget._visible_range = (2, 2)
    thumbnail_widget._load_visible_thumbnails()
    
    # Should have loaded only the last thumbnail
    assert len(mock_pdf.preview_calls) == 1
    call = mock_pdf.preview_calls[0]
    assert call[2]  # Should be thumbnail
    assert call[0] == 2  # Last page 
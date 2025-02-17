"""Unit tests for the thumbnail widget components."""

import pytest
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QImage, QContextMenuEvent
from PyQt6.QtWidgets import QFrame

from pdfsplitter.thumbnail_widget import ThumbnailLabel, ThumbnailWidget

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

def test_thumbnail_widget_set_thumbnails(qtbot, thumbnail_widget, sample_image):
    """Test setting thumbnails in the widget."""
    # Add thumbnails
    images = [sample_image] * 3
    thumbnail_widget.set_thumbnails(images)
    
    # Verify thumbnails
    assert len(thumbnail_widget.thumbnails) == 3
    for i, thumbnail in enumerate(thumbnail_widget.thumbnails, start=1):
        assert isinstance(thumbnail, ThumbnailLabel)
        assert thumbnail.page_number == i

def test_thumbnail_widget_selection(qtbot, thumbnail_widget, sample_image):
    """Test thumbnail selection in the widget."""
    # Add thumbnails
    images = [sample_image] * 3
    thumbnail_widget.set_thumbnails(images)
    
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

def test_thumbnail_widget_context_menu(qtbot, thumbnail_widget, sample_image):
    """Test context menu handling in the widget."""
    # Add thumbnails
    images = [sample_image] * 3
    thumbnail_widget.set_thumbnails(images)
    
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

def test_thumbnail_widget_clear(qtbot, thumbnail_widget, sample_image):
    """Test clearing thumbnails from the widget."""
    # Add thumbnails
    images = [sample_image] * 3
    thumbnail_widget.set_thumbnails(images)
    assert len(thumbnail_widget.thumbnails) == 3
    
    # Select a page
    thumbnail_widget.set_selected_page(1)
    assert thumbnail_widget.selected_page == 1
    
    # Clear thumbnails
    thumbnail_widget.clear()
    assert thumbnail_widget.thumbnails == []
    assert thumbnail_widget.selected_page is None
    assert thumbnail_widget.content_layout.count() == 0 
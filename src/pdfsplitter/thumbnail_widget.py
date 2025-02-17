"""
Widget for displaying PDF page thumbnails with selection and context menu support.
"""

import logging
from typing import Optional, List, Callable
from PyQt6.QtCore import Qt, QSize, pyqtSignal
from PyQt6.QtGui import QImage, QPixmap, QContextMenuEvent
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QMenu, QScrollArea,
    QFrame
)

logger = logging.getLogger(__name__)

class ThumbnailLabel(QLabel):
    """
    Custom label for displaying a page thumbnail with selection support.
    
    This widget handles mouse events for selection and context menu.
    """
    
    clicked = pyqtSignal(int)  # Signal emitted when thumbnail is clicked
    context_menu_requested = pyqtSignal(int, 'QPoint')  # Signal for context menu
    
    def __init__(
        self,
        page_number: int,
        image: QImage,
        parent: Optional[QWidget] = None
    ) -> None:
        """
        Initialize the thumbnail label.
        
        Args:
            page_number: The page number this thumbnail represents (1-based)
            image: The thumbnail image to display
            parent: Optional parent widget
        """
        super().__init__(parent)
        self.page_number = page_number
        self.selected = False
        
        # Set up the widget
        self.setPixmap(QPixmap.fromImage(image))
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setFrameStyle(QFrame.Shape.Box)
        self.setLineWidth(1)
        self.setMinimumSize(QSize(200, 300))
        
        # Make the widget clickable
        self.setMouseTracking(True)
        
    def mousePressEvent(self, event):
        """Handle mouse press events for selection."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.page_number)
            event.accept()
        else:
            super().mousePressEvent(event)
            
    def contextMenuEvent(self, event: QContextMenuEvent):
        """Handle context menu events."""
        self.context_menu_requested.emit(self.page_number, event.globalPos())
        event.accept()
        
    def set_selected(self, selected: bool) -> None:
        """
        Set the selection state of the thumbnail.
        
        Args:
            selected: Whether the thumbnail should be selected
        """
        if self.selected != selected:
            self.selected = selected
            # Update visual style
            self.setFrameStyle(
                QFrame.Shape.Box | 
                (QFrame.Shape.Panel if selected else QFrame.Shape.NoFrame)
            )
            self.setLineWidth(2 if selected else 1)
            
class ThumbnailWidget(QWidget):
    """
    Widget for displaying a scrollable list of page thumbnails.
    
    This widget manages thumbnail display, selection, and context menus.
    """
    
    page_selected = pyqtSignal(int)  # Signal emitted when a page is selected
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """Initialize the thumbnail widget."""
        super().__init__(parent)
        
        self.thumbnails: List[ThumbnailLabel] = []
        self.selected_page: Optional[int] = None
        self._context_menu_handler: Optional[Callable[[int, 'QPoint'], None]] = None
        
        self._init_ui()
        
    def _init_ui(self) -> None:
        """Initialize the UI components."""
        # Create main layout
        layout = QVBoxLayout(self)
        layout.setSpacing(5)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create scroll area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # Create widget to hold thumbnails
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setSpacing(5)
        self.content_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        
        self.scroll_area.setWidget(self.content_widget)
        layout.addWidget(self.scroll_area)
        
    def set_thumbnails(self, images: List[QImage]) -> None:
        """
        Set the thumbnails to display.
        
        Args:
            images: List of thumbnail images to display
        """
        # Clear existing thumbnails
        self.clear()
        
        # Create new thumbnail labels
        for i, image in enumerate(images, start=1):
            thumbnail = ThumbnailLabel(i, image, self.content_widget)
            thumbnail.clicked.connect(self._handle_thumbnail_click)
            thumbnail.context_menu_requested.connect(self._handle_context_menu)
            self.content_layout.addWidget(thumbnail)
            self.thumbnails.append(thumbnail)
            
        logger.info("Updated thumbnails: %d pages", len(images))
        
    def clear(self) -> None:
        """Remove all thumbnails."""
        self.selected_page = None
        self.thumbnails.clear()
        
        # Remove all widgets from the layout
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
                
    def set_selected_page(self, page_number: Optional[int]) -> None:
        """
        Set the selected page.
        
        Args:
            page_number: The page number to select (1-based), or None to clear selection
        """
        # Clear old selection
        if self.selected_page and 1 <= self.selected_page <= len(self.thumbnails):
            self.thumbnails[self.selected_page - 1].set_selected(False)
            
        # Set new selection
        self.selected_page = page_number
        if page_number and 1 <= page_number <= len(self.thumbnails):
            self.thumbnails[page_number - 1].set_selected(True)
            
    def set_context_menu_handler(
        self,
        handler: Optional[Callable[[int, 'QPoint'], None]]
    ) -> None:
        """
        Set the handler for context menu requests.
        
        Args:
            handler: Callback function that takes page number and global position
        """
        self._context_menu_handler = handler
        
    def _handle_thumbnail_click(self, page_number: int) -> None:
        """Handle thumbnail click events."""
        self.set_selected_page(page_number)
        self.page_selected.emit(page_number)
        
    def _handle_context_menu(self, page_number: int, pos: 'QPoint') -> None:
        """Handle context menu requests."""
        if self._context_menu_handler:
            self._context_menu_handler(page_number, pos) 
"""
Widget for displaying PDF page thumbnails with selection and context menu support.
"""

import logging
from typing import Optional, List, Callable
from PyQt6.QtCore import Qt, QSize, pyqtSignal, QPoint
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
        
        # Set up selection style
        self.setStyleSheet("""
            QLabel {
                background-color: transparent;
                border: 1px solid #ccc;
                padding: 4px;
            }
            QLabel[selected="true"] {
                background-color: #0078d4;
                border: 2px solid #005a9e;
            }
        """)
        self.setProperty("selected", False)
        
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
            self.setProperty("selected", selected)
            self.style().polish(self)  # Force style update
            
class ThumbnailWidget(QWidget):
    """
    Widget for displaying a scrollable list of page thumbnails.
    
    This widget manages thumbnail display, selection, and context menus.
    Implements lazy loading for better performance with large PDFs.
    """
    
    page_selected = pyqtSignal(int)  # Signal emitted when a page is selected
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """Initialize the thumbnail widget."""
        super().__init__(parent)
        
        self.thumbnails: List[ThumbnailLabel] = []
        self.selected_page: Optional[int] = None
        self._context_menu_handler: Optional[Callable[[int, 'QPoint'], None]] = None
        self._pdf_doc: Optional['PDFDocument'] = None
        self._visible_range: tuple[int, int] = (0, 0)
        self._loaded_thumbnails: set[int] = set()
        
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
        
        # Connect scroll events for lazy loading
        self.scroll_area.verticalScrollBar().valueChanged.connect(self._handle_scroll)
        
    def set_pdf_document(self, pdf_doc: 'PDFDocument') -> None:
        """
        Set the PDF document and initialize placeholders.
        
        Args:
            pdf_doc: The PDF document to display thumbnails for
        """
        self._pdf_doc = pdf_doc
        self.clear()
        
        # Create placeholder labels
        for i in range(pdf_doc.get_page_count()):
            thumbnail = ThumbnailLabel(i + 1, self._create_placeholder_image(), self.content_widget)
            thumbnail.clicked.connect(self._handle_thumbnail_click)
            thumbnail.context_menu_requested.connect(self._handle_context_menu)
            self.content_layout.addWidget(thumbnail)
            self.thumbnails.append(thumbnail)
            
        logger.info("Initialized thumbnails: %d pages", pdf_doc.get_page_count())
        
    def _create_placeholder_image(self) -> QImage:
        """Create a placeholder image for thumbnails."""
        image = QImage(200, 300, QImage.Format.Format_RGB32)
        image.fill(Qt.GlobalColor.lightGray)
        return image
        
    def _handle_scroll(self, value: int) -> None:
        """Handle scroll events for lazy loading."""
        self._update_visible_thumbnails()
        
    def _update_visible_thumbnails(self) -> None:
        """Update thumbnails that are currently visible."""
        if not self._pdf_doc:
            return
            
        # Calculate visible range
        viewport = self.scroll_area.viewport()
        viewport_rect = viewport.rect()
        viewport_rect.moveTo(self.scroll_area.mapToGlobal(viewport.pos()))
        
        first_visible = -1
        last_visible = -1
        
        # Find visible thumbnails
        for i, thumbnail in enumerate(self.thumbnails):
            thumbnail_rect = thumbnail.rect()
            thumbnail_rect.moveTo(thumbnail.mapToGlobal(QPoint(0, 0)))
            
            if thumbnail_rect.intersects(viewport_rect):
                if first_visible == -1:
                    first_visible = i
                last_visible = i
                
        if first_visible == -1:
            # If no thumbnails are visible, use the current visible range
            first_visible, last_visible = self._visible_range
        
        # Add buffer for smoother scrolling
        buffer_size = 2
        first_visible = max(0, first_visible - buffer_size)
        last_visible = min(len(self.thumbnails) - 1, last_visible + buffer_size)
        
        # Update range if changed
        if (first_visible, last_visible) != self._visible_range:
            self._visible_range = (first_visible, last_visible)
            self._load_visible_thumbnails()
            
    def _load_visible_thumbnails(self) -> None:
        """Load thumbnails in the visible range."""
        if not self._pdf_doc:
            return
            
        first, last = self._visible_range
        for i in range(first, last + 1):
            if i not in self._loaded_thumbnails:
                # Load the actual thumbnail
                image = self._pdf_doc.generate_preview(
                    i,
                    size=(200, 300),
                    is_thumbnail=True
                )
                self.thumbnails[i].setPixmap(QPixmap.fromImage(image))
                self._loaded_thumbnails.add(i)
                
    def clear(self) -> None:
        """Remove all thumbnails."""
        self.selected_page = None
        self._visible_range = (0, 0)
        self._loaded_thumbnails.clear()
        
        # Remove all widgets from the layout
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
                
        self.thumbnails.clear()
        
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
            # Select the thumbnail
            thumbnail = self.thumbnails[page_number - 1]
            thumbnail.set_selected(True)
            
            # Scroll to make the thumbnail visible
            self.scroll_area.ensureWidgetVisible(thumbnail)
            
            # Emit signal for preview update
            self.page_selected.emit(page_number)
            
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
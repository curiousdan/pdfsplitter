"""
Main window for the PDF Chapter Splitter application.
"""
import logging
from pathlib import Path
from typing import Optional, List

from PyQt6.QtCore import Qt, QSize, pyqtSignal, QObject
from PyQt6.QtGui import QAction, QKeySequence, QPixmap, QImage
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QFileDialog, QScrollArea, QLabel,
    QMessageBox, QStyle, QToolBar, QStatusBar
)

from .pdf_document import PDFDocument, PDFLoadError
from .range_management import RangeManagementWidget
from .progress_dialog import ProgressDialog, WorkerThread

logger = logging.getLogger(__name__)

class ThumbnailGenerator(QObject):
    """Helper class to handle thumbnail generation in a thread-safe way."""
    thumbnails_ready = pyqtSignal(list)  # Signal emitting the list of thumbnails

    def __init__(self, pdf_doc: PDFDocument, size: tuple[int, int]) -> None:
        """Initialize the generator."""
        super().__init__()
        self.pdf_doc = pdf_doc
        self.size = size

    def generate(self, progress_callback) -> None:
        """Generate thumbnails and emit them."""
        thumbnails = self.pdf_doc.generate_thumbnails(self.size, progress_callback)
        self.thumbnails_ready.emit(thumbnails)

class MainWindow(QMainWindow):
    """Main window for the PDF Chapter Splitter application."""
    
    def __init__(self) -> None:
        """Initialize the main window."""
        super().__init__()
        
        self.pdf_doc: Optional[PDFDocument] = None
        self.thumbnail_size = (200, 300)
        self._current_page = 0
        
        self._init_ui()
        self._create_actions()
        self._create_toolbar()
        self._create_statusbar()
        
        # Set window properties
        self.setWindowTitle("PDF Chapter Splitter")
        self.setMinimumSize(1000, 700)
        self.setUnifiedTitleAndToolBarOnMac(True)
    
    def _init_ui(self) -> None:
        """Initialize the UI components."""
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Create horizontal layout for thumbnails and range management
        h_layout = QHBoxLayout()
        
        # Add scrollable thumbnail area
        thumbnail_group = QWidget()
        thumbnail_layout = QVBoxLayout(thumbnail_group)
        thumbnail_layout.setContentsMargins(0, 0, 0, 0)
        
        thumbnail_label = QLabel("Page Thumbnails")
        thumbnail_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        thumbnail_layout.addWidget(thumbnail_label)
        
        self.thumbnail_area = QScrollArea()
        self.thumbnail_area.setWidgetResizable(True)
        self.thumbnail_area.setMinimumWidth(300)
        self.thumbnail_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.thumbnail_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # Create widget to hold thumbnails
        self.thumbnail_widget = QWidget()
        self.thumbnail_layout = QVBoxLayout(self.thumbnail_widget)
        self.thumbnail_layout.setSpacing(5)
        self.thumbnail_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.thumbnail_area.setWidget(self.thumbnail_widget)
        
        # Connect scroll bar value change to update current page
        self.thumbnail_area.verticalScrollBar().valueChanged.connect(self._on_scroll)
        
        thumbnail_layout.addWidget(self.thumbnail_area)
        h_layout.addWidget(thumbnail_group)
        
        # Add range management widget
        self.range_widget = RangeManagementWidget()
        h_layout.addWidget(self.range_widget)
        
        # Set stretch factors
        h_layout.setStretch(0, 1)  # Thumbnail area
        h_layout.setStretch(1, 1)  # Range management
        
        layout.addLayout(h_layout)
    
    def _create_actions(self) -> None:
        """Create application actions."""
        # Open PDF action
        self.open_action = QAction("Open PDF...", self)
        self.open_action.setShortcut(QKeySequence.StandardKey.Open)
        self.open_action.setStatusTip("Open a PDF file")
        self.open_action.triggered.connect(self._select_file)
        self.open_action.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogOpenButton))
        
        # Exit action
        self.exit_action = QAction("Exit", self)
        self.exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        self.exit_action.setStatusTip("Exit application")
        self.exit_action.triggered.connect(self.close)
    
    def _create_toolbar(self) -> None:
        """Create application toolbar."""
        toolbar = QToolBar()
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(24, 24))
        toolbar.addAction(self.open_action)
        self.addToolBar(toolbar)
    
    def _create_statusbar(self) -> None:
        """Create application status bar."""
        status_bar = QStatusBar()
        self.setStatusBar(status_bar)
        status_bar.showMessage("Ready")
    
    def _update_thumbnails(self, thumbnails: List[QImage]) -> None:
        """Update thumbnail display with new thumbnails."""
        # Clear existing thumbnails
        for i in reversed(range(self.thumbnail_layout.count())):
            self.thumbnail_layout.itemAt(i).widget().setParent(None)
        
        # Add new thumbnails with labels
        for i, thumbnail in enumerate(thumbnails, 1):
            container = QWidget()
            container_layout = QVBoxLayout(container)
            container_layout.setContentsMargins(5, 5, 5, 5)
            container_layout.setSpacing(5)
            
            # Add thumbnail
            thumb_label = QLabel()
            pixmap = QPixmap.fromImage(thumbnail)
            thumb_label.setPixmap(pixmap)
            thumb_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            thumb_label.setStyleSheet("border: 1px solid #ccc; padding: 5px;")
            container_layout.addWidget(thumb_label)
            
            # Add page number
            page_label = QLabel(f"Page {i}")
            page_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            container_layout.addWidget(page_label)
            
            self.thumbnail_layout.addWidget(container)
    
    def _on_scroll(self, value: int) -> None:
        """Handle scroll events to update current page."""
        if not self.pdf_doc:
            return
            
        # Calculate current page based on scroll position
        viewport_height = self.thumbnail_area.viewport().height()
        content_height = self.thumbnail_widget.height()
        scroll_ratio = value / (content_height - viewport_height) if content_height > viewport_height else 0
        
        # Estimate current page
        total_pages = self.pdf_doc.get_page_count()
        current_page = int(scroll_ratio * (total_pages - 1))
        
        # Update if changed
        if current_page != self._current_page:
            self._current_page = current_page
            self.pdf_doc.update_current_page(current_page)
            logger.debug("Current page updated to %d", current_page)

    def _select_file(self) -> None:
        """Handle file selection."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select PDF File",
            str(Path.home()),
            "PDF Files (*.pdf)"
        )
        
        if not file_path:
            return
        
        try:
            # Load PDF document
            self.pdf_doc = PDFDocument(Path(file_path))
            self.statusBar().showMessage(f"Loaded PDF: {Path(file_path).name}")
            
            # Create thumbnail generator
            generator = ThumbnailGenerator(self.pdf_doc, self.thumbnail_size)
            generator.thumbnails_ready.connect(self._update_thumbnails)
            
            # Create worker thread
            worker = WorkerThread(generator.generate)
            
            # Show progress dialog
            dialog = ProgressDialog(
                "Generating Thumbnails",
                "Preparing to generate thumbnails...",
                parent=self
            )
            dialog.run_operation(worker)
            
            # Update range management widget
            self.range_widget.set_pdf_document(self.pdf_doc)
            
            # Update window title
            self.setWindowTitle(f"PDF Chapter Splitter - {Path(file_path).name}")
            
            logger.info("Successfully loaded PDF: %s", file_path)
        except PDFLoadError as e:
            self.statusBar().showMessage("Failed to load PDF")
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to load PDF: {str(e)}"
            )
            logger.error("Failed to load PDF: %s", str(e))
    
    def closeEvent(self, event) -> None:
        """Handle window close event."""
        if self.pdf_doc:
            reply = QMessageBox.question(
                self,
                "Exit Application",
                "Are you sure you want to exit?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                event.accept()
            else:
                event.ignore()
        else:
            event.accept() 
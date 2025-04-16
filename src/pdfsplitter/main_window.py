"""
Main window for the PDF Chapter Splitter application.
"""
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple, Callable

from PyQt6.QtCore import Qt, QSize, pyqtSignal, QObject, QPoint, QThread
from PyQt6.QtGui import QAction, QKeySequence, QPixmap, QImage, QIcon
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QFileDialog, QScrollArea, QLabel,
    QMessageBox, QStyle, QToolBar, QStatusBar, QInputDialog,
    QMenu, QDockWidget, QSplitter
)

from .pdf_document import PDFDocument, PDFLoadError
from .range_management import RangeManagementWidget
from .progress_dialog import ProgressDialog, WorkerThread
from .bookmark_panel import BookmarkPanel
from .thumbnail_widget import ThumbnailWidget
from .bookmark_detection import BookmarkTree, PageRange
from .bookmark_manager import BookmarkManager

logger = logging.getLogger(__name__)

class ThumbnailGenerator(QObject):
    """Helper class to handle thumbnail generation in a thread-safe way."""
    progress_updated = pyqtSignal(int, str)  # Signal for progress updates

    def __init__(self, pdf_doc: PDFDocument, size: tuple[int, int]) -> None:
        """Initialize the generator."""
        super().__init__()
        self.pdf_doc = pdf_doc
        self.size = size

    def generate(self, progress_callback) -> None:
        """
        Pre-load visible thumbnails and setup the PDF document.
        This prepares the thumbnail cache for faster display.
        """
        # Get the number of pages
        page_count = self.pdf_doc.get_page_count()
        
        # Generate first few thumbnails to improve initial load performance
        visible_page_count = min(10, page_count)
        for i in range(visible_page_count):
            # Pre-generate the first few thumbnails
            self.pdf_doc.generate_preview(
                i, 
                size=self.size, 
                is_thumbnail=True
            )
            
            # Update progress
            progress = int((i + 1) * 100 / visible_page_count)
            # Use the provided progress_callback directly
            progress_callback(
                progress, 
                f"Preparing thumbnails... ({i + 1}/{visible_page_count})"
            )

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
        
        # Create and add thumbnail widget
        self.thumbnail_widget = ThumbnailWidget()
        self.thumbnail_widget.setMinimumWidth(300)
        self.thumbnail_widget.page_selected.connect(self._on_thumbnail_selected)
        self.thumbnail_widget.set_context_menu_handler(self._handle_thumbnail_context_menu)
        thumbnail_layout.addWidget(self.thumbnail_widget)
        
        h_layout.addWidget(thumbnail_group)
        
        # Add range management widget
        self.range_widget = RangeManagementWidget()
        self.range_widget.split_button.clicked.connect(self._trigger_split)
        h_layout.addWidget(self.range_widget)
        
        # Set stretch factors
        h_layout.setStretch(0, 2)  # Thumbnail area (more space)
        h_layout.setStretch(1, 1)  # Range management (less space since we removed input fields)
        
        layout.addLayout(h_layout)
        
        # Create and add bookmark panel
        self.bookmark_panel = BookmarkPanel(self)
        self.bookmark_panel.page_selected.connect(self._on_bookmark_selected)
        self.bookmark_panel.range_selected.connect(self._on_range_selected)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.bookmark_panel)
    
    def _create_actions(self) -> None:
        """Create application actions."""
        # Open PDF action
        self.open_action = QAction("Open PDF...", self)
        self.open_action.setShortcut(QKeySequence.StandardKey.Open)
        self.open_action.setStatusTip("Open a PDF file")
        self.open_action.triggered.connect(self._select_file)
        self.open_action.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogOpenButton))
        
        # Save action
        self.save_action = QAction("Save", self)
        self.save_action.setShortcut(QKeySequence.StandardKey.Save)
        self.save_action.setStatusTip("Save changes")
        self.save_action.triggered.connect(self._save_changes)
        self.save_action.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogSaveButton))
        self.save_action.setEnabled(False)
        
        # Toggle bookmark panel action
        self.toggle_bookmarks_action = QAction("Show Bookmarks", self)
        self.toggle_bookmarks_action.setCheckable(True)
        self.toggle_bookmarks_action.setChecked(True)
        self.toggle_bookmarks_action.triggered.connect(self._toggle_bookmark_panel)
        self.toggle_bookmarks_action.setIcon(
            self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogDetailedView)
        )
        
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
        toolbar.addAction(self.save_action)
        toolbar.addAction(self.toggle_bookmarks_action)
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
    
    def _on_bookmark_selected(self, page: int) -> None:
        """Handle bookmark selection."""
        if not self.pdf_doc:
            return
            
        # Update thumbnail selection
        self.thumbnail_widget.set_selected_page(page + 1)  # Convert to 1-based
        
        # Update preview to show the selected page
        self.pdf_doc.update_current_page(page)
        
        # Update status
        self.statusBar().showMessage(f"Navigated to page {page + 1}")
        logger.debug("Selected page %d from bookmark", page + 1)
    
    def _on_range_selected(self, start: int, end: int, title: str) -> None:
        """Handle chapter range selection."""
        if not self.pdf_doc:
            return
            
        # Enable the split button when a range is selected
        self.range_widget.set_split_enabled(True)
        
        # Update status
        self.statusBar().showMessage(f"Selected chapter '{title}' (pages {start + 1}-{end + 1})")
        logger.debug("Selected range %s (pages %d-%d)", title, start + 1, end + 1)
    
    def _toggle_bookmark_panel(self, checked: bool) -> None:
        """Toggle bookmark panel visibility."""
        self.bookmark_panel.setVisible(checked)
        logger.debug("Bookmark panel visibility set to %s", checked)

    def _select_file(self) -> None:
        """Handle file selection action."""
        file_path = QFileDialog.getOpenFileName(
            self,
            "Select PDF File",
            str(Path.home()),
            "PDF Files (*.pdf)"
        )[0]
        
        if not file_path:
            return
            
        try:
            # Load PDF document
            self.pdf_doc = PDFDocument(file_path)
            
            # Update window title
            self.setWindowTitle(f"PDF Chapter Splitter - {Path(file_path).name}")
            
            # Initialize the thumbnail widget with the PDF document
            self.thumbnail_widget.set_pdf_document(self.pdf_doc)
            
            # Update thumbnail view with progress dialog
            dialog = ProgressDialog("Loading PDF", "Preparing thumbnails...", self)
            
            # Create thumbnail generator for initial thumbnail preparation
            generator = ThumbnailGenerator(self.pdf_doc, self.thumbnail_size)
            
            # Create worker thread for background processing
            worker = WorkerThread(generator.generate)
            dialog.run_operation(worker)
            
            # Update range widget and bookmark panel
            self.range_widget.set_pdf_document(self.pdf_doc)
            
            # Disable split button initially
            self.range_widget.set_split_enabled(False)
            
            # Create and initialize bookmark manager
            self.bookmark_manager = BookmarkManager.from_pdf(Path(file_path))
            
            # Display bookmarks using the manager
            self.bookmark_panel.display_bookmarks(self.bookmark_manager)
            
            # Connect changes_made signal to enable save
            self.bookmark_panel.changes_made.connect(self._on_bookmark_changes)
            
            # Update save action
            self.save_action.setEnabled(False)
            
            # Update status
            self.statusBar().showMessage(f"Loaded PDF with {self.pdf_doc.get_page_count()} pages")
            logger.info("Loaded PDF: %s", file_path)
            
        except PDFLoadError as e:
            QMessageBox.critical(
                self,
                "Error Loading PDF",
                f"Failed to load PDF: {str(e)}"
            )
            logger.error("Failed to load PDF: %s", str(e))
    
    def _save_changes(self) -> None:
        """Save changes to the PDF file."""
        if not self.pdf_doc:
            return

        try:
            # Save changes using bookmark manager
            if hasattr(self, 'bookmark_manager') and self.bookmark_manager.modified:
                # Save bookmarks to PDF using the manager
                self.bookmark_manager.save_to_pdf(self.pdf_doc.file_path)
                
                # Reload PDF document to reflect changes
                file_path = self.pdf_doc.file_path
                self.pdf_doc = PDFDocument(file_path)
                
                # Refresh bookmark related views
                self.bookmark_panel.update_tree_from_manager()
                
                # Update status
                self.statusBar().showMessage("Bookmark changes saved")
                logger.info("Saved bookmark changes to %s", file_path)
            else:
                # Fall back to standard save method
                self.pdf_doc.save_changes()
                self.statusBar().showMessage("Changes saved")
                
            # Disable save action after successful save
            self.save_action.setEnabled(False)
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to save changes: {str(e)}"
            )
            logger.error("Failed to save changes: %s", str(e))

    def closeEvent(self, event) -> None:
        """Handle window close event."""
        if self.pdf_doc:
            # Check for unsaved changes in bookmarks or other PDF changes
            has_unsaved_changes = (
                self.pdf_doc.has_unsaved_changes() or
                self.range_widget.has_unsaved_changes() or
                (hasattr(self, 'bookmark_manager') and self.bookmark_manager.modified)
            )
            
            if has_unsaved_changes:
                reply = QMessageBox.question(
                    self,
                    "Exit Application",
                    "You have unsaved changes. Do you want to save before exiting?",
                    QMessageBox.StandardButton.Save |
                    QMessageBox.StandardButton.Discard |
                    QMessageBox.StandardButton.Cancel,
                    QMessageBox.StandardButton.Save
                )
                
                if reply == QMessageBox.StandardButton.Save:
                    try:
                        self._save_changes()
                        self.thumbnail_widget.clear()
                        event.accept()
                    except Exception as e:
                        QMessageBox.critical(
                            self,
                            "Error",
                            f"Failed to save changes: {str(e)}"
                        )
                        event.ignore()
                elif reply == QMessageBox.StandardButton.Discard:
                    self.thumbnail_widget.clear()
                    event.accept()
                else:  # Cancel
                    event.ignore()
            else:
                self.thumbnail_widget.clear()
                event.accept()
        else:
            event.accept()

    def _handle_thumbnail_context_menu(self, page_number: int, pos: QPoint) -> None:
        """Handle thumbnail context menu."""
        if not self.pdf_doc:
            return

        menu = QMenu(self)
        add_bookmark_action = menu.addAction("Add Bookmark")
        
        action = menu.exec(pos)
        if action == add_bookmark_action:
            # Get bookmark title from user
            title, ok = QInputDialog.getText(
                self,
                "Add Bookmark",
                "Enter bookmark title:",
                text=f"Page {page_number}"
            )
            
            if ok and title.strip():
                try:
                    # Add bookmark to PDF
                    self.pdf_doc.add_bookmark(title.strip(), page_number - 1)  # Convert to 0-based
                    
                    # Update bookmark manager and panel
                    if hasattr(self, 'bookmark_manager'):
                        # Recreate the bookmark manager to reflect changes
                        self.bookmark_manager = BookmarkManager.from_pdf(self.pdf_doc.file_path)
                        self.bookmark_panel.display_bookmarks(self.bookmark_manager)
                    
                    # Enable save action
                    self.save_action.setEnabled(True)
                    
                    # Update status
                    self.statusBar().showMessage(f"Added bookmark '{title}' at page {page_number}")
                    logger.info("Added bookmark '%s' at page %d", title, page_number)
                except Exception as e:
                    QMessageBox.warning(
                        self,
                        "Error",
                        f"Failed to add bookmark: {str(e)}"
                    )
                    logger.error("Failed to add bookmark: %s", str(e))

    def _on_thumbnail_selected(self, page_number: int) -> None:
        """Handle thumbnail selection."""
        if not self.pdf_doc:
            return
            
        # Update bookmark panel selection
        self.bookmark_panel.select_page(page_number - 1)  # Convert to 0-based
        logger.debug("Selected page %d from thumbnail", page_number)
    
    def _trigger_split(self) -> None:
        """Handle split button click by obtaining ranges from bookmark panel and triggering PDF split."""
        if not self.pdf_doc:
            logger.warning("Cannot split PDF: no PDF document loaded")
            QMessageBox.warning(
                self,
                "Cannot Split PDF",
                "No PDF document is loaded."
            )
            return
        
        # Get chapter ranges from the bookmark panel
        chapter_ranges = self._get_chapter_ranges_from_bookmarks()
        
        if not chapter_ranges:
            logger.warning("Cannot split PDF: no chapter ranges available")
            QMessageBox.warning(
                self,
                "Cannot Split PDF",
                "No chapter ranges are available. Please ensure the PDF has bookmarks or chapter structure."
            )
            return
        
        # Call the range widget's split method with the ranges
        self.range_widget._split_pdf(chapter_ranges)
    
    def _get_chapter_ranges_from_bookmarks(self) -> List[Tuple[str, int, int]]:
        """
        Get the chapter ranges from the bookmark panel.
        
        Returns:
            List of (name, start_page, end_page) tuples representing chapter ranges
        """
        # If we have a bookmark tree from the PDF document, use that
        if self.pdf_doc and hasattr(self.pdf_doc, 'get_bookmark_tree'):
            bookmark_tree = self.pdf_doc.get_bookmark_tree()
            if bookmark_tree and bookmark_tree.chapter_ranges:
                # Convert PageRange objects to (name, start, end) tuples
                ranges = [(r.title, r.start, r.end) for r in bookmark_tree.chapter_ranges]
                logger.debug("Found %d chapter ranges from PDF document", len(ranges))
                return ranges
                
        # Fallback: if we're using the bookmark manager but don't have ranges from tree
        # We could implement chapter detection based on the bookmark manager structure
        # For now, we'll just return an empty list
        return []

    def _on_bookmark_changes(self) -> None:
        """Handle bookmark changes from the panel."""
        if self.pdf_doc:
            self.save_action.setEnabled(True)
            self.statusBar().showMessage("Bookmark structure modified (unsaved)") 
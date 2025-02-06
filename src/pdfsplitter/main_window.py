"""
Main window implementation for the PDF Chapter Splitter application.
"""
import logging
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QImage, QPixmap
from PyQt6.QtWidgets import (
    QFileDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from .pdf_document import PDFDocument, PDFLoadError
from .range_management import RangeManagementWidget

logger = logging.getLogger(__name__)

class ThumbnailViewer(QScrollArea):
    """Widget for displaying PDF page thumbnails in a scrollable grid."""
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """Initialize the thumbnail viewer."""
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # Container widget for the grid
        self.container = QWidget()
        self.grid_layout = QGridLayout(self.container)
        self.setWidget(self.container)
        
        # Style
        self.setMinimumHeight(400)
        self.setMinimumWidth(600)
        
        # Set object name for testing
        self.setObjectName("thumbnailViewer")
    
    def display_thumbnails(self, thumbnails: list[QImage]) -> None:
        """
        Display the given thumbnails in a grid layout.
        
        Args:
            thumbnails: List of QImage thumbnails to display
        """
        # Clear existing thumbnails
        for i in reversed(range(self.grid_layout.count())):
            self.grid_layout.itemAt(i).widget().setParent(None)
        
        # Calculate grid dimensions
        cols = max(1, self.width() // 220)  # 200px thumbnail + 20px margin
        
        # Add thumbnails to grid
        for i, thumbnail in enumerate(thumbnails):
            label = QLabel()
            # Convert QImage to QPixmap and scale it
            pixmap = QPixmap.fromImage(thumbnail).scaled(
                200, 300,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            label.setPixmap(pixmap)
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setStyleSheet("border: 1px solid #ccc; padding: 5px; margin: 5px;")
            label.setToolTip(f"Page {i + 1}")
            label.setObjectName(f"thumbnailLabel_{i}")
            
            row = i // cols
            col = i % cols
            self.grid_layout.addWidget(label, row, col)
        
        # Update layout
        self.container.setLayout(self.grid_layout)

class MainWindow(QMainWindow):
    """Main window of the PDF Chapter Splitter application."""
    
    def __init__(self) -> None:
        """Initialize the main window."""
        super().__init__()
        self.pdf_doc: Optional[PDFDocument] = None
        self.output_dir: Optional[Path] = None
        
        self._init_ui()
        logger.info("Main window initialized")
    
    def _init_ui(self) -> None:
        """Initialize the user interface."""
        self.setWindowTitle("PDF Chapter Splitter")
        self.setMinimumSize(800, 600)
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Create toolbar
        toolbar = self._create_toolbar()
        toolbar.setObjectName("mainToolbar")
        
        # Create main content area
        content_layout = QHBoxLayout()
        
        # Left side: Thumbnail viewer
        self.thumbnail_viewer = ThumbnailViewer()
        content_layout.addWidget(self.thumbnail_viewer)
        
        # Right side: Range management
        self.range_manager = RangeManagementWidget()
        content_layout.addWidget(self.range_manager)
        
        layout.addLayout(content_layout)
        
        # Create bottom panel
        bottom_panel = QHBoxLayout()
        
        # Output directory selection
        self.output_dir_label = QLabel("Output Directory: Not selected")
        self.output_dir_label.setObjectName("outputDirLabel")
        
        select_output_dir_btn = QPushButton("Select Output Directory")
        select_output_dir_btn.setObjectName("selectOutputDirButton")
        select_output_dir_btn.clicked.connect(self._select_output_directory)
        
        bottom_panel.addWidget(self.output_dir_label)
        bottom_panel.addWidget(select_output_dir_btn)
        
        layout.addLayout(bottom_panel)
    
    def _create_toolbar(self) -> None:
        """Create the main toolbar."""
        toolbar = self.addToolBar("Main Toolbar")
        toolbar.setMovable(False)
        
        # Open PDF action
        open_action = QAction("Open PDF", self)
        open_action.setStatusTip("Open a PDF file")
        open_action.setObjectName("openPdfAction")
        open_action.triggered.connect(self._open_pdf)
        toolbar.addAction(open_action)
        
        return toolbar
    
    def _open_pdf(self) -> None:
        """Open a PDF file and display its thumbnails."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open PDF File",
            str(Path.home()),
            "PDF Files (*.pdf)"
        )
        
        if not file_path:
            return
        
        try:
            self.pdf_doc = PDFDocument(Path(file_path))
            thumbnails = self.pdf_doc.generate_thumbnails()
            self.thumbnail_viewer.display_thumbnails(thumbnails)
            self.range_manager.set_pdf_document(self.pdf_doc)
            logger.info(f"Opened PDF: {file_path}")
            
            # Update window title
            self.setWindowTitle(f"PDF Chapter Splitter - {Path(file_path).name}")
        except PDFLoadError as e:
            logger.error(f"Failed to load PDF: {e}")
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to load PDF: {str(e)}"
            )
    
    def _select_output_directory(self) -> None:
        """Select the output directory for split PDFs."""
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Output Directory",
            str(Path.home())
        )
        
        if directory:
            self.output_dir = Path(directory)
            self.output_dir_label.setText(f"Output Directory: {directory}")
            logger.info(f"Selected output directory: {directory}")
    
    def closeEvent(self, event) -> None:
        """Handle window close event."""
        logger.info("Application closing") 
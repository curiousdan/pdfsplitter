"""
Range management components for the PDF Chapter Splitter.
"""
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from .pdf_document import PDFDocument, PDFLoadError

logger = logging.getLogger(__name__)

@dataclass
class ChapterRange:
    """Represents a chapter range in the PDF."""
    name: str
    start_page: int  # 0-based
    end_page: int    # 0-based, inclusive
    
    def __str__(self) -> str:
        """Return a string representation of the range."""
        return f"{self.name}: Pages {self.start_page + 1}-{self.end_page + 1}"
    
    def validate(self, max_pages: int) -> tuple[bool, str]:
        """
        Validate the range.
        
        Args:
            max_pages: Maximum number of pages in the PDF
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not self.name.strip():
            return False, "Chapter name cannot be empty"
        
        if self.start_page < 0 or self.start_page >= max_pages:
            return False, f"Start page must be between 1 and {max_pages}"
        
        if self.end_page < 0 or self.end_page >= max_pages:
            return False, f"End page must be between 1 and {max_pages}"
        
        if self.start_page > self.end_page:
            return False, "Start page cannot be greater than end page"
        
        return True, ""

class RangeManagementWidget(QWidget):
    """Widget for managing chapter ranges."""
    
    # Signal emitted when ranges are updated
    ranges_updated = pyqtSignal()
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """Initialize the range management widget."""
        super().__init__(parent)
        self.ranges: List[ChapterRange] = []
        self.pdf_doc: Optional[PDFDocument] = None
        self._init_ui()
    
    def _init_ui(self) -> None:
        """Initialize the user interface."""
        layout = QHBoxLayout(self)
        
        # Left side: Range input
        input_group = QGroupBox("Add Chapter Range")
        input_layout = QFormLayout()
        
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("e.g., Chapter 1")
        self.name_edit.setObjectName("chapterNameEdit")
        
        self.start_page = QSpinBox()
        self.start_page.setMinimum(1)
        self.start_page.setObjectName("startPageSpinBox")
        
        self.end_page = QSpinBox()
        self.end_page.setMinimum(1)
        self.end_page.setObjectName("endPageSpinBox")
        
        input_layout.addRow("Chapter Name:", self.name_edit)
        input_layout.addRow("Start Page:", self.start_page)
        input_layout.addRow("End Page:", self.end_page)
        
        add_button = QPushButton("Add Range")
        add_button.setObjectName("addRangeButton")
        add_button.clicked.connect(self._add_range)
        input_layout.addRow("", add_button)
        
        input_group.setLayout(input_layout)
        
        # Right side: Range list
        list_layout = QVBoxLayout()
        list_label = QLabel("Chapter Ranges:")
        self.range_list = QListWidget()
        self.range_list.setObjectName("rangeList")
        
        remove_button = QPushButton("Remove Selected")
        remove_button.setObjectName("removeRangeButton")
        remove_button.clicked.connect(self._remove_range)
        
        split_button = QPushButton("Split PDF")
        split_button.setObjectName("splitPdfButton")
        split_button.clicked.connect(self._split_pdf)
        
        list_layout.addWidget(list_label)
        list_layout.addWidget(self.range_list)
        list_layout.addWidget(remove_button)
        list_layout.addWidget(split_button)
        
        # Add both sides to main layout
        layout.addWidget(input_group)
        layout.addLayout(list_layout)
        
        self.setEnabled(False)  # Disabled until PDF is loaded
    
    def set_pdf_document(self, doc: Optional[PDFDocument]) -> None:
        """
        Set the current PDF document and update the UI accordingly.
        
        Args:
            doc: The PDF document to work with, or None to clear
        """
        self.pdf_doc = doc
        self.ranges.clear()
        self.range_list.clear()
        
        if doc:
            max_pages = doc.get_page_count()
            self.start_page.setMaximum(max_pages)
            self.end_page.setMaximum(max_pages)
            self.setEnabled(True)
            logger.info("Range management enabled for PDF with %d pages", max_pages)
        else:
            self.setEnabled(False)
            logger.info("Range management disabled - no PDF loaded")
    
    def _add_range(self) -> None:
        """Add a new chapter range."""
        if not self.pdf_doc:
            return
        
        name = self.name_edit.text().strip()
        start = self.start_page.value() - 1  # Convert to 0-based
        end = self.end_page.value() - 1      # Convert to 0-based
        
        new_range = ChapterRange(name, start, end)
        valid, error = new_range.validate(self.pdf_doc.get_page_count())
        
        if not valid:
            QMessageBox.warning(
                self,
                "Invalid Range",
                error
            )
            logger.warning("Invalid range: %s", error)
            return
        
        self.ranges.append(new_range)
        self.range_list.addItem(str(new_range))
        
        # Clear inputs
        self.name_edit.clear()
        self.start_page.setValue(1)
        self.end_page.setValue(1)
        
        self.ranges_updated.emit()
        logger.info("Added chapter range: %s", new_range)
    
    def _remove_range(self) -> None:
        """Remove the selected range."""
        current = self.range_list.currentRow()
        if current >= 0:
            self.range_list.takeItem(current)
            removed = self.ranges.pop(current)
            self.ranges_updated.emit()
            logger.info("Removed chapter range: %s", removed)
    
    def _split_pdf(self) -> None:
        """Split the PDF according to the defined ranges."""
        if not self.pdf_doc or not self.ranges:
            return
        
        try:
            for chapter_range in self.ranges:
                output_path = Path(str(self.pdf_doc.file_path)).parent / f"{chapter_range.name}.pdf"
                self.pdf_doc.extract_pages(
                    chapter_range.start_page,
                    chapter_range.end_page,
                    output_path
                )
            logger.info("Successfully split PDF into %d chapters", len(self.ranges))
            QMessageBox.information(
                self,
                "Success",
                f"Successfully split PDF into {len(self.ranges)} chapters"
            )
        except (PDFLoadError, ValueError) as e:
            error_msg = str(e)
            logger.error("Failed to split PDF: %s", error_msg)
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to split PDF: {error_msg}"
            ) 
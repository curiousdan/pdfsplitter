"""
Range management components for the PDF Chapter Splitter.
"""
import logging
from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path
from typing import List, Optional, Tuple, Set

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QApplication,
    QFileDialog,
)

from .pdf_document import PDFDocument, PDFLoadError
from .progress_dialog import ProgressDialog, WorkerThread

logger = logging.getLogger(__name__)

class ValidationError(Enum):
    """Types of validation errors."""
    EMPTY_NAME = auto()
    DUPLICATE_NAME = auto()
    START_GREATER_THAN_END = auto()
    PAGE_OUT_OF_BOUNDS = auto()
    RANGE_OVERLAP = auto()

@dataclass(frozen=True)
class ValidationResult:
    """Result of a validation check."""
    is_valid: bool
    error_type: Optional[ValidationError] = None
    error_message: str = ""

class RangeValidator:
    """Validates chapter range inputs."""
    
    def __init__(self, max_pages: int, existing_ranges: Optional[List[Tuple[str, int, int]]] = None) -> None:
        """
        Initialize the validator.
        
        Args:
            max_pages: Maximum number of pages in the PDF
            existing_ranges: List of existing ranges to check for overlaps and duplicates
        """
        self.max_pages = max_pages
        self.existing_ranges = existing_ranges or []
    
    def validate_name(self, name: str) -> ValidationResult:
        """
        Validate a chapter name.
        
        Args:
            name: The name to validate
            
        Returns:
            ValidationResult indicating if the name is valid
        """
        if not name.strip():
            return ValidationResult(
                False,
                ValidationError.EMPTY_NAME,
                "Chapter name cannot be empty"
            )
        
        if any(r[0] == name for r in self.existing_ranges):
            return ValidationResult(
                False,
                ValidationError.DUPLICATE_NAME,
                "A chapter with this name already exists"
            )
        
        return ValidationResult(True)
    
    def validate_page_range(self, start: int, end: int) -> ValidationResult:
        """
        Validate a page range.
        
        Args:
            start: Start page (0-based)
            end: End page (0-based)
            
        Returns:
            ValidationResult indicating if the range is valid
        """
        logger.debug(
            "Validating page range - start: %d, end: %d, max_pages: %d, existing_ranges: %s",
            start, end, self.max_pages, self.existing_ranges
        )
        
        if start > end:
            return ValidationResult(
                False,
                ValidationError.START_GREATER_THAN_END,
                "Start page must be less than or equal to end page"
            )
        
        if not (0 <= start < self.max_pages and 0 <= end < self.max_pages):
            return ValidationResult(
                False,
                ValidationError.PAGE_OUT_OF_BOUNDS,
                f"Pages must be between 1 and {self.max_pages}"
            )
        
        # Check for overlaps with existing ranges
        for _, existing_start, existing_end in self.existing_ranges:
            if (start <= existing_end and end >= existing_start):
                logger.debug(
                    "Range overlap detected - current: %d-%d, existing: %d-%d",
                    start, end, existing_start, existing_end
                )
                return ValidationResult(
                    False,
                    ValidationError.RANGE_OVERLAP,
                    "Range overlaps with an existing chapter"
                )
        
        return ValidationResult(True)
    
    def validate_all(self, name: str, start: int, end: int) -> ValidationResult:
        """
        Validate all aspects of a chapter range.
        
        Args:
            name: Chapter name
            start: Start page (0-based)
            end: End page (0-based)
            
        Returns:
            ValidationResult indicating if all aspects are valid
        """
        # Check name first
        name_result = self.validate_name(name)
        if not name_result.is_valid:
            return name_result
        
        # Then check page range
        return self.validate_page_range(start, end)

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
    """Widget for managing PDF splitting."""
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """Initialize the widget."""
        super().__init__(parent)
        self._pdf_doc: Optional[PDFDocument] = None
        self._modified = False
        
        # Create layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # Create split button
        button_layout = QHBoxLayout()
        self.split_button = QPushButton("Split PDF")
        self.split_button.setEnabled(False)
        self.split_button.setToolTip("Split PDF into separate files for each chapter")
        button_layout.addStretch()
        button_layout.addWidget(self.split_button)
        
        main_layout.addLayout(button_layout)
        
        # Disable widget initially
        self.setEnabled(False)
    
    def set_pdf_document(self, doc: Optional[PDFDocument]) -> None:
        """
        Set the PDF document for the widget.
        
        Args:
            doc: The PDF document to use, or None to clear
        """
        self._pdf_doc = doc
        self.setEnabled(doc is not None)
    
    def set_split_enabled(self, enabled: bool) -> None:
        """
        Set whether the split button is enabled.
        
        Args:
            enabled: Whether to enable the button
        """
        self.split_button.setEnabled(enabled)
    
    def _update_button_states(self) -> None:
        """Update the state of buttons based on current state."""
        has_pdf = self._pdf_doc is not None
        self.split_button.setEnabled(has_pdf)  # Now controlled externally via set_split_enabled
    
    def _split_pdf(self, ranges_to_split: List[Tuple[str, int, int]]) -> None:
        """
        Split the PDF into separate files based on the provided ranges.
        
        Args:
            ranges_to_split: List of (name, start_page, end_page) tuples representing chapter ranges
        """
        if not self._pdf_doc or not ranges_to_split:
            logger.warning("Cannot split PDF: no PDF document or no ranges")
            return
        
        # Prompt for output directory
        output_dir = Path(QFileDialog.getExistingDirectory(
            self,
            "Select Output Directory",
            str(Path.home()),
            QFileDialog.Option.ShowDirsOnly
        ))
        
        if not output_dir.is_dir():
            logger.info("Split operation cancelled - no directory selected")
            return
        
        # Create and run the worker in a dialog
        dialog = ProgressDialog("Splitting PDF", "", self)
        worker = WorkerThread()
        
        def split_work(progress_callback) -> None:
            """Split the PDF into chapters."""
            logger.info("Starting PDF split operation")
            
            # Extract each range
            for i, (name, start, end) in enumerate(ranges_to_split, 1):
                # Update progress
                progress = int(100 * i / len(ranges_to_split))
                progress_callback(progress, f"Extracting {name}...")
                
                # Create output file
                output_path = output_dir / f"{name}.pdf"
                self._pdf_doc.extract_pages(
                    start,
                    end,
                    output_path,
                    progress_callback
                )
            
            # Final progress update
            progress_callback(100, "Complete")
            logger.info("PDF split operation completed")
        
        worker.operation = split_work
        worker.finished.connect(lambda: self._on_split_complete(output_dir))
        
        dialog.run_operation(worker)
    
    def _on_split_complete(self, output_dir: Path) -> None:
        """
        Handle split operation completion.
        
        Args:
            output_dir: The directory where output files were saved
        """
        QMessageBox.information(
            self,
            "Split Complete",
            f"PDF has been split into separate files in:\n{str(output_dir)}"
        )
        logger.info("PDF split operation completed successfully")
    
    def has_unsaved_changes(self) -> bool:
        """Check if there are unsaved changes."""
        return self._modified 
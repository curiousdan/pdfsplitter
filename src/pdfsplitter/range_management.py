"""
Range management components for the PDF Chapter Splitter.
"""
import logging
from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path
from typing import List, Optional, Tuple, Set

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QValidator
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
    QApplication,
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

class RangeSpinBox(QSpinBox):
    """Custom spinbox that handles range input."""
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """Initialize the spinbox."""
        super().__init__(parent)
        self.setMinimum(1)  # Pages are 1-based for users
        self.valueChanged.connect(self._on_value_changed)
    
    def _on_value_changed(self, value: int) -> None:
        """Handle value changes."""
        if hasattr(self.parent(), "handle_spinbox_change"):
            self.parent().handle_spinbox_change(self, value)

class RangeManagementWidget(QWidget):
    """Widget for managing chapter ranges."""
    
    # Signal emitted when ranges are updated
    ranges_updated = pyqtSignal()
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """Initialize the widget."""
        super().__init__(parent)
        self.pdf_doc: Optional[PDFDocument] = None
        self.ranges: List[Tuple[str, int, int]] = []  # [(name, start_page, end_page), ...]
        
        # Create widgets
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Chapter name")
        self.name_edit.textChanged.connect(self._update_validation)
        self.name_edit.setToolTip("Enter a unique name for this chapter")
        
        # Create spinboxes with labels
        spinbox_layout = QHBoxLayout()
        
        start_label = QLabel("Start:")
        self.start_page = RangeSpinBox()
        self.start_page.setMinimum(1)
        self.start_page.valueChanged.connect(self._update_validation)
        self.start_page.setToolTip("First page of the chapter")
        spinbox_layout.addWidget(start_label)
        spinbox_layout.addWidget(self.start_page)
        
        end_label = QLabel("End:")
        self.end_page = RangeSpinBox()
        self.end_page.setMinimum(1)
        self.end_page.valueChanged.connect(self._update_validation)
        self.end_page.setToolTip("Last page of the chapter")
        spinbox_layout.addWidget(end_label)
        spinbox_layout.addWidget(self.end_page)
        
        # Create buttons
        self.add_button = QPushButton("Add")
        self.add_button.setEnabled(False)
        self.add_button.clicked.connect(self._on_add_clicked)
        self.add_button.setToolTip("Add this chapter range")
        
        self.split_button = QPushButton("Split PDF")
        self.split_button.setEnabled(False)
        self.split_button.clicked.connect(self._split_pdf)
        self.split_button.setToolTip("Split PDF into separate files for each chapter")
        
        # Create range list widget with label
        list_label = QLabel("Chapter Ranges:")
        self.range_list = QListWidget()
        self.range_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.range_list.setToolTip("List of defined chapter ranges")
        
        # Create remove button
        self.remove_button = QPushButton("Remove")
        self.remove_button.setEnabled(False)
        self.remove_button.clicked.connect(self._remove_range)
        self.remove_button.setToolTip("Remove selected chapter range")
        
        # Connect range list selection to remove button
        self.range_list.itemSelectionChanged.connect(
            lambda: self.remove_button.setEnabled(bool(self.range_list.selectedItems()))
        )
        
        # Layout
        main_layout = QVBoxLayout()
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Input group
        input_group = QGroupBox("Add Chapter")
        input_layout = QVBoxLayout()
        input_layout.setSpacing(10)
        
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Name:"))
        name_layout.addWidget(self.name_edit)
        
        input_layout.addLayout(name_layout)
        input_layout.addLayout(spinbox_layout)
        input_layout.addWidget(self.add_button)
        input_group.setLayout(input_layout)
        
        main_layout.addWidget(input_group)
        
        # Range list group
        list_group = QGroupBox("Chapters")
        list_layout = QVBoxLayout()
        list_layout.addWidget(self.range_list)
        
        # Button layout
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.remove_button)
        button_layout.addStretch()
        button_layout.addWidget(self.split_button)
        list_layout.addLayout(button_layout)
        
        list_group.setLayout(list_layout)
        main_layout.addWidget(list_group)
        
        self.setLayout(main_layout)
        self.setEnabled(False)  # Initially disabled until PDF is loaded
        
        # Initial validation
        self._update_validation()
    
    def handle_spinbox_change(self, spinbox: RangeSpinBox, value: int) -> None:
        """Handle spinbox value changes."""
        self._update_validation()
    
    def _update_validation(self) -> None:
        """Update UI state based on validation results."""
        is_valid = self.validate_input()
        self.add_button.setEnabled(is_valid)
        self._update_tooltips(is_valid)
    
    def _update_tooltips(self, is_valid: bool) -> None:
        """Update tooltips based on validation results."""
        if is_valid:
            self.name_edit.setStyleSheet("")
            self.start_page.setStyleSheet("")
            self.end_page.setStyleSheet("")
            self.name_edit.setToolTip("Enter a unique name for this chapter")
            self.start_page.setToolTip("First page of the chapter")
            self.end_page.setToolTip("Last page of the chapter")
            return
        
        error_style = "border: 1px solid red;"
        
        self.name_edit.setStyleSheet(error_style)
        self.name_edit.setToolTip("Invalid input")
        self.start_page.setStyleSheet(error_style)
        self.end_page.setStyleSheet(error_style)
        self.start_page.setToolTip("Invalid input")
        self.end_page.setToolTip("Invalid input")
    
    def validate_input(self) -> bool:
        """
        Validate current input against business rules.
        
        This is a public method primarily for testing, but can also be used
        to check validity without side effects.
        
        Returns:
            bool: True if current input is valid, False otherwise
        """
        if not self.pdf_doc:
            logger.debug("Validation failed: No PDF document loaded")
            return False
        
        name = self.name_edit.text().strip()
        start = self.start_page.value()
        end = self.end_page.value()
        
        logger.debug(
            "Validating input - name: %s, start: %d, end: %d, current ranges: %s",
            name, start, end, self.ranges
        )
        
        # Create validator for current state
        validator = RangeValidator(
            self.pdf_doc.get_page_count(),
            [(n, s, e) for n, s, e in self.ranges]  # Create a copy to avoid modifying original
        )
        
        # Validate name first
        name_result = validator.validate_name(name)
        if not name_result.is_valid:
            logger.debug("Name validation failed: %s", name_result.error_message)
            self._update_tooltips(False)
            return False
        
        # Then validate page range - convert to 0-based for internal validation
        range_result = validator.validate_page_range(start - 1, end - 1)
        if not range_result.is_valid:
            # Only fail if it's not a range overlap
            if range_result.error_type != ValidationError.RANGE_OVERLAP:
                logger.debug("Range validation failed: %s", range_result.error_message)
                self._update_tooltips(False)
                return False
            
            # For range overlaps, check if it's with the same name
            # If it's a different name, it's valid
            for existing_name, _, _ in self.ranges:
                if existing_name == name:
                    logger.debug("Range validation failed: duplicate name")
                    self._update_tooltips(False)
                    return False
        
        # All valid
        logger.debug("Validation passed")
        self._update_tooltips(True)
        return True
    
    def set_pdf_document(self, doc: Optional[PDFDocument]) -> None:
        """Set the PDF document to work with."""
        self.pdf_doc = doc
        self.setEnabled(bool(doc))  # Enable widget only when PDF is loaded
        
        if doc:
            max_pages = doc.get_page_count()
            self.start_page.setMaximum(max_pages)
            self.end_page.setMaximum(max_pages)
        else:
            self.start_page.setMaximum(1)
            self.end_page.setMaximum(1)
            self.range_list.clear()
            self.ranges.clear()
            
        self._update_validation()
    
    def _on_add_clicked(self) -> None:
        """Handle add button click."""
        name = self.name_edit.text().strip()
        start = self.start_page.value()
        end = self.end_page.value()
        self._add_range(name, start - 1, end - 1)  # Convert to 0-based
    
    def _add_range(self, name: str, start: int, end: int) -> None:
        """
        Add a new chapter range.
        
        Args:
            name: Name of the chapter
            start: Start page (0-based)
            end: End page (0-based)
        """
        # Validate the range
        validator = RangeValidator(
            self.pdf_doc.get_page_count() if self.pdf_doc else 0,
            [(n, s, e) for n, s, e in self.ranges]
        )
        
        name_result = validator.validate_name(name)
        range_result = validator.validate_page_range(start, end)
        
        if not name_result.is_valid:
            logger.warning("Invalid range name: %s", name_result.error_message)
            QMessageBox.warning(
                self,
                "Invalid Range",
                name_result.error_message
            )
            return
            
        if not range_result.is_valid:
            logger.warning("Invalid page range: %s", range_result.error_message)
            QMessageBox.warning(
                self,
                "Invalid Range",
                range_result.error_message
            )
            return
        
        # Store the range
        self.ranges.append((name, start, end))
        
        # Add to list widget (display 1-based page numbers)
        item = QListWidgetItem(f"{name}: Pages {start + 1}-{end + 1}")
        self.range_list.addItem(item)
        
        # Clear inputs and set next available page if this was added via UI
        if self.name_edit.text().strip() == name:
            self.name_edit.clear()
            next_page = end + 2  # Start from the next page after the current range
            if next_page <= self.pdf_doc.get_page_count():
                self.start_page.setValue(next_page)
                self.end_page.setValue(next_page)
        
        # Update UI state
        self.split_button.setEnabled(True)
        self._update_validation()
        
        # Log for debugging
        logger.debug(
            "Added range - name: %s, start: %d, end: %d, current ranges: %s",
            name, start + 1, end + 1, self.ranges
        )
        
        # Emit signal
        self.ranges_updated.emit()
    
    def _remove_range(self) -> None:
        """Remove the selected range."""
        current = self.range_list.currentRow()
        if current >= 0:
            removed = self.ranges.pop(current)
            self.range_list.takeItem(current)
            self.ranges_updated.emit()
            logger.info("Removed chapter range: %s", removed[0])
            self._update_button_states()
            self._update_validation()
    
    def _update_button_states(self) -> None:
        """Update button states based on current selection and ranges."""
        self.remove_button.setEnabled(bool(self.range_list.selectedItems()))
        self.split_button.setEnabled(bool(self.ranges))
    
    def _split_pdf(self) -> None:
        """Split the PDF according to the defined ranges."""
        if not self.pdf_doc or not self.ranges:
            return
        
        try:
            # Get output directory from input file path
            output_dir = self.pdf_doc.file_path.parent
            
            def split_work(progress_callback) -> None:
                """Worker function to split PDF."""
                for i, (name, start, end) in enumerate(self.ranges, 1):
                    # Create output path
                    output_path = output_dir / f"{name}.pdf"
                    
                    # Extract pages with progress updates
                    self.pdf_doc.extract_pages(
                        start,
                        end,
                        output_path,
                        progress_callback
                    )
            
            # Create worker thread
            worker = WorkerThread(split_work)
            
            # Show progress dialog
            dialog = ProgressDialog(
                "Splitting PDF",
                "Preparing to split PDF...",
                parent=self
            )
            dialog.run_operation(worker)
            
            # Show success message with output directory
            QMessageBox.information(
                self,
                "Success",
                f"PDF split into {len(self.ranges)} files.\n\n"
                f"Files saved in:\n{output_dir}"
            )
            
            # Clear ranges after successful split
            self.ranges.clear()
            self.range_list.clear()
            self._update_button_states()
            
        except (PDFLoadError, ValueError) as e:
            error_msg = str(e)
            logger.error("Failed to split PDF: %s", error_msg)
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to split PDF: {error_msg}"
            ) 
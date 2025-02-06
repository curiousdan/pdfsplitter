"""
Progress dialog for long-running operations.
"""
import logging
from typing import Optional

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QDialog, QLabel, QProgressBar, QVBoxLayout,
    QPushButton, QMessageBox, QFrame
)

logger = logging.getLogger(__name__)

class WorkerThread(QThread):
    """Worker thread for running operations in the background."""
    
    # Signal emitted when progress is made
    progress = pyqtSignal(int, str)  # (progress_value, status_message)
    # Signal emitted when an error occurs
    error = pyqtSignal(str)
    # Signal emitted when operation completes successfully
    finished = pyqtSignal()
    
    def __init__(self, operation: callable, *args, **kwargs) -> None:
        """
        Initialize the worker thread.
        
        Args:
            operation: The function to run in the background
            *args: Positional arguments for the operation
            **kwargs: Keyword arguments for the operation
        """
        super().__init__()
        self.operation = operation
        self.args = args
        self.kwargs = kwargs
    
    def run(self) -> None:
        """Run the operation in the background."""
        try:
            self.operation(
                *self.args,
                progress_callback=self.progress.emit,
                **self.kwargs
            )
            self.finished.emit()
        except Exception as e:
            logger.error("Operation failed: %s", str(e))
            self.error.emit(str(e))

class ProgressDialog(QDialog):
    """Dialog showing progress of long-running operations."""
    
    def __init__(
        self,
        title: str,
        initial_message: str,
        parent: Optional[QDialog] = None,
    ) -> None:
        """
        Initialize the progress dialog.
        
        Args:
            title: Title of the dialog
            initial_message: Initial status message
            parent: Parent widget
        """
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setFixedSize(400, 150)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)
        
        # Create UI
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Status label
        self.status_label = QLabel(initial_message)
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("%p%")
        layout.addWidget(self.progress_bar)
        
        # Separator line
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(line)
        
        # Cancel button
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self._cancel_operation)
        layout.addWidget(self.cancel_button)
        
        # Initialize worker to None
        self.worker: Optional[WorkerThread] = None
    
    def run_operation(self, worker: WorkerThread) -> None:
        """
        Run an operation in the background.
        
        Args:
            worker: The worker thread to run
        """
        self.worker = worker
        self.worker.progress.connect(self._update_progress)
        self.worker.error.connect(self._handle_error)
        self.worker.finished.connect(self.accept)
        
        # Start operation
        self.worker.start()
        
        # Show dialog
        self.exec()
    
    def _update_progress(self, value: int, message: str) -> None:
        """
        Update progress display.
        
        Args:
            value: Progress value (0-100)
            message: Status message to display
        """
        self.progress_bar.setValue(value)
        self.status_label.setText(message)
    
    def _handle_error(self, error_msg: str) -> None:
        """
        Handle operation error.
        
        Args:
            error_msg: Error message to display
        """
        self.status_label.setText("Operation failed!")
        QMessageBox.critical(
            self,
            "Error",
            f"Operation failed: {error_msg}"
        )
        self.reject()
    
    def _cancel_operation(self) -> None:
        """Handle cancel button click."""
        if self.worker and self.worker.isRunning():
            if QMessageBox.question(
                self,
                "Cancel Operation",
                "Are you sure you want to cancel the operation?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            ) == QMessageBox.StandardButton.Yes:
                self.worker.terminate()
                self.worker.wait()
                self.reject()
    
    def closeEvent(self, event) -> None:
        """Handle dialog close event."""
        self._cancel_operation()
        event.ignore()  # Prevent closing unless cancelled 
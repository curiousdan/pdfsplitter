"""
Main entry point for the PDF Chapter Splitter application.
"""
import logging
import sys
from pathlib import Path

from PyQt6.QtWidgets import QApplication

from .main_window import MainWindow

def setup_logging() -> None:
    """Set up logging configuration."""
    log_dir = Path.home() / ".pdfsplitter"
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / "pdfsplitter.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )

def main() -> None:
    """Main application entry point."""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        app = QApplication(sys.argv)
        window = MainWindow()
        window.show()
        logger.info("Application started")
        sys.exit(app.exec())
    except Exception as e:
        logger.exception("Unhandled exception occurred")
        sys.exit(1)

if __name__ == "__main__":
    main() 
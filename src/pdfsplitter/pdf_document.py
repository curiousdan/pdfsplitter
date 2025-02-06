"""
Core PDF document handling functionality.
"""
from pathlib import Path
from typing import Any, List

import fitz  # PyMuPDF
from PyQt6.QtGui import QImage

class PDFLoadError(Exception):
    """Raised when there are issues loading a PDF file."""
    pass

class PDFDocument:
    """Handles PDF loading, validation, and page operations."""
    
    MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
    
    def __init__(self, file_path: Path) -> None:
        """
        Initialize a PDFDocument instance.
        
        Args:
            file_path: Path to the PDF file
            
        Raises:
            PDFLoadError: If the file cannot be loaded or is invalid
        """
        self.file_path = file_path
        self.doc: Any = None  # Will hold the fitz.Document instance
        self._validate_and_load()
    
    def _validate_and_load(self) -> None:
        """
        Validate the PDF file and load it.
        
        Raises:
            PDFLoadError: If validation fails or file cannot be loaded
        """
        if not self.file_path.exists():
            raise PDFLoadError(f"File not found: {self.file_path}")
        
        if not self.file_path.is_file():
            raise PDFLoadError(f"Not a file: {self.file_path}")
        
        if self.file_path.suffix.lower() != '.pdf':
            raise PDFLoadError(f"Not a PDF file: {self.file_path}")
        
        if self.file_path.stat().st_size > self.MAX_FILE_SIZE:
            raise PDFLoadError(f"File too large (max {self.MAX_FILE_SIZE/1024/1024}MB)")
        
        try:
            self.doc = fitz.open(self.file_path)
            # Validate that we can access pages
            _ = len(self.doc)
        except Exception as e:
            raise PDFLoadError(f"Failed to load PDF: {str(e)}")
    
    def generate_thumbnails(self, size: tuple[int, int] = (200, 300)) -> List[QImage]:
        """
        Generate thumbnails for all pages in the PDF.
        
        Args:
            size: Tuple of (width, height) for the thumbnails
            
        Returns:
            List of QImage thumbnails
            
        Raises:
            PDFLoadError: If thumbnail generation fails
        """
        thumbnails = []
        try:
            for page in self.doc:
                try:
                    # Use a lower resolution matrix for faster thumbnail generation
                    matrix = fitz.Matrix(1, 1)
                    pix = page.get_pixmap(matrix=matrix)
                    img = QImage(pix.samples, pix.width, pix.height,
                               pix.stride, QImage.Format.Format_RGB888)
                    thumbnails.append(img)
                except Exception as e:
                    raise PDFLoadError(f"Failed to generate thumbnail for page {page.number + 1}: {str(e)}")
        except Exception as e:
            raise PDFLoadError(f"Failed to generate thumbnails: {str(e)}")
        
        return thumbnails
    
    def get_page_count(self) -> int:
        """
        Get the total number of pages in the PDF.
        
        Returns:
            Number of pages
        """
        return len(self.doc)
    
    def extract_pages(self, start: int, end: int, output_path: Path) -> None:
        """
        Extract a range of pages to a new PDF file.
        
        Args:
            start: Start page number (0-based)
            end: End page number (0-based, inclusive)
            output_path: Path where to save the extracted pages
            
        Raises:
            PDFLoadError: If page extraction fails
            ValueError: If page range is invalid
        """
        if start > end:
            raise ValueError(f"Start page ({start}) greater than end page ({end})")
            
        if not (0 <= start < self.get_page_count()):
            raise ValueError(f"Invalid start page: {start}")
            
        if not (0 <= end < self.get_page_count()):
            raise ValueError(f"Invalid end page: {end}")
            
        try:
            doc_out = fitz.open()
            doc_out.insert_pdf(self.doc, from_page=start, to_page=end)
            doc_out.save(str(output_path))
            doc_out.close()
        except Exception as e:
            raise PDFLoadError(f"Failed to extract pages: {str(e)}")
    
    def __del__(self) -> None:
        """Ensure the PDF document is properly closed."""
        if self.doc:
            self.doc.close() 
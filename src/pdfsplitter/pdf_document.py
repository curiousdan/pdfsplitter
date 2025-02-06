"""
Core PDF document handling functionality.
"""
from pathlib import Path
from typing import Any, Callable, List, Optional, Tuple

import fitz  # PyMuPDF
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QImage

from .preview_cache import PreviewCache

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
        self._preview_cache = PreviewCache()
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
    
    def generate_preview(
        self,
        page_num: int,
        size: Tuple[int, int] = (200, 300)
    ) -> QImage:
        """
        Generate a preview for a single page.
        
        Args:
            page_num: Page number to generate preview for (0-based)
            size: Tuple of (width, height) for the preview
            
        Returns:
            QImage preview of the page
            
        Raises:
            PDFLoadError: If preview generation fails
            ValueError: If page number is invalid
        """
        if not (0 <= page_num < self.get_page_count()):
            raise ValueError(f"Invalid page number: {page_num}")
        
        # Check cache first
        cached = self._preview_cache.get(page_num)
        if cached is not None:
            return cached
        
        try:
            page = self.doc[page_num]
            
            # Calculate zoom factors to achieve desired size
            zoom_w = size[0] / page.rect.width
            zoom_h = size[1] / page.rect.height
            zoom = min(zoom_w, zoom_h)  # Keep aspect ratio
            
            # Use calculated zoom for the matrix
            matrix = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=matrix)
            
            # Create QImage
            img = QImage(pix.samples, pix.width, pix.height,
                        pix.stride, QImage.Format.Format_RGB888)
            
            # Scale to exact size, ignoring aspect ratio
            img = img.scaled(
                QSize(size[0], size[1]),
                Qt.AspectRatioMode.IgnoreAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            
            # Cache the preview
            self._preview_cache.put(page_num, img)
            
            return img
        except Exception as e:
            raise PDFLoadError(f"Failed to generate preview for page {page_num + 1}: {str(e)}")
    
    def generate_thumbnails(
        self,
        size: tuple[int, int] = (200, 300),
        progress_callback: Optional[Callable[[int, str], None]] = None
    ) -> List[QImage]:
        """
        Generate thumbnails for all pages in the PDF.
        
        Args:
            size: Tuple of (width, height) for the thumbnails
            progress_callback: Optional callback for progress updates
            
        Returns:
            List of QImage thumbnails
            
        Raises:
            PDFLoadError: If thumbnail generation fails
        """
        thumbnails = []
        total_pages = len(self.doc)
        
        try:
            for i in range(total_pages):
                try:
                    thumbnail = self.generate_preview(i, size)
                    thumbnails.append(thumbnail)
                    
                    # Report progress
                    if progress_callback:
                        progress = int((i + 1) * 100 / total_pages)
                        progress_callback(progress, f"Generating thumbnails... ({i + 1}/{total_pages})")
                except Exception as e:
                    raise PDFLoadError(f"Failed to generate thumbnail for page {i + 1}: {str(e)}")
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
    
    def extract_pages(
        self,
        start: int,
        end: int,
        output_path: Path,
        progress_callback: Optional[Callable[[int, str], None]] = None
    ) -> None:
        """
        Extract a range of pages to a new PDF file.
        
        Args:
            start: Start page number (0-based)
            end: End page number (0-based, inclusive)
            output_path: Path where to save the extracted pages
            progress_callback: Optional callback for progress updates
            
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
        
        if progress_callback:
            progress_callback(0, "Creating output document...")
        
        try:
            doc_out = fitz.open()
            
            # Insert pages one by one to show progress
            total_pages = end - start + 1
            for i, page_num in enumerate(range(start, end + 1)):
                doc_out.insert_pdf(self.doc, from_page=page_num, to_page=page_num)
                
                if progress_callback:
                    progress = int((i + 1) * 80 / total_pages)  # Use 80% for copying
                    progress_callback(progress, f"Copying pages... ({i + 1}/{total_pages})")
            
            if progress_callback:
                progress_callback(90, "Saving output file...")
            
            doc_out.save(str(output_path))
            doc_out.close()
            
            if progress_callback:
                progress_callback(100, "Complete!")
        except Exception as e:
            raise PDFLoadError(f"Failed to extract pages: {str(e)}")
    
    def update_current_page(self, page_num: int) -> None:
        """
        Update the current page for cache management.
        
        Args:
            page_num: The new current page number
        """
        self._preview_cache.update_current_page(page_num)
    
    def __del__(self) -> None:
        """Ensure the PDF document is properly closed."""
        if self.doc:
            self.doc.close()
            self._preview_cache.clear() 
"""
Core PDF document handling functionality.
"""
from pathlib import Path
from typing import Any, Callable, List, Optional, Tuple
import logging
import io

import fitz  # PyMuPDF
from PyQt6.QtCore import Qt, QSize, QObject, pyqtSignal, QByteArray, QBuffer
from PyQt6.QtGui import QImage

from .preview_cache import PreviewCache
from .bookmark_detection import BookmarkDetector, BookmarkTree, PageRange

logger = logging.getLogger(__name__)

class PreviewConfig:
    """Configuration for preview generation."""
    
    # Default preview sizes
    THUMBNAIL_SIZE = (150, 225)  # Smaller thumbnails for list
    PREVIEW_SIZE = (300, 450)    # Larger for main view
    
    # Quality settings
    THUMBNAIL_DPI = 72   # Lower DPI for thumbnails
    PREVIEW_DPI = 144   # Higher DPI for previews
    
    # Color settings
    USE_GRAYSCALE = True  # Use grayscale for thumbnails
    JPEG_QUALITY = 85    # JPEG quality for compression

class PDFLoadError(Exception):
    """Raised when there are issues loading a PDF file."""
    pass

class PreviewGenerator(QObject):
    """Handles asynchronous preview generation."""
    
    preview_ready = pyqtSignal(int, QImage)  # Signals when a preview is ready
    
    def __init__(self, doc: fitz.Document) -> None:
        """Initialize the generator."""
        super().__init__()
        self.doc = doc
    
    def generate_preview(
        self,
        page_num: int,
        size: Tuple[int, int],
        dpi: int = PreviewConfig.PREVIEW_DPI,
        grayscale: bool = False,
        quality: int = PreviewConfig.JPEG_QUALITY
    ) -> QImage:
        """Generate an optimized preview."""
        try:
            page = self.doc[page_num]
            
            # Calculate matrix for desired DPI
            matrix = fitz.Matrix(dpi/72.0, dpi/72.0)
            
            # Generate pixmap with optimization flags
            try:
                if grayscale:
                    pix = page.get_pixmap(
                        matrix=matrix,
                        colorspace="gray",
                        alpha=False
                    )
                else:
                    pix = page.get_pixmap(
                        matrix=matrix,
                        alpha=False
                    )
            except RuntimeError as e:
                # Handle MuPDF layer error by trying again without layers
                if "No default Layer config" in str(e):
                    logger.warning("Layer error encountered, retrying without layers")
                    if grayscale:
                        pix = page.get_pixmap(
                            matrix=matrix,
                            colorspace="gray",
                            alpha=False,
                            no_layers=True
                        )
                    else:
                        pix = page.get_pixmap(
                            matrix=matrix,
                            alpha=False,
                            no_layers=True
                        )
                else:
                    raise
            
            # Create base QImage
            if grayscale:
                img = QImage(
                    pix.samples,
                    pix.width,
                    pix.height,
                    pix.stride,
                    QImage.Format.Format_Grayscale8
                )
            else:
                img = QImage(
                    pix.samples,
                    pix.width,
                    pix.height,
                    pix.stride,
                    QImage.Format.Format_RGB888
                )
            
            # Scale to desired size
            target_size = QSize(*size)
            target_aspect = target_size.width() / target_size.height()
            img_aspect = img.width() / img.height()

            if abs(target_aspect - img_aspect) < 0.01:  # Almost same aspect ratio
                scaled = img.scaled(
                    target_size,
                    Qt.AspectRatioMode.IgnoreAspectRatio,  # Force exact size
                    Qt.TransformationMode.SmoothTransformation
                )
            else:
                # Calculate dimensions that will fit within target size while preserving aspect ratio
                if img_aspect > target_aspect:  # Image is wider
                    new_width = target_size.width()
                    new_height = int(new_width / img_aspect)
                else:  # Image is taller
                    new_height = target_size.height()
                    new_width = int(new_height * img_aspect)
                
                scaled = img.scaled(
                    QSize(new_width, new_height),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
            
            # Compress if quality specified
            if quality < 100:
                # Create a buffer for the compressed image
                buffer = QBuffer()
                buffer.open(QBuffer.OpenModeFlag.WriteOnly)
                
                # Save as JPEG with specified quality
                success = scaled.save(buffer, "JPEG", quality)
                buffer.close()
                
                if not success:
                    logger.warning("Failed to compress image, using uncompressed version")
                    return scaled
                
                # Create new image with reduced memory footprint
                compressed_data = buffer.data()
                compressed_image = QImage()
                if not compressed_image.loadFromData(compressed_data, "JPEG"):
                    logger.warning("Failed to load compressed image, using uncompressed version")
                    return scaled
                
                # Convert to 8-bit format for better memory usage
                if grayscale:
                    final_image = compressed_image.convertToFormat(QImage.Format.Format_Grayscale8)
                else:
                    final_image = compressed_image.convertToFormat(QImage.Format.Format_RGB888)
                
                return final_image
            
            return scaled
        except Exception as e:
            logger.error("Failed to generate preview: %s", str(e))
            raise

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
        self._bookmark_detector = BookmarkDetector()
        self._bookmark_tree: Optional[BookmarkTree] = None
        self._preview_generator: Optional[PreviewGenerator] = None
        self._has_unsaved_changes = False
        self._validate_and_load()
    
    def generate_preview(
        self,
        page_num: int,
        size: Optional[Tuple[int, int]] = None,
        is_thumbnail: bool = False
    ) -> QImage:
        """
        Generate a preview for a single page.
        
        Args:
            page_num: Page number to generate preview for (0-based)
            size: Optional tuple of (width, height) for the preview
            is_thumbnail: Whether this is a thumbnail (uses lower quality)
            
        Returns:
            QImage preview of the page
            
        Raises:
            PDFLoadError: If preview generation fails
            ValueError: If page number is invalid
        """
        if not (0 <= page_num < self.get_page_count()):
            raise ValueError(f"Invalid page number: {page_num}")
        
        # Determine preview configuration
        if size is None:
            size = (
                PreviewConfig.THUMBNAIL_SIZE if is_thumbnail
                else PreviewConfig.PREVIEW_SIZE
            )
        
        # Check cache first
        cached = self._preview_cache.get(page_num)
        if cached is not None:
            return cached
        
        try:
            # Generate optimized preview
            preview = self._preview_generator.generate_preview(
                page_num,
                size,
                dpi=PreviewConfig.THUMBNAIL_DPI if is_thumbnail else PreviewConfig.PREVIEW_DPI,
                grayscale=PreviewConfig.USE_GRAYSCALE and is_thumbnail,
                quality=PreviewConfig.JPEG_QUALITY
            )
            
            # Cache the preview
            self._preview_cache.put(page_num, preview)
            
            return preview
        except Exception as e:
            logger.error("Failed to generate preview for page %d: %s", page_num + 1, str(e))
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
    
    def get_bookmark_tree(self) -> Optional[BookmarkTree]:
        """
        Get the bookmark tree for this document.
        
        Returns:
            BookmarkTree if document has bookmarks, None otherwise
        """
        return self._bookmark_tree
    
    def get_chapter_ranges(self) -> List[PageRange]:
        """
        Get detected chapter ranges.
        
        Returns:
            List of detected page ranges
        """
        if self._bookmark_tree:
            return self._bookmark_tree.chapter_ranges
        return []
    
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
            
            # Initialize preview generator
            self._preview_generator = PreviewGenerator(self.doc)
            
            # Analyze bookmarks
            self._bookmark_tree = self._bookmark_detector.analyze_document(self.doc)
        except Exception as e:
            raise PDFLoadError(f"Failed to load PDF: {str(e)}")

    def has_unsaved_changes(self) -> bool:
        """Check if there are unsaved bookmark changes."""
        return self._has_unsaved_changes

    def save_changes(self) -> None:
        """Save any changes to the PDF file."""
        if not self._has_unsaved_changes:
            return

        try:
            # Save the document
            self.doc.save(self.file_path, incremental=True, encryption=self.doc.encryption)
            self._has_unsaved_changes = False
            logger.info("Saved changes to PDF file")
        except Exception as e:
            raise PDFLoadError(f"Failed to save changes: {e}")

    def add_bookmark(self, title: str, page: int) -> None:
        """
        Add a new bookmark to the PDF.
        
        Args:
            title: Title of the bookmark
            page: Target page number (0-based)
            
        Raises:
            PDFLoadError: If bookmark cannot be added
        """
        try:
            # Get current outline
            current_toc = self.doc.get_toc()
            
            # Add new bookmark at level 1 (top level)
            current_toc.append([1, title, page])
            
            # Update PDF outline
            self.doc.set_toc(current_toc)
            
            # Update our bookmark tree
            self._bookmark_tree = self._bookmark_detector.analyze_document(self.doc)
            
            # Mark as having unsaved changes
            self._has_unsaved_changes = True
            
            logger.info("Added bookmark '%s' at page %d", title, page + 1)
            
        except Exception as e:
            raise PDFLoadError(f"Failed to add bookmark: {e}") 
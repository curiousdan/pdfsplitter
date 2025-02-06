"""
Preview caching system for efficient memory management of PDF page previews.
"""
import logging
from collections import OrderedDict
from typing import Optional, Tuple

from PyQt6.QtGui import QImage

logger = logging.getLogger(__name__)

class PreviewCache:
    """
    Memory-efficient cache for PDF page previews.
    
    This class implements a least-recently-used (LRU) cache for page previews
    with a fixed maximum size and automatic cleanup of distant pages.
    """
    
    def __init__(self, max_size: int = 10, cleanup_threshold: int = 5) -> None:
        """
        Initialize the preview cache.
        
        Args:
            max_size: Maximum number of previews to keep in cache
            cleanup_threshold: Number of pages away from current to trigger cleanup
        """
        self._cache: OrderedDict[int, QImage] = OrderedDict()
        self._max_size = max_size
        self._cleanup_threshold = cleanup_threshold
        self._current_page: Optional[int] = None
        
        logger.debug(
            "Initialized PreviewCache with max_size=%d, cleanup_threshold=%d",
            max_size, cleanup_threshold
        )
    
    def get(self, page_num: int) -> Optional[QImage]:
        """
        Get a preview for the specified page number.
        
        Args:
            page_num: The page number to get preview for
            
        Returns:
            The cached preview image or None if not in cache
        """
        if page_num in self._cache:
            # Move to end (most recently used)
            preview = self._cache.pop(page_num)
            self._cache[page_num] = preview
            logger.debug("Cache hit for page %d", page_num)
            return preview
            
        logger.debug("Cache miss for page %d", page_num)
        return None
    
    def put(self, page_num: int, preview: QImage) -> None:
        """
        Add a preview to the cache.
        
        Args:
            page_num: The page number for this preview
            preview: The preview image to cache
        """
        # If at max size, remove least recently used
        if len(self._cache) >= self._max_size:
            _, _ = self._cache.popitem(last=False)
            logger.debug("Removed least recently used preview from cache")
        
        self._cache[page_num] = preview
        logger.debug("Added preview for page %d to cache", page_num)
    
    def update_current_page(self, page_num: int) -> None:
        """
        Update the current page and trigger cleanup if needed.
        
        Args:
            page_num: The new current page number
        """
        self._current_page = page_num
        self._cleanup_distant_pages()
        logger.debug("Updated current page to %d", page_num)
    
    def _cleanup_distant_pages(self) -> None:
        """Remove previews for pages far from the current page."""
        if self._current_page is None:
            return
            
        to_remove = []
        for cached_page in self._cache:
            if abs(cached_page - self._current_page) > self._cleanup_threshold:
                to_remove.append(cached_page)
        
        for page in to_remove:
            del self._cache[page]
            
        if to_remove:
            logger.debug(
                "Cleaned up %d distant pages from cache",
                len(to_remove)
            )
    
    def clear(self) -> None:
        """Clear all cached previews."""
        self._cache.clear()
        self._current_page = None
        logger.debug("Cleared preview cache")
    
    def get_stats(self) -> Tuple[int, int]:
        """
        Get current cache statistics.
        
        Returns:
            Tuple of (current cache size, maximum cache size)
        """
        return len(self._cache), self._max_size 
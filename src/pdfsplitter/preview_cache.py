"""
Preview caching system for efficient memory management of PDF page previews.
"""
import logging
import os
import psutil
from collections import OrderedDict
from typing import Optional, Tuple, Dict
from time import time

from PyQt6.QtGui import QImage
from PyQt6.QtCore import QTimer, QObject

logger = logging.getLogger(__name__)

class MemoryPressure:
    """Monitors system memory pressure."""
    
    # Memory thresholds (percentage)
    HIGH_PRESSURE = 85
    MEDIUM_PRESSURE = 70
    
    @staticmethod
    def get_memory_usage() -> float:
        """Get current memory usage percentage."""
        return psutil.Process(os.getpid()).memory_percent()
    
    @staticmethod
    def get_system_memory_usage() -> float:
        """Get system memory usage percentage."""
        return psutil.virtual_memory().percent
    
    @classmethod
    def get_pressure_level(cls) -> str:
        """Get current memory pressure level."""
        usage = cls.get_system_memory_usage()
        if usage > cls.HIGH_PRESSURE:
            return "high"
        elif usage > cls.MEDIUM_PRESSURE:
            return "medium"
        return "low"

class PreviewCache(QObject):
    """
    Memory-efficient cache for PDF page previews.
    
    This class implements a least-recently-used (LRU) cache for page previews
    with dynamic sizing based on memory pressure and predictive loading.
    """
    
    def __init__(
        self,
        initial_size: int = 10,
        cleanup_threshold: int = 5,
        idle_cleanup_seconds: int = 30
    ) -> None:
        """
        Initialize the preview cache.
        
        Args:
            initial_size: Initial maximum number of previews to keep in cache
            cleanup_threshold: Number of pages away from current to trigger cleanup
            idle_cleanup_seconds: Seconds of idle time before cleanup
        """
        super().__init__()
        self._cache: OrderedDict[int, QImage] = OrderedDict()
        self._access_times: Dict[int, float] = {}
        self._initial_size = initial_size
        self._max_size = initial_size
        self._cleanup_threshold = cleanup_threshold
        self._current_page: Optional[int] = None
        self._last_access_time = time()
        self._memory_usage = 0
        self._idle_cleanup_interval = idle_cleanup_seconds
        
        # Set up idle cleanup timer
        self._cleanup_timer = QTimer(self)
        self._cleanup_timer.timeout.connect(self._idle_cleanup)
        self._cleanup_timer.start(idle_cleanup_seconds * 1000)
        
        logger.debug(
            "Initialized PreviewCache with initial_size=%d, cleanup_threshold=%d",
            initial_size, cleanup_threshold
        )
    
    def get(self, page_num: int) -> Optional[QImage]:
        """
        Get a preview for the specified page number.
        
        Args:
            page_num: The page number to get preview for
            
        Returns:
            The cached preview image or None if not in cache
        """
        self._last_access_time = time()
        
        if page_num in self._cache:
            # Move to end (most recently used)
            preview = self._cache.pop(page_num)
            self._cache[page_num] = preview
            self._access_times[page_num] = time()
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
        self._last_access_time = time()
        
        # Check memory pressure and adjust cache size
        self._adjust_cache_size()
        
        # If at max size, remove least recently used
        while len(self._cache) >= self._max_size:
            removed_page, _ = self._cache.popitem(last=False)
            self._access_times.pop(removed_page, None)
            logger.debug("Removed least recently used preview from cache")
        
        # Add new preview
        self._cache[page_num] = preview
        self._access_times[page_num] = time()
        self._update_memory_usage()
        logger.debug("Added preview for page %d to cache", page_num)
    
    def update_current_page(self, page_num: int) -> None:
        """
        Update the current page and trigger cleanup if needed.
        
        Args:
            page_num: The new current page number
        """
        self._current_page = page_num
        self._cleanup_distant_pages()
        self._preload_adjacent_pages()
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
            self._access_times.pop(page, None)
            
        if to_remove:
            self._update_memory_usage()
            logger.debug(
                "Cleaned up %d distant pages from cache",
                len(to_remove)
            )
    
    def _idle_cleanup(self) -> None:
        """Clean up cache if idle for too long."""
        idle_time = time() - self._last_access_time
        if idle_time > self._idle_cleanup_interval:
            old_size = len(self._cache)
            
            # Clear all pages if idle
            self._cache.clear()
            self._access_times.clear()
            self._update_memory_usage()
            
            if old_size > 0:
                logger.debug(
                    "Idle cleanup removed %d pages from cache",
                    old_size
                )
    
    def _adjust_cache_size(self) -> None:
        """Adjust cache size based on memory pressure."""
        pressure = MemoryPressure.get_pressure_level()
        
        if pressure == "high":
            self._max_size = max(2, self._initial_size // 2)
            logger.debug("High memory pressure: reduced cache size to %d", self._max_size)
        elif pressure == "medium":
            self._max_size = max(3, int(self._initial_size * 0.75))
            logger.debug("Medium memory pressure: adjusted cache size to %d", self._max_size)
        elif len(self._cache) == self._max_size and pressure == "low":
            self._max_size = min(self._initial_size * 2, 20)
            logger.debug("Low memory pressure: increased cache size to %d", self._max_size)
    
    def _update_memory_usage(self) -> None:
        """Update tracked memory usage."""
        self._memory_usage = sum(
            image.sizeInBytes() for image in self._cache.values()
        )
        logger.debug("Current cache memory usage: %.2f MB", self._memory_usage / 1024 / 1024)
    
    def _preload_adjacent_pages(self) -> None:
        """Preload adjacent pages based on current page."""
        if self._current_page is None:
            return
            
        # Signal that adjacent pages should be loaded
        # This will be handled by the PDFDocument class
        logger.debug("Signaling preload for pages adjacent to %d", self._current_page)
    
    def clear(self) -> None:
        """Clear all cached previews."""
        self._cache.clear()
        self._access_times.clear()
        self._current_page = None
        self._memory_usage = 0
        self._max_size = self._initial_size  # Reset to initial size
        logger.debug("Cleared preview cache")
    
    def get_stats(self) -> Tuple[int, int, float]:
        """
        Get current cache statistics.
        
        Returns:
            Tuple of (current cache size, maximum cache size, memory usage in MB)
        """
        return len(self._cache), self._max_size, self._memory_usage / 1024 / 1024 
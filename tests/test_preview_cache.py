"""Tests for the preview cache implementation."""
import pytest
from unittest.mock import patch, MagicMock
from PyQt6.QtGui import QImage
from PyQt6.QtCore import QTimer

from pdfsplitter.preview_cache import PreviewCache, MemoryPressure

@pytest.fixture
def cache():
    """Create a PreviewCache instance for testing."""
    return PreviewCache(initial_size=3, cleanup_threshold=2)

@pytest.fixture
def sample_image():
    """Create a sample QImage for testing."""
    return QImage(100, 100, QImage.Format.Format_RGB888)

def test_cache_initialization(cache):
    """Test that cache is initialized with correct parameters."""
    stats = cache.get_stats()
    assert stats[0] == 0  # current size
    assert stats[1] == 3  # max size
    assert stats[2] == 0  # memory usage

def test_cache_put_and_get(cache, sample_image):
    """Test basic put and get operations."""
    cache.put(0, sample_image)
    cached = cache.get(0)
    assert cached is not None
    assert cached.width() == sample_image.width()
    assert cached.height() == sample_image.height()

def test_cache_miss(cache):
    """Test that getting non-existent page returns None."""
    assert cache.get(0) is None

def test_cache_max_size(cache, sample_image):
    """Test that cache respects max size limit."""
    # Fill cache
    for i in range(4):  # Max size is 3
        cache.put(i, sample_image)
    
    # First page should be evicted
    assert cache.get(0) is None
    # Later pages should still be present
    assert cache.get(1) is not None
    assert cache.get(2) is not None
    assert cache.get(3) is not None

def test_cache_lru_behavior(cache, sample_image):
    """Test least-recently-used eviction policy."""
    # Fill cache
    for i in range(3):
        cache.put(i, sample_image)
    
    # Access page 0 to make it most recently used
    cache.get(0)
    
    # Add new page, should evict page 1
    cache.put(3, sample_image)
    
    assert cache.get(0) is not None  # Most recently used
    assert cache.get(1) is None      # Evicted
    assert cache.get(2) is not None  # Still present
    assert cache.get(3) is not None  # Newly added

def test_cleanup_distant_pages(cache, sample_image):
    """Test cleanup of pages far from current page."""
    # Fill cache
    for i in range(3):
        cache.put(i, sample_image)
    
    # Set current page to 5
    cache.update_current_page(5)
    
    # Pages 0-2 should be cleaned up (threshold is 2)
    assert cache.get(0) is None
    assert cache.get(1) is None
    assert cache.get(2) is None

def test_clear_cache(cache, sample_image):
    """Test cache clearing."""
    # Fill cache
    for i in range(3):
        cache.put(i, sample_image)
    
    cache.clear()
    stats = cache.get_stats()
    assert stats[0] == 0  # size
    assert stats[1] == 3  # max size
    assert stats[2] == 0  # memory usage
    
    # All pages should be gone
    for i in range(3):
        assert cache.get(i) is None

def test_update_current_page_within_threshold(cache, sample_image):
    """Test that pages within threshold are preserved."""
    # Fill cache
    for i in range(3):
        cache.put(i, sample_image)
    
    # Set current page to 1 (threshold is 2)
    cache.update_current_page(1)
    
    # All pages should still be present (within threshold)
    assert cache.get(0) is not None
    assert cache.get(1) is not None
    assert cache.get(2) is not None

@patch('pdfsplitter.preview_cache.MemoryPressure.get_pressure_level')
def test_memory_pressure_high(mock_pressure, cache, sample_image):
    """Test cache behavior under high memory pressure."""
    mock_pressure.return_value = "high"
    
    # Fill cache
    for i in range(3):
        cache.put(i, sample_image)
    
    # Add another page under high pressure
    cache.put(3, sample_image)
    
    # Cache size should be reduced
    stats = cache.get_stats()
    assert stats[1] <= 2  # max size should be reduced

@patch('pdfsplitter.preview_cache.MemoryPressure.get_pressure_level')
def test_memory_pressure_low(mock_pressure, cache, sample_image):
    """Test cache behavior under low memory pressure."""
    mock_pressure.return_value = "low"
    
    # Fill cache to max
    for i in range(3):
        cache.put(i, sample_image)
    
    # Add another page under low pressure
    cache.put(3, sample_image)
    
    # Cache size should be increased
    stats = cache.get_stats()
    assert stats[1] > 3  # max size should be increased

def test_idle_cleanup(cache, sample_image):
    """Test cleanup of idle pages."""
    # Set cleanup interval to 100ms for testing
    cache._idle_cleanup_interval = 0.1  # 100ms
    cache._cleanup_timer.setInterval(100)
    
    # Fill cache
    for i in range(3):
        cache.put(i, sample_image)
    
    # Simulate idle time
    cache._last_access_time -= 1  # Set last access to 1 second ago
    
    # Trigger cleanup
    cache._idle_cleanup()
    
    # Cache should be empty
    assert len(cache._cache) == 0

def test_memory_usage_tracking(cache, sample_image):
    """Test memory usage tracking."""
    # Add some images
    for i in range(3):
        cache.put(i, sample_image)
    
    # Check memory usage
    stats = cache.get_stats()
    assert stats[2] > 0  # Memory usage should be tracked

def test_memory_pressure_detection():
    """Test memory pressure detection."""
    # Test pressure levels
    with patch('psutil.virtual_memory') as mock_vm:
        # Test high pressure
        mock_vm.return_value = MagicMock(percent=90)
        assert MemoryPressure.get_pressure_level() == "high"
        
        # Test medium pressure
        mock_vm.return_value = MagicMock(percent=75)
        assert MemoryPressure.get_pressure_level() == "medium"
        
        # Test low pressure
        mock_vm.return_value = MagicMock(percent=50)
        assert MemoryPressure.get_pressure_level() == "low" 
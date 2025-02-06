"""Tests for the RangeValidator class."""
import pytest
from pdfsplitter.range_management import RangeValidator, ValidationResult, ValidationError

@pytest.fixture
def validator():
    """Create a RangeValidator instance for testing."""
    return RangeValidator(max_pages=10)

@pytest.fixture
def validator_with_ranges():
    """Create a RangeValidator with existing ranges."""
    return RangeValidator(
        max_pages=10,
        existing_ranges=[
            ("Chapter 1", 0, 2),  # Pages 1-3
            ("Chapter 2", 3, 5),  # Pages 4-6
        ]
    )

def test_validate_name_empty(validator):
    """Test validation of empty name."""
    result = validator.validate_name("")
    assert not result.is_valid
    assert result.error_type == ValidationError.EMPTY_NAME
    assert "empty" in result.error_message.lower()
    
    result = validator.validate_name("   ")
    assert not result.is_valid
    assert result.error_type == ValidationError.EMPTY_NAME
    assert "empty" in result.error_message.lower()

def test_validate_name_duplicate(validator_with_ranges):
    """Test validation of duplicate names."""
    result = validator_with_ranges.validate_name("Chapter 1")
    assert not result.is_valid
    assert result.error_type == ValidationError.DUPLICATE_NAME
    assert "already exists" in result.error_message.lower()

def test_validate_name_valid(validator):
    """Test validation of valid names."""
    result = validator.validate_name("New Chapter")
    assert result.is_valid
    assert result.error_type is None
    assert result.error_message == ""

def test_validate_page_range_invalid_order(validator):
    """Test validation of invalid page order."""
    result = validator.validate_page_range(5, 3)
    assert not result.is_valid
    assert result.error_type == ValidationError.START_GREATER_THAN_END
    assert "less than" in result.error_message.lower()

def test_validate_page_range_out_of_bounds(validator):
    """Test validation of out-of-bounds pages."""
    # Test negative pages
    result = validator.validate_page_range(-1, 5)
    assert not result.is_valid
    assert result.error_type == ValidationError.PAGE_OUT_OF_BOUNDS
    
    # Test pages beyond max
    result = validator.validate_page_range(0, 10)
    assert not result.is_valid
    assert result.error_type == ValidationError.PAGE_OUT_OF_BOUNDS

def test_validate_page_range_overlap(validator_with_ranges):
    """Test validation of overlapping ranges."""
    # Test overlap with first range
    result = validator_with_ranges.validate_page_range(1, 3)
    assert not result.is_valid
    assert result.error_type == ValidationError.RANGE_OVERLAP
    
    # Test overlap with second range
    result = validator_with_ranges.validate_page_range(4, 6)
    assert not result.is_valid
    assert result.error_type == ValidationError.RANGE_OVERLAP
    
    # Test overlap spanning multiple ranges
    result = validator_with_ranges.validate_page_range(2, 4)
    assert not result.is_valid
    assert result.error_type == ValidationError.RANGE_OVERLAP

def test_validate_page_range_valid(validator_with_ranges):
    """Test validation of valid page ranges."""
    # Test range between existing ranges
    result = validator_with_ranges.validate_page_range(6, 7)
    assert result.is_valid
    assert result.error_type is None
    assert result.error_message == ""
    
    # Test range after existing ranges
    result = validator_with_ranges.validate_page_range(8, 9)
    assert result.is_valid
    assert result.error_type is None
    assert result.error_message == ""

def test_validate_all(validator):
    """Test complete validation."""
    # Test all valid
    result = validator.validate_all("New Chapter", 0, 2)
    assert result.is_valid
    assert result.error_type is None
    assert result.error_message == ""
    
    # Test invalid name (fails first)
    result = validator.validate_all("", 0, 2)
    assert not result.is_valid
    assert result.error_type == ValidationError.EMPTY_NAME
    
    # Test invalid range (fails after name)
    result = validator.validate_all("New Chapter", 5, 3)
    assert not result.is_valid
    assert result.error_type == ValidationError.START_GREATER_THAN_END

def test_validation_with_edge_cases(validator):
    """Test validation with edge cases."""
    # Test single-page range
    result = validator.validate_page_range(5, 5)
    assert result.is_valid
    
    # Test adjacent to max page
    result = validator.validate_page_range(8, 9)
    assert result.is_valid
    
    # Test first page
    result = validator.validate_page_range(0, 1)
    assert result.is_valid

def test_validation_with_special_characters(validator):
    """Test validation with special characters in names."""
    # Test with symbols
    result = validator.validate_name("Chapter #1")
    assert result.is_valid
    
    # Test with unicode
    result = validator.validate_name("Chapter 1 - 📚")
    assert result.is_valid
    
    # Test with whitespace
    result = validator.validate_name("  Chapter 1  ")
    assert result.is_valid 
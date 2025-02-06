"""Test utilities and test doubles."""
from typing import Optional, List, Tuple
from dataclasses import dataclass
from unittest.mock import Mock
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import pyqtSignal

@dataclass
class ValidationState:
    """Represents the current validation state for testing."""
    is_valid: bool = False
    error_message: str = ""
    error_fields: List[str] = None
    
    def __post_init__(self):
        if self.error_fields is None:
            self.error_fields = []

class MockRangeWidget(QWidget):
    """Mock range management widget for testing."""
    
    # Signals
    validation_changed = pyqtSignal(bool)
    range_added = pyqtSignal(str, int, int)
    range_removed = pyqtSignal(int)
    
    def __init__(self):
        super().__init__()
        self.validation_state = ValidationState()
        self.ranges: List[Tuple[str, int, int]] = []
        
        # Mock methods
        self.validate_input = Mock(return_value=True)
        self.set_error_state = Mock()
    
    def simulate_validation_change(self, is_valid: bool, message: str = "", fields: List[str] = None):
        """Simulate a validation state change."""
        self.validation_state = ValidationState(is_valid, message, fields)
        self.validation_changed.emit(is_valid)
        if not is_valid:
            self.set_error_state(message, fields)
    
    def simulate_range_added(self, name: str, start: int, end: int):
        """Simulate adding a range."""
        self.ranges.append((name, start, end))
        self.range_added.emit(name, start, end)
    
    def simulate_range_removed(self, index: int):
        """Simulate removing a range."""
        if 0 <= index < len(self.ranges):
            self.ranges.pop(index)
            self.range_removed.emit(index)

class MockSpinBox(QWidget):
    """Mock spin box for testing."""
    
    value_changed = pyqtSignal(int)
    
    def __init__(self):
        super().__init__()
        self._value = 0
        self._minimum = 0
        self._maximum = 100
        self.error_state = False
        self.error_message = ""
    
    def value(self) -> int:
        """Get current value."""
        return self._value
    
    def setValue(self, value: int):
        """Set current value."""
        if value < self._minimum:
            value = self._minimum
        elif value > self._maximum:
            value = self._maximum
            
        if value != self._value:
            self._value = value
            self.value_changed.emit(value)
    
    def setMinimum(self, value: int):
        """Set minimum value."""
        self._minimum = value
        if self._value < value:
            self.setValue(value)
    
    def setMaximum(self, value: int):
        """Set maximum value."""
        self._maximum = value
        if self._value > value:
            self.setValue(value)
    
    def set_error(self, error: bool, message: str = ""):
        """Set error state."""
        self.error_state = error
        self.error_message = message

def create_mock_validator(
    name_valid: bool = True,
    range_valid: bool = True,
    name_error: str = "",
    range_error: str = ""
) -> Mock:
    """Create a mock validator with predefined behavior."""
    validator = Mock()
    
    # Configure validate_name
    name_result = Mock()
    name_result.is_valid = name_valid
    name_result.error_message = name_error
    validator.validate_name.return_value = name_result
    
    # Configure validate_page_range
    range_result = Mock()
    range_result.is_valid = range_valid
    range_result.error_message = range_error
    validator.validate_page_range.return_value = range_result
    
    return validator

def assert_validation_state(widget: MockRangeWidget, expected_state: ValidationState):
    """Assert that a widget's validation state matches expectations."""
    assert widget.validation_state.is_valid == expected_state.is_valid
    if not expected_state.is_valid:
        assert widget.validation_state.error_message == expected_state.error_message
        assert set(widget.validation_state.error_fields) == set(expected_state.error_fields)

def assert_range_state(
    widget: MockRangeWidget,
    expected_ranges: List[Tuple[str, int, int]]
):
    """Assert that a widget's ranges match expectations."""
    assert len(widget.ranges) == len(expected_ranges)
    for actual, expected in zip(widget.ranges, expected_ranges):
        assert actual == expected 
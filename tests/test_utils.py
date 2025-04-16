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
    """
    Mock range management widget for testing.
    
    This has been simplified to match the updated RangeManagementWidget 
    that no longer manages ranges directly but just provides a split button.
    """
    
    # Signals
    validation_changed = pyqtSignal(bool)
    range_added = pyqtSignal(str, int, int)
    
    def __init__(self):
        super().__init__()
        self.validation_state = ValidationState()
        self.ranges: List[Tuple[str, int, int]] = []
        self.split_button = Mock()
    
    def simulate_validation_change(self, is_valid: bool, message: str = "", fields: List[str] = None):
        """Simulate a validation state change."""
        self.validation_state = ValidationState(is_valid, message, fields)
        self.validation_changed.emit(is_valid)
    
    def simulate_range_added(self, name: str, start: int, end: int):
        """Simulate adding a range."""
        self.ranges.append((name, start, end))
        self.range_added.emit(name, start, end)
    
    def set_split_enabled(self, enabled: bool):
        """Set whether the split button is enabled."""
        self.split_button.setEnabled(enabled)

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
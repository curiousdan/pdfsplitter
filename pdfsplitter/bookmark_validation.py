"""
Bookmark validation components for drag-drop operations.
"""
from dataclasses import dataclass
from enum import Enum
from typing import Optional

from .bookmark_manager import BookmarkNode, BookmarkLevel, BookmarkValidationError

class DropPosition(Enum):
    """Possible positions for dropping a bookmark."""
    BEFORE = "before"
    AFTER = "after"
    INSIDE = "inside"

@dataclass
class ValidationResult:
    """Result of a bookmark move validation."""
    valid: bool
    message: str
    level_change: Optional[int] = None  # Only used for INSIDE moves

class BookmarkLevelValidator:
    """
    Validates bookmark moves according to core rules:
    1. Basic structural rules (no cycles, valid parent-child)
    2. Page order within same level
    3. Simple level rules (children one level deeper than parent)
    """
    
    def validate_move(
        self,
        source: BookmarkNode,
        target: BookmarkNode,
        position: DropPosition
    ) -> ValidationResult:
        """
        Validate a bookmark move operation.
        
        Args:
            source: The bookmark being moved
            target: The target bookmark
            position: Where to drop relative to target
            
        Returns:
            ValidationResult with validation status and message
        """
        # 1. First validate structure
        structure_result = self._validate_structure(source, target, position)
        if not structure_result.valid:
            return structure_result
            
        # 2. Then validate levels
        level_result = self._validate_levels(source, target, position)
        if not level_result.valid:
            return level_result
            
        # 3. Finally validate page order
        page_result = self._validate_page_order(source, target, position)
        if not page_result.valid:
            return page_result
            
        # All validations passed - use level_change from level validation
        return level_result

    def _validate_structure(
        self,
        source: BookmarkNode,
        target: BookmarkNode,
        position: DropPosition
    ) -> ValidationResult:
        """
        Validate basic structural rules.
        
        Checks:
        1. Cannot move root
        2. Cannot move to self
        3. Cannot move to descendant
        """
        # Cannot move root
        if source.level == BookmarkLevel.ROOT:
            return ValidationResult(False, "Cannot move root bookmark")
            
        # Cannot move to self
        if source is target:
            return ValidationResult(False, "Cannot move bookmark to itself")
            
        # Cannot move to descendant
        current = target
        while current:
            if current is source:
                return ValidationResult(False, "Cannot move bookmark to its own descendant")
            current = current.parent
            
        return ValidationResult(True, "Structure valid")

    def _validate_page_order(
        self,
        source: BookmarkNode,
        target: BookmarkNode,
        position: DropPosition
    ) -> ValidationResult:
        """
        Validate that page order is maintained within levels.
        
        Rules:
        1. No duplicate pages at same level
        2. Pages must be in ascending order within level
        """
        if position == DropPosition.INSIDE:
            # When moving inside, just check against target's children
            for child in target.children:
                if child is not source and child.page == source.page:
                    return ValidationResult(False, "Multiple bookmarks on same page not allowed at same level")
        else:
            # For BEFORE/AFTER, check surrounding bookmarks at same level
            if not target.parent:
                return ValidationResult(True, "No siblings to check")
                
            # Check if source and target are siblings at the same level
            if (target.parent is source.parent and 
                source.level == target.level):
                return ValidationResult(True, "Siblings at same level can be reordered")
                
            # Get siblings at the same level, excluding source and target
            siblings = [s for s in target.parent.children 
                      if s is not source and s is not target and s.level == target.level]
            if not siblings:
                return ValidationResult(True, "No siblings to check")
                
            # Find target's position among remaining siblings
            target_idx = target.parent.children.index(target)
            
            # Get prev/next siblings for page order check
            prev_siblings = [s for s in siblings if target.parent.children.index(s) < target_idx]
            next_siblings = [s for s in siblings if target.parent.children.index(s) > target_idx]
                               
            if position == DropPosition.BEFORE:
                if prev_siblings and source.page < prev_siblings[-1].page:
                    return ValidationResult(False, "Move would violate page order")
            else:  # AFTER
                if next_siblings and source.page > next_siblings[0].page:
                    return ValidationResult(False, "Move would violate page order")
                    
        return ValidationResult(True, "Page order valid")

    def _validate_levels(
        self,
        source: BookmarkNode,
        target: BookmarkNode,
        position: DropPosition
    ) -> ValidationResult:
        """
        Validate level rules.
        
        Rules:
        1. Children must be exactly one level deeper than parent
        2. Siblings must be at same level
        3. Level can only change by 1 between adjacent bookmarks
        """
        if position == DropPosition.INSIDE:
            # For INSIDE moves, source must be exactly one level deeper than target
            target_level = target.level.value
            source_level = source.level.value
            
            # For INSIDE moves, we always want the source to be one level deeper
            # than the target, so calculate the change needed
            level_change = 1  # Always move one level deeper for INSIDE moves
            
            # Validate the level change
            if abs(source_level - (target_level + 1)) > 1:
                return ValidationResult(
                    valid=False,
                    message="Level can only change by 1 between adjacent bookmarks",
                    level_change=None
                )
                
            return ValidationResult(
                valid=True,
                message="Level rules valid",
                level_change=level_change
            )
        
        # For BEFORE/AFTER moves
        if source.level != target.level:
            # Calculate level difference
            level_diff = abs(source.level.value - target.level.value)
            if level_diff > 1:
                return ValidationResult(
                    valid=False,
                    message="Level can only change by 1 between adjacent bookmarks",
                    level_change=None
                )
            
            # Level change is 0 for BEFORE/AFTER since we're staying at same level
            return ValidationResult(
                valid=True,
                message="Level rules valid",
                level_change=0
            )
            
        return ValidationResult(
            valid=True,
            message="Level rules valid",
            level_change=0
        ) 
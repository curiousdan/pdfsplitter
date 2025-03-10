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
    """Result of a bookmark drop validation."""
    valid: bool
    message: str
    level_change: Optional[int] = None

class BookmarkLevelValidator:
    """
    Validates bookmark level changes during drag-drop operations.
    
    Follows PyMuPDF's bookmark hierarchy rules:
    1. Levels start at 1 (0 is reserved for root)
    2. A level can only be 1 more than the previous bookmark's level
    3. Page order must be maintained at each level
    """
    
    def validate_move(
        self,
        source: BookmarkNode,
        target: BookmarkNode,
        position: DropPosition
    ) -> ValidationResult:
        """
        Validate a bookmark move operation following PyMuPDF's rules.
        
        Args:
            source: The bookmark being moved
            target: The target bookmark
            position: Where to drop relative to target
            
        Returns:
            ValidationResult with validation status and message
        """
        # 1. Basic structural validation
        if source.level == BookmarkLevel.ROOT:
            return ValidationResult(
                valid=False,
                message="Cannot move root bookmark"
            )
            
        if source is target:
            return ValidationResult(
                valid=False,
                message="Cannot move bookmark to itself"
            )
            
        # Check for descendant relationship
        current = target
        while current:
            if current is source:
                return ValidationResult(
                    valid=False,
                    message="Cannot move bookmark to its own descendant"
                )
            current = current.parent

        # 2. Calculate new level and validate level changes
        if position == DropPosition.INSIDE:
            # When moving inside, new level is parent level + 1
            new_level = target.level.value + 1
            level_change = new_level - source.level.value
            
            # Check level difference with existing children
            if target.children:
                for child in target.children:
                    if child is not source and abs(child.level.value - new_level) > 1:
                        return ValidationResult(
                            valid=False,
                            message="Level can only change by 1 between parent and children"
                        )
        else:  # BEFORE or AFTER
            # When moving before/after, check adjacent bookmarks
            new_level = target.level.value
            level_change = new_level - source.level.value
            
            if target.parent:
                siblings = [s for s in target.parent.children if s is not source]
                if not siblings:
                    return ValidationResult(
                        valid=True,
                        message="Move operation valid",
                        level_change=level_change
                    )
                    
                idx = siblings.index(target)
                
                # Check previous sibling if moving BEFORE
                if position == DropPosition.BEFORE and idx > 0:
                    prev_sibling = siblings[idx - 1]
                    if abs(prev_sibling.level.value - new_level) > 1:
                        return ValidationResult(
                            valid=False,
                            message="Level can only change by 1 between adjacent bookmarks"
                        )
                
                # Check next sibling if moving AFTER
                if position == DropPosition.AFTER and idx < len(siblings) - 1:
                    next_sibling = siblings[idx + 1]
                    if abs(next_sibling.level.value - new_level) > 1:
                        return ValidationResult(
                            valid=False,
                            message="Level can only change by 1 between adjacent bookmarks"
                        )
                        
            # Check level difference with target
            if abs(target.level.value - source.level.value) > 1:
                return ValidationResult(
                    valid=False,
                    message="Level can only change by 1 between adjacent bookmarks"
                )

        # 3. Page order validation
        page_order_result = self.validate_page_order(source, target, position)
        if not page_order_result.valid:
            return page_order_result

        return ValidationResult(
            valid=True,
            message="Move operation valid",
            level_change=level_change
        )
    
    def validate_page_order(
        self,
        source: BookmarkNode,
        target: BookmarkNode,
        position: DropPosition
    ) -> ValidationResult:
        """
        Validate that the move maintains page order within each level.
        
        Args:
            source: The bookmark being moved
            target: The target bookmark
            position: Where to drop relative to target
            
        Returns:
            ValidationResult with validation status and message
        """
        if position == DropPosition.INSIDE:
            # When moving inside, only need to check against other children
            siblings = [s for s in target.children if s is not source]
            target_page = source.page
            
            # Check that page number is valid relative to siblings
            for sibling in siblings:
                if sibling.page == target_page:
                    return ValidationResult(
                        valid=False,
                        message="Multiple bookmarks on same page not allowed at same level"
                    )
        else:
            # When moving before/after, check surrounding bookmarks
            parent = target.parent
            if not parent:
                return ValidationResult(valid=True, message="Root level move allowed")
            
            siblings = [s for s in parent.children if s is not source]
            if not siblings:
                return ValidationResult(valid=True, message="No siblings to check")
                
            target_idx = siblings.index(target)
            
            # Get previous and next siblings at same level
            prev_sibling = next(
                (s for s in reversed(siblings[:target_idx]) if s.level == target.level),
                None
            )
            next_sibling = next(
                (s for s in siblings[target_idx + 1:] if s.level == target.level),
                None
            )
            
            # Check page order
            if position == DropPosition.BEFORE:
                if prev_sibling and source.page < prev_sibling.page:
                    return ValidationResult(
                        valid=False,
                        message="Move would violate page order"
                    )
                if source.page > target.page:
                    return ValidationResult(
                        valid=False,
                        message="Move would violate page order"
                    )
            else:  # AFTER
                if next_sibling and source.page > next_sibling.page:
                    return ValidationResult(
                        valid=False,
                        message="Move would violate page order"
                    )
                if source.page < target.page:
                    return ValidationResult(
                        valid=False,
                        message="Move would violate page order"
                    )
        
        return ValidationResult(valid=True, message="Page order valid") 
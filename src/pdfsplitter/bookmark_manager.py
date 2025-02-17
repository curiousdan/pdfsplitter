"""
Module for managing PDF bookmarks with validation and state tracking.

This module provides the core functionality for managing bookmarks in a PDF document,
including adding, removing, and modifying bookmarks with validation.
"""

from dataclasses import dataclass, field
from typing import Optional, List
from pathlib import Path
import logging
from enum import Enum

# Configure module logger
logger = logging.getLogger(__name__)

class BookmarkError(Exception):
    """Base exception for bookmark-related errors."""
    pass

class BookmarkValidationError(BookmarkError):
    """Exception raised when bookmark validation fails."""
    pass

class BookmarkOperationError(BookmarkError):
    """Exception raised when a bookmark operation fails."""
    pass

class BookmarkLevel(Enum):
    """Enumeration of possible bookmark levels."""
    ROOT = 0
    H1 = 1
    H2 = 2
    H3 = 3
    H4 = 4

@dataclass
class BookmarkNode:
    """
    Represents a single bookmark node in the bookmark tree.
    
    Attributes:
        title: The display text of the bookmark
        page: The target page number (1-based indexing)
        level: The nesting level of the bookmark
        children: List of child bookmarks
        modified: Whether this node has been modified
        parent: Optional reference to parent node
    """
    title: str
    page: int
    level: BookmarkLevel
    children: List['BookmarkNode'] = field(default_factory=list)
    modified: bool = False
    parent: Optional['BookmarkNode'] = None

    def __post_init__(self):
        """Validate bookmark attributes after initialization."""
        # Allow empty title only for root node
        if not self.title.strip() and self.level != BookmarkLevel.ROOT:
            raise BookmarkValidationError("Bookmark title cannot be empty")
        if self.page < 1:
            raise BookmarkValidationError(f"Invalid page number: {self.page}")

class BookmarkManager:
    """
    Manages the bookmark hierarchy and operations.
    
    This class handles all bookmark-related operations including addition,
    deletion, and modification of bookmarks. It maintains the bookmark tree
    structure and tracks modifications.
    """
    
    def __init__(self, total_pages: int):
        """
        Initialize the bookmark manager.
        
        Args:
            total_pages: Total number of pages in the PDF document
        """
        self.root = BookmarkNode("", 1, BookmarkLevel.ROOT)  # Root is a special node
        self.total_pages = total_pages
        self._modified = False
        logger.info("Initialized BookmarkManager with %d pages", total_pages)

    @property
    def modified(self) -> bool:
        """Whether any bookmarks have been modified."""
        return self._modified

    def _validate_page(self, page: int) -> None:
        """
        Validate that a page number is within bounds.
        
        Args:
            page: Page number to validate
            
        Raises:
            BookmarkValidationError: If page number is invalid
        """
        if not 1 <= page <= self.total_pages:
            raise BookmarkValidationError(
                f"Page number {page} out of range (1-{self.total_pages})"
            )

    def _validate_title(self, title: str, parent: Optional[BookmarkNode] = None) -> None:
        """
        Validate bookmark title.
        
        Args:
            title: Title to validate
            parent: Optional parent node to check for duplicates
            
        Raises:
            BookmarkValidationError: If title is invalid
        """
        if not title.strip():
            raise BookmarkValidationError("Bookmark title cannot be empty")
            
        # Check for duplicate titles at the same level
        if parent:
            siblings = parent.children
        else:
            siblings = self.root.children
            
        if any(node.title == title for node in siblings):
            raise BookmarkValidationError(
                f"Duplicate bookmark title '{title}' at the same level"
            )

    def add_bookmark(
        self, 
        page: int, 
        title: str, 
        parent: Optional[BookmarkNode] = None,
        level: BookmarkLevel = BookmarkLevel.H1
    ) -> BookmarkNode:
        """
        Add a new bookmark.
        
        Args:
            page: Target page number (1-based)
            title: Display text for the bookmark
            parent: Optional parent bookmark node
            level: Bookmark level in the hierarchy
            
        Returns:
            The newly created BookmarkNode
            
        Raises:
            BookmarkValidationError: If the bookmark parameters are invalid
        """
        self._validate_page(page)
        self._validate_title(title, parent)
        
        # Determine the actual parent node
        actual_parent = parent if parent is not None else self.root
        
        # Create and add the new bookmark
        new_bookmark = BookmarkNode(
            title=title,
            page=page,
            level=level,
            parent=actual_parent
        )
        
        actual_parent.children.append(new_bookmark)
        self._modified = True
        
        logger.info(
            "Added bookmark '%s' for page %d under parent '%s'",
            title, page, actual_parent.title or "ROOT"
        )
        
        return new_bookmark

    def delete_bookmark(self, node: BookmarkNode) -> None:
        """
        Delete a bookmark and its children.
        
        Args:
            node: The bookmark node to delete
            
        Raises:
            BookmarkOperationError: If the bookmark cannot be deleted
        """
        if node is self.root:
            raise BookmarkOperationError("Cannot delete root bookmark")
            
        if node.parent is None:
            raise BookmarkOperationError("Cannot delete bookmark with no parent")
            
        node.parent.children.remove(node)
        self._modified = True
        
        logger.info("Deleted bookmark '%s' and its children", node.title)

    def move_bookmark(
        self, 
        node: BookmarkNode, 
        new_parent: Optional[BookmarkNode],
        new_level: Optional[BookmarkLevel] = None
    ) -> None:
        """
        Move a bookmark to a new parent.
        
        Args:
            node: The bookmark to move
            new_parent: The new parent node (None for root level)
            new_level: Optional new level for the bookmark
            
        Raises:
            BookmarkOperationError: If the move operation is invalid
        """
        if node is self.root:
            raise BookmarkOperationError("Cannot move root bookmark")
            
        if new_parent is node:
            raise BookmarkOperationError("Cannot move bookmark to itself")
            
        # Check if new_parent is a descendant of node
        current = new_parent
        while current:
            if current is node:
                raise BookmarkOperationError(
                    "Cannot move bookmark to its own descendant"
                )
            current = current.parent
            
        # Remove from old parent
        if node.parent:
            node.parent.children.remove(node)
            
        # Add to new parent
        actual_parent = new_parent if new_parent is not None else self.root
        actual_parent.children.append(node)
        node.parent = actual_parent
        
        # Update level if specified
        if new_level is not None:
            node.level = new_level
            
        self._modified = True
        
        logger.info(
            "Moved bookmark '%s' to parent '%s'",
            node.title,
            actual_parent.title or "ROOT"
        )

    def get_bookmarks(self) -> List[BookmarkNode]:
        """Get all bookmarks in the current hierarchy."""
        return self.root.children.copy()

    def clear_modified_flag(self) -> None:
        """Clear the modified flag after saving."""
        self._modified = False
        logger.info("Cleared modified flag") 
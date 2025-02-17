"""
Module for managing PDF bookmarks with validation and state tracking.

This module provides the core functionality for managing bookmarks in a PDF document,
including adding, removing, and modifying bookmarks with validation.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Tuple
from pathlib import Path
import logging
from enum import Enum
import fitz  # PyMuPDF

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

class BookmarkSaveError(BookmarkError):
    """Exception raised when saving bookmarks fails."""
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
            
    def to_pdf_outline(self) -> List[Any]:
        """
        Convert the bookmark to a PDF outline list.
        
        Returns:
            A list in the format expected by PyMuPDF: [level, title, page, ...]
        """
        result = []
        
        def add_node(node: 'BookmarkNode', level: int):
            """Recursively add node and its children to the outline."""
            if node.level != BookmarkLevel.ROOT:
                # Add this node
                result.append([
                    level,
                    node.title,
                    node.page - 1  # Convert to 0-based indexing
                ])
            
            # Add children
            for child in node.children:
                add_node(child, level + 1 if node.level != BookmarkLevel.ROOT else 1)
        
        add_node(self, 1)
        return result

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
        
    @classmethod
    def from_pdf(cls, pdf_path: Path) -> 'BookmarkManager':
        """
        Create a BookmarkManager from a PDF file.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            A new BookmarkManager initialized with the PDF's bookmarks
            
        Raises:
            BookmarkError: If the PDF cannot be read
        """
        try:
            doc = fitz.open(str(pdf_path))
            manager = cls(doc.page_count)
            
            # Get the outline
            toc = doc.get_toc()
            
            # Track parent nodes at each level
            parents = {0: manager.root}
            
            # Process each outline item
            for item in toc:
                level, title, page = item[:3]  # Unpack level, title, page
                
                # Convert to 1-based page number
                page = doc[page].number + 1
                
                # Convert level to BookmarkLevel
                bookmark_level = BookmarkLevel(min(level, BookmarkLevel.H4.value))
                
                # Find the parent node
                parent_level = level - 1
                while parent_level not in parents and parent_level > 0:
                    parent_level -= 1
                parent = parents[parent_level]
                
                # Add the bookmark
                bookmark = manager.add_bookmark(
                    page=page,
                    title=title,
                    parent=parent,
                    level=bookmark_level
                )
                
                # Track this node as a potential parent
                parents[level] = bookmark
            
            manager._modified = False  # Reset modified flag after loading
            doc.close()
            
            return manager
            
        except Exception as e:
            raise BookmarkError(f"Failed to read PDF bookmarks: {e}")
            
    def save_to_pdf(self, pdf_path: Path, output_path: Optional[Path] = None) -> None:
        """
        Save the current bookmarks to a PDF file.
        
        Args:
            pdf_path: Path to the source PDF file
            output_path: Optional path for the output file. If not provided,
                        the source file will be modified in place.
                        
        Raises:
            BookmarkSaveError: If saving fails
        """
        try:
            # Open the PDF
            doc = fitz.open(str(pdf_path))
            
            # Convert bookmarks to outline
            outline = self.root.to_pdf_outline()
            
            # Set the outline
            doc.set_toc(outline)
            
            # Save the PDF
            save_path = output_path or pdf_path
            if save_path == pdf_path:
                # For in-place saves, use a temporary file
                temp_path = pdf_path.with_suffix('.tmp.pdf')
                try:
                    doc.save(str(temp_path))
                    doc.close()
                    temp_path.replace(pdf_path)
                finally:
                    # Clean up temp file if it still exists
                    if temp_path.exists():
                        temp_path.unlink()
            else:
                # Save to new file
                doc.save(str(save_path))
                doc.close()
            
            self._modified = False
            logger.info("Saved bookmarks to %s", save_path)
            
        except Exception as e:
            raise BookmarkSaveError(f"Failed to save bookmarks: {e}") 
"""
Bookmark detection and analysis functionality.
"""
import logging
from dataclasses import dataclass, field
from typing import List, Optional, Protocol

import fitz

logger = logging.getLogger(__name__)

@dataclass
class PageRange:
    """Represents a range of pages in the PDF."""
    start: int  # 0-based page number
    end: int    # 0-based page number, inclusive
    title: str
    level: int

    def __post_init__(self):
        """Validate page range."""
        if self.start > self.end:
            raise ValueError(f"Invalid page range: {self.start} > {self.end}")
        if self.start < 0:
            raise ValueError(f"Invalid start page: {self.start}")
        if self.level < 0:
            raise ValueError(f"Invalid level: {self.level}")

@dataclass
class BookmarkNode:
    """Represents a node in the PDF bookmark tree."""
    title: str
    page: int  # 0-based page number
    level: int
    children: List['BookmarkNode'] = field(default_factory=list)

@dataclass
class BookmarkTree:
    """Complete bookmark structure with detected chapter ranges."""
    root: BookmarkNode
    chapter_ranges: List[PageRange]

class PatternMatcher(Protocol):
    """Interface for chapter detection patterns."""
    
    def matches(self, bookmark: BookmarkNode) -> bool:
        """
        Check if this bookmark matches the pattern.
        
        Args:
            bookmark: The bookmark node to check
            
        Returns:
            True if the bookmark matches this pattern
        """
        ...
    
    def extract_range(self, bookmark: BookmarkNode, next_bookmark: Optional[BookmarkNode]) -> PageRange:
        """
        Extract page range from matching bookmark.
        
        Args:
            bookmark: The bookmark node that matched
            next_bookmark: The next bookmark at the same level, if any
            
        Returns:
            Extracted page range
            
        Raises:
            ValueError: If range cannot be extracted
        """
        ...

class ChapterTitlePattern(PatternMatcher):
    """Detects chapters based on common chapter title patterns."""
    
    _CHAPTER_KEYWORDS = {'chapter', 'section', 'part'}
    
    def matches(self, bookmark: BookmarkNode) -> bool:
        """Check if bookmark title matches chapter patterns."""
        # Only match top-level bookmarks (level 0)
        if bookmark.level > 0:
            return False
            
        title_lower = bookmark.title.lower()
        
        # Check for common chapter title patterns
        for keyword in self._CHAPTER_KEYWORDS:
            if title_lower.startswith(keyword):
                logger.debug("Matched chapter title pattern: %s", bookmark.title)
                return True
        
        # Check for numbered section pattern (e.g., "1.", "1.1", "A.")
        words = title_lower.split()
        if words and (
            (words[0][0].isdigit() and '.' not in words[0]) or  # Just a number
            (words[0][0].isalpha() and words[0][-1] == '.')  # Letter with period
        ):
            logger.debug("Matched numbered section pattern: %s", bookmark.title)
            return True
        
        return False
    
    def extract_range(self, bookmark: BookmarkNode, next_bookmark: Optional[BookmarkNode]) -> PageRange:
        """Extract page range from chapter bookmark."""
        start = bookmark.page
        
        # End page is either the page before next bookmark or end of document
        end = next_bookmark.page - 1 if next_bookmark else start + 10  # Default chunk size
        
        return PageRange(
            start=start,
            end=end,
            title=bookmark.title,
            level=bookmark.level
        )

class BookmarkDetector:
    """Handles PDF bookmark analysis and chapter detection."""
    
    def __init__(self) -> None:
        """Initialize the detector with default patterns."""
        self._patterns: List[PatternMatcher] = [
            ChapterTitlePattern()
        ]
        logger.debug("Initialized BookmarkDetector with %d patterns", len(self._patterns))
    
    def _build_tree(self, doc: fitz.Document) -> BookmarkNode:
        """
        Build bookmark tree from PDF document.
        
        Args:
            doc: The PDF document to analyze
            
        Returns:
            Root node of bookmark tree
        """
        # Create root node
        root = BookmarkNode(title="root", page=0, level=-1)
        
        # Get raw bookmark data
        try:
            bookmarks = doc.get_toc()
            logger.debug("Found %d bookmarks in document", len(bookmarks))
        except Exception as e:
            logger.warning("Failed to get bookmarks: %s", str(e))
            return root
        
        # Convert to nodes
        current_path = [root]
        
        for level, title, page in bookmarks:
            # Adjust for 0-based page numbers
            page = page - 1 if page > 0 else 0
            
            # Create new node
            node = BookmarkNode(
                title=title,
                page=page,
                level=level - 1  # Convert to 0-based levels
            )
            
            # Find parent node
            while len(current_path) > level:
                current_path.pop()
            
            # Add to parent
            current_path[-1].children.append(node)
            current_path.append(node)
        
        return root
    
    def _detect_ranges(self, tree: BookmarkNode) -> List[PageRange]:
        """
        Detect chapter ranges from bookmark tree.
        
        Args:
            tree: Root of bookmark tree
            
        Returns:
            List of detected page ranges
        """
        ranges: List[PageRange] = []
        
        def process_level(nodes: List[BookmarkNode]) -> None:
            """Process all nodes at current level."""
            for i, node in enumerate(nodes):
                # Try each pattern
                for pattern in self._patterns:
                    if pattern.matches(node):
                        try:
                            # Get next node at same level for range end
                            next_node = nodes[i + 1] if i + 1 < len(nodes) else None
                            page_range = pattern.extract_range(node, next_node)
                            ranges.append(page_range)
                            logger.debug(
                                "Detected range: %s (pages %d-%d)",
                                page_range.title, page_range.start + 1, page_range.end + 1
                            )
                            break
                        except ValueError as e:
                            logger.warning(
                                "Failed to extract range for '%s': %s",
                                node.title, str(e)
                            )
                
                # Process child nodes
                if node.children:
                    process_level(node.children)
        
        # Start processing from root's children
        if tree.children:
            process_level(tree.children)
        
        return ranges
    
    def analyze_document(self, doc: fitz.Document) -> BookmarkTree:
        """
        Analyze PDF document and detect chapter ranges.
        
        Args:
            doc: The PDF document to analyze
            
        Returns:
            BookmarkTree with structure and detected ranges
        """
        logger.info("Starting bookmark analysis")
        
        # Build tree
        tree = self._build_tree(doc)
        
        # Detect ranges
        ranges = self._detect_ranges(tree)
        
        logger.info("Bookmark analysis complete, found %d ranges", len(ranges))
        return BookmarkTree(root=tree, chapter_ranges=ranges)
    
    def add_pattern(self, pattern: PatternMatcher) -> None:
        """
        Add a new pattern matcher.
        
        Args:
            pattern: Pattern matcher to add
        """
        self._patterns.append(pattern)
        logger.debug("Added new pattern matcher, total patterns: %d", len(self._patterns)) 
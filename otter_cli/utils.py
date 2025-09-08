"""
Utility functions for the Otter CLI
"""

import re


def slugify(text: str, max_length: int = 100) -> str:
    """
    Convert text to a safe filename slug - preserves case for human readability
    
    Keeps alphanumeric, hyphens, and underscores
    Removes/replaces spaces and special characters
    Mac and Dropbox safe
    """
    if not text:
        return "Untitled"
    
    # Convert to string and strip whitespace (preserve case)
    slug = str(text).strip()
    
    # Replace common separators with hyphens
    slug = re.sub(r'[\s/_\|]+', '-', slug)
    
    # Remove special characters but keep safe ones (preserve case with \w)
    slug = re.sub(r'[^\w\-\.]', '', slug)
    
    # Remove multiple consecutive hyphens
    slug = re.sub(r'\-+', '-', slug)
    
    # Remove leading/trailing hyphens
    slug = slug.strip('-')
    
    # Ensure max length
    if len(slug) > max_length:
        slug = slug[:max_length].rstrip('-')
    
    # Fallback if slug becomes empty
    if not slug:
        return "Untitled"
        
    return slug

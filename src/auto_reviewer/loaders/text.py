"""Text document loader with stable paragraph ID generation."""

import hashlib
import re
from pathlib import Path
from typing import List, Dict

from ..config import DocumentChunk


def load_paragraphs(path: str) -> List[DocumentChunk]:
    """
    Load paragraphs from a text file with stable paragraph IDs.
    
    Args:
        path: Path to the text file
        
    Returns:
        List of DocumentChunk objects with stable IDs
    """
    file_path = Path(path)
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Split into paragraphs - any double newline or more
    paragraphs = re.split(r'\n\s*\n+', content.strip())
    
    chunks = []
    for i, paragraph in enumerate(paragraphs):
        paragraph = paragraph.strip()
        
        # Skip empty paragraphs
        if not paragraph:
            continue
        
        # Generate stable paragraph ID
        # Format: filename_hash_index for uniqueness and stability
        content_hash = hashlib.md5(paragraph.encode('utf-8')).hexdigest()[:8]
        paragraph_id = f"{file_path.stem}_{content_hash}_{i:03d}"
        
        # Create document chunk
        chunk = DocumentChunk(
            paragraph_id=paragraph_id,
            text=paragraph,
            hash=content_hash,
            page_number=None,  # Text files don't have page numbers
            chunk_index=i
        )
        
        chunks.append(chunk)
    
    return chunks


def is_supported_format(path: str) -> bool:
    """Check if the file format is supported by this loader."""
    supported_extensions = {'.txt', '.md', '.text'}
    return Path(path).suffix.lower() in supported_extensions


def get_document_info(path: str) -> Dict[str, any]:
    """Get basic information about the text document."""
    file_path = Path(path)
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Count paragraphs (non-empty after splitting)
    paragraphs = [p.strip() for p in re.split(r'\n\s*\n+', content.strip()) if p.strip()]
    
    # Basic statistics
    word_count = len(content.split())
    char_count = len(content)
    line_count = len(content.splitlines())
    
    return {
        'format': 'text',
        'file_size': file_path.stat().st_size,
        'paragraph_count': len(paragraphs),
        'word_count': word_count,
        'character_count': char_count,
        'line_count': line_count,
        'encoding': 'utf-8'
    }
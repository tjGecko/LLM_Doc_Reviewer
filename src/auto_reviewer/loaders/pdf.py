"""PDF document loader with stable paragraph ID generation."""

import hashlib
import re
from pathlib import Path
from typing import List, Dict, Optional

try:
    import pypdf
    HAS_PYPDF = True
except ImportError:
    HAS_PYPDF = False

from ..config import DocumentChunk


def load_paragraphs(path: str) -> List[DocumentChunk]:
    """
    Load paragraphs from a PDF file with stable paragraph IDs.
    
    Args:
        path: Path to the PDF file
        
    Returns:
        List of DocumentChunk objects with stable IDs
        
    Raises:
        ImportError: If pypdf is not installed
        Exception: If PDF cannot be read
    """
    if not HAS_PYPDF:
        raise ImportError(
            "pypdf is required for PDF support. Install with: pip install pypdf"
        )
    
    file_path = Path(path)
    chunks = []
    chunk_index = 0
    
    try:
        with open(file_path, 'rb') as f:
            reader = pypdf.PdfReader(f)
            
            for page_num, page in enumerate(reader.pages, 1):
                # Extract text from the page
                try:
                    text = page.extract_text()
                except Exception as e:
                    # Skip problematic pages but log the issue
                    print(f"Warning: Could not extract text from page {page_num}: {e}")
                    continue
                
                if not text.strip():
                    continue
                
                # Split page text into paragraphs
                paragraphs = re.split(r'\n\s*\n+', text.strip())
                
                for para_num, paragraph in enumerate(paragraphs):
                    paragraph = paragraph.strip()
                    
                    # Skip empty or very short paragraphs
                    if not paragraph or len(paragraph) < 10:
                        continue
                    
                    # Clean up common PDF extraction artifacts
                    paragraph = clean_pdf_text(paragraph)
                    
                    # Generate stable paragraph ID
                    content_hash = hashlib.md5(paragraph.encode('utf-8')).hexdigest()[:8]
                    paragraph_id = f"{file_path.stem}_p{page_num:03d}_{content_hash}_{chunk_index:03d}"
                    
                    # Create document chunk
                    chunk = DocumentChunk(
                        paragraph_id=paragraph_id,
                        text=paragraph,
                        hash=content_hash,
                        page_number=page_num,
                        chunk_index=chunk_index
                    )
                    
                    chunks.append(chunk)
                    chunk_index += 1
    
    except Exception as e:
        raise Exception(f"Failed to read PDF {path}: {e}")
    
    return chunks


def clean_pdf_text(text: str) -> str:
    """
    Clean common PDF extraction artifacts.
    
    Args:
        text: Raw text extracted from PDF
        
    Returns:
        Cleaned text
    """
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove common PDF artifacts
    # Remove single character lines (often formatting artifacts)
    lines = text.split('\n')
    cleaned_lines = []
    
    for line in lines:
        line = line.strip()
        # Skip very short lines that are likely formatting artifacts
        if len(line) > 2:
            cleaned_lines.append(line)
    
    text = '\n'.join(cleaned_lines)
    
    # Fix common word breaks
    text = re.sub(r'(\w+)-\s+(\w+)', r'\1\2', text)  # Fix hyphenated words
    text = re.sub(r'\s+', ' ', text)  # Normalize whitespace again
    
    return text.strip()


def is_supported_format(path: str) -> bool:
    """Check if the file format is supported by this loader."""
    return Path(path).suffix.lower() == '.pdf'


def get_document_info(path: str) -> Dict[str, any]:
    """Get basic information about the PDF document."""
    if not HAS_PYPDF:
        return {
            'format': 'pdf',
            'error': 'pypdf not installed'
        }
    
    file_path = Path(path)
    
    try:
        with open(file_path, 'rb') as f:
            reader = pypdf.PdfReader(f)
            
            # Extract metadata
            metadata = reader.metadata or {}
            
            # Count pages and estimate content
            page_count = len(reader.pages)
            total_text = ""
            
            for page in reader.pages[:min(5, page_count)]:  # Sample first 5 pages
                try:
                    text = page.extract_text()
                    total_text += text + "\n"
                except:
                    continue
            
            # Estimate total content based on sample
            if total_text:
                sample_words = len(total_text.split())
                estimated_total_words = int(sample_words * page_count / min(5, page_count))
            else:
                estimated_total_words = 0
            
            return {
                'format': 'pdf',
                'file_size': file_path.stat().st_size,
                'page_count': page_count,
                'estimated_word_count': estimated_total_words,
                'title': metadata.get('/Title', 'Unknown'),
                'author': metadata.get('/Author', 'Unknown'),
                'creator': metadata.get('/Creator', 'Unknown'),
                'creation_date': str(metadata.get('/CreationDate', 'Unknown')),
                'has_text_content': len(total_text.strip()) > 0
            }
    
    except Exception as e:
        return {
            'format': 'pdf',
            'file_size': file_path.stat().st_size,
            'error': str(e)
        }
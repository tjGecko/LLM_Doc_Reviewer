"""Unified document loader interface for all supported formats."""

from pathlib import Path
from typing import List, Dict

from ..config import DocumentChunk
from . import text, pdf, docx


def load_document(path: str) -> List[DocumentChunk]:
    """
    Load document paragraphs using the appropriate loader for the file format.
    
    Args:
        path: Path to the document file
        
    Returns:
        List of DocumentChunk objects with stable IDs
        
    Raises:
        ValueError: If file format is not supported
        ImportError: If required dependencies are missing
        Exception: If document cannot be read
    """
    file_path = Path(path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"Document not found: {path}")
    
    # Determine the appropriate loader based on file extension
    suffix = file_path.suffix.lower()
    
    if suffix in {'.txt', '.md', '.text'}:
        return text.load_paragraphs(path)
    elif suffix == '.pdf':
        return pdf.load_paragraphs(path)
    elif suffix in {'.docx', '.doc'}:
        return docx.load_paragraphs(path)
    else:
        raise ValueError(
            f"Unsupported document format: {suffix}. "
            f"Supported formats: .txt, .md, .pdf, .docx, .doc"
        )


def get_document_info(path: str) -> Dict[str, any]:
    """
    Get information about a document using the appropriate loader.
    
    Args:
        path: Path to the document file
        
    Returns:
        Dictionary with document information
    """
    file_path = Path(path)
    
    if not file_path.exists():
        return {
            'error': f'Document not found: {path}',
            'exists': False
        }
    
    # Determine the appropriate loader based on file extension
    suffix = file_path.suffix.lower()
    
    try:
        if suffix in {'.txt', '.md', '.text'}:
            return text.get_document_info(path)
        elif suffix == '.pdf':
            return pdf.get_document_info(path)
        elif suffix in {'.docx', '.doc'}:
            return docx.get_document_info(path)
        else:
            return {
                'format': 'unknown',
                'file_size': file_path.stat().st_size,
                'error': f'Unsupported format: {suffix}'
            }
    except Exception as e:
        return {
            'format': suffix.lstrip('.'),
            'file_size': file_path.stat().st_size if file_path.exists() else 0,
            'error': str(e)
        }


def is_supported_format(path: str) -> bool:
    """
    Check if the document format is supported.
    
    Args:
        path: Path to the document file
        
    Returns:
        True if format is supported, False otherwise
    """
    suffix = Path(path).suffix.lower()
    return suffix in {'.txt', '.md', '.text', '.pdf', '.docx', '.doc'}


def get_supported_formats() -> Dict[str, List[str]]:
    """
    Get information about supported document formats.
    
    Returns:
        Dictionary mapping format categories to file extensions
    """
    return {
        'text': ['.txt', '.md', '.text'],
        'pdf': ['.pdf'],
        'word': ['.docx', '.doc'],
        'all': ['.txt', '.md', '.text', '.pdf', '.docx', '.doc']
    }


def validate_document_access(path: str) -> None:
    """
    Validate that a document can be accessed and processed.
    
    Args:
        path: Path to the document file
        
    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If format is not supported
        PermissionError: If file cannot be read
    """
    file_path = Path(path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"Document not found: {path}")
    
    if not is_supported_format(path):
        suffix = file_path.suffix.lower()
        supported = get_supported_formats()['all']
        raise ValueError(
            f"Unsupported document format: {suffix}. "
            f"Supported formats: {', '.join(supported)}"
        )
    
    # Check if file is readable
    try:
        with open(file_path, 'rb') as f:
            f.read(1)  # Try to read one byte
    except PermissionError:
        raise PermissionError(f"Cannot read document: {path}")
    except Exception as e:
        raise Exception(f"Error accessing document {path}: {e}")


__all__ = [
    'load_document',
    'get_document_info', 
    'is_supported_format',
    'get_supported_formats',
    'validate_document_access'
]
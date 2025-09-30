"""Embedding utilities for document vectorization."""

import logging
import numpy as np
from typing import List, Dict, Optional, Union
from pathlib import Path
import pickle

try:
    from sentence_transformers import SentenceTransformer
    HAS_SENTENCE_TRANSFORMERS = True
except ImportError:
    HAS_SENTENCE_TRANSFORMERS = False

from .config import EmbeddingConfig, DocumentChunk

logger = logging.getLogger(__name__)


class EmbeddingModel:
    """Wrapper for embedding models with caching and batch processing."""
    
    def __init__(self, config: EmbeddingConfig):
        """
        Initialize the embedding model.
        
        Args:
            config: Embedding configuration
            
        Raises:
            ImportError: If sentence-transformers is not installed
        """
        if not HAS_SENTENCE_TRANSFORMERS:
            raise ImportError(
                "sentence-transformers is required for embeddings. "
                "Install with: pip install sentence-transformers"
            )
        
        self.config = config
        self.model = None
        self._model_loaded = False
        
    def _load_model(self):
        """Load the sentence transformer model."""
        if not self._model_loaded:
            logger.info(f"Loading embedding model: {self.config.model}")
            try:
                self.model = SentenceTransformer(self.config.model)
                self._model_loaded = True
                logger.info(f"Successfully loaded model: {self.config.model}")
            except Exception as e:
                logger.error(f"Failed to load embedding model: {e}")
                raise
    
    def embed_texts(self, texts: List[str]) -> np.ndarray:
        """
        Generate embeddings for a list of texts.
        
        Args:
            texts: List of text strings to embed
            
        Returns:
            numpy array of embeddings with shape (n_texts, embedding_dim)
        """
        if not texts:
            return np.array([])
        
        self._load_model()
        
        try:
            # Process in batches to manage memory
            embeddings = []
            batch_size = self.config.batch_size
            
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                
                # Truncate texts if they're too long
                truncated_batch = []
                for text in batch:
                    if len(text) > self.config.max_length:
                        # Simple truncation - could be improved with smart truncation
                        text = text[:self.config.max_length - 3] + "..."
                    truncated_batch.append(text)
                
                batch_embeddings = self.model.encode(
                    truncated_batch,
                    batch_size=len(truncated_batch),
                    show_progress_bar=len(texts) > 50  # Only show progress for large batches
                )
                embeddings.append(batch_embeddings)
            
            return np.vstack(embeddings) if embeddings else np.array([])
            
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            raise
    
    def embed_chunks(self, chunks: List[DocumentChunk]) -> np.ndarray:
        """
        Generate embeddings for document chunks.
        
        Args:
            chunks: List of document chunks
            
        Returns:
            numpy array of embeddings
        """
        texts = [chunk.text for chunk in chunks]
        return self.embed_texts(texts)
    
    def get_embedding_dim(self) -> int:
        """Get the dimensionality of the embeddings."""
        self._load_model()
        return self.model.get_sentence_embedding_dimension()
    
    def save_cache(self, cache_path: Path, texts: List[str], embeddings: np.ndarray):
        """
        Save embeddings to cache file.
        
        Args:
            cache_path: Path to save cache
            texts: Original texts
            embeddings: Corresponding embeddings
        """
        cache_data = {
            'model': self.config.model,
            'texts': texts,
            'embeddings': embeddings,
            'text_hashes': [hash(text) for text in texts]  # For quick lookup
        }
        
        try:
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            with open(cache_path, 'wb') as f:
                pickle.dump(cache_data, f)
            logger.debug(f"Saved embedding cache to {cache_path}")
        except Exception as e:
            logger.warning(f"Failed to save embedding cache: {e}")
    
    def load_cache(self, cache_path: Path) -> Optional[Dict]:
        """
        Load embeddings from cache file.
        
        Args:
            cache_path: Path to cache file
            
        Returns:
            Cache data if valid, None otherwise
        """
        if not cache_path.exists():
            return None
        
        try:
            with open(cache_path, 'rb') as f:
                cache_data = pickle.load(f)
            
            # Validate cache is for the same model
            if cache_data.get('model') != self.config.model:
                logger.debug(f"Cache model mismatch: {cache_data.get('model')} vs {self.config.model}")
                return None
            
            logger.debug(f"Loaded embedding cache from {cache_path}")
            return cache_data
            
        except Exception as e:
            logger.warning(f"Failed to load embedding cache: {e}")
            return None


def create_embeddings(
    chunks: List[DocumentChunk], 
    config: EmbeddingConfig,
    cache_dir: Optional[Path] = None
) -> np.ndarray:
    """
    Create embeddings for document chunks with optional caching.
    
    Args:
        chunks: Document chunks to embed
        config: Embedding configuration
        cache_dir: Optional directory for caching embeddings
        
    Returns:
        numpy array of embeddings
    """
    if not chunks:
        return np.array([])
    
    # Initialize embedding model
    embedding_model = EmbeddingModel(config)
    
    # Check cache if enabled
    if cache_dir:
        cache_path = cache_dir / f"embeddings_{config.model.replace('/', '_')}.pkl"
        cached_data = embedding_model.load_cache(cache_path)
        
        if cached_data:
            # Check if all chunks are in cache
            cached_hashes = set(cached_data['text_hashes'])
            chunk_hashes = [hash(chunk.text) for chunk in chunks]
            
            if all(h in cached_hashes for h in chunk_hashes):
                # All chunks are cached, extract relevant embeddings
                cached_texts = cached_data['texts']
                cached_embeddings = cached_data['embeddings']
                
                # Create mapping from hash to embedding
                hash_to_embedding = {}
                for text, embedding in zip(cached_texts, cached_embeddings):
                    hash_to_embedding[hash(text)] = embedding
                
                # Extract embeddings in order
                result_embeddings = []
                for chunk_hash in chunk_hashes:
                    result_embeddings.append(hash_to_embedding[chunk_hash])
                
                logger.info(f"Loaded {len(chunks)} embeddings from cache")
                return np.array(result_embeddings)
    
    # Generate new embeddings
    logger.info(f"Generating embeddings for {len(chunks)} chunks")
    embeddings = embedding_model.embed_chunks(chunks)
    
    # Save to cache if enabled
    if cache_dir and embeddings.size > 0:
        texts = [chunk.text for chunk in chunks]
        embedding_model.save_cache(cache_dir / f"embeddings_{config.model.replace('/', '_')}.pkl", 
                                 texts, embeddings)
    
    return embeddings


def compute_similarity(embeddings1: np.ndarray, embeddings2: np.ndarray) -> np.ndarray:
    """
    Compute cosine similarity between two sets of embeddings.
    
    Args:
        embeddings1: First set of embeddings (n1, dim)
        embeddings2: Second set of embeddings (n2, dim)
        
    Returns:
        Similarity matrix (n1, n2)
    """
    if embeddings1.size == 0 or embeddings2.size == 0:
        return np.array([])
    
    # Normalize embeddings
    embeddings1_norm = embeddings1 / np.linalg.norm(embeddings1, axis=1, keepdims=True)
    embeddings2_norm = embeddings2 / np.linalg.norm(embeddings2, axis=1, keepdims=True)
    
    # Compute cosine similarity
    similarity = np.dot(embeddings1_norm, embeddings2_norm.T)
    
    return similarity
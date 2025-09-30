"""FAISS-based vector database for document storage and retrieval."""

import logging
import numpy as np
from typing import List, Dict, Optional, Tuple, Any
from pathlib import Path
import json
import pickle

try:
    import faiss
    HAS_FAISS = True
except ImportError:
    HAS_FAISS = False

from .config import DocumentChunk, RetrievalConfig
from .embed import compute_similarity

logger = logging.getLogger(__name__)


class VectorDatabase:
    """FAISS-based vector database for document chunks."""
    
    def __init__(self, embedding_dim: int, index_type: str = "IndexFlatIP"):
        """
        Initialize the vector database.
        
        Args:
            embedding_dim: Dimension of the embeddings
            index_type: Type of FAISS index to use (IndexFlatIP for cosine similarity)
            
        Raises:
            ImportError: If FAISS is not installed
        """
        if not HAS_FAISS:
            raise ImportError(
                "faiss-cpu is required for vector database. "
                "Install with: pip install faiss-cpu"
            )
        
        self.embedding_dim = embedding_dim
        self.index_type = index_type
        
        # Initialize FAISS index
        if index_type == "IndexFlatIP":
            self.index = faiss.IndexFlatIP(embedding_dim)  # Inner product (cosine similarity)
        elif index_type == "IndexFlatL2":
            self.index = faiss.IndexFlatL2(embedding_dim)  # L2 distance
        else:
            raise ValueError(f"Unsupported index type: {index_type}")
        
        # Store document chunks and metadata
        self.chunks: List[DocumentChunk] = []
        self.chunk_metadata: List[Dict[str, Any]] = []
        
    def add_chunks(self, chunks: List[DocumentChunk], embeddings: np.ndarray):
        """
        Add document chunks and their embeddings to the database.
        
        Args:
            chunks: List of document chunks
            embeddings: Corresponding embeddings array
        """
        if len(chunks) != embeddings.shape[0]:
            raise ValueError("Number of chunks must match number of embeddings")
        
        if embeddings.shape[1] != self.embedding_dim:
            raise ValueError(f"Embedding dimension mismatch: {embeddings.shape[1]} vs {self.embedding_dim}")
        
        # Normalize embeddings for cosine similarity (if using IndexFlatIP)
        if self.index_type == "IndexFlatIP":
            norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
            embeddings = embeddings / norms
        
        # Add to FAISS index
        self.index.add(embeddings.astype('float32'))
        
        # Store chunks and metadata
        for chunk in chunks:
            self.chunks.append(chunk)
            self.chunk_metadata.append({
                'paragraph_id': chunk.paragraph_id,
                'hash': chunk.hash,
                'page_number': chunk.page_number,
                'chunk_index': chunk.chunk_index,
                'text_length': len(chunk.text)
            })
        
        logger.debug(f"Added {len(chunks)} chunks to vector database")
    
    def search(
        self, 
        query_embedding: np.ndarray, 
        k: int = 5, 
        similarity_threshold: float = 0.7
    ) -> List[Tuple[DocumentChunk, float]]:
        """
        Search for similar document chunks.
        
        Args:
            query_embedding: Query embedding vector
            k: Number of results to return
            similarity_threshold: Minimum similarity threshold
            
        Returns:
            List of (chunk, similarity_score) tuples
        """
        if self.index.ntotal == 0:
            return []
        
        # Ensure query embedding is the right shape
        if query_embedding.ndim == 1:
            query_embedding = query_embedding.reshape(1, -1)
        
        # Normalize query embedding for cosine similarity
        if self.index_type == "IndexFlatIP":
            norm = np.linalg.norm(query_embedding)
            if norm > 0:
                query_embedding = query_embedding / norm
        
        # Search
        k = min(k, self.index.ntotal)  # Don't search for more than available
        similarities, indices = self.index.search(query_embedding.astype('float32'), k)
        
        # Filter results by similarity threshold and return chunks
        results = []
        for similarity, idx in zip(similarities[0], indices[0]):
            if similarity >= similarity_threshold:
                chunk = self.chunks[idx]
                results.append((chunk, float(similarity)))
        
        return results
    
    def search_by_text(
        self, 
        query_text: str, 
        embedding_model, 
        config: RetrievalConfig
    ) -> List[Tuple[DocumentChunk, float]]:
        """
        Search for similar chunks using text query.
        
        Args:
            query_text: Text to search for
            embedding_model: Model to generate query embedding
            config: Retrieval configuration
            
        Returns:
            List of (chunk, similarity_score) tuples
        """
        # Generate query embedding
        query_embedding = embedding_model.embed_texts([query_text])
        
        # Search
        return self.search(
            query_embedding[0], 
            k=config.top_k,
            similarity_threshold=config.similarity_threshold
        )
    
    def get_all_chunks(self) -> List[DocumentChunk]:
        """Get all stored chunks."""
        return self.chunks.copy()
    
    def get_chunk_by_id(self, paragraph_id: str) -> Optional[DocumentChunk]:
        """Get a specific chunk by its paragraph ID."""
        for chunk in self.chunks:
            if chunk.paragraph_id == paragraph_id:
                return chunk
        return None
    
    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        return {
            'total_chunks': len(self.chunks),
            'embedding_dim': self.embedding_dim,
            'index_type': self.index_type,
            'index_size': self.index.ntotal,
            'unique_documents': len(set(chunk.paragraph_id.split('_')[0] for chunk in self.chunks)),
            'avg_text_length': np.mean([len(chunk.text) for chunk in self.chunks]) if self.chunks else 0
        }
    
    def save(self, path: Path):
        """
        Save the vector database to disk.
        
        Args:
            path: Directory path to save the database
        """
        path.mkdir(parents=True, exist_ok=True)
        
        # Save FAISS index
        faiss.write_index(self.index, str(path / "index.faiss"))
        
        # Save chunks and metadata
        with open(path / "chunks.pkl", 'wb') as f:
            pickle.dump(self.chunks, f)
        
        with open(path / "metadata.json", 'w') as f:
            json.dump({
                'embedding_dim': self.embedding_dim,
                'index_type': self.index_type,
                'chunk_count': len(self.chunks),
                'chunk_metadata': self.chunk_metadata
            }, f, indent=2)
        
        logger.info(f"Saved vector database to {path}")
    
    def load(self, path: Path):
        """
        Load the vector database from disk.
        
        Args:
            path: Directory path to load the database from
        """
        if not path.exists():
            raise FileNotFoundError(f"Database path does not exist: {path}")
        
        # Load metadata first
        with open(path / "metadata.json", 'r') as f:
            metadata = json.load(f)
        
        # Verify compatibility
        if metadata['embedding_dim'] != self.embedding_dim:
            raise ValueError(
                f"Embedding dimension mismatch: {metadata['embedding_dim']} vs {self.embedding_dim}"
            )
        
        if metadata['index_type'] != self.index_type:
            raise ValueError(
                f"Index type mismatch: {metadata['index_type']} vs {self.index_type}"
            )
        
        # Load FAISS index
        self.index = faiss.read_index(str(path / "index.faiss"))
        
        # Load chunks
        with open(path / "chunks.pkl", 'rb') as f:
            self.chunks = pickle.load(f)
        
        self.chunk_metadata = metadata['chunk_metadata']
        
        logger.info(f"Loaded vector database from {path} ({len(self.chunks)} chunks)")
    
    @classmethod
    def create_from_chunks(
        cls, 
        chunks: List[DocumentChunk], 
        embeddings: np.ndarray,
        index_type: str = "IndexFlatIP"
    ) -> "VectorDatabase":
        """
        Create a new vector database from chunks and embeddings.
        
        Args:
            chunks: Document chunks
            embeddings: Corresponding embeddings
            index_type: FAISS index type
            
        Returns:
            Initialized VectorDatabase
        """
        if len(chunks) == 0:
            raise ValueError("Cannot create database from empty chunks")
        
        embedding_dim = embeddings.shape[1]
        db = cls(embedding_dim, index_type)
        db.add_chunks(chunks, embeddings)
        
        return db


class MultiAgentVectorDB:
    """Manager for multiple agent-specific vector databases."""
    
    def __init__(self, embedding_dim: int):
        """Initialize the multi-agent vector database manager."""
        self.embedding_dim = embedding_dim
        self.databases: Dict[str, VectorDatabase] = {}
        self.main_db: Optional[VectorDatabase] = None
    
    def create_main_database(self, chunks: List[DocumentChunk], embeddings: np.ndarray):
        """Create the main document database."""
        self.main_db = VectorDatabase.create_from_chunks(chunks, embeddings)
        logger.info(f"Created main database with {len(chunks)} chunks")
    
    def create_agent_database(
        self, 
        agent_name: str, 
        kb_chunks: List[DocumentChunk], 
        kb_embeddings: np.ndarray
    ):
        """Create a knowledge base database for a specific agent."""
        if len(kb_chunks) > 0:
            self.databases[agent_name] = VectorDatabase.create_from_chunks(
                kb_chunks, kb_embeddings
            )
            logger.info(f"Created knowledge base for agent '{agent_name}' with {len(kb_chunks)} chunks")
    
    def get_database(self, agent_name: Optional[str] = None) -> VectorDatabase:
        """Get database for agent (or main database if agent_name is None)."""
        if agent_name is None:
            if self.main_db is None:
                raise ValueError("Main database not initialized")
            return self.main_db
        
        if agent_name not in self.databases:
            raise ValueError(f"No database found for agent: {agent_name}")
        
        return self.databases[agent_name]
    
    def search_all_databases(
        self, 
        query_embedding: np.ndarray, 
        config: RetrievalConfig
    ) -> Dict[str, List[Tuple[DocumentChunk, float]]]:
        """Search all databases and return results grouped by source."""
        results = {}
        
        # Search main database
        if self.main_db:
            results['main'] = self.main_db.search(
                query_embedding, 
                config.top_k, 
                config.similarity_threshold
            )
        
        # Search agent databases
        for agent_name, db in self.databases.items():
            results[agent_name] = db.search(
                query_embedding, 
                config.top_k, 
                config.similarity_threshold
            )
        
        return results

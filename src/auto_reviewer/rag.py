"""RAG (Retrieval-Augmented Generation) system for context-aware agent decision making."""

import logging
from typing import List, Dict, Optional, Tuple, Any
from pathlib import Path

from .config import DocumentChunk, RetrievalConfig, AgentConfig
from .vectordb import MultiAgentVectorDB, VectorDatabase
from .embed import EmbeddingModel
from .loaders import load_document

logger = logging.getLogger(__name__)


class RAGContext:
    """Container for retrieval context used by agents."""
    
    def __init__(
        self, 
        target_chunk: DocumentChunk,
        retrieved_chunks: List[Tuple[DocumentChunk, float]],
        agent_knowledge: List[Tuple[DocumentChunk, float]],
        global_rubric: Optional[str] = None
    ):
        """
        Initialize RAG context.
        
        Args:
            target_chunk: The document chunk being reviewed
            retrieved_chunks: Relevant chunks from the main document
            agent_knowledge: Relevant chunks from agent's knowledge base
            global_rubric: Optional global rubric text
        """
        self.target_chunk = target_chunk
        self.retrieved_chunks = retrieved_chunks
        self.agent_knowledge = agent_knowledge
        self.global_rubric = global_rubric
    
    def format_context_for_agent(self, agent_name: str, max_context_length: int = 2000) -> str:
        """
        Format the retrieval context into a string for agent consumption.
        
        Args:
            agent_name: Name of the agent
            max_context_length: Maximum length of context string
            
        Returns:
            Formatted context string
        """
        context_parts = []
        
        # Add global rubric if available
        if self.global_rubric:
            context_parts.append(f"GLOBAL RUBRIC:\n{self.global_rubric}\n")
        
        # Add relevant document context
        if self.retrieved_chunks:
            context_parts.append("RELEVANT DOCUMENT CONTEXT:")
            for chunk, similarity in self.retrieved_chunks[:3]:  # Top 3 most relevant
                context_parts.append(f"[Similarity: {similarity:.2f}] {chunk.text}")
            context_parts.append("")
        
        # Add agent-specific knowledge
        if self.agent_knowledge:
            context_parts.append(f"KNOWLEDGE BASE (for {agent_name}):")
            for chunk, similarity in self.agent_knowledge[:2]:  # Top 2 from KB
                context_parts.append(f"[Similarity: {similarity:.2f}] {chunk.text}")
            context_parts.append("")
        
        # Add the target paragraph
        context_parts.append(f"PARAGRAPH TO REVIEW (ID: {self.target_chunk.paragraph_id}):")
        context_parts.append(self.target_chunk.text)
        
        # Join and truncate if necessary
        full_context = "\n".join(context_parts)
        
        if len(full_context) > max_context_length:
            # Truncate but try to keep the target paragraph
            target_text = f"\nPARAGRAPH TO REVIEW (ID: {self.target_chunk.paragraph_id}):\n{self.target_chunk.text}"
            available_length = max_context_length - len(target_text) - 50  # Buffer for truncation notice
            
            if available_length > 0:
                truncated_context = full_context[:available_length] + "\n[...CONTEXT TRUNCATED...]\n" + target_text
            else:
                truncated_context = target_text
            
            return truncated_context
        
        return full_context
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the retrieval context."""
        return {
            'target_chunk_id': self.target_chunk.paragraph_id,
            'target_chunk_length': len(self.target_chunk.text),
            'retrieved_chunks_count': len(self.retrieved_chunks),
            'agent_knowledge_count': len(self.agent_knowledge),
            'has_global_rubric': self.global_rubric is not None,
            'total_context_length': len(self.format_context_for_agent("test", max_context_length=10000))
        }


class RAGSystem:
    """Retrieval-Augmented Generation system for the auto-reviewer."""
    
    def __init__(
        self, 
        vector_db: MultiAgentVectorDB, 
        embedding_model: EmbeddingModel,
        global_rubric: Optional[str] = None
    ):
        """
        Initialize the RAG system.
        
        Args:
            vector_db: Multi-agent vector database
            embedding_model: Embedding model for queries
            global_rubric: Optional global rubric text
        """
        self.vector_db = vector_db
        self.embedding_model = embedding_model
        self.global_rubric = global_rubric
    
    def get_context_for_chunk(
        self, 
        chunk: DocumentChunk, 
        agent_config: AgentConfig
    ) -> RAGContext:
        """
        Get retrieval context for a specific chunk and agent.
        
        Args:
            chunk: Document chunk to get context for
            agent_config: Configuration of the requesting agent
            
        Returns:
            RAG context containing relevant information
        """
        # Generate query embedding from the chunk text
        query_embedding = self.embedding_model.embed_texts([chunk.text])[0]
        
        # Retrieve relevant chunks from main document
        main_db = self.vector_db.get_database()  # Main document database
        retrieved_chunks = main_db.search(
            query_embedding,
            k=agent_config.retrieval.top_k,
            similarity_threshold=agent_config.retrieval.similarity_threshold
        )
        
        # Filter out the target chunk itself from results
        retrieved_chunks = [
            (retrieved_chunk, sim) for retrieved_chunk, sim in retrieved_chunks 
            if retrieved_chunk.paragraph_id != chunk.paragraph_id
        ]
        
        # Retrieve from agent-specific knowledge base if available
        agent_knowledge = []
        try:
            agent_db = self.vector_db.get_database(agent_config.name)
            agent_knowledge = agent_db.search(
                query_embedding,
                k=agent_config.retrieval.top_k,
                similarity_threshold=agent_config.retrieval.similarity_threshold
            )
        except ValueError:
            # No knowledge base for this agent
            pass
        
        return RAGContext(
            target_chunk=chunk,
            retrieved_chunks=retrieved_chunks,
            agent_knowledge=agent_knowledge,
            global_rubric=self.global_rubric
        )
    
    def batch_get_context(
        self, 
        chunks: List[DocumentChunk], 
        agent_config: AgentConfig
    ) -> List[RAGContext]:
        """Get context for multiple chunks efficiently."""
        contexts = []
        
        for chunk in chunks:
            context = self.get_context_for_chunk(chunk, agent_config)
            contexts.append(context)
        
        return contexts
    
    def add_agent_knowledge_base(self, agent_name: str, kb_files: List[str]):
        """
        Add knowledge base files for a specific agent.
        
        Args:
            agent_name: Name of the agent
            kb_files: List of paths to knowledge base files
        """
        if not kb_files:
            return
        
        kb_chunks = []
        
        for kb_file in kb_files:
            try:
                file_chunks = load_document(kb_file)
                kb_chunks.extend(file_chunks)
                logger.info(f"Loaded {len(file_chunks)} chunks from {kb_file} for agent {agent_name}")
            except Exception as e:
                logger.warning(f"Failed to load knowledge base file {kb_file} for agent {agent_name}: {e}")
        
        if kb_chunks:
            # Generate embeddings for knowledge base
            kb_embeddings = self.embedding_model.embed_chunks(kb_chunks)
            
            # Create agent-specific database
            self.vector_db.create_agent_database(agent_name, kb_chunks, kb_embeddings)
            
            logger.info(f"Created knowledge base for agent {agent_name} with {len(kb_chunks)} total chunks")
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get statistics about the RAG system."""
        stats = {
            'has_main_database': self.vector_db.main_db is not None,
            'agent_databases_count': len(self.vector_db.databases),
            'has_global_rubric': self.global_rubric is not None
        }
        
        if self.vector_db.main_db:
            main_stats = self.vector_db.main_db.get_stats()
            stats.update({f'main_db_{k}': v for k, v in main_stats.items()})
        
        # Agent database stats
        for agent_name, db in self.vector_db.databases.items():
            agent_stats = db.get_stats()
            stats.update({f'agent_{agent_name}_{k}': v for k, v in agent_stats.items()})
        
        return stats
    
    @classmethod
    def create_from_document(
        cls,
        document_chunks: List[DocumentChunk],
        document_embeddings,
        embedding_model: EmbeddingModel,
        global_rubric: Optional[str] = None
    ) -> "RAGSystem":
        """
        Create a RAG system from document chunks.
        
        Args:
            document_chunks: Main document chunks
            document_embeddings: Embeddings for document chunks
            embedding_model: Embedding model instance
            global_rubric: Optional global rubric text
            
        Returns:
            Initialized RAG system
        """
        # Get embedding dimension
        embedding_dim = embedding_model.get_embedding_dim()
        
        # Create multi-agent vector database
        vector_db = MultiAgentVectorDB(embedding_dim)
        vector_db.create_main_database(document_chunks, document_embeddings)
        
        return cls(vector_db, embedding_model, global_rubric)


def create_rag_system(
    document_chunks: List[DocumentChunk],
    embedding_model: EmbeddingModel,
    agent_configs: List[AgentConfig],
    global_rubric_path: Optional[Path] = None
) -> RAGSystem:
    """
    Create a complete RAG system with document and knowledge bases.
    
    Args:
        document_chunks: Main document chunks
        embedding_model: Embedding model
        agent_configs: List of agent configurations
        global_rubric_path: Optional path to global rubric file
        
    Returns:
        Configured RAG system
    """
    # Load global rubric if provided
    global_rubric = None
    if global_rubric_path and global_rubric_path.exists():
        try:
            with open(global_rubric_path, 'r', encoding='utf-8') as f:
                global_rubric = f.read()
            logger.info(f"Loaded global rubric from {global_rubric_path}")
        except Exception as e:
            logger.warning(f"Failed to load global rubric: {e}")
    
    # Generate embeddings for main document
    document_embeddings = embedding_model.embed_chunks(document_chunks)
    
    # Create RAG system
    rag_system = RAGSystem.create_from_document(
        document_chunks, document_embeddings, embedding_model, global_rubric
    )
    
    # Add knowledge bases for agents
    for agent_config in agent_configs:
        if agent_config.kb_refs:
            rag_system.add_agent_knowledge_base(agent_config.name, agent_config.kb_refs)
    
    logger.info(f"Created RAG system with {len(document_chunks)} document chunks and {len(agent_configs)} agents")
    
    return rag_system

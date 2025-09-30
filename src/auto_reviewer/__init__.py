"""Auto-Reviewer: Multi-Agent Document Review System."""

__version__ = "0.1.0"
__author__ = "Auto-Reviewer Team"
__description__ = "Automated multi-agent document review system with CrewAI and RAG"

from .config import (
    ReviewConfig, 
    AgentsConfig, 
    AgentConfig, 
    LLMConfig, 
    EmbeddingConfig,
    DocumentChunk,
    AgentReview,
    ReviewResults
)

from .review import ReviewEngine, run_review_from_config, run_review_from_paths
from .loaders import load_document, get_document_info, is_supported_format
from .embed import EmbeddingModel, create_embeddings
from .rag import RAGSystem, RAGContext, create_rag_system
from .agents import ReviewAgent, ReviewCrew
from .synthesize import ResultSynthesizer

__all__ = [
    # Configuration
    'ReviewConfig',
    'AgentsConfig', 
    'AgentConfig',
    'LLMConfig',
    'EmbeddingConfig',
    'DocumentChunk',
    'AgentReview', 
    'ReviewResults',
    
    # Main Engine
    'ReviewEngine',
    'run_review_from_config',
    'run_review_from_paths',
    
    # Document Loading
    'load_document',
    'get_document_info',
    'is_supported_format',
    
    # Embeddings
    'EmbeddingModel',
    'create_embeddings',
    
    # RAG System
    'RAGSystem',
    'RAGContext', 
    'create_rag_system',
    
    # Agents
    'ReviewAgent',
    'ReviewCrew',
    
    # Result Synthesis
    'ResultSynthesizer',
]
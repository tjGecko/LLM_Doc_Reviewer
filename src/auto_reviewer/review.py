"""Main review orchestration module."""

import json
from pathlib import Path
from typing import Dict, List, Optional, Union, Any, Tuple

import structlog
import numpy as np
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings

from .agents import ReviewCrew
from .config import AgentConfig, ReviewConfig, DocumentChunk, AgentReview
from .loaders import load_document
from .embed import EmbeddingModel

logger = structlog.get_logger()


class ReviewEngine:
    """Core review orchestration engine.
    
    Manages the complete document review workflow including:
    - Document loading and processing
    - RAG context preparation
    - Multi-agent review execution
    - Result aggregation
    """
    
    def __init__(
        self,
        config: ReviewConfig,
        vector_db_path: Optional[Path] = None,
        cache_dir: Optional[Path] = None,
    ):
        self.config = config
        self.vector_db_path = vector_db_path or Path("data/vector_db")
        self.cache_dir = cache_dir or Path("data/cache")
        
        self.embedder = None
        self.vector_db = None
        self.crew = None
        self.document_chunks = []
        
        # Ensure directories exist
        self.vector_db_path.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def review_document(
        self,
        document_path: Union[str, Path],
        output_dir: Union[str, Path],
    ) -> List[AgentReview]:
        """Execute complete document review workflow.
        
        Args:
            document_path: Path to document to review
            output_dir: Directory to save results
            
        Returns:
            List of agent reviews from all agents
        """
        document_path = Path(document_path)
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(
            "Starting document review",
            document=str(document_path),
            agents=len(self.config.agents),
            output_dir=str(output_dir)
        )
        
        try:
            # 1. Load and process document
            logger.info("Loading document")
            self.document_chunks = self._load_document(document_path)
            
            # 2. Setup RAG context
            logger.info("Setting up RAG context")
            self._setup_rag_context()
            
            # 3. Initialize review crew
            logger.info("Initializing review crew")
            self._initialize_crew()
            
            # 4. Execute reviews
            logger.info("Executing agent reviews")
            results = self._execute_reviews(output_dir)
            
            logger.info(
                "Review completed successfully", 
                results_count=len(results)
            )
            return results
            
        except Exception as e:
            logger.error(
                "Review failed", 
                error=str(e), 
                document=str(document_path)
            )
            raise
    
    def _load_document(self, document_path: Path) -> List[DocumentChunk]:
        """Load and process document into chunks."""
        logger.info("Loading and chunking document", path=str(document_path))
        
        # Load document content using existing loader
        chunks = load_document(str(document_path))
        
        logger.info("Document loaded and chunked", chunks=len(chunks))
        return chunks
    
    def _setup_rag_context(self) -> None:
        """Setup RAG context with document embeddings."""
        logger.info("Initializing embedder", model=self.config.embedder_model)
        
        # Initialize embedder using existing structure
        embedding_config = self.config.embedding if hasattr(self.config, 'embedding') else None
        if embedding_config:
            self.embedder = EmbeddingModel(embedding_config)
        else:
            # Fallback to sentence transformer
            self.embedder = SentenceTransformer(getattr(self.config, 'embedder_model', 'all-MiniLM-L6-v2'))
        
        # Setup ChromaDB
        logger.info("Initializing vector database", path=str(self.vector_db_path))
        client = chromadb.PersistentClient(
            path=str(self.vector_db_path),
            settings=Settings(allow_reset=True, anonymized_telemetry=False)
        )
        
        # Create or get collection
        collection_name = f"review_{hash(str(self.document_chunks))}"
        try:
            self.vector_db = client.get_collection(name=collection_name)
            logger.info("Using existing vector database collection")
        except Exception:
            logger.info("Creating new vector database collection")
            # Create embeddings for all chunks
            texts = [chunk.text for chunk in self.document_chunks]
            embeddings = self.embedder.encode(texts)
            
            # Create collection and add documents
            self.vector_db = client.create_collection(
                name=collection_name,
                metadata={"description": "Document chunks for review"}
            )
            
            # Add documents to vector database
            ids = [f"chunk_{i}" for i in range(len(self.document_chunks))]
            metadatas = [
                {
                    "chunk_id": i,
                    "paragraph_number": chunk.paragraph_number,
                    "section": chunk.section or "main",
                    "content_length": len(chunk.content)
                }
                for i, chunk in enumerate(self.document_chunks)
            ]
            
            self.vector_db.add(
                embeddings=embeddings.tolist(),
                documents=texts,
                metadatas=metadatas,
                ids=ids
            )
            
            logger.info("Vector database populated", documents=len(texts))
    
    def _initialize_crew(self) -> None:
        """Initialize the review crew with agents."""
        logger.info("Initializing review crew", agents=len(self.config.agents))
        
        # Initialize crew with configuration
        # This will use the existing RAG system and agents structure
        from .rag import create_rag_system
        
        # Create agents configuration for existing structure
        agents_config = self.config
        
        # Create RAG system for the existing structure
        rag_system = create_rag_system(
            document_chunks=self.document_chunks,
            embedding_model=self.embedder,
            agent_configs=self.config.agents,
            global_rubric_path=getattr(self.config, 'rubric_path', None)
        )
        
        # Initialize crew with existing structure
        self.crew = ReviewCrew(
            agents_config=agents_config,
            llm_config=getattr(self.config, 'llm', {}),
            rag_system=rag_system
        )
        
        logger.info("Review crew initialized")
    
    def _execute_reviews(self, output_dir: Path) -> List[AgentReview]:
        """Execute reviews with all configured agents."""
        logger.info("Starting multi-agent review execution")
        
        # Execute review using existing crew interface
        results = self.crew.review_document(
            chunks=self.document_chunks,
            max_workers=getattr(self.config, 'workers', 4)
        )
        
        # Save individual results
        for i, result in enumerate(results):
            result_file = output_dir / f"agent_{i}_{result.agent_name.replace(' ', '_')}.json"
            with open(result_file, 'w', encoding='utf-8') as f:
                # Convert to dict for JSON serialization
                result_dict = {
                    'agent_name': result.agent_name,
                    'paragraph_number': result.paragraph_number,
                    'overall_score': result.overall_score,
                    'confidence': result.confidence,
                    'comments': result.comments,
                    'rewritten_text': result.rewritten_text,
                    'review_timestamp': result.review_timestamp
                }
                json.dump(result_dict, f, indent=2, ensure_ascii=False)
            logger.info("Saved agent result", file=str(result_file))
        
        logger.info("Multi-agent review completed", results=len(results))
        return results
    
    def _retrieve_context(
        self, 
        query: str, 
        n_results: int = 5
    ) -> List[Tuple[DocumentChunk, float]]:
        """Retrieve relevant document chunks for a query."""
        if not self.vector_db or not self.embedder:
            return []
        
        # Encode query
        query_embedding = self.embedder.encode([query])
        
        # Search vector database
        results = self.vector_db.query(
            query_embeddings=query_embedding.tolist(),
            n_results=min(n_results, len(self.document_chunks))
        )
        
        # Return chunks with relevance scores
        context = []
        for i, (doc_id, distance) in enumerate(
            zip(results['ids'][0], results['distances'][0])
        ):
            chunk_idx = int(doc_id.split('_')[1])
            chunk = self.document_chunks[chunk_idx]
            relevance_score = 1.0 - distance  # Convert distance to similarity
            context.append((chunk, relevance_score))
        
        return context


# Convenience functions for CLI integration

def run_review_from_config(
    document_path: Union[str, Path],
    config_path: Union[str, Path],
    output_dir: Union[str, Path],
    **kwargs
) -> List[AgentReview]:
    """Run review from configuration file."""
    config_path = Path(config_path)
    
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    with open(config_path, encoding='utf-8') as f:
        config_data = json.load(f)
    
    # Override config with kwargs
    config_data.update(kwargs)
    
    config = ReviewConfig(**config_data)
    engine = ReviewEngine(config)
    
    return engine.review_document(document_path, output_dir)


def run_review_from_paths(
    document_path: Union[str, Path],
    agents_path: Union[str, Path], 
    output_dir: Union[str, Path],
    rubric_path: Optional[Union[str, Path]] = None,
    **kwargs
) -> List[AgentReview]:
    """Run review from individual file paths."""
    agents_path = Path(agents_path)
    
    if not agents_path.exists():
        raise FileNotFoundError(f"Agents configuration file not found: {agents_path}")
    
    with open(agents_path, encoding='utf-8') as f:
        agents_data = json.load(f)
    
    # Validate agents data structure
    if not isinstance(agents_data, list):
        raise ValueError("Agents configuration must be a list of agent configs")
    
    # Load rubric if provided
    rubric_content = None
    if rubric_path:
        rubric_path = Path(rubric_path)
        if rubric_path.exists():
            rubric_content = rubric_path.read_text(encoding='utf-8')
        else:
            logger.warning("Rubric file not found", path=str(rubric_path))
    
    # Create config
    agents = [AgentConfig(**agent_data) for agent_data in agents_data]
    config = ReviewConfig(
        agents=agents,
        global_rubric=rubric_content,
        **kwargs
    )
    
    engine = ReviewEngine(config)
    
    return engine.review_document(document_path, output_dir)

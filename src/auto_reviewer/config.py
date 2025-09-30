"""Configuration models for the auto-reviewer system."""

from typing import List, Dict, Any, Optional, Union
from pathlib import Path
from pydantic import BaseModel, Field, validator
import os


class RetrievalConfig(BaseModel):
    """Configuration for document retrieval."""
    top_k: int = Field(default=4, description="Number of top documents to retrieve")
    use_neighbors: bool = Field(default=True, description="Whether to use neighbor retrieval")
    similarity_threshold: float = Field(default=0.7, description="Minimum similarity threshold")


class RubricConfig(BaseModel):
    """Scoring rubric configuration."""
    criteria: List[str] = Field(description="List of evaluation criteria")
    scale_min: int = Field(default=1, description="Minimum score")
    scale_max: int = Field(default=5, description="Maximum score")
    
    @validator('criteria')
    def criteria_not_empty(cls, v):
        if not v:
            raise ValueError("Criteria list cannot be empty")
        return v
    
    @validator('scale_min', 'scale_max')
    def valid_scale(cls, v):
        if v < 1 or v > 10:
            raise ValueError("Scale values must be between 1 and 10")
        return v


class AgentConfig(BaseModel):
    """Configuration for individual review agents."""
    name: str = Field(description="Agent name")
    tone: str = Field(description="Agent's review tone and style")
    goals: List[str] = Field(description="Agent's primary goals and focus areas")
    rubric: RubricConfig = Field(description="Scoring rubric for this agent")
    kb_refs: List[str] = Field(default_factory=list, description="Knowledge base reference files")
    retrieval: RetrievalConfig = Field(default_factory=RetrievalConfig, description="Retrieval configuration")
    
    @validator('goals')
    def goals_not_empty(cls, v):
        if not v:
            raise ValueError("Goals list cannot be empty")
        return v


class AgentsConfig(BaseModel):
    """Configuration for all review agents."""
    model: str = Field(description="LLM model to use")
    max_agents: int = Field(default=7, description="Maximum number of agents")
    agents: List[AgentConfig] = Field(description="List of agent configurations")
    
    @validator('agents')
    def validate_agent_count(cls, v, values):
        max_agents = values.get('max_agents', 7)
        if len(v) > max_agents:
            raise ValueError(f"Cannot have more than {max_agents} agents")
        if len(v) == 0:
            raise ValueError("At least one agent must be configured")
        return v
    
    @validator('agents')
    def unique_agent_names(cls, v):
        names = [agent.name for agent in v]
        if len(names) != len(set(names)):
            raise ValueError("Agent names must be unique")
        return v


class LLMConfig(BaseModel):
    """LLM configuration."""
    api_key: str = Field(default="lm-studio", description="API key for LLM service")
    base_url: str = Field(default="http://localhost:1234/v1", description="Base URL for LLM API")
    model: str = Field(description="Model name")
    temperature: float = Field(default=0.2, ge=0.0, le=2.0, description="Temperature for generation")
    max_tokens: int = Field(default=2000, gt=0, description="Maximum tokens per response")
    
    @classmethod
    def from_env(cls) -> "LLMConfig":
        """Create LLM config from environment variables."""
        return cls(
            api_key=os.getenv("OPENAI_API_KEY", "lm-studio"),
            base_url=os.getenv("OPENAI_BASE_URL", "http://localhost:1234/v1"),
            model=os.getenv("OPENAI_MODEL", "openai/gpt-oss-20b"),
            temperature=float(os.getenv("TEMPERATURE", "0.2")),
            max_tokens=int(os.getenv("MAX_TOKENS", "2000"))
        )


class EmbeddingConfig(BaseModel):
    """Embedding model configuration."""
    model: str = Field(default="sentence-transformers/all-MiniLM-L6-v2", description="Embedding model name")
    batch_size: int = Field(default=32, gt=0, description="Batch size for embedding")
    max_length: int = Field(default=512, gt=0, description="Maximum sequence length")
    
    @classmethod
    def from_env(cls) -> "EmbeddingConfig":
        """Create embedding config from environment variables."""
        return cls(
            model=os.getenv("EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2"),
            batch_size=int(os.getenv("EMBED_BATCH_SIZE", "32")),
            max_length=int(os.getenv("EMBED_MAX_LENGTH", "512"))
        )


class ReviewConfig(BaseModel):
    """Main review configuration."""
    document_path: Path = Field(description="Path to document to review")
    agents_config_path: Path = Field(description="Path to agents configuration file")
    output_dir: Path = Field(description="Output directory for results")
    rubric_path: Optional[Path] = Field(default=None, description="Optional global rubric file")
    workers: int = Field(default=4, gt=0, description="Number of worker processes")
    llm: LLMConfig = Field(default_factory=LLMConfig.from_env)
    embedding: EmbeddingConfig = Field(default_factory=EmbeddingConfig.from_env)
    
    @validator('document_path', 'agents_config_path')
    def paths_must_exist(cls, v):
        if not v.exists():
            raise ValueError(f"Path does not exist: {v}")
        return v
    
    @validator('output_dir')
    def create_output_dir(cls, v):
        v.mkdir(parents=True, exist_ok=True)
        return v
    
    @classmethod
    def from_env(cls) -> "ReviewConfig":
        """Create review config with environment defaults."""
        return cls(
            document_path=Path("document.pdf"),
            agents_config_path=Path("agents.json"),
            output_dir=Path("outputs"),
            workers=int(os.getenv("MAX_WORKERS", "4")),
            llm=LLMConfig.from_env(),
            embedding=EmbeddingConfig.from_env()
        )


class DocumentChunk(BaseModel):
    """Represents a document chunk with metadata."""
    paragraph_id: str = Field(description="Stable, immutable paragraph identifier")
    text: str = Field(description="Paragraph text content")
    hash: str = Field(description="Content hash for integrity verification")
    page_number: Optional[int] = Field(default=None, description="Page number if applicable")
    chunk_index: int = Field(description="Index within the document")
    
    class Config:
        frozen = True  # Immutable chunks preserve document integrity


class AgentReview(BaseModel):
    """Individual agent review for a document chunk."""
    agent_name: str = Field(description="Name of the reviewing agent")
    paragraph_id: str = Field(description="ID of the reviewed paragraph")
    scores: Dict[str, float] = Field(description="Scores by criteria")
    overall_score: float = Field(description="Overall average score")
    comments: str = Field(description="Agent's comments and feedback")
    suggested_rewrite: Optional[str] = Field(default=None, description="Suggested paragraph rewrite")
    confidence: float = Field(ge=0.0, le=1.0, description="Agent's confidence in the review")
    
    @validator('overall_score')
    def valid_overall_score(cls, v, values):
        if 'scores' in values and values['scores']:
            calculated_avg = sum(values['scores'].values()) / len(values['scores'])
            if abs(v - calculated_avg) > 0.01:  # Allow small floating point differences
                raise ValueError("Overall score must be the average of individual scores")
        return v


class ReviewResults(BaseModel):
    """Complete review results."""
    document_path: str = Field(description="Path to the reviewed document")
    run_timestamp: str = Field(description="Timestamp of the review run")
    agents_used: List[str] = Field(description="Names of agents that performed reviews")
    total_paragraphs: int = Field(description="Total number of paragraphs reviewed")
    agent_reviews: List[AgentReview] = Field(description="All individual agent reviews")
    consolidated_scores: Dict[str, float] = Field(description="Consolidated scores across agents")
    overall_rating: float = Field(description="Overall document rating")
    
    def get_reviews_by_agent(self, agent_name: str) -> List[AgentReview]:
        """Get all reviews by a specific agent."""
        return [r for r in self.agent_reviews if r.agent_name == agent_name]
    
    def get_reviews_by_paragraph(self, paragraph_id: str) -> List[AgentReview]:
        """Get all agent reviews for a specific paragraph."""
        return [r for r in self.agent_reviews if r.paragraph_id == paragraph_id]
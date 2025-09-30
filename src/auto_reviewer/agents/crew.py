"""CrewAI integration for multi-agent document review."""

import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
import asyncio
from pathlib import Path

try:
    from crewai import Agent, Task, Crew, Process
    from crewai_tools import BaseTool
    HAS_CREWAI = True
except ImportError:
    HAS_CREWAI = False

from ..config import AgentConfig, AgentsConfig, DocumentChunk, AgentReview, LLMConfig
from ..rag import RAGSystem, RAGContext
from .prompts import get_agent_system_prompt, format_review_context

logger = logging.getLogger(__name__)


class DocumentReviewTool(BaseTool):
    """Custom tool for document review tasks."""
    
    name: str = "document_reviewer"
    description: str = "Reviews document paragraphs and provides structured feedback"
    
    def __init__(self, rag_system: RAGSystem, agent_config: AgentConfig):
        super().__init__()
        self.rag_system = rag_system
        self.agent_config = agent_config
    
    def _run(self, paragraph_id: str, paragraph_text: str) -> str:
        """Run the document review tool."""
        try:
            # Get RAG context for the paragraph
            chunk = next((c for c in self.rag_system.vector_db.get_database().get_all_chunks() 
                         if c.paragraph_id == paragraph_id), None)
            
            if not chunk:
                return json.dumps({"error": f"Paragraph {paragraph_id} not found"})
            
            # Get context using RAG system
            rag_context = self.rag_system.get_context_for_chunk(chunk, self.agent_config)
            context_text = rag_context.format_context_for_agent(self.agent_config.name)
            
            # Return formatted context for the agent
            return format_review_context(context_text, paragraph_text, self.agent_config.name)
            
        except Exception as e:
            logger.error(f"Error in document review tool: {e}")
            return json.dumps({"error": str(e)})


class ReviewAgent:
    """Wrapper for CrewAI agents with review-specific functionality."""
    
    def __init__(
        self, 
        agent_config: AgentConfig, 
        llm_config: LLMConfig, 
        rag_system: RAGSystem,
        specialized_type: str = None
    ):
        """
        Initialize a review agent.
        
        Args:
            agent_config: Agent configuration
            llm_config: LLM configuration
            rag_system: RAG system for context
            specialized_type: Optional specialized agent type
        """
        if not HAS_CREWAI:
            raise ImportError("CrewAI is required. Install with: pip install crewai")
        
        self.config = agent_config
        self.llm_config = llm_config
        self.rag_system = rag_system
        self.specialized_type = specialized_type
        
        # Create the CrewAI agent
        self.agent = self._create_crewai_agent()
    
    def _create_crewai_agent(self) -> Agent:
        """Create the underlying CrewAI agent."""
        
        # Generate system prompt
        system_prompt = get_agent_system_prompt(self.config, self.specialized_type)
        
        # Create custom tool for document review
        review_tool = DocumentReviewTool(self.rag_system, self.config)
        
        # Create the agent
        agent = Agent(
            role=f"{self.config.name} Document Reviewer",
            goal="\n".join(self.config.goals),
            backstory=system_prompt,
            tools=[review_tool],
            verbose=True,
            allow_delegation=False,  # Prevent delegation to maintain isolation
            max_iter=3,  # Limit iterations to prevent infinite loops
            memory=False,  # Disable memory to ensure clean reviews
            llm=self._configure_llm()
        )
        
        return agent
    
    def _configure_llm(self):
        """Configure the LLM for this agent."""
        try:
            from langchain_openai import ChatOpenAI
            
            return ChatOpenAI(
                openai_api_key=self.llm_config.api_key,
                openai_api_base=self.llm_config.base_url,
                model_name=self.llm_config.model,
                temperature=self.llm_config.temperature,
                max_tokens=self.llm_config.max_tokens
            )
        except ImportError:
            logger.warning("langchain_openai not available, using default LLM")
            return None
    
    def review_paragraph(self, chunk: DocumentChunk, context: RAGContext) -> AgentReview:
        """
        Review a single paragraph.
        
        Args:
            chunk: Document chunk to review
            context: RAG context for the review
            
        Returns:
            Agent review result
        """
        try:
            # Format context for the agent
            context_text = context.format_context_for_agent(
                self.config.name, 
                max_context_length=2000
            )
            
            # Create a review task
            task_description = f"""Review the following paragraph and provide structured feedback:

CONTEXT:
{context_text}

PARAGRAPH TO REVIEW:
{chunk.text}

Provide your review as a JSON object with scores, comments, and suggestions."""
            
            task = Task(
                description=task_description,
                expected_output="JSON object with review results",
                agent=self.agent
            )
            
            # Create crew and execute
            crew = Crew(
                agents=[self.agent],
                tasks=[task],
                process=Process.sequential,
                verbose=False
            )
            
            # Execute the task
            result = crew.kickoff()
            
            # Parse the result
            return self._parse_review_result(result, chunk)
            
        except Exception as e:
            logger.error(f"Error reviewing paragraph {chunk.paragraph_id}: {e}")
            return self._create_error_review(chunk, str(e))
    
    def _parse_review_result(self, result: str, chunk: DocumentChunk) -> AgentReview:
        """Parse the raw result into an AgentReview object."""
        try:
            # Clean the result - remove markdown formatting if present
            clean_result = result.strip()
            if clean_result.startswith("```json"):
                clean_result = clean_result[7:]
            if clean_result.endswith("```"):
                clean_result = clean_result[:-3]
            clean_result = clean_result.strip()
            
            # Parse JSON
            review_data = json.loads(clean_result)
            
            # Validate and create AgentReview
            scores = review_data.get("scores", {})
            overall_score = review_data.get("overall_score", 0.0)
            
            # Validate overall score matches average
            if scores:
                calculated_avg = sum(scores.values()) / len(scores)
                if abs(overall_score - calculated_avg) > 0.01:
                    logger.warning(f"Overall score mismatch, using calculated average: {calculated_avg}")
                    overall_score = calculated_avg
            
            return AgentReview(
                agent_name=self.config.name,
                paragraph_id=chunk.paragraph_id,
                scores=scores,
                overall_score=overall_score,
                comments=review_data.get("comments", "No comments provided"),
                suggested_rewrite=review_data.get("suggested_rewrite"),
                confidence=review_data.get("confidence", 0.8)
            )
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON result: {e}")
            logger.error(f"Raw result: {result}")
            return self._create_error_review(chunk, f"JSON parse error: {e}")
        except Exception as e:
            logger.error(f"Error processing review result: {e}")
            return self._create_error_review(chunk, str(e))
    
    def _create_error_review(self, chunk: DocumentChunk, error_msg: str) -> AgentReview:
        """Create an error review when processing fails."""
        return AgentReview(
            agent_name=self.config.name,
            paragraph_id=chunk.paragraph_id,
            scores={"error": 0.0},
            overall_score=0.0,
            comments=f"Review failed: {error_msg}",
            suggested_rewrite=None,
            confidence=0.0
        )


class ReviewCrew:
    """Manages a crew of review agents for document analysis."""
    
    def __init__(
        self, 
        agents_config: AgentsConfig, 
        llm_config: LLMConfig, 
        rag_system: RAGSystem
    ):
        """
        Initialize the review crew.
        
        Args:
            agents_config: Configuration for all agents
            llm_config: LLM configuration
            rag_system: RAG system for context
        """
        if not HAS_CREWAI:
            raise ImportError("CrewAI is required. Install with: pip install crewai")
        
        self.agents_config = agents_config
        self.llm_config = llm_config
        self.rag_system = rag_system
        
        # Create review agents
        self.agents = self._create_agents()
        
        logger.info(f"Initialized review crew with {len(self.agents)} agents")
    
    def _create_agents(self) -> List[ReviewAgent]:
        """Create all review agents."""
        agents = []
        
        for agent_config in self.agents_config.agents:
            # Determine specialized type based on agent name/goals
            specialized_type = self._infer_specialized_type(agent_config)
            
            try:
                agent = ReviewAgent(
                    agent_config=agent_config,
                    llm_config=self.llm_config,
                    rag_system=self.rag_system,
                    specialized_type=specialized_type
                )
                agents.append(agent)
                logger.info(f"Created agent: {agent_config.name} (type: {specialized_type or 'general'})")
                
            except Exception as e:
                logger.error(f"Failed to create agent {agent_config.name}: {e}")
        
        return agents
    
    def _infer_specialized_type(self, agent_config: AgentConfig) -> Optional[str]:
        """Infer specialized type from agent configuration."""
        name_lower = agent_config.name.lower()
        goals_text = " ".join(agent_config.goals).lower()
        
        # Check for specialized types
        if any(keyword in name_lower or keyword in goals_text 
               for keyword in ["technical", "tech", "accuracy", "facts"]):
            return "technical"
        elif any(keyword in name_lower or keyword in goals_text 
                 for keyword in ["clarity", "clear", "readable", "communication"]):
            return "clarity"
        elif any(keyword in name_lower or keyword in goals_text 
                 for keyword in ["compliance", "standards", "policy", "regulatory"]):
            return "compliance"
        elif any(keyword in name_lower or keyword in goals_text 
                 for keyword in ["audience", "user", "reader", "engagement"]):
            return "audience"
        
        return None
    
    def review_document(
        self, 
        chunks: List[DocumentChunk], 
        max_workers: int = 4
    ) -> List[AgentReview]:
        """
        Review a complete document with all agents.
        
        Args:
            chunks: Document chunks to review
            max_workers: Maximum concurrent workers
            
        Returns:
            List of all agent reviews
        """
        all_reviews = []
        
        logger.info(f"Starting document review with {len(self.agents)} agents on {len(chunks)} chunks")
        
        # Process each agent sequentially to maintain isolation
        for agent in self.agents:
            logger.info(f"Starting reviews for agent: {agent.config.name}")
            
            agent_reviews = self._review_with_agent(agent, chunks, max_workers)
            all_reviews.extend(agent_reviews)
            
            logger.info(f"Completed {len(agent_reviews)} reviews for agent: {agent.config.name}")
        
        logger.info(f"Document review completed. Total reviews: {len(all_reviews)}")
        return all_reviews
    
    def _review_with_agent(
        self, 
        agent: ReviewAgent, 
        chunks: List[DocumentChunk], 
        max_workers: int
    ) -> List[AgentReview]:
        """Review all chunks with a single agent."""
        reviews = []
        
        # Get contexts for all chunks
        contexts = self.rag_system.batch_get_context(chunks, agent.config)
        
        # Process chunks with the agent (can be parallelized per agent)
        if max_workers > 1:
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_chunk = {
                    executor.submit(agent.review_paragraph, chunk, context): (chunk, context)
                    for chunk, context in zip(chunks, contexts)
                }
                
                for future in as_completed(future_to_chunk):
                    chunk, context = future_to_chunk[future]
                    try:
                        review = future.result()
                        reviews.append(review)
                    except Exception as e:
                        logger.error(f"Error reviewing chunk {chunk.paragraph_id} with {agent.config.name}: {e}")
                        reviews.append(agent._create_error_review(chunk, str(e)))
        else:
            # Sequential processing
            for chunk, context in zip(chunks, contexts):
                try:
                    review = agent.review_paragraph(chunk, context)
                    reviews.append(review)
                except Exception as e:
                    logger.error(f"Error reviewing chunk {chunk.paragraph_id} with {agent.config.name}: {e}")
                    reviews.append(agent._create_error_review(chunk, str(e)))
        
        return reviews
    
    def get_agent_stats(self) -> Dict[str, Any]:
        """Get statistics about the review crew."""
        return {
            "total_agents": len(self.agents),
            "agent_names": [agent.config.name for agent in self.agents],
            "specialized_agents": {
                agent.config.name: agent.specialized_type or "general" 
                for agent in self.agents
            },
            "model_used": self.llm_config.model,
            "total_criteria": sum(len(agent.config.rubric.criteria) for agent in self.agents)
        }
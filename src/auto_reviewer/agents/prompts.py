"""Agent prompt templates for CrewAI integration."""

from typing import Dict, Any
from ..config import AgentConfig, RubricConfig


class AgentPrompts:
    """Collection of prompt templates for different agent types."""
    
    @staticmethod
    def create_agent_role_prompt(agent_config: AgentConfig) -> str:
        """
        Create a role-based prompt for an agent.
        
        Args:
            agent_config: Configuration for the agent
            
        Returns:
            Formatted role prompt
        """
        goals_str = "\n".join(f"- {goal}" for goal in agent_config.goals)
        
        role_prompt = f"""You are a {agent_config.name}, a specialized document reviewer with expertise in evaluating written content.

Your reviewing style is: {agent_config.tone}

Your primary goals are:
{goals_str}

You will analyze document paragraphs and provide detailed, constructive feedback following specific scoring criteria."""

        return role_prompt
    
    @staticmethod
    def create_agent_backstory(agent_config: AgentConfig) -> str:
        """
        Create a backstory for the agent to establish context and expertise.
        
        Args:
            agent_config: Configuration for the agent
            
        Returns:
            Agent backstory
        """
        expertise_areas = ", ".join(agent_config.goals[:3])  # Use first 3 goals as expertise
        
        backstory = f"""You have extensive experience in document review and analysis, with particular expertise in {expertise_areas}.

Your approach to reviewing is {agent_config.tone}, ensuring that feedback is both thorough and actionable. You draw from a wealth of knowledge about best practices in writing, communication, and document quality.

You understand that your role is to help improve document quality while maintaining the author's intent and voice. Your reviews are detailed, specific, and always include concrete suggestions for improvement."""

        return backstory
    
    @staticmethod
    def create_review_task_prompt(agent_config: AgentConfig) -> str:
        """
        Create the main task prompt for document review.
        
        Args:
            agent_config: Configuration for the agent
            
        Returns:
            Task prompt for document review
        """
        criteria_str = "\n".join(f"- {criterion}" for criterion in agent_config.rubric.criteria)
        scale = f"{agent_config.rubric.scale_min}-{agent_config.rubric.scale_max}"
        
        task_prompt = f"""**TASK**: Review and evaluate the provided document paragraph.

**EVALUATION CRITERIA** (Rate each on a {scale} scale):
{criteria_str}

**INSTRUCTIONS**:
1. Read the paragraph carefully along with any provided context
2. Evaluate the paragraph against each criterion listed above
3. Provide a numerical score ({scale}) for each criterion
4. Calculate the overall average score
5. Write detailed comments explaining your evaluation
6. Provide a specific rewrite suggestion if the score is below {agent_config.rubric.scale_max}

**OUTPUT FORMAT**:
Your response must be a valid JSON object with exactly this structure:
{{
    "scores": {{
        "{agent_config.rubric.criteria[0] if agent_config.rubric.criteria else 'Quality'}": <score>,
        // ... one entry for each criterion
    }},
    "overall_score": <average_score>,
    "comments": "<detailed explanation of your evaluation>",
    "suggested_rewrite": "<your improved version of the paragraph, or null if not needed>",
    "confidence": <0.0-1.0 confidence in your review>
}}

**IMPORTANT**: 
- Only respond with the JSON object, no additional text
- Ensure all scores are numbers between {agent_config.rubric.scale_min} and {agent_config.rubric.scale_max}
- Overall score must be the mathematical average of individual scores
- Comments should be specific and actionable
- Suggested rewrite should maintain the original meaning while addressing identified issues"""

        return task_prompt


class ContextualPrompts:
    """Contextual prompts that incorporate RAG context."""
    
    @staticmethod
    def format_context_prompt(context_text: str, paragraph_text: str) -> str:
        """
        Format context and paragraph for agent consumption.
        
        Args:
            context_text: RAG context from knowledge bases and similar documents
            paragraph_text: The paragraph to be reviewed
            
        Returns:
            Formatted prompt with context
        """
        return f"""**CONTEXT INFORMATION**:
{context_text}

**PARAGRAPH TO REVIEW**:
{paragraph_text}

Please review the paragraph above using the context information provided."""

    @staticmethod  
    def create_knowledge_integration_prompt() -> str:
        """Create a prompt for integrating knowledge base information."""
        return """When reviewing, consider the following:

1. Use the provided context to inform your evaluation
2. Reference relevant standards or guidelines from your knowledge base
3. Consider how this paragraph fits within the broader document context
4. Apply domain-specific expertise based on the reference materials
5. Ensure suggestions align with established best practices

Your review should demonstrate deep understanding of both the specific content and the broader context in which it exists."""


class SpecializedPrompts:
    """Specialized prompts for different types of agents."""
    
    @staticmethod
    def create_technical_reviewer_prompt() -> str:
        """Prompt for technical accuracy reviewers."""
        return """**TECHNICAL REVIEW FOCUS**:

As a technical reviewer, pay special attention to:
- Accuracy of technical statements and claims  
- Proper use of technical terminology
- Logical consistency in technical explanations
- Clarity for the intended technical audience
- Completeness of technical information
- Appropriate level of technical detail

Flag any technical inaccuracies, unclear explanations, or missing critical technical information."""

    @staticmethod
    def create_clarity_reviewer_prompt() -> str:
        """Prompt for clarity and communication reviewers."""
        return """**CLARITY REVIEW FOCUS**:

As a clarity reviewer, focus on:
- Sentence structure and readability
- Logical flow and organization
- Appropriate word choice and tone
- Elimination of jargon without losing meaning
- Accessibility to the target audience
- Coherence with surrounding content

Prioritize making complex ideas accessible while maintaining accuracy and completeness."""

    @staticmethod
    def create_compliance_reviewer_prompt() -> str:
        """Prompt for compliance and standards reviewers."""  
        return """**COMPLIANCE REVIEW FOCUS**:

As a compliance reviewer, examine:
- Adherence to relevant standards and guidelines
- Proper citation and referencing
- Compliance with style guides
- Meeting regulatory or policy requirements
- Appropriate disclaimers or caveats
- Risk mitigation through proper language

Ensure all content meets applicable standards and reduces potential compliance risks."""

    @staticmethod
    def create_audience_reviewer_prompt() -> str:
        """Prompt for audience-focused reviewers."""
        return """**AUDIENCE REVIEW FOCUS**:

As an audience reviewer, consider:
- Appropriateness for the intended audience
- Level of detail and complexity
- Cultural sensitivity and inclusivity
- Engagement and accessibility
- Actionability for readers
- Relevance to audience needs

Evaluate whether the content effectively serves its intended audience and achieves its communication goals."""


def get_agent_system_prompt(agent_config: AgentConfig, specialized_type: str = None) -> str:
    """
    Generate complete system prompt for an agent.
    
    Args:
        agent_config: Agent configuration
        specialized_type: Optional specialized agent type
        
    Returns:
        Complete system prompt
    """
    base_role = AgentPrompts.create_agent_role_prompt(agent_config)
    backstory = AgentPrompts.create_agent_backstory(agent_config)
    task = AgentPrompts.create_review_task_prompt(agent_config)
    knowledge_integration = ContextualPrompts.create_knowledge_integration_prompt()
    
    # Add specialized prompts if specified
    specialized_prompt = ""
    if specialized_type:
        specialized_prompts = {
            "technical": SpecializedPrompts.create_technical_reviewer_prompt(),
            "clarity": SpecializedPrompts.create_clarity_reviewer_prompt(),
            "compliance": SpecializedPrompts.create_compliance_reviewer_prompt(),
            "audience": SpecializedPrompts.create_audience_reviewer_prompt()
        }
        specialized_prompt = specialized_prompts.get(specialized_type, "")
    
    # Combine all parts
    full_prompt = f"""
{base_role}

{backstory}

{specialized_prompt}

{knowledge_integration}

{task}
""".strip()
    
    return full_prompt


def format_review_context(context_text: str, paragraph_text: str, agent_name: str) -> str:
    """
    Format the complete context for a review request.
    
    Args:
        context_text: RAG context information
        paragraph_text: Paragraph to review
        agent_name: Name of the reviewing agent
        
    Returns:
        Formatted context prompt
    """
    return ContextualPrompts.format_context_prompt(context_text, paragraph_text)
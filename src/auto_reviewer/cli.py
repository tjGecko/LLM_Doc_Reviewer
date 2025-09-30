"""Command-line interface for the auto-reviewer system."""

import json
import logging
import os
import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.logging import RichHandler
from rich.progress import Progress, SpinnerColumn, TextColumn

from .config import ReviewConfig, LLMConfig, EmbeddingConfig
from .review import ReviewEngine


# Setup rich console and logging
console = Console()
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(console=console, rich_tracebacks=True)]
)
logger = logging.getLogger(__name__)


def setup_logging(debug: bool = False):
    """Setup logging configuration."""
    level = logging.DEBUG if debug else logging.INFO
    
    # Check for LOG_LEVEL environment variable
    env_level = os.getenv("LOG_LEVEL", "").upper()
    if env_level in ["DEBUG", "INFO", "WARNING", "ERROR"]:
        level = getattr(logging, env_level)
    
    logging.getLogger().setLevel(level)
    logging.getLogger("auto_reviewer").setLevel(level)
    
    if debug:
        logger.debug("Debug logging enabled")


@click.command()
@click.option(
    "--doc", 
    type=click.Path(exists=True, path_type=Path), 
    required=True,
    help="Path to document to review (PDF, DOCX, or TXT)"
)
@click.option(
    "--agents", 
    type=click.Path(exists=True, path_type=Path), 
    required=True,
    help="Path to agents configuration JSON file"
)
@click.option(
    "--out", 
    type=click.Path(path_type=Path), 
    default="outputs",
    help="Output directory for results (default: outputs)"
)
@click.option(
    "--rubric", 
    type=click.Path(exists=True, path_type=Path), 
    default=None,
    help="Optional global rubric markdown file"
)
@click.option(
    "--workers", 
    type=int, 
    default=4,
    help="Number of concurrent workers (default: 4)"
)
@click.option(
    "--embedder", 
    type=str, 
    default=None,
    help="Embedding model name (overrides EMBED_MODEL env var)"
)
@click.option(
    "--temperature", 
    type=float, 
    default=None,
    help="LLM temperature (overrides TEMPERATURE env var)"
)
@click.option(
    "--model", 
    type=str, 
    default=None,
    help="LLM model name (overrides OPENAI_MODEL env var)"
)
@click.option(
    "--debug", 
    is_flag=True,
    help="Enable debug logging"
)
@click.option(
    "--dry-run", 
    is_flag=True,
    help="Show configuration and exit without running review"
)
def main(
    doc: Path,
    agents: Path,
    out: Path,
    rubric: Optional[Path],
    workers: int,
    embedder: Optional[str],
    temperature: Optional[float],
    model: Optional[str],
    debug: bool,
    dry_run: bool
):
    """
    Auto-Reviewer: Multi-Agent Document Review System
    
    Analyze documents using multiple AI agents with different perspectives,
    providing scores, comments, and actionable rewrites while preserving 
    original document integrity.
    
    Example usage:
    
        auto-reviewer --doc report.pdf --agents agents.json --out results/
        
        auto-reviewer --doc document.docx --agents config/agents.json \\
                      --rubric guidelines.md --workers 6 --temperature 0.1
    """
    setup_logging(debug)
    
    try:
        # Create configuration
        config = create_config(
            doc=doc,
            agents=agents,
            out=out,
            rubric=rubric,
            workers=workers,
            embedder=embedder,
            temperature=temperature,
            model=model
        )
        
        if dry_run:
            show_config(config)
            return
        
        # Validate configuration
        validate_config(config)
        
        # Run the review
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True,
        ) as progress:
            task = progress.add_task("Initializing review engine...", total=None)
            
            engine = ReviewEngine(config)
            
            progress.update(task, description="Running document review...")
            results = engine.run_review()
            
            progress.update(task, description="Review completed!", completed=True)
        
        # Display results summary
        show_results_summary(results, config.output_dir)
        
    except Exception as e:
        logger.error(f"Review failed: {e}")
        if debug:
            logger.exception("Full traceback:")
        sys.exit(1)


def create_config(
    doc: Path,
    agents: Path,
    out: Path,
    rubric: Optional[Path],
    workers: int,
    embedder: Optional[str],
    temperature: Optional[float],
    model: Optional[str]
) -> ReviewConfig:
    """Create review configuration from command-line arguments."""
    
    # Start with environment defaults
    llm_config = LLMConfig.from_env()
    embedding_config = EmbeddingConfig.from_env()
    
    # Override with command-line arguments
    if model:
        llm_config.model = model
    if temperature is not None:
        llm_config.temperature = temperature
    if embedder:
        embedding_config.model = embedder
    
    return ReviewConfig(
        document_path=doc,
        agents_config_path=agents,
        output_dir=out,
        rubric_path=rubric,
        workers=workers,
        llm=llm_config,
        embedding=embedding_config
    )


def validate_config(config: ReviewConfig) -> None:
    """Validate configuration before running review."""
    
    # Check document format
    supported_extensions = {'.pdf', '.docx', '.doc', '.txt', '.md'}
    if config.document_path.suffix.lower() not in supported_extensions:
        raise ValueError(
            f"Unsupported document format: {config.document_path.suffix}. "
            f"Supported: {', '.join(supported_extensions)}"
        )
    
    # Validate agents configuration
    try:
        with open(config.agents_config_path) as f:
            agents_data = json.load(f)
        
        if not isinstance(agents_data, dict) or 'agents' not in agents_data:
            raise ValueError("Agents config must contain 'agents' key")
        
        if not agents_data['agents']:
            raise ValueError("At least one agent must be configured")
        
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in agents config: {e}")
    
    logger.info(f"✓ Configuration validated")


def show_config(config: ReviewConfig) -> None:
    """Display configuration details."""
    console.print("\n[bold blue]Auto-Reviewer Configuration[/bold blue]")
    console.print(f"📄 Document: {config.document_path}")
    console.print(f"🤖 Agents Config: {config.agents_config_path}")
    console.print(f"📁 Output Directory: {config.output_dir}")
    
    if config.rubric_path:
        console.print(f"📋 Rubric: {config.rubric_path}")
    
    console.print(f"\n[bold green]LLM Settings[/bold green]")
    console.print(f"🌐 Base URL: {config.llm.base_url}")
    console.print(f"🎯 Model: {config.llm.model}")
    console.print(f"🌡️  Temperature: {config.llm.temperature}")
    console.print(f"📝 Max Tokens: {config.llm.max_tokens}")
    
    console.print(f"\n[bold yellow]Embedding Settings[/bold yellow]")
    console.print(f"🧠 Model: {config.embedding.model}")
    console.print(f"📦 Batch Size: {config.embedding.batch_size}")
    
    console.print(f"\n[bold magenta]Processing Settings[/bold magenta]")
    console.print(f"⚡ Workers: {config.workers}")


def show_results_summary(results, output_dir: Path) -> None:
    """Display review results summary."""
    console.print(f"\n[bold green]✅ Review Completed![/bold green]")
    
    console.print(f"\n[bold blue]Results Summary[/bold blue]")
    console.print(f"📊 Overall Rating: {results.overall_rating:.2f}/5.0")
    console.print(f"📄 Paragraphs Reviewed: {results.total_paragraphs}")
    console.print(f"🤖 Agents Used: {len(results.agents_used)}")
    console.print(f"📝 Total Reviews: {len(results.agent_reviews)}")
    
    console.print(f"\n[bold yellow]Agent Performance[/bold yellow]")
    for agent_name in results.agents_used:
        agent_reviews = results.get_reviews_by_agent(agent_name)
        avg_score = sum(r.overall_score for r in agent_reviews) / len(agent_reviews)
        console.print(f"  {agent_name}: {avg_score:.2f}/5.0 avg ({len(agent_reviews)} reviews)")
    
    console.print(f"\n[bold cyan]Output Files[/bold cyan]")
    console.print(f"📁 Results saved to: {output_dir.absolute()}")
    
    # List output files
    if output_dir.exists():
        output_files = list(output_dir.glob("*"))
        for file in sorted(output_files):
            if file.is_file():
                size_kb = file.stat().st_size / 1024
                console.print(f"  📄 {file.name} ({size_kb:.1f} KB)")


if __name__ == "__main__":
    main()
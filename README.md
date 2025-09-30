# Auto-Reviewer: Multi-Agent Document Review System

An automated document review system that uses multiple AI agents to analyze documents with different perspectives, providing scores, comments, and actionable rewrites while preserving original document integrity.

## Features

- **Multi-agent review**: Deploy up to 7 specialized reviewer agents, each with unique personas and rubrics
- **Document integrity**: Original documents remain unchanged; all analysis uses stable paragraph IDs as "gold anchors"
- **Per-agent RAG**: Each agent maintains isolated knowledge bases to prevent contamination
- **Comprehensive scoring**: 1-5 scale scoring across multiple criteria with transparent averaging
- **Actionable feedback**: Agents provide specific rewrites tied to original paragraph IDs
- **LM Studio compatibility**: Works with your local LM Studio setup
- **Multiple formats**: Supports PDF, DOCX, and TXT documents

## Quick Start

### 1. Prerequisites

- Python 3.10+
- LM Studio running with an OpenAI-compatible server
- Git (for development)

### 2. Installation

```bash
# Clone and install the package
git clone <your-repo>
cd auto_reviewer
pip install -e .
```

### 3. Configuration

Copy the environment template and configure for your LM Studio setup:

```bash
cp .env.example .env
# Edit .env with your LM Studio model and server details
```

### 4. Run Your First Review

```bash
auto-reviewer \
  --doc ./examples/sample.txt \
  --agents ./examples/agents.json \
  --out ./outputs
```

## Architecture

### Core Workflow

1. **Document Ingestion**: Splits documents into paragraphs with stable IDs
2. **Embedding & Indexing**: Creates vector indices for the main document and per-agent references
3. **Multi-Agent Review**: Each agent analyzes paragraphs using RAG for context
4. **Scoring & Output**: Generates detailed reports with scores, comments, and suggested rewrites

### Directory Structure

```
auto_reviewer/
├── src/auto_reviewer/
│   ├── cli.py              # Command-line interface
│   ├── config.py           # Configuration models
│   ├── review.py           # Main orchestration engine
│   ├── embed.py            # Embedding utilities
│   ├── vectordb.py         # FAISS vector database
│   ├── rag.py              # Retrieval-augmented generation
│   ├── chunking.py         # Text processing utilities
│   ├── io_utils.py         # I/O helpers
│   ├── synthesize.py       # Result synthesis
│   ├── loaders/            # Document loaders
│   │   ├── pdf.py          # PDF processing
│   │   ├── docx.py         # Word document processing
│   │   └── text.py         # Plain text processing
│   └── agents/             # Agent system
│       ├── crew.py         # CrewAI integration
│       └── prompts.py      # Agent prompts and templates
├── examples/
│   ├── agents.json         # Sample agent configuration
│   ├── rubric.md          # Global rubric guidelines
│   └── sample.txt         # Sample document
├── docker/
│   ├── Dockerfile         # Container definition
│   └── entrypoint.sh      # Container entry point
└── outputs/               # Generated reports and data
```

## Configuration

### Agent Configuration (agents.json)

Configure your reviewing agents with specific personas, goals, and knowledge bases:

```json
{
  "model": "${OPENAI_MODEL}",
  "max_agents": 7,
  "agents": [
    {
      "name": "Quality Reviewer",
      "tone": "precise, constructive, firm",
      "goals": [
        "Identify logical gaps and unsupported claims",
        "Flag unverifiable references and missing evidence"
      ],
      "rubric": {
        "criteria": [
          "Factual support",
          "Logical coherence", 
          "Clarity",
          "Structure",
          "Actionability of suggestions"
        ],
        "scale_min": 1,
        "scale_max": 5
      },
      "kb_refs": ["refs/quality_guide.pdf", "refs/style_guide.md"],
      "retrieval": {"top_k": 4, "use_neighbors": true}
    }
  ]
}
```

### Environment Variables

Key environment variables for LM Studio integration:

- `OPENAI_API_KEY`: API key (use "lm-studio" for LM Studio)
- `OPENAI_BASE_URL`: Server URL (typically http://localhost:1234/v1)
- `OPENAI_MODEL`: Model name as configured in LM Studio
- `EMBED_MODEL`: Embedding model for document vectorization

## Usage

### Basic Review

```bash
auto-reviewer --doc document.pdf --agents agents.json --out results/
```

### Advanced Options

```bash
auto-reviewer \
  --doc ./documents/report.pdf \
  --agents ./config/specialized_agents.json \
  --rubric ./config/rubric_guidelines.md \
  --out ./results/run_$(date +%Y%m%d_%H%M%S) \
  --workers 6 \
  --embedder sentence-transformers/all-MiniLM-L6-v2 \
  --temperature 0.1
```

## Output Format

The system generates several output files:

- `run.json`: Run metadata and overall scores
- `{AgentName}.jsonl`: Per-paragraph findings for each agent
- `{AgentName}.md`: Human-readable reports (optional)
- `consolidated.json`: Synthesized findings across agents

## Docker Deployment

Build and run in a container:

```bash
docker build -f docker/Dockerfile -t auto-reviewer .
docker run -v $(pwd)/documents:/documents -v $(pwd)/outputs:/outputs \
  auto-reviewer --doc /documents/report.pdf --agents /app/examples/agents.json
```

## Development

### Setting Up Development Environment

```bash
# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest tests/

# Format code
black src/ tests/
isort src/ tests/
```

### Adding New Document Loaders

Implement the loader interface in `src/auto_reviewer/loaders/`:

```python
def load_paragraphs(path: str) -> List[Dict]:
    """Return list of {"paragraph_id": str, "text": str, "hash": str}"""
    pass
```

### Creating Custom Agents

Extend the agent configuration in `agents.json` with new personas, rubrics, and knowledge bases.

## Troubleshooting

### Common Issues

1. **LM Studio Connection**: Ensure LM Studio server is running and accessible
2. **Model Loading**: Verify the model name matches your LM Studio configuration
3. **Memory Issues**: Reduce embedding model size or document chunk size
4. **Agent Limits**: Maximum 7 agents supported for optimal performance

### Debugging

Enable verbose logging:

```bash
export LOG_LEVEL=DEBUG
auto-reviewer --doc document.pdf --agents agents.json
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Submit a pull request

## License

[Add your license here]

## Support

For issues and questions, please check the documentation or create an issue in the repository.
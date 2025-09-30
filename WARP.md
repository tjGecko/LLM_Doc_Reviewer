# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

Auto-Reviewer is a multi-agent document review system that uses specialized AI agents to analyze documents with different perspectives. The system maintains document integrity by using stable paragraph IDs as "gold anchors" while providing comprehensive scoring, comments, and actionable rewrites.

## Quick Start for Development

```bash
# 1. Set up environment
Copy-Item .env.example .env  # Windows
# Edit .env with your LM Studio settings

# 2. Install dependencies
pip install -e .

# 3. Create basic CLI entry point (currently missing)
# You'll need to implement src/auto_reviewer/cli.py first

# 4. Test basic functionality once implemented
auto-reviewer --help
```

**Note**: This project currently lacks implementation files. The documentation describes the intended architecture, but the actual Python code needs to be written.

## Essential Commands

### Development Setup
```bash
# Install the package in development mode
pip install -e .

# Install with development dependencies (when available)
pip install -e ".[dev]"

# Configure environment for LM Studio
# Windows PowerShell:
Copy-Item .env.example .env
# Linux/Mac:
cp .env.example .env

# Edit .env with your LM Studio configuration
# Key settings: OPENAI_BASE_URL, OPENAI_MODEL, EMBED_MODEL
```

### Running Reviews
```bash
# Basic document review
auto-reviewer --doc document.pdf --agents agents.json --out results/

# Advanced review with custom settings (Linux/Mac)
auto-reviewer \
  --doc ./documents/report.pdf \
  --agents ./config/specialized_agents.json \
  --rubric ./config/rubric_guidelines.md \
  --out ./results/run_$(date +%Y%m%d_%H%M%S) \
  --workers 6 \
  --embedder sentence-transformers/all-MiniLM-L6-v2 \
  --temperature 0.1

# Advanced review (Windows PowerShell)
auto-reviewer `
  --doc ./documents/report.pdf `
  --agents ./config/specialized_agents.json `
  --rubric ./config/rubric_guidelines.md `
  --out "./results/run_$(Get-Date -Format 'yyyyMMdd_HHmmss')" `
  --workers 6 `
  --embedder sentence-transformers/all-MiniLM-L6-v2 `
  --temperature 0.1
```

### Testing & Development
```bash
# Currently no test suite implemented - this is a development opportunity
# Future: pytest tests/

# Code formatting (not yet configured but recommended)
# Future: black src/ && isort src/

# Enable debug logging
$env:LOG_LEVEL="DEBUG"  # Windows PowerShell
export LOG_LEVEL=DEBUG  # Linux/Mac
auto-reviewer --doc document.pdf --agents agents.json
```

### Docker Operations
```bash
# Build container
docker build -f docker/Dockerfile -t auto-reviewer .

# Run containerized review (Linux/Mac)
docker run -v $(pwd)/documents:/documents -v $(pwd)/outputs:/outputs \
  auto-reviewer --doc /documents/report.pdf --agents /app/examples/agents.json

# Run containerized review (Windows PowerShell)
docker run -v "${PWD}/documents:/documents" -v "${PWD}/outputs:/outputs" `
  auto-reviewer --doc /documents/report.pdf --agents /app/examples/agents.json
```

## Architecture Overview

### Multi-Agent Review Pipeline
1. **Document Ingestion**: Documents are split into paragraphs with stable, immutable IDs
2. **Embedding & Indexing**: Creates vector indices for the main document and per-agent knowledge bases
3. **Isolated Agent Processing**: Each of up to 7 agents maintains separate RAG contexts to prevent contamination
4. **Scoring & Synthesis**: Generates comprehensive reports with 1-5 scale scoring and actionable rewrites

### Core Components
- **CLI Entry Point** (`cli.py`): Command-line interface and orchestration
- **Review Engine** (`review.py`): Main workflow coordination
- **Multi-Modal Loaders** (`loaders/`): PDF, DOCX, and TXT document processing
- **Vector Database** (`vectordb.py`): FAISS-based embedding storage and retrieval
- **RAG System** (`rag.py`): Retrieval-augmented generation for context-aware reviews
- **Agent System** (`agents/`): CrewAI-based multi-agent coordination
- **Synthesis Engine** (`synthesize.py`): Cross-agent result consolidation

### Key Design Principles
- **Document Integrity**: Original documents remain unchanged; all references use stable paragraph IDs
- **Agent Isolation**: Each agent maintains separate knowledge bases to prevent cross-contamination
- **LM Studio Integration**: Built for local LLM deployment with OpenAI-compatible API
- **Scalable Processing**: Configurable worker concurrency and embedding models

## Configuration

### Agent Configuration Structure
Agents are configured via JSON with specific personas, rubrics, and knowledge bases:
- **Persona Definition**: Each agent has unique tone, goals, and expertise areas
- **Scoring Rubrics**: 1-5 scale across multiple criteria with transparent averaging
- **Knowledge Integration**: Per-agent reference documents for specialized context
- **Retrieval Settings**: Configurable top-k and neighbor retrieval parameters

### Environment Requirements
- **LM Studio**: Local LLM server running on OpenAI-compatible endpoint
- **Embedding Model**: Sentence transformers for document vectorization (CPU-friendly default)
- **Python 3.10+**: Required for modern type hints and async features
- **Memory Considerations**: Embedding model size affects memory usage

### Output Structure
The system generates structured outputs in the `outputs/` directory:
- `run.json`: Run metadata and aggregate scores
- `{AgentName}.jsonl`: Per-paragraph findings for each agent
- `{AgentName}.md`: Human-readable reports (optional)
- `consolidated.json`: Synthesized findings across all agents

## Development Status

### Current Implementation Status
This project appears to be in early development phase:
- **Source Code**: No Python implementation files found in `src/auto_reviewer/`
- **Tests**: No test suite currently implemented
- **Examples**: Empty examples directory
- **Documentation**: Comprehensive documentation exists but code is missing

### Missing Components to Implement
1. Core Python modules (cli.py, review.py, config.py, etc.)
2. Document loaders (PDF, DOCX, TXT processors)
3. Agent system integration with CrewAI
4. Vector database and RAG implementation
5. Example configurations and sample documents
6. Test suite and CI/CD setup

### Recommended Development Workflow
1. **Start with Core Module**: Implement `cli.py` with basic argument parsing
2. **Add Configuration**: Create `config.py` with Pydantic models for settings
3. **Document Loading**: Implement text loader first, then PDF/DOCX
4. **Embedding System**: Set up sentence-transformers integration
5. **Basic RAG**: Implement FAISS-based vector storage and retrieval
6. **Agent Integration**: Connect CrewAI with basic agent definitions
7. **Output Generation**: Create JSON/JSONL output formatters
8. **Testing**: Add pytest fixtures and basic integration tests

## Development Patterns

### Adding Document Loaders
Implement the standard loader interface in `src/auto_reviewer/loaders/`:
```python
def load_paragraphs(path: str) -> List[Dict]:
    """Return list of {"paragraph_id": str, "text": str, "hash": str}"""
    pass
```

### Creating Custom Agents
Extend agent configurations with new personas, specialized rubrics, and domain-specific knowledge bases. Each agent should have distinct evaluation criteria to provide diverse perspectives.

### Extending RAG Context
Per-agent knowledge bases (`kb_refs`) allow specialized context without contamination. Reference documents are embedded separately for each agent's vector space.

## Troubleshooting

### LM Studio Integration
- Verify LM Studio server is running on configured endpoint (default: http://localhost:1234/v1)
- Ensure model name in configuration matches LM Studio model identifier
- Check API key configuration (use "lm-studio" for local setup)

### Performance Optimization
- Reduce embedding model size for memory-constrained environments
- Adjust worker count based on available CPU cores
- Monitor document chunk size for optimal processing

### Agent Limitations
- Maximum 7 agents supported for optimal performance
- Each agent maintains separate vector indices (memory scaling consideration)
- Agent isolation prevents knowledge sharing by design

## LM Studio Configuration

This project is specifically designed to work with local LM Studio deployments:
- Configure `OPENAI_BASE_URL` to your LM Studio server endpoint
- Use `OPENAI_API_KEY=lm-studio` for local authentication
- Set `OPENAI_MODEL` to match your loaded model in LM Studio
- Default embedding model is CPU-friendly for local processing

## Docker Deployment

### Quick Start with Docker
```bash
# Windows PowerShell (Recommended)
.\docker\build-and-run.ps1 build  # Build images
.\docker\build-and-run.ps1 dev    # Development mode
.\docker\build-and-run.ps1 prod -Document "./documents/report.pdf"  # Run review

# Windows Batch
docker-run.bat build  # Build images
docker-run.bat dev    # Development mode
docker-run.bat prod   # Production mode

# Direct Docker Compose
docker-compose up --build auto-reviewer      # Production
docker-compose up --build auto-reviewer-dev  # Development
```

### Docker Architecture
- **Production Container**: Optimized for document reviews with CrewAI agents
- **Development Container**: Source code mounting, debugging tools, Jupyter
- **Vector Database**: FAISS (embedded) or optional Qdrant service
- **LM Studio Integration**: Automatic connection to host LM Studio via `host.docker.internal`

### Container Features
- **Persistent Data**: Vector databases, embeddings cache, and outputs preserved
- **Resource Management**: Configurable CPU/memory limits and health checks
- **Network Access**: Windows-optimized networking to reach host LM Studio
- **Security**: Non-root execution with minimal attack surface

### Environment Variables for Docker
```env
OPENAI_BASE_URL=http://host.docker.internal:1234/v1  # Windows/Mac
EMBED_MODEL=sentence-transformers/all-MiniLM-L6-v2
MAX_WORKERS=4
LOG_LEVEL=INFO
```

### Volume Mounts
- `./data/vector_db` → `/app/data/vector_db` (Vector database storage)
- `./data/cache` → `/app/data/cache` (Embedding cache)
- `./data/outputs` → `/app/outputs` (Review results)
- `./documents` → `/app/documents` (Input documents, read-only)
- `./examples` → `/app/examples` (Agent configs, read-only)

### Development Workflow
```bash
# Start development environment
.\docker\build-and-run.ps1 dev

# Access container shell
docker exec -it auto-reviewer-dev bash

# Run tests
.\docker\build-and-run.ps1 test

# View logs
.\docker\build-and-run.ps1 logs
```

See `docker/README.md` for comprehensive Docker setup documentation.

# Docker Setup for Auto-Reviewer

This Docker setup provides a complete runtime environment for the auto-reviewer system with CrewAI agents and vector database support, designed to connect to your local LM Studio instance.

## Prerequisites

1. **Docker Desktop**: Install Docker Desktop for Windows
2. **LM Studio**: Running locally on port 1234 with server mode enabled
3. **WSL2** (recommended): For better Docker performance on Windows

## Quick Start

### Option 1: PowerShell Script (Recommended)
```powershell
# Build both production and development images
.\docker\build-and-run.ps1 build

# Start development environment
.\docker\build-and-run.ps1 dev

# Run a document review
.\docker\build-and-run.ps1 prod -Document ".\documents\report.pdf"
```

### Option 2: Batch File
```batch
# Build images
docker-run.bat build

# Start development environment  
docker-run.bat dev

# Start production environment
docker-run.bat prod
```

### Option 3: Docker Compose Directly
```bash
# Build and start production
docker-compose up --build auto-reviewer

# Build and start development
docker-compose up --build auto-reviewer-dev
```

## Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Your Windows  │    │ Docker Container│    │  Vector Database│
│   LM Studio     │◄───┤ Auto-Reviewer   │◄──►│   (In Container)│
│   localhost:1234│    │ CrewAI Agents   │    │   FAISS/Qdrant  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                       ┌─────────────────┐
                       │  Persistent     │
                       │  Data Volumes   │
                       │  ./data/        │
                       └─────────────────┘
```

## Container Services

### 1. auto-reviewer (Production)
- **Purpose**: Production-ready container for document reviews
- **Build Target**: `production`
- **Network**: Bridge mode with `host.docker.internal` access
- **Volumes**: Persistent data, read-only documents and config

### 2. auto-reviewer-dev (Development)
- **Purpose**: Development environment with mounted source code
- **Build Target**: `development`
- **Features**: Source code mounting, debugging tools, Jupyter notebook
- **Access**: Interactive shell for development work

### 3. vector-db (Optional)
- **Purpose**: Standalone Qdrant vector database
- **Image**: `qdrant/qdrant:v1.6.0`
- **Ports**: 6333 (HTTP), 6334 (gRPC)
- **Profile**: `vector-db` (start with `--profile vector-db`)

## Network Configuration

### Windows Setup (Default)
```yaml
# docker-compose.override.yml automatically handles Windows networking
services:
  auto-reviewer:
    network_mode: "bridge"
    extra_hosts:
      - "host.docker.internal:host-gateway"
    environment:
      - OPENAI_BASE_URL=http://host.docker.internal:1234/v1
```

### Linux Setup
```yaml
# For Linux, modify docker-compose.yml
services:
  auto-reviewer:
    network_mode: "host"  # Direct host access
    environment:
      - OPENAI_BASE_URL=http://localhost:1234/v1
```

## Environment Variables

### LM Studio Configuration
```env
OPENAI_API_KEY=lm-studio
OPENAI_BASE_URL=http://host.docker.internal:1234/v1
OPENAI_MODEL=openai/gpt-oss-20b
TEMPERATURE=0.2
MAX_TOKENS=2000
```

### Embedding Configuration
```env
EMBED_MODEL=sentence-transformers/all-MiniLM-L6-v2
EMBED_BATCH_SIZE=32
EMBED_MAX_LENGTH=512
```

### Processing Settings
```env
MAX_WORKERS=4
LOG_LEVEL=INFO
```

## Volume Mounts

| Host Path | Container Path | Purpose |
|-----------|---------------|---------|
| `./data/vector_db` | `/app/data/vector_db` | Vector database storage |
| `./data/cache` | `/app/data/cache` | Embedding cache |
| `./data/outputs` | `/app/outputs` | Review results |
| `./documents` | `/app/documents` | Input documents (read-only) |
| `./examples` | `/app/examples` | Example configurations (read-only) |
| `.env` | `/app/.env` | Environment configuration (read-only) |

## Usage Examples

### 1. Basic Document Review
```powershell
# Place your document in ./documents/
Copy-Item "C:\path\to\report.pdf" ".\documents\"

# Run review
.\docker\build-and-run.ps1 prod -Document ".\documents\report.pdf"
```

### 2. Development Mode
```powershell
# Start development container
.\docker\build-and-run.ps1 dev

# Access shell in running container
docker exec -it auto-reviewer-dev bash

# Or start a new shell session
.\docker\build-and-run.ps1 shell
```

### 3. Custom Agent Configuration
```powershell
# Create your agents.json in examples/
# Run with custom agents
docker-compose run --rm auto-reviewer auto-reviewer \
  --doc /app/documents/report.pdf \
  --agents /app/examples/my-agents.json \
  --out /app/outputs
```

### 4. With Vector Database Service
```bash
# Start with external vector database
docker-compose --profile vector-db up -d

# The auto-reviewer can then connect to qdrant at localhost:6333
```

## Troubleshooting

### LM Studio Connection Issues

1. **Check LM Studio Server**:
   ```powershell
   # Test if LM Studio is accessible
   Invoke-WebRequest -Uri "http://localhost:1234/v1/models"
   ```

2. **Enable Server Mode**:
   - Open LM Studio
   - Go to "Local Server" tab
   - Click "Start Server"
   - Ensure it's running on port 1234

3. **Windows Firewall**:
   - Allow Docker Desktop through Windows Firewall
   - Allow LM Studio through Windows Firewall

### Container Connection Test
```bash
# Test from inside container
docker exec -it auto-reviewer curl http://host.docker.internal:1234/v1/models

# Check container networking
docker exec -it auto-reviewer nslookup host.docker.internal
```

### Memory Issues
```yaml
# Adjust resource limits in docker-compose.yml
deploy:
  resources:
    limits:
      memory: 8G  # Increase if needed
      cpus: '4.0'
```

### Debug Mode
```powershell
# Start with debug logging
$env:LOG_LEVEL = "DEBUG"
.\docker\build-and-run.ps1 dev
```

## Development Workflow

### 1. Code Changes
```bash
# Start dev container with source mounting
docker-compose up -d auto-reviewer-dev

# Code changes are reflected immediately
# Restart container if needed
docker-compose restart auto-reviewer-dev
```

### 2. Testing
```bash
# Run tests in container
docker-compose run --rm auto-reviewer-dev pytest /app/tests/ -v

# Or use the script
.\docker\build-and-run.ps1 test
```

### 3. Jupyter Notebook (Development Image)
```bash
# Start notebook server
docker exec -it auto-reviewer-dev jupyter notebook --ip=0.0.0.0 --port=8888 --allow-root

# Access at http://localhost:8888
```

## Performance Optimization

### 1. Docker Resource Allocation
- Increase Docker Desktop memory to 8GB+
- Enable WSL2 backend for better performance
- Use SSD storage for Docker data

### 2. Embedding Cache
- Enable persistent volume for `/app/data/cache`
- Use faster embedding models if needed
- Adjust batch size based on available memory

### 3. Vector Database
- Use external Qdrant for better performance
- Configure appropriate index parameters
- Monitor memory usage during large document processing

## Security Considerations

1. **Non-root User**: Container runs as `appuser`
2. **Read-only Mounts**: Configuration and documents are read-only
3. **Network Isolation**: Only necessary ports exposed
4. **Data Volumes**: Persistent data isolated in volumes

## Monitoring and Logs

```bash
# View container logs
docker-compose logs -f auto-reviewer

# Monitor resource usage
docker stats auto-reviewer

# Health check status
docker inspect --format='{{.State.Health.Status}}' auto-reviewer
```

## Clean Up

```powershell
# Stop and remove containers
.\docker\build-and-run.ps1 clean

# Or manually
docker-compose down --rmi all --volumes --remove-orphans
docker system prune -a
```
# PowerShell script to build and run the auto-reviewer Docker container
# Usage: ./build-and-run.ps1 [build|dev|prod|clean|test|shell]

param(
    [Parameter(Position=0)]
    [ValidateSet("build", "dev", "prod", "clean", "test", "shell", "logs", "status")]
    [string]$Action = "build",
    
    [Parameter(Position=1)]
    [string]$Document = "",
    
    [Parameter(Position=2)]
    [string]$Agents = "./examples/agents.json",
    
    [switch]$Force,
    [switch]$NoCache,
    [switch]$Verbose
)

# Set error action preference
$ErrorActionPreference = "Stop"

# Colors for output
function Write-ColorOutput {
    param(
        [string]$Message,
        [ConsoleColor]$ForegroundColor = [ConsoleColor]::White
    )
    Write-Host $Message -ForegroundColor $ForegroundColor
}

function Write-Success { param([string]$msg) Write-ColorOutput $msg Green }
function Write-Warning { param([string]$msg) Write-ColorOutput $msg Yellow }
function Write-Error { param([string]$msg) Write-ColorOutput $msg Red }
function Write-Info { param([string]$msg) Write-ColorOutput $msg Cyan }

# Check if Docker is running
function Test-DockerRunning {
    try {
        docker version *>$null
        return $true
    }
    catch {
        Write-Error "Docker is not running or not installed. Please start Docker Desktop."
        exit 1
    }
}

# Check if LM Studio is accessible
function Test-LMStudioConnection {
    Write-Info "Testing LM Studio connection..."
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:1234/v1/models" -Method GET -TimeoutSec 10
        if ($response.StatusCode -eq 200) {
            Write-Success "✓ LM Studio is accessible on localhost:1234"
            return $true
        }
    }
    catch {
        Write-Warning "⚠ LM Studio not accessible on localhost:1234"
        Write-Warning "Make sure LM Studio is running with server enabled"
        Write-Warning "You can continue, but the container won't be able to access your local models"
        return $false
    }
}

# Create necessary directories
function Initialize-Directories {
    Write-Info "Creating necessary directories..."
    
    $directories = @(
        "./data/vector_db",
        "./data/cache", 
        "./data/outputs",
        "./documents",
        "./examples"
    )
    
    foreach ($dir in $directories) {
        if (-not (Test-Path $dir)) {
            New-Item -ItemType Directory -Path $dir -Force | Out-Null
            Write-Success "Created directory: $dir"
        }
    }
}

# Build Docker images
function Build-DockerImage {
    param([string]$Target = "production")
    
    Write-Info "Building Docker image for $Target..."
    
    $buildArgs = @(
        "build",
        "-f", "Dockerfile",
        "--target", $Target,
        "-t", "auto-reviewer:$Target"
    )
    
    if ($NoCache) {
        $buildArgs += "--no-cache"
    }
    
    $buildArgs += "."
    
    if ($Verbose) {
        Write-Info "Running: docker $($buildArgs -join ' ')"
    }
    
    & docker @buildArgs
    
    if ($LASTEXITCODE -eq 0) {
        Write-Success "✓ Successfully built auto-reviewer:$Target"
    } else {
        Write-Error "✗ Failed to build Docker image"
        exit 1
    }
}

# Run container
function Start-Container {
    param(
        [string]$Service = "auto-reviewer",
        [string[]]$ExtraArgs = @()
    )
    
    Write-Info "Starting $Service container..."
    
    $composeArgs = @("up", "-d")
    if ($Force) {
        $composeArgs += "--force-recreate"
    }
    $composeArgs += $Service
    
    & docker-compose @composeArgs
    
    if ($LASTEXITCODE -eq 0) {
        Write-Success "✓ Container $Service started successfully"
        Write-Info "Use 'docker logs $Service' to view logs"
    } else {
        Write-Error "✗ Failed to start container"
        exit 1
    }
}

# Run a document review
function Start-DocumentReview {
    param(
        [string]$DocumentPath,
        [string]$AgentsPath = "./examples/agents.json"
    )
    
    if (-not $DocumentPath) {
        Write-Error "Document path is required for review"
        Write-Info "Usage: ./build-and-run.ps1 prod -Document './documents/report.pdf'"
        exit 1
    }
    
    if (-not (Test-Path $DocumentPath)) {
        Write-Error "Document file not found: $DocumentPath"
        exit 1
    }
    
    # Copy document to documents directory if not already there
    $docInContainer = "./documents/$(Split-Path $DocumentPath -Leaf)"
    if ($DocumentPath -ne $docInContainer) {
        Copy-Item $DocumentPath $docInContainer -Force
        Write-Info "Copied document to $docInContainer"
    }
    
    Write-Info "Starting document review..."
    Write-Info "Document: $DocumentPath"
    Write-Info "Agents: $AgentsPath"
    
    $containerDocPath = "/app/documents/$(Split-Path $DocumentPath -Leaf)"
    $containerAgentsPath = "/app/$AgentsPath"
    
    & docker-compose run --rm auto-reviewer auto-reviewer `
        --doc $containerDocPath `
        --agents $containerAgentsPath `
        --out /app/outputs
    
    if ($LASTEXITCODE -eq 0) {
        Write-Success "✓ Document review completed"
        Write-Info "Results saved to ./data/outputs/"
    }
}

# Main script logic
Test-DockerRunning
Initialize-Directories

switch ($Action) {
    "build" {
        Test-LMStudioConnection
        Build-DockerImage "production"
        Build-DockerImage "development"
        Write-Success "✓ All images built successfully"
    }
    
    "dev" {
        Test-LMStudioConnection
        Build-DockerImage "development"
        Start-Container "auto-reviewer-dev"
        Write-Info "Development container is running. Use 'docker exec -it auto-reviewer-dev bash' to access shell"
    }
    
    "prod" {
        Test-LMStudioConnection
        Build-DockerImage "production"
        if ($Document) {
            Start-DocumentReview $Document $Agents
        } else {
            Start-Container "auto-reviewer"
        }
    }
    
    "test" {
        Write-Info "Running tests in container..."
        & docker-compose run --rm auto-reviewer-dev pytest /app/tests/ -v
    }
    
    "shell" {
        Write-Info "Starting interactive shell..."
        & docker-compose run --rm auto-reviewer-dev bash
    }
    
    "logs" {
        Write-Info "Showing container logs..."
        & docker-compose logs -f auto-reviewer
    }
    
    "status" {
        Write-Info "Container status:"
        & docker-compose ps
    }
    
    "clean" {
        Write-Warning "Cleaning up containers and images..."
        & docker-compose down --rmi all --volumes --remove-orphans
        & docker system prune -f
        Write-Success "✓ Cleanup completed"
    }
    
    default {
        Write-Error "Unknown action: $Action"
        Write-Info "Available actions: build, dev, prod, clean, test, shell, logs, status"
        exit 1
    }
}

Write-Success "✓ Operation completed successfully"
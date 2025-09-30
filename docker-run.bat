@echo off
REM Simple batch file to run Docker operations for auto-reviewer
REM Usage: docker-run.bat [build|dev|prod|clean]

set ACTION=%1
if "%ACTION%"=="" set ACTION=build

echo ====================================
echo Auto-Reviewer Docker Runner
echo ====================================

REM Check if Docker is running
docker version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Docker is not running. Please start Docker Desktop.
    pause
    exit /b 1
)

REM Create necessary directories
if not exist "data\vector_db" mkdir "data\vector_db"
if not exist "data\cache" mkdir "data\cache" 
if not exist "data\outputs" mkdir "data\outputs"
if not exist "documents" mkdir "documents"
if not exist "examples" mkdir "examples"

if "%ACTION%"=="build" (
    echo Building Docker images...
    docker build -f Dockerfile --target production -t auto-reviewer:production .
    docker build -f Dockerfile --target development -t auto-reviewer:development .
    echo Build completed!
) else if "%ACTION%"=="dev" (
    echo Starting development container...
    docker-compose up -d auto-reviewer-dev
    echo Development container started. Access with: docker exec -it auto-reviewer-dev bash
) else if "%ACTION%"=="prod" (
    echo Starting production container...
    docker-compose up -d auto-reviewer
    echo Production container started.
) else if "%ACTION%"=="clean" (
    echo Cleaning up containers and images...
    docker-compose down --rmi all --volumes --remove-orphans
    docker system prune -f
    echo Cleanup completed!
) else if "%ACTION%"=="shell" (
    echo Starting interactive shell...
    docker-compose run --rm auto-reviewer-dev bash
) else if "%ACTION%"=="logs" (
    echo Showing container logs...
    docker-compose logs -f auto-reviewer
) else (
    echo Unknown action: %ACTION%
    echo Available actions: build, dev, prod, clean, shell, logs
    exit /b 1
)

echo Operation completed!
pause
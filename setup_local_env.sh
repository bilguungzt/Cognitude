#!/bin/bash

# Script to set up the local development environment for Cognitude
# This script handles Python, dependencies, and both frontend/backend setup

echo "Setting up Cognitude local development environment..."

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check if Docker is installed and running
if ! command_exists docker; then
    echo "Docker is not installed. Please install Docker Desktop:"
    echo "  https://www.docker.com/products/docker-desktop"
    exit 1
fi

if ! docker info >/dev/null 2>&1; then
    echo "Docker is installed but not running. Please start Docker Desktop."
    exit 1
fi

# Check if Python is installed
if ! command_exists python3; then
    echo "Python 3 is not installed. Please install Python 3.9 or higher."
    echo "On macOS, you can install it using Homebrew:"
    echo "  brew install python@3.11"
    echo ""
    echo "On Ubuntu/Debian:"
    echo "  sudo apt update && sudo apt install python3.11 python3.11-venv python3.11-dev"
    exit 1
fi

# Check if pip is installed
if ! command_exists pip3; then
    echo "pip is not installed. Installing pip..."
    python3 -m ensurepip --upgrade
fi

# Use python3 and pip3 to be explicit
PYTHON_CMD=python3
PIP_CMD=pip3

echo "Using Python: $($PYTHON_CMD --version)"
echo "Using Pip: $($PIP_CMD --version)"

# Check if virtual environment exists, create if not
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    $PYTHON_CMD -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
$PIP_CMD install --upgrade pip

# Install Python dependencies
echo "Installing Python dependencies..."
$PIP_CMD install -r requirements.txt

# Verify that required packages are installed
echo "Verifying required packages..."
if ! command_exists uvicorn; then
    echo "Installing uvicorn..."
    $PIP_CMD install uvicorn[standard]
fi

if ! command_exists alembic; then
    echo "Installing alembic..."
    $PIP_CMD install alembic
fi

# Start Docker services for local development
echo "Starting Docker services (PostgreSQL and Redis)..."
docker-compose -f docker-compose.dev.yml up -d

# Wait for services to be ready with better checking
echo "Waiting for database and Redis to be ready..."
for i in {1..30}; do
    if docker-compose -f docker-compose.dev.yml exec db pg_isready >/dev/null 2>&1; then
        echo "Database is ready!"
        break
    fi
    echo "Waiting for database... ($i/30)"
    sleep 2
done

# Additional wait for Redis
sleep 5

# Run database migrations
echo "Running database migrations..."
alembic upgrade head

# Setup frontend
echo "Setting up frontend..."
cd frontend

# Install Node dependencies if not already installed
if [ ! -d "node_modules" ]; then
    echo "Installing Node.js dependencies..."
    if ! command_exists npm; then
        echo "npm is not installed. Please install Node.js (which includes npm)."
        echo "On macOS, you can install it using Homebrew:"
        echo "  brew install node"
        echo ""
        echo "On Ubuntu/Debian:"
        echo "  curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash - && sudo apt-get install -y nodejs"
        exit 1
    fi
    
    npm install
else
    echo "Node.js dependencies already installed."
fi

# Ensure frontend .env is set up for local development
if [ ! -f ".env" ]; then
    echo "VITE_API_URL=http://localhost:8000" > .env
    echo "Created frontend .env file"
fi

echo ""
echo "Setup complete!"
echo ""
echo "To start the development servers:"
echo ""
echo "Terminal 1 (Backend):"
echo "  cd /Users/billy/Documents/Projects/cognitude_mvp"
echo "  source venv/bin/activate"
echo "  uvicorn app.main:app --reload --port 8000"
echo ""
echo "Terminal 2 (Frontend):"
echo "  cd /Users/billy/Documents/Projects/cognitude_mvp/frontend"
echo "  npm run dev"
echo ""
echo "Or use the provided script: ./start_local_dev.sh"
echo ""
echo "To stop Docker services when done:"
echo " docker-compose -f docker-compose.dev.yml down"
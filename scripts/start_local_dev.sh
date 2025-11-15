#!/bin/bash

# Script to start both frontend and backend for local development
# This script starts both servers in the proper order

echo "Starting Cognitude local development environment..."

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Detect processes listening on a port and optionally prompt/auto-kill them.
# Usage: detect_and_handle_port <port>
detect_and_handle_port() {
    local PORT="$1"
    local PIDS=""

    if command_exists lsof; then
        PIDS=$(lsof -ti tcp:$PORT 2>/dev/null || true)
    else
        # try netstat as fallback (macOS/net-tools)
        if command_exists netstat; then
            PIDS=$(netstat -anv | awk "/\.$PORT .*LISTEN/ {print \$9}" 2>/dev/null || true)
        fi
    fi

    if [ -z "$PIDS" ]; then
        return 0
    fi

    echo "Detected processes listening on port $PORT:"
    for pid in $PIDS; do
        ps -o pid,cmd -p $pid 2>/dev/null || echo "  PID $pid"
    done

    # auto-kill if env var set
    if [ "${START_LOCAL_DEV_AUTO_KILL:-}" = "true" ]; then
        echo "Auto-kill enabled (START_LOCAL_DEV_AUTO_KILL=true). Killing processes on port $PORT..."
        for pid in $PIDS; do
            echo "Killing PID $pid..."
            kill $pid 2>/dev/null || true
            sleep 1
            if kill -0 $pid 2>/dev/null; then
                echo "PID $pid did not exit, forcing..."
                kill -9 $pid 2>/dev/null || true
            fi
        done
        sleep 1
        return 0
    fi

    # Prompt mode
    for pid in $PIDS; do
        ps -o pid,cmd -p $pid 2>/dev/null
        read -p "Do you want to kill PID $pid ? [y/N] " yn
        case "$yn" in
            [Yy]*)
                kill $pid 2>/dev/null || true
                sleep 1
                if kill -0 $pid 2>/dev/null; then
                    echo "PID $pid did not exit, forcing..."
                    kill -9 $pid 2>/dev/null || true
                fi
                ;;
            *)
                echo "User chose not to kill PID $pid. Aborting startup."
                return 1
                ;;
        esac
    done

    return 0
}

# Check if Docker is running
if ! command_exists docker; then
    echo "Docker is not installed. Please install Docker Desktop."
    exit 1
fi

if ! docker info >/dev/null 2>&1; then
    echo "Docker is not running. Please start Docker Desktop."
    exit 1
fi

# Function to start backend
start_backend() {
    echo "Starting backend server..."
    cd "$SCRIPT_DIR"
    
    # Activate virtual environment if it exists
    if [ -d "venv" ]; then
        source venv/bin/activate
    else
        echo "Error: venv not found. Run ./setup_local_env.sh first."
        exit 1
    fi
    
    # If the venv has python3 but not python, create a symlink for convenience
    if [ -d "venv/bin" ] && [ -x "venv/bin/python3" ] && [ ! -x "venv/bin/python" ]; then
        echo "Creating python -> python3 symlink inside venv/bin"
        ln -s python3 venv/bin/python || true
    fi
    
    # Resolve python executable: prefer active venv, fallback to python3 or python
    if [ -n "$VIRTUAL_ENV" ] && [ -x "$VIRTUAL_ENV/bin/python" ]; then
        PYTHON="$VIRTUAL_ENV/bin/python"
    elif command_exists python3; then
        PYTHON=python3
    elif command_exists python; then
        PYTHON=python
    else
        echo "Python is not available. Please install Python 3 and create the virtualenv."
        exit 1
    fi

    # Ensure dependencies are installed into the venv
    if ! $PYTHON -c "import uvicorn" >/dev/null 2>&1; then
        echo "uvicorn (and/or other requirements) not found. Installing dependencies into venv..."
        $PYTHON -m pip install -r requirements.txt
        # re-evaluate availability
        if ! $PYTHON -c "import uvicorn" >/dev/null 2>&1; then
            echo "Failed to install uvicorn. Please check pip output and try again."
            exit 1
        fi
    fi
    
    # Check if Docker services are running
    if ! docker compose -f docker-compose.dev.yml ps | grep -q "Up"; then
        echo "Starting Docker services (PostgreSQL and Redis)..."
        docker compose -f docker-compose.dev.yml up -d
        
        # Wait for services to be ready with better checking
        echo "Waiting for database and Redis to be ready..."
        for i in {1..30}; do
            if docker compose -f docker-compose.dev.yml exec -T db pg_isready >/dev/null 2>&1; then
                echo "Database is ready!"
                break
            fi
            echo "Waiting for database... ($i/30)"
            sleep 2
        done
        
        if ! docker compose -f docker-compose.dev.yml exec -T db pg_isready >/dev/null 2>&1; then
            echo "❌ Error: Database failed to start after 30 seconds"
            echo "Logs:"
            docker compose -f docker-compose.dev.yml logs db
            exit 1
        fi
        
        # Additional wait for Redis
        sleep 5
    else
        echo "Docker services are already running."
    fi
    
    # Check for port conflicts on 8000 and handle according to START_LOCAL_DEV_AUTO_KILL or prompt
    if ! detect_and_handle_port 8000; then
        echo "Port conflict not resolved. Aborting backend start."
        exit 1
    fi

    # Start the backend server using the resolved python
    $PYTHON -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
}

# Function to start frontend
start_frontend() {
    echo "Starting frontend server..."
    cd "$SCRIPT_DIR/frontend"
    
    # Check if node_modules exists
    if [ ! -d "node_modules" ]; then
        echo "Error: node_modules not found. Run ./setup_local_env.sh first."
        exit 1
    fi
    
    # Check for port conflicts on 5173 (Vite default)
    if ! detect_and_handle_port 5173; then
        echo "Port conflict not resolved. Aborting frontend start."
        exit 1
    fi
    
    # Start the frontend server
    npm run dev
}

# Check if we're running both or just one
case "${1:-both}" in
    "backend")
        echo "Starting only backend..."
        start_backend
        ;;
    "frontend")
        echo "Starting only frontend..."
        start_frontend
        ;;
    "both")
        echo "Starting both frontend and backend..."
        
        # Start backend in background
        cd "$SCRIPT_DIR"
        if [ -d "venv" ]; then
            source venv/bin/activate
        else
            echo "Error: venv not found. Run ./setup_local_env.sh first."
            exit 1
        fi
        
        # If the venv has python3 but not python, create a symlink for convenience
        if [ -d "venv/bin" ] && [ -x "venv/bin/python3" ] && [ ! -x "venv/bin/python" ]; then
            echo "Creating python -> python3 symlink inside venv/bin"
            ln -s python3 venv/bin/python || true
        fi

        # Resolve python executable
        if [ -n "$VIRTUAL_ENV" ] && [ -x "$VIRTUAL_ENV/bin/python" ]; then
            PYTHON="$VIRTUAL_ENV/bin/python"
        elif command_exists python3; then
            PYTHON=python3
        elif command_exists python; then
            PYTHON=python
        else
            echo "Python is not available. Please install Python 3 and create the virtualenv."
            exit 1
        fi

        # Ensure dependencies are installed into the venv
        if ! $PYTHON -c "import uvicorn" >/dev/null 2>&1; then
            echo "uvicorn (and/or other requirements) not found. Installing dependencies into venv..."
            $PYTHON -m pip install -r requirements.txt
            if ! $PYTHON -c "import uvicorn" >/dev/null 2>&1; then
                echo "Failed to install uvicorn. Please check pip output and try again."
                exit 1
            fi
        fi
        
        # Check if Docker services are running
        if ! docker compose -f docker-compose.dev.yml ps | grep -q "Up"; then
            echo "Starting Docker services (PostgreSQL and Redis)..."
            docker compose -f docker-compose.dev.yml up -d
            
            # Wait for services to be ready with better checking
            echo "Waiting for database and Redis to be ready..."
            for i in {1..30}; do
                if docker compose -f docker-compose.dev.yml exec -T db pg_isready >/dev/null 2>&1; then
                    echo "Database is ready!"
                    break
                fi
                echo "Waiting for database... ($i/30)"
                sleep 2
            done
            
            if ! docker compose -f docker-compose.dev.yml exec -T db pg_isready >/dev/null 2>&1; then
                echo "❌ Error: Database failed to start after 30 seconds"
                echo "Logs:"
                docker compose -f docker-compose.dev.yml logs db
                docker compose -f docker-compose.dev.yml down
                exit 1
            fi
            
            # Additional wait for Redis
            sleep 5
        else
            echo "Docker services are already running."
        fi
        
        echo "Starting backend server..."
        # Create log directory if it doesn't exist
        mkdir -p /tmp
        
        # Check for port conflicts on 8000 and handle according to START_LOCAL_DEV_AUTO_KILL or prompt
        if ! detect_and_handle_port 8000; then
            echo "Port conflict not resolved. Aborting backend start."
            docker compose -f docker-compose.dev.yml down
            exit 1
        fi

        # Start uvicorn using the venv/python so correct environment is used
        $PYTHON -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 > /tmp/backend.log 2>&1 &
        BACKEND_PID=$!
        
        # Give backend a moment to start and check if it's running properly
        sleep 8
        
        # Check if backend started successfully by checking if the process is still alive
        if ! kill -0 $BACKEND_PID 2>/dev/null; then
            echo "❌ Error: Backend failed to start. Check /tmp/backend.log for details."
            # Show the last few lines of the log for debugging
            if [ -f "/tmp/backend.log" ]; then
                echo "Last 20 lines of backend log:"
                tail -n 20 /tmp/backend.log
            fi
            docker compose -f docker-compose.dev.yml down
            exit 1
        fi
        
        echo "✅ Backend started successfully with PID $BACKEND_PID"
        echo "📄 Backend logs are available at /tmp/backend.log"
        
        # Start frontend
        cd "$SCRIPT_DIR/frontend"
        echo "Starting frontend server..."
        
        # Check frontend port
        if ! detect_and_handle_port 5173; then
            echo "Port conflict not resolved. Aborting frontend start."
            kill $BACKEND_PID 2>/dev/null
            exit 1
        fi
        
        npm run dev
        
        # When frontend stops, kill backend too
        kill $BACKEND_PID 2>/dev/null
        ;;
    *)
        echo "Usage: $0 [both|backend|frontend]"
        echo "  both (default): Start both frontend and backend"
        echo "  backend: Start only backend"
        echo "  frontend: Start only frontend"
        exit 1
        ;;
esac

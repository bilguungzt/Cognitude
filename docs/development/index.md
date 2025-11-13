# Local Development Setup

This guide explains how to run both the frontend and backend locally for development and testing.

## Prerequisites

- Node.js (v18 or higher)
- Python (v3.9 or higher)
- pip
- Docker Desktop (for database and Redis)
- Docker Compose

## Quick Setup (Recommended)

The easiest way to set up your local environment is to use the automated setup script:

```bash
./setup_local_env.sh
```

This script will:
- Check if Python, Node.js, and Docker are installed and running
- Create a virtual environment
- Install all required dependencies
- Start Docker services (PostgreSQL and Redis)
- Run database migrations
- Set up frontend environment

## Manual Setup

### 1. Install Python (if not already installed)

On macOS:
```bash
# Install Homebrew if you don't have it
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python
brew install python@3.11
```

On Ubuntu/Debian:
```bash
sudo apt update
sudo apt install python3.11 python3.11-venv python3.11-dev
```

### 2. Install Docker

Download and install Docker Desktop:
- [Docker Desktop for Mac](https://www.docker.com/products/docker-desktop)
- [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop)

### 3. Backend Setup

```bash
# Create a virtual environment
python3 -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt

# Start Docker services for local development
docker-compose -f docker-compose.dev.yml up -d

# Wait for services to be ready (about 10 seconds)
sleep 10

# Run database migrations
alembic upgrade head
```

### 4. Set Up Environment Variables

Create a `.env` file in the root directory:

```bash
# Database - Using Docker container
DATABASE_URL=postgresql+psycopg2://myuser:mypassword@localhost:5432/mydatabase

# Redis - Using Docker container
REDIS_URL=redis://localhost:6379/0

# Security
SECRET_KEY=your-super-secret-key-here-32-characters-minimum-must-be-very-long

# Optional: Provider API keys (for LLM functionality)
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key

# For local development, you can use test values
ENVIRONMENT=development
```

### 5. Frontend Setup

```bash
cd frontend

# Install Node dependencies
npm install

# Set up environment for local development
echo "VITE_API_URL=http://localhost:8000" > .env
```

### 6. Start Backend Server

```bash
# Activate virtual environment
source venv/bin/activate

# Make sure Docker services are running
docker-compose -f docker-compose.dev.yml up -d

# Start the backend server
uvicorn app.main:app --reload --host 0.0.0 --port 8000
```

The backend will be available at `http://localhost:8000`

### 7. Start Frontend Server

```bash
cd frontend
npm run dev
```

The frontend will be available at `http://localhost:5173` (or similar port if 5173 is taken)

## Docker Setup (Required)

This project requires Docker to run PostgreSQL and Redis for local development:

```bash
# Start database and Redis with Docker
docker-compose -f docker-compose.dev.yml up -d

# Check if services are running
docker-compose -f docker-compose.dev.yml ps

# Stop services when done
docker-compose -f docker-compose.dev.yml down
```

## Testing the Registration Flow

1. Make sure Docker services, backend, and frontend are all running
2. Open the frontend in your browser (usually `http://localhost:5175`)
3. Navigate to the registration page
4. Try to register a new organization
5. Check that no CORS errors occur in the browser console

## Troubleshooting

### Common Issues

1. **Command not found**: Make sure you're using `python3` and `pip3` instead of `python` and `pip`
2. **Database Connection Error**: Make sure Docker is running and the database service is up:
   ```bash
   docker-compose -f docker-compose.dev.yml ps
   ```
3. **Redis Connection Error**: Make sure the Redis service is running in Docker
4. **CORS Error**: Verify that the backend is running on `http://localhost:8000` and the frontend is configured to use this URL

### Docker Troubleshooting

If Docker services don't start:
```bash
# Check Docker status
docker info

# View Docker logs
docker-compose -f docker-compose.dev.yml logs

# Restart Docker services
docker-compose -f docker-compose.dev.yml down
docker-compose -f docker-compose.dev.yml up -d
```

### Port Conflicts

If you encounter port conflicts:
- Change backend port: `uvicorn app.main:app --reload --port 8001`
- Update `VITE_API_URL` in frontend `.env` accordingly

## Development Workflow

For local development, run both servers in separate terminals:

Terminal 1 (Backend):
```bash
cd /path/to/cognitude_mvp
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0 --port 8000
```

Terminal 2 (Frontend):
```bash
cd /path/to/cognitude_mvp/frontend
npm run dev
```

Both servers will automatically reload when you make changes to the code.
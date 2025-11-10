# Local Testing: Frontend and Backend

This guide explains how to test both the frontend and backend locally, which will help you verify that the CORS issue is resolved before deploying to production.

## Overview

This setup allows you to:
- Run the backend API server locally on `http://localhost:8000`
- Run the frontend development server locally on `http://localhost:5175`
- Test the registration flow without CORS issues
- Verify all functionality before deployment

## Prerequisites

- Node.js (v18 or higher)
- Python (v3.9 or higher)
- pip
- Docker Desktop (for database and Redis)
- Docker Compose

## Setup Instructions

### 1. Quick Setup (Recommended)

Use the automated setup script:

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

### 2. Manual Setup (Alternative)

#### Backend Setup

```bash
# Navigate to project root
cd /Users/billy/Documents/Projects/cognitude_mvp

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate

# Upgrade pip and install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Start Docker services for local development
docker-compose -f docker-compose.dev.yml up -d

# Wait for services to be ready (about 10 seconds)
sleep 10

# Create .env file with required environment variables
cat > .env << EOF
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
EOF

# Run database migrations
alembic upgrade head
```

#### Frontend Setup

```bash
# Navigate to frontend directory
cd /Users/billy/Documents/Projects/cognitude_mvp/frontend

# Install dependencies
npm install

# Set up environment for local development
echo "VITE_API_URL=http://localhost:8000" > .env
```

### 3. Start Services

#### Option A: Using the Provided Script

```bash
# Run both frontend and backend
./start_local_dev.sh
```

#### Option B: Manual Start

Terminal 1 (Backend):
```bash
cd /Users/billy/Documents/Projects/cognitude_mvp
source venv/bin/activate
# Make sure Docker services are running
docker-compose -f docker-compose.dev.yml up -d
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Terminal 2 (Frontend):
```bash
cd /Users/billy/Documents/Projects/cognitude_mvp/frontend
npm run dev
```

## Testing the Registration Flow

1. Make sure Docker services, backend, and frontend are all running
2. Open your browser and go to `http://localhost:5175` (or the port shown in the frontend output)
3. Navigate to the registration page
4. Try to register a new organization
5. Check the browser console for any errors
6. Verify that the registration request completes successfully

## Docker for Dependencies (Required)

This project requires Docker to run PostgreSQL and Redis for local development:

```bash
# Start database and Redis with Docker
docker-compose -f docker-compose.dev.yml up -d

# Check if services are running
docker-compose -f docker-compose.dev.yml ps

# Stop services when done
docker-compose -f docker-compose.dev.yml down
```

## CORS Configuration for Local Development

The frontend's Vite configuration (`frontend/vite.config.ts`) includes a proxy that forwards API requests from the frontend server to the backend server, which eliminates CORS issues during development:

```typescript
proxy: {
  '/api': {
    target: 'http://localhost:8000',
    changeOrigin: true,
    secure: false,
 },
  '/auth': {
    target: 'http://localhost:8000',
    changeOrigin: true,
    secure: false,
  },
  '/v1': {
    target: 'http://localhost:8000',
    changeOrigin: true,
    secure: false,
  },
  '/analytics': {
    target: 'http://localhost:8000',
    changeOrigin: true,
    secure: false,
  },
  '/providers': {
    target: 'http://localhost:8000',
    changeOrigin: true,
    secure: false,
  },
  '/cache': {
    target: 'http://localhost:8000',
    changeOrigin: true,
    secure: false,
  },
  '/alerts': {
    target: 'http://localhost:8000',
    changeOrigin: true,
    secure: false,
  },
  '/rate-limits': {
    target: 'http://localhost:8000',
    changeOrigin: true,
    secure: false,
  },
  '/health': {
    target: 'http://localhost:8000',
    changeOrigin: true,
    secure: false,
  }
}
```

This means that even though the frontend runs on port 5175 and backend on port 800, all API requests are proxied through the frontend server, avoiding CORS issues.

## Verification Steps

1. **Backend Health Check**: Visit `http://localhost:8000/health` in your browser
2. **API Documentation**: Visit `http://localhost:8000/docs` to see the API documentation
3. **Registration Test**: Try registering a new organization through the frontend
4. **Browser Console**: Check for any CORS errors or other issues

## Troubleshooting

### Common Issues

1. **Command not found**: Make sure you're using `python3` and `pip3` instead of `python` and `pip`
2. **Port Already in Use**: If port 8000 or 5175 is taken, the servers will suggest alternative ports
3. **Database Connection**: Ensure Docker is running and the database service is up:
   ```bash
   docker-compose -f docker-compose.dev.yml ps
   ```
4. **Redis Connection**: Ensure the Redis service is running in Docker
5. **Missing Dependencies**: Make sure all Python and Node dependencies are installed

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

### Checking Process Status

```bash
# Check if backend is running
lsof -i :800

# Check if frontend is running
lsof -i :5175
```

## Production vs Local Development

- **Local**: Frontend runs on `http://localhost:5175`, backend on `http://localhost:8000`
- **Production**: Frontend and backend are separated by domain, requiring proper CORS configuration
- **Local Proxy**: The Vite proxy eliminates CORS issues during development
- **Production**: Requires nginx CORS headers (as provided in the CORS fix)

## Next Steps

Once you've verified that the registration flow works correctly in your local environment:

1. Apply the nginx CORS fix to your production server using the files provided in this repository
2. Test the production registration flow
3. Verify that CORS issues are resolved in production
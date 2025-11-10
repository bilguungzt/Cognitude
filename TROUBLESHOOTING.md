# Troubleshooting Guide

This guide helps you troubleshoot common issues when setting up and running the Cognitude application locally.

## Common Registration Issues

### 1. 500 Internal Server Error on Registration

**Symptoms:**
- Request URL: `http://localhost:8000/auth/register`
- Request Method: POST
- Status Code: 500 Internal Server Error

**Solutions:**

1. **Check Docker Services:**
   ```bash
   # Verify Docker is running
   docker info
   
   # Check if database and Redis services are running
   docker-compose -f docker-compose.dev.yml ps
   
   # If services are not running, start them
   docker-compose -f docker-compose.dev.yml up -d
   ```

2. **Verify Environment Variables:**
   Make sure your `.env` file has the correct database URL:
   ```bash
   # Database - Using Docker container
   DATABASE_URL=postgresql+psycopg2://myuser:mypassword@localhost:5432/mydatabase
   ```

3. **Check Database Migrations:**
   ```bash
   # Run database migrations
   alembic upgrade head
   ```

4. **View Backend Logs:**
   ```bash
   # Check backend logs for detailed error messages
   tail -f /tmp/backend.log
   ```

### 2. Backend Fails to Start with "Backend failed to start" Error

**Symptoms:**
- When running `./start_local_dev.sh`, you see:
  ```
 Error: Backend failed to start. Check /tmp/backend.log for details.
  ```

**Solutions:**

1. **Check if Docker Services are Ready:**
   The database may not be fully initialized when the backend tries to connect.
   ```bash
   # Check if database is ready
   docker-compose -f docker-compose.dev.yml exec db pg_isready
   
   # If not ready, wait a bit longer or restart the database container
   docker-compose -f docker-compose.dev.yml restart db
   ```

2. **View Backend Logs:**
   ```bash
   # Check the backend log file for specific error messages
   cat /tmp/backend.log
   
   # Or watch the logs in real-time
   tail -f /tmp/backend.log
   ```

3. **Check Database Connection:**
   The backend might be unable to connect to the database. Wait for the database to be fully initialized:
   ```bash
   # Wait and check database status
   sleep 15
   docker-compose -f docker-compose.dev.yml exec db pg_isready
   ```

4. **Manual Startup Process:**
   If the script fails, try starting services manually:
   ```bash
   # Terminal 1: Start Docker services
   docker-compose -f docker-compose.dev.yml up -d
   
   # Wait for services to be ready
   for i in {1..30}; do
       if docker-compose -f docker-compose.dev.yml exec db pg_isready >/dev/null 2>&1; then
           echo "Database is ready!"
           break
       fi
       echo "Waiting for database... ($i/30)"
       sleep 2
   done
   
   # Terminal 2: Activate virtual environment and start backend
   source venv/bin/activate
   uvicorn app.main:app --reload --host 0.0.0 --port 8000 --log-level debug
   ```

### 3. Command Not Found Errors (e.g., uvicorn: command not found)

**Symptoms:**
- When running the start script, you see:
  ```
  ./start_local_dev.sh: line XX: uvicorn: command not found
  ```

**Solutions:**

1. **Install Python Dependencies:**
   The virtual environment may not have all required packages installed.
   ```bash
   # Activate virtual environment
   source venv/bin/activate
   
   # Install dependencies
   pip install -r requirements.txt
   
   # Install uvicorn specifically if needed
   pip install uvicorn[standard]
   ```

2. **Run the Setup Script:**
   ```bash
   ./setup_local_env.sh
   ```
   This will ensure all dependencies are properly installed in the virtual environment.

3. **Verify Virtual Environment Activation:**
   Make sure the virtual environment is activated before running the backend:
   ```bash
   # Check if virtual environment is activated
   which python
   # Should show path to venv/bin/python
   
   # If not activated, activate it:
   source venv/bin/activate
   ```

4. **Manually Install Missing Packages:**
   If specific packages are missing:
   ```bash
   source venv/bin/activate
   pip install uvicorn[standard]
   pip install -r requirements.txt
   ```

### 4. Database Connection Issues

**Symptoms:**
- `sqlalchemy.exc.OperationalError: (psycopg2.OperationalError) FATAL: database "mydatabase" does not exist`
- Connection refused errors

**Solutions:**

1. **Wait for Database to Start:**
   The PostgreSQL container may take a few seconds to fully initialize after startup.
   ```bash
   # Wait 10-15 seconds after starting Docker services before running the backend
   sleep 15
   ```

2. **Verify Database Credentials:**
   Ensure your `.env` file matches the Docker Compose configuration:
   ```bash
   # In .env file
   DATABASE_URL=postgresql+psycopg2://myuser:mypassword@localhost:5432/mydatabase
   ```

3. **Check Docker Container Logs:**
   ```bash
   # View database logs
   docker-compose -f docker-compose.dev.yml logs db
   
   # View Redis logs
   docker-compose -f docker-compose.dev.yml logs redis
   ```

### 5. Redis Connection Issues

**Symptoms:**
- `redis.exceptions.ConnectionError: Error 61 connecting to localhost:6379`
- Cache-related errors

**Solutions:**

1. **Verify Redis Service:**
   ```bash
   # Check if Redis is running
   docker-compose -f docker-compose.dev.yml ps
   
   # Test Redis connection
   redis-cli -h localhost -p 6379 ping
   ```

2. **Check Redis Environment:**
   Ensure your `.env` file has the correct Redis URL:
   ```bash
   REDIS_URL=redis://localhost:6379/0
   ```

### 6. CORS Issues

**Symptoms:**
- `Access to fetch from origin 'http://localhost:5175' has been blocked by CORS policy`
- Cross-Origin errors in browser console

**Solutions:**

1. **Verify Vite Proxy Configuration:**
   Check `frontend/vite.config.ts` has the correct proxy settings:
   ```typescript
   proxy: {
     '/auth': {
       target: 'http://localhost:8000',
       changeOrigin: true,
       secure: false,
     },
     // ... other endpoints
   }
   ```

2. **Use Direct Backend URL:**
   If proxy isn't working, temporarily update frontend to use direct backend URL:
   ```bash
   # In frontend/.env
   VITE_API_URL=http://localhost:8000
   ```

## Docker Troubleshooting

### 1. Docker Container Won't Start

```bash
# Stop all containers
docker-compose -f docker-compose.dev.yml down

# Remove containers and volumes (be careful: this will remove all data)
docker-compose -f docker-compose.dev.yml down -v

# Start fresh
docker-compose -f docker-compose.dev.yml up -d
```

### 2. Port Already in Use

```bash
# Check what's using port 5432 (PostgreSQL)
lsof -i :5432

# Check what's using port 6379 (Redis)
lsof -i :6379

# Check what's using port 8000 (Backend)
lsof -i :8000

# Kill processes if needed (replace PID with actual process ID)
kill -9 PID
```

### 3. Docker Compose Version Warning

If you see the warning: `the attribute 'version' is obsolete, it will be ignored`, it's just a warning and doesn't affect functionality. The version field has been removed from the docker-compose.dev.yml file to eliminate this warning.

## Backend Troubleshooting

### 1. Manual Backend Start for Debugging

```bash
# Navigate to project root
cd /Users/billy/Documents/Projects/cognitude_mvp

# Activate virtual environment
source venv/bin/activate

# Make sure Docker services are running and ready
docker-compose -f docker-compose.dev.yml up -d

# Wait for services to be ready (important!)
for i in {1..30}; do
    if docker-compose -f docker-compose.dev.yml exec db pg_isready >/dev/null 2>&1; then
        echo "Database is ready!"
        break
    fi
    echo "Waiting for database... ($i/30)"
    sleep 2
done

# Start backend with more verbose logging
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 --log-level debug
```

### 2. Check Database Connection Manually

```bash
# Install a database client if needed
pip install psycopg2-binary

# Test database connection
python -c "
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
load_dotenv()

engine = create_engine(os.getenv('DATABASE_URL'))
with engine.connect() as conn:
    result = conn.execute(text('SELECT 1'))
    print('Database connection successful:', result.fetchone())
"
```

## Frontend Troubleshooting

### 1. Clear Browser Cache

Sometimes browser cache can cause issues with CORS or authentication:
- Open browser dev tools (F12)
- Right-click refresh button and select "Empty Cache and Hard Reload"
- Or use Ctrl+Shift+R (Cmd+Shift+R on Mac)

### 2. Check Frontend Environment

Verify the frontend is using the correct API URL:
```bash
# In frontend directory
cat .env
```

## Environment Verification

### 1. Quick Environment Check

Run this script to verify your environment is properly set up:

```bash
#!/bin/bash
echo "=== Environment Check ==="

echo "1. Checking Python..."
python3 --version

echo "2. Checking Node.js..."
node --version
npm --version

echo "3. Checking Docker..."
docker --version
if docker info >/dev/null 2>&1; then
  echo "Docker is running"
else
  echo "Docker is not running"
fi

echo "4. Checking Docker services..."
docker-compose -f docker-compose.dev.yml ps

echo "5. Checking virtual environment..."
if [ -d "venv" ]; then
  echo "Virtual environment exists"
else
  echo "Virtual environment missing"
fi

echo "6. Checking if required packages are installed..."
if source venv/bin/activate 2>/dev/null && command -v uvicorn >/dev/null 2>&1; then
  echo "uvicorn is installed"
else
  echo "uvicorn is not installed"
fi

echo "7. Checking .env file..."
if [ -f ".env" ]; then
  echo "Environment file exists"
  grep -E "(DATABASE_URL|REDIS_URL)" .env
else
  echo "Environment file missing"
fi

echo "8. Checking frontend .env file..."
if [ -f "frontend/.env" ]; then
  echo "Frontend environment file exists"
  cat frontend/.env
else
  echo "Frontend environment file missing"
fi
```

Save this as `check_env.sh` and run:
```bash
chmod +x check_env.sh
./check_env.sh
```

## Common Fixes Summary

If you're still experiencing issues, try this sequence:

1. Stop everything:
   ```bash
   docker-compose -f docker-compose.dev.yml down
   # Kill any running backend processes
   pkill -f uvicorn
   ```

2. Ensure dependencies are installed:
   ```bash
   ./setup_local_env.sh
   ```

3. Start Docker services:
   ```bash
   docker-compose -f docker-compose.dev.yml up -d
   
   # Wait for services to be ready
   for i in {1..30}; do
       if docker-compose -f docker-compose.dev.yml exec db pg_isready >/dev/null 2>&1; then
           echo "Database is ready!"
           break
       fi
       echo "Waiting for database... ($i/30)"
       sleep 2
   done
   ```

4. Run migrations:
   ```bash
   alembic upgrade head
   ```

5. Start backend and frontend in separate terminals:
   ```bash
   # Terminal 1
   source venv/bin/activate
   uvicorn app.main:app --reload --host 0.0.0 --port 8000
   
   # Terminal 2
   cd frontend
   npm run dev
   ```

6. Test registration again in the browser.
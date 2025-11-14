#!/bin/bash
# Fix script for API container database connection issue

echo "🔧 Fixing API container database connection..."

# Navigate to the app directory
cd /root/driftguard_mvp  # Use the correct path

# Stop the current container
echo "Stopping unhealthy API container..."
docker stop driftguard_mvp_api_1

# Remove the container
echo "Removing old container..."
docker rm driftguard_mvp_api_1

# Start the services with docker-compose to ensure proper environment
echo "Starting services with correct environment..."
docker-compose -f docker-compose.prod.yml up -d api

# Wait a moment for startup
sleep 10

# Check container status
echo "Checking container status..."
docker ps | grep api

# Test database connection
echo "Testing database connection..."
docker exec driftguard_mvp_api_1 python -c "
from app.database import engine
from sqlalchemy import text
try:
    with engine.connect() as conn:
        result = conn.execute(text('SELECT 1'))
        print('✅ Database connection successful')
except Exception as e:
    print(f'❌ Database connection failed: {e}')
"

# Test health endpoint
echo "Testing health endpoint..."
curl -f http://localhost:8000/health || echo "❌ Health check failed"

echo "✅ Fix complete. Try the registration endpoint now."
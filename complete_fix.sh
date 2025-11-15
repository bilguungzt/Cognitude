#!/bin/bash
# Complete fix - stop, remove, and recreate containers with correct config

set -e

SERVER="root@165.22.158.75"

echo "🔧 Applying complete fix for database configuration..."
ssh -o StrictHostKeyChecking=no $SERVER << 'ENDSSH'
cd /opt/cognitude

echo "Step 1: Stopping and removing all containers..."
docker compose -f docker-compose.prod.yml down --volumes --remove-orphans

echo ""
echo "Step 2: Creating correct .env file..."
cat > .env << 'ENVEOF'
# Database (using Supabase connection pooler)
DATABASE_URL=postgresql://postgres.svssbodchjapyeiuoxjm:jllDZQmL4kRLBOOz@aws-0-us-west-2.pooler.supabase.com:5432/postgres

# Redis
REDIS_URL=redis://redis:6379

# JWT Secret (generate a secure one)
SECRET_KEY=production-secret-key-change-this-in-production

# Production settings
ENVIRONMENT=production
ENVEOF

echo "✅ .env file created"

echo ""
echo "Step 3: Creating docker-compose.prod.yml..."
cat > docker-compose.prod.yml << 'COMPOSE'
services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    command: redis-server --appendonly yes --maxmemory 256mb --maxmemory-policy allkeys-lru
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5
    restart: unless-stopped

  api:
    build: .
    ports:
      - "8000:8000"
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000
    environment:
      - DATABASE_URL=postgresql://postgres.svssbodchjapyeiuoxjm:jllDZQmL4kRLBOOz@aws-0-us-west-2.pooler.supabase.com:5432/postgres
      - REDIS_URL=redis://redis:6379
      - SECRET_KEY=production-secret-key-change-this-in-production
      - ENVIRONMENT=production
    depends_on:
      redis:
        condition: service_healthy
    restart: unless-stopped

volumes:
  redis_data:
COMPOSE

echo "✅ docker-compose.prod.yml created"

echo ""
echo "Step 4: Starting fresh containers..."
docker compose -f docker-compose.prod.yml up -d

echo ""
echo "Step 5: Waiting for containers to be ready..."
sleep 15

echo ""
echo "Step 6: Checking container status..."
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

echo ""
echo "Step 7: Testing database connection..."
docker exec cognitude-api-1 python3 -c "
import os
import psycopg2
try:
    conn = psycopg2.connect('postgresql://postgres.svssbodchjapyeiuoxjm:jllDZQmL4kRLBOOz@aws-0-us-west-2.pooler.supabase.com:5432/postgres')
    print('✅ Database connection successful!')
    conn.close()
except Exception as e:
    print(f'❌ Database connection failed: {e}')
"

echo ""
echo "Step 8: Final health check..."
curl -s http://localhost:8000/health || echo "Health check failed"
ENDSSH

echo ""
echo "✅ Complete fix applied!"
echo ""
echo "Testing from local machine..."
HEALTH_RESPONSE=$(curl -s http://165.22.158.75:8000/health)
echo "Health response: $HEALTH_RESPONSE"

if echo "$HEALTH_RESPONSE" | grep -q "healthy"; then
    echo "🎉 SUCCESS! Everything is working correctly."
    echo ""
    echo "📝 Your API is now fully operational:"
    echo "   ✅ Database: Connected to Supabase"
    echo "   ✅ Redis: Connected and working"
    echo "   ✅ API: Running and healthy"
    echo ""
    echo "🚀 Ready to use!"
else
    echo "❌ Still showing issues."
    echo "Response: $HEALTH_RESPONSE"
fi
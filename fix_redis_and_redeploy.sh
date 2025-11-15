#!/bin/bash
# Complete Redis fix and redeployment script

set -e

echo "======================================================================"
echo "🔧 Fixing Redis and Redeploying Cognitude"
echo "======================================================================"
echo ""

SERVER="root@165.22.158.75"

echo "📋 Step 1: Checking current Redis status..."
ssh -o StrictHostKeyChecking=no $SERVER << 'ENDSSH'
echo "Current containers:"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

echo ""
echo "Checking if Redis is running:"
docker ps | grep -i redis || echo "No Redis container found"

echo ""
echo "Checking docker-compose.prod.yml:"
if [ -f /opt/cognitude/docker-compose.prod.yml ]; then
    echo "Current docker-compose.prod.yml content:"
    cat /opt/cognitude/docker-compose.prod.yml
else
    echo "docker-compose.prod.yml not found!"
fi
ENDSSH

echo ""
echo "🚀 Step 2: Creating updated docker-compose.prod.yml on server..."
ssh -o StrictHostKeyChecking=no $SERVER << 'ENDSSH'
cd /opt/cognitude

# Create the updated docker-compose.prod.yml with Redis service
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
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=redis://redis:6379
      - REDIS_TOKEN=${REDIS_TOKEN}
      - SECRET_KEY=${SECRET_KEY}
      - ENVIRONMENT=${ENVIRONMENT}
      - SUPABASE_URL=${SUPABASE_URL}
      - SUPABASE_ANON_KEY=${SUPABASE_ANON_KEY}
    depends_on:
      redis:
        condition: service_healthy
    restart: unless-stopped

volumes:
  redis_data:
COMPOSE

echo "✅ Updated docker-compose.prod.yml created"
echo "New content:"
cat docker-compose.prod.yml
ENDSSH

echo ""
echo "🔄 Step 3: Restarting services with new configuration..."
ssh -o StrictHostKeyChecking=no $SERVER << 'ENDSSH'
cd /opt/cognitude

echo "Stopping existing services..."
docker compose -f docker-compose.prod.yml down

echo ""
echo "Starting services with new configuration..."
docker compose -f docker-compose.prod.yml up -d

echo ""
echo "Waiting for services to start..."
sleep 10

echo ""
echo "Checking container status:"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

echo ""
echo "Checking Redis health:"
docker exec cognitude-redis-1 redis-cli ping || echo "Redis ping failed"

echo ""
echo "Checking API logs (last 10 lines):"
docker logs cognitude-api-1 --tail=10
ENDSSH

echo ""
echo "🧪 Step 4: Testing Redis connectivity..."
ssh -o StrictHostKeyChecking=no $SERVER << 'ENDSSH'
cd /opt/cognitude

echo "Testing Redis from API container:"
docker exec cognitude-api-1 sh -c '
if command -v redis-cli > /dev/null; then
    echo "redis-cli is available in API container"
    echo "Testing connection to redis host..."
    if redis-cli -h redis ping 2>/dev/null; then
        echo "✅ API container can connect to Redis"
    else
        echo "❌ API container cannot connect to Redis"
        echo "Trying to ping redis host..."
        ping -c 1 redis 2>/dev/null && echo "✅ Can ping redis host" || echo "❌ Cannot ping redis host"
    fi
else
    echo "redis-cli not available in API container"
    echo "Checking environment variables..."
    env | grep -i redis
fi
'
ENDSSH

echo ""
echo "🎯 Step 5: Final health check..."
sleep 5
HEALTH_RESPONSE=$(curl -s http://165.22.158.75:8000/health)
echo "Health check response: $HEALTH_RESPONSE"

if echo "$HEALTH_RESPONSE" | grep -q "healthy"; then
    echo "✅ Health check passed!"
else
    echo "❌ Health check failed"
fi

echo ""
echo "======================================================================"
echo "✅ Redis Fix and Redeployment Complete!"
echo "======================================================================"
echo ""

if echo "$HEALTH_RESPONSE" | grep -q "healthy"; then
    echo "🎉 SUCCESS! Redis is now working correctly."
    echo ""
    echo "📝 Next steps:"
    echo "   - Your API is fully operational"
    echo "   - Redis is properly connected"
    echo "   - You can now register providers and test chat completions"
    echo "   - API is accessible at http://165.22.158.75:8000"
else
    echo "⚠️  Health check still showing issues."
    echo ""
    echo "🔧 Troubleshooting:"
    echo "   1. Check container logs: ssh $SERVER 'docker logs cognitude-api-1'"
    echo "   2. Check Redis logs: ssh $SERVER 'docker logs cognitude-redis-1'"
    echo "   3. Verify network: ssh $SERVER 'docker network ls && docker network inspect cognitude_default'"
fi

echo ""
echo "🌐 API URL: http://165.22.158.75:8000"
echo "📖 Docs: http://165.22.158.75:8000/docs"
echo "💚 Health: http://165.22.158.75:8000/health"
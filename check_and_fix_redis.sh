#!/bin/bash
# Check Redis status and redeploy if necessary

set -e

echo "======================================================================"
echo "🔍 Checking Redis Status and Fixing if Needed"
echo "======================================================================"
echo ""

SERVER="root@165.22.158.75"

echo "📊 Step 1: Checking current container status..."
ssh -o StrictHostKeyChecking=no $SERVER << 'ENDSSH'
echo "Current containers:"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

echo ""
echo "Checking docker-compose.prod.yml content:"
if [ -f /opt/cognitude/docker-compose.prod.yml ]; then
    echo "✅ docker-compose.prod.yml exists"
    echo "Content:"
    cat /opt/cognitude/docker-compose.prod.yml
else
    echo "❌ docker-compose.prod.yml not found"
fi
ENDSSH

echo ""
echo "🧪 Step 2: Testing Redis connectivity from API container..."
ssh -o StrictHostKeyChecking=no $SERVER << 'ENDSSH'
cd /opt/cognitude

echo "Testing Redis connection from API container..."
docker exec cognitude-api-1 sh -c '
if command -v redis-cli > /dev/null; then
    echo "redis-cli is available"
    # Try to connect to Redis
    if redis-cli -h redis ping > /dev/null 2>&1; then
        echo "✅ Can connect to Redis from API container"
    else
        echo "❌ Cannot connect to Redis from API container"
        echo "Trying localhost..."
        if redis-cli ping > /dev/null 2>&1; then
            echo "✅ Can connect to Redis on localhost"
        else
            echo "❌ Cannot connect to Redis on localhost either"
        fi
    fi
else
    echo "redis-cli not available in API container"
    echo "Checking if Redis is running as separate container..."
    docker ps | grep -i redis || echo "No Redis container found"
fi
'
ENDSSH

echo ""
echo "🔧 Step 3: Checking Redis container separately..."
ssh -o StrictHostKeyChecking=no $SERVER << 'ENDSSH'
echo "Checking for Redis containers:"
docker ps -a | grep -i redis || echo "No Redis containers found"

echo ""
echo "Checking Docker networks:"
docker network ls

echo ""
echo "Checking if containers are on the same network:"
docker inspect cognitude-api-1 --format='{{json .NetworkSettings.Networks}}' | jq .
ENDSSH

echo ""
echo "💡 Step 4: Recommendations..."
echo ""
echo "If Redis is not running or not connected:"
echo "1. Redeploy with: ./deploy_manual.sh"
echo "2. Or manually restart: ssh $SERVER 'cd /opt/cognitude && docker compose -f docker-compose.prod.yml down && docker compose -f docker-compose.prod.yml up -d'"
echo ""
echo "If Redis is running but API can't connect:"
echo "1. Check network: docker network ls"
echo "2. Check container networks: docker inspect cognitude-api-1"
echo "3. Restart services: docker compose restart"

echo ""
echo "======================================================================"
echo "✅ Redis check complete!"
echo "======================================================================"
#!/bin/bash
set -e

echo "======================================"
echo "Production Container Fix Script"
echo "======================================"
echo ""

# Configuration
CONTAINER_NAME="driftguard_mvp_api_1"
IMAGE_NAME="driftguard_mvp_api:latest"
ENV_FILE_PATH=".env"
PORT_MAPPING="8000:8000"

echo "Step 1: Checking environment file..."
if [ ! -f "$ENV_FILE_PATH" ]; then
    echo "❌ ERROR: Environment file not found at $ENV_FILE_PATH"
    echo "Please ensure the .env file exists with correct configuration."
    exit 1
fi
echo "✅ Environment file found at $ENV_FILE_PATH"
echo ""

echo "Step 2: Checking required environment variables..."
required_vars=("DATABASE_URL" "REDIS_URL" "REDIS_TOKEN" "SUPABASE_URL" "SUPABASE_ANON_KEY")
missing_vars=()

for var in "${required_vars[@]}"; do
    if ! grep -q "^${var}=" "$ENV_FILE_PATH"; then
        missing_vars+=("$var")
    fi
done

if [ ${#missing_vars[@]} -gt 0 ]; then
    echo "⚠️  WARNING: Missing environment variables in $ENV_FILE_PATH:"
    for var in "${missing_vars[@]}"; do
        echo "   - $var"
    done
    echo ""
    read -p "Continue anyway? (y/n): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Exiting..."
        exit 1
    fi
else
    echo "✅ All required environment variables found"
fi
echo ""

echo "Step 3: Stopping existing container..."
if docker ps -a | grep -q "$CONTAINER_NAME"; then
    echo "Found existing container: $CONTAINER_NAME"
    
    if docker ps | grep -q "$CONTAINER_NAME"; then
        echo "Stopping running container..."
        docker stop "$CONTAINER_NAME"
        echo "✅ Container stopped"
    fi
    
    echo "Removing container..."
    docker rm "$CONTAINER_NAME"
    echo "✅ Container removed"
else
    echo "ℹ️  No existing container found with name $CONTAINER_NAME"
fi
echo ""

echo "Step 4: Starting new container with correct environment..."
echo "Using environment file: $ENV_FILE_PATH"
echo "Image: $IMAGE_NAME"
echo "Port mapping: $PORT_MAPPING"
echo ""

docker run -d \
    --name "$CONTAINER_NAME" \
    --env-file "$ENV_FILE_PATH" \
    -p "$PORT_MAPPING" \
    --restart unless-stopped \
    "$IMAGE_NAME"

echo "✅ New container started successfully"
echo ""

echo "Step 5: Waiting for container to initialize..."
sleep 5

echo "Step 6: Checking container status..."
if docker ps | grep -q "$CONTAINER_NAME"; then
    echo "✅ Container is running"
    
    # Show container info
    echo ""
    echo "Container details:"
    docker ps --filter "name=$CONTAINER_NAME" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    
    # Show logs
    echo ""
    echo "Recent logs:"
    docker logs --tail 20 "$CONTAINER_NAME"
else
    echo "❌ Container is not running. Checking logs..."
    docker logs "$CONTAINER_NAME"
    exit 1
fi
echo ""

echo "Step 7: Running configuration validation..."
echo "Testing Redis connection..."
docker exec "$CONTAINER_NAME" python3 -c "
from app.services.redis_cache import redis_cache
health = redis_cache.health_check()
print(f'Redis status: {health[\"status\"]}')
if health['status'] != 'healthy':
    print(f'Error: {health.get(\"message\", \"Unknown error\")}')
"

echo ""
echo "Testing database connection..."
docker exec "$CONTAINER_NAME" python3 -c "
from app.config import get_settings
from sqlalchemy import create_engine, text
settings = get_settings()
try:
    engine = create_engine(str(settings.DATABASE_URL))
    with engine.connect() as conn:
        result = conn.execute(text('SELECT version();'))
        print(f'Database connected: {result.scalar()}')
except Exception as e:
    print(f'Database connection failed: {e}')
"

echo ""
echo "======================================"
echo "✅ Production container fix completed!"
echo "======================================"
echo ""
echo "Next steps:"
echo "1. Test the API endpoints"
echo "2. Verify smart routing with Gemini models"
echo "3. Monitor logs for any issues: docker logs -f $CONTAINER_NAME"
echo ""
echo "To view logs: docker logs -f $CONTAINER_NAME"
echo "To stop container: docker stop $CONTAINER_NAME"
echo "To restart container: docker restart $CONTAINER_NAME"
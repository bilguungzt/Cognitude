#!/bin/bash
# Complete fix script for your deployment issues
# Run this on your server: bash fix_deployment.sh

set -e

echo "🔧 Fixing environment variables..."

# Navigate to app directory
cd /opt/cognitude

# Backup original .env
cp .env .env.backup.$(date +%s)

# Fix all quoted variables in .env
sed -i 's/REDIS_URL="https:/REDIS_URL=https:/g' .env
sed -i 's/REDIS_TOKEN="/REDIS_TOKEN=/g' .env
sed -i 's/SUPABASE_URL="/SUPABASE_URL=/g' .env
sed -i 's/SUPABASE_ANON_KEY="/SUPABASE_ANON_KEY=/g' .env
sed -i 's/SECRET_KEY="/SECRET_KEY=/g' .env
sed -i 's/ENVIRONMENT="/ENVIRONMENT=/g' .env

# Remove trailing quotes
sed -i 's/"$//' .env

# Comment out empty SENTRY_DSN
sed -i 's/^SENTRY_DSN=/#SENTRY_DSN=/g' .env

echo "✅ Environment variables fixed"

# Show the fixed variables
echo ""
echo "📋 Current Redis configuration:"
grep -E "REDIS_URL|REDIS_TOKEN" .env | head -2

echo ""
echo "🐳 Rebuilding Docker container..."

# Stop and remove old container if exists
docker stop driftguard_mvp_api_1 2>/dev/null || true
docker rm driftguard_mvp_api_1 2>/dev/null || true

# Rebuild image
docker build -t driftguard_mvp_api:latest .

echo ""
echo "🚀 Starting new container..."

# Start new container
docker run -d \
  --name driftguard_mvp_api_1 \
  --add-host=host.docker.internal:host-gateway \
  -p 8000:8000 \
  --env-file .env \
  driftguard_mvp_api:latest \
  uvicorn app.main:app --host 0.0.0.0 --port 8000

echo ""
echo "⏳ Waiting for container to be ready..."
sleep 5

echo ""
echo "📊 Container status:"
docker ps | grep driftguard_mvp_api_1

echo ""
echo "📝 Container logs (last 30 lines):"
docker logs driftguard_mvp_api_1 2>&1 | tail -30

echo ""
echo "🏥 Health check:"
sleep 2
curl -s http://localhost:8000/health | jq '.' || curl -s http://localhost:8000/health

echo ""
echo "✅ Deployment complete!"
echo ""
echo "Next steps:"
echo "1. Check if Redis is connected in the logs above"
echo "2. Register a provider with: curl -X POST http://localhost:8000/providers ..."
echo "3. Test chat completions"
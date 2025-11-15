#!/bin/bash
# Fix database configuration on server

set -e

SERVER="root@165.22.158.75"

echo "🔧 Fixing database configuration on server..."
ssh -o StrictHostKeyChecking=no $SERVER << 'ENDSSH'
cd /opt/cognitude

echo "Current .env file content:"
if [ -f .env ]; then
    cat .env
else
    echo "No .env file found!"
fi

echo ""
echo "Updating DATABASE_URL to use Supabase..."
# Backup current .env
cp .env .env.backup.$(date +%s) 2>/dev/null || true

# Create proper .env with Supabase database
cat > .env << 'ENVEOF'
# Database (using Supabase connection pooler)
DATABASE_URL=postgresql://postgres.svssbodchjapyeiuoxjm:jllDZQmL4kRLBOOz@aws-0-us-west-2.pooler.supabase.com:5432/postgres

# Redis
REDIS_URL=redis://redis:6379

# API Keys (add your keys here)
# OPENAI_API_KEY=sk-...
# ANTHROPIC_API_KEY=sk-ant-...
# GOOGLE_API_KEY=...

# JWT Secret (generate a secure one)
SECRET_KEY=$(openssl rand -hex 32)

# Email (optional)
# SMTP_HOST=smtp.gmail.com
# SMTP_PORT=587
# SMTP_USER=your-email@gmail.com
# SMTP_PASSWORD=your-password
# FROM_EMAIL=alerts@cognitude.io

# Production settings
ENVIRONMENT=production
ENVEOF

echo "✅ Updated .env file:"
cat .env

echo ""
echo "Restarting API container to apply new database configuration..."
docker compose -f docker-compose.prod.yml restart api

echo ""
echo "Waiting for container to restart..."
sleep 10

echo ""
echo "Checking API logs:"
docker logs cognitude-api-1 --tail=20

echo ""
echo "Testing health endpoint:"
curl -s http://localhost:8000/health || echo "Health check failed"
ENDSSH

echo ""
echo "✅ Database configuration fix complete!"
echo ""
echo "Testing health endpoint from local..."
HEALTH_RESPONSE=$(curl -s http://165.22.158.75:8000/health)
echo "Health response: $HEALTH_RESPONSE"

if echo "$HEALTH_RESPONSE" | grep -q "healthy"; then
    echo "🎉 SUCCESS! Database connection is working."
else
    echo "❌ Health check still showing issues."
    echo "Response: $HEALTH_RESPONSE"
fi
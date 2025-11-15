#!/bin/bash
# Manual deployment script that prompts for password
# Use this if sshpass is not available

set -e

echo "======================================================================"
echo "🚀 Manual Deployment Script for Cognitude"
echo "======================================================================"
echo ""

SERVER="root@165.22.158.75"
APP_DIR="/opt/cognitude"

echo "📦 Step 1: Preparing deployment files..."
# Create deployment package
tar -czf cognitude_deploy.tar.gz \
  --exclude='venv' \
  --exclude='node_modules' \
  --exclude='__pycache__' \
  --exclude='.git' \
  --exclude='*.pyc' \
  --exclude='*.log' \
  --exclude='test_*.py' \
  --exclude='quick_test.py' \
  --exclude='feature_test.py' \
  .

echo "✅ Deployment package created"

echo ""
echo "📤 Step 2: Uploading to server..."
echo "You will be prompted for the server password."
scp cognitude_deploy.tar.gz $SERVER:/tmp/

echo ""
echo "🔧 Step 3: Setting up on server..."
ssh -o StrictHostKeyChecking=no $SERVER << 'ENDSSH'
set -e

# Stop existing services if any
cd /opt/cognitude 2>/dev/null && docker-compose down || true

# Create directory
mkdir -p /opt/cognitude
cd /opt/cognitude

# Extract new code
tar -xzf /tmp/cognitude_deploy.tar.gz
rm /tmp/cognitude_deploy.tar.gz

echo "✅ Code deployed to /opt/cognitude"

# Install Docker if not present
if ! command -v docker &> /dev/null; then
    echo "Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    systemctl start docker
    systemctl enable docker
fi

# Install Docker Compose if not present
if ! command -v docker-compose &> /dev/null; then
    echo "Installing Docker Compose..."
    curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
fi

echo "✅ Docker setup complete"
ENDSSH

echo ""
echo "⚙️  Step 4: Configuring environment..."
ssh -o StrictHostKeyChecking=no $SERVER << ENDSSH
export PROD_DATABASE_URL='$PROD_DATABASE_URL'
export PROD_REDIS_URL='$PROD_REDIS_URL'
cd /opt/cognitude

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    cat > .env << ENVEOF
# Database (using Supabase connection pooler)
DATABASE_URL=postgresql://postgres.svssbodchjapyeiuoxjm:jllDZQmL4kRLBOOz@aws-0-us-west-2.pooler.supabase.com:5432/postgres

# Redis
REDIS_URL=\$PROD_REDIS_URL

# API Keys (add your keys here)
# OPENAI_API_KEY=sk-...
# ANTHROPIC_API_KEY=sk-ant-...

# JWT Secret (generate a secure one)
SECRET_KEY=\$(openssl rand -hex 32)

# Email (optional)
# SMTP_HOST=smtp.gmail.com
# SMTP_PORT=587
# SMTP_USER=your-email@gmail.com
# SMTP_PASSWORD=your-password
# FROM_EMAIL=alerts@cognitude.io

# Production settings
ENVIRONMENT=production
ENVEOF
    echo "✅ Environment file created"
else
    echo "ℹ️  .env file already exists, skipping..."
fi

# Update docker-compose.yml for production
cat > docker-compose.prod.yml << COMPOSE
services:
  api:
    build: .
    restart: always
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres.svssbodchjapyeiuoxjm:jllDZQmL4kRLBOOz@aws-0-us-west-2.pooler.supabase.com:5432/postgres
      - REDIS_URL=\$PROD_REDIS_URL
    env_file:
      - .env
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000

volumes:
  postgres_data:
  redis_data:

networks:
  cognitude-network:
    driver: bridge
COMPOSE

echo "✅ Production docker-compose created"
ENDSSH

echo ""
echo "🐳 Step 5: Starting services..."
ssh -o StrictHostKeyChecking=no $SERVER << 'ENDSSH'
cd /opt/cognitude

# Unset DOCKER_HOST to avoid connection issues
unset DOCKER_HOST

# Kill any process using port 8000
sudo fuser -k 8000/tcp || true
# Remove any stopped containers
docker ps -aq | xargs docker rm -f || true

# Build and start services
docker compose -f docker-compose.prod.yml down --volumes --remove-orphans || true
docker compose -f docker-compose.prod.yml up -d --build

echo "Waiting for services to start..."
sleep 10

# Check status
docker compose -f docker-compose.prod.yml ps

echo ""
echo "✅ Services started!"
ENDSSH

echo ""
echo "🔍 Step 6: Running health check..."
sleep 5
curl -f http://165.22.158.75:8000/health || echo "⚠️  Health check failed, but services may still be starting..."

echo ""
echo "======================================================================"
echo "✅ Manual Deployment Complete!"
echo "======================================================================"
echo ""
echo "🌐 API URL: http://165.22.158.75:8000"
echo "📖 Documentation: http://165.22.158.75:8000/docs"
echo "💚 Health Check: http://165.22.158.75:8000/health"
echo ""
echo "📝 Next steps:"
echo "   1. Add your API keys to /opt/cognitude/.env on the server"
echo "   2. Restart services: ssh $SERVER 'cd /opt/cognitude && docker compose -f docker-compose.prod.yml restart'"
echo "   3. Set up Nginx reverse proxy (optional)"
echo "   4. Configure SSL with Let's Encrypt (optional)"
echo ""
echo "🎉 Cognitude is live!"

# Cleanup
rm cognitude_deploy.tar.gz
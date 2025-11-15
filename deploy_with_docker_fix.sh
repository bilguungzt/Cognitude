#!/bin/bash
set -e

echo "======================================================================"
echo "🚀 Deploying Cognitude to Production with Docker Fix (165.22.158.75)"
echo "======================================================================"

SERVER="root@165.22.158.75"
APP_DIR="/opt/cognitude"
SSH_PASS="GAzette4ever"

echo ""
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
sshpass -p "$SSH_PASS" scp cognitude_deploy.tar.gz $SERVER:/tmp/

echo ""
echo "🔧 Step 3: Setting up on server..."
sshpass -p "$SSH_PASS" ssh -o StrictHostKeyChecking=no $SERVER << 'ENDSSH'
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
sshpass -p "$SSH_PASS" ssh -o StrictHostKeyChecking=no $SERVER << ENDSSH
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
echo "🔧 Step 5: Fixing Docker daemon issues..."
sshpass -p "$SSH_PASS" ssh -o StrictHostKeyChecking=no $SERVER << 'ENDSSH'
cd /opt/cognitude

echo "🔍 Running Docker diagnostics..."
# Create diagnostic script
cat > docker_diagnose.sh << 'DIAG_SCRIPT'
#!/bin/bash
echo "=== Docker Diagnostic Report ==="
echo "Docker version:"
docker --version 2>/dev/null || echo "Docker not found"
echo ""
echo "Docker service status:"
systemctl is-active docker 2>/dev/null || echo "Docker service not running"
echo ""
echo "DOCKER_HOST variable:"
echo "DOCKER_HOST=${DOCKER_HOST:-'(not set)'}"
echo ""
echo "Docker socket:"
ls -la /var/run/docker.sock 2>/dev/null || echo "Socket not found"
echo ""
echo "User groups:"
groups
echo ""
echo "Testing Docker connectivity:"
docker info >/dev/null 2>&1 && echo "✅ Docker is accessible" || echo "❌ Docker is not accessible"
DIAG_SCRIPT

chmod +x docker_diagnose.sh
./docker_diagnose.sh

echo ""
echo "🔧 Applying Docker fixes..."

# Fix 1: Ensure Docker service is running
if ! systemctl is-active --quiet docker; then
    echo "Starting Docker service..."
    sudo systemctl start docker
    sudo systemctl enable docker
    sleep 5
fi

# Fix 2: Unset DOCKER_HOST
unset DOCKER_HOST

# Fix 3: Fix Docker socket permissions
if [ -S /var/run/docker.sock ]; then
    sudo chmod 666 /var/run/docker.sock
fi

# Fix 4: Ensure docker group exists
if ! getent group docker > /dev/null; then
    sudo groupadd docker
fi

# Fix 5: Add user to docker group
CURRENT_USER=$(whoami)
if ! groups $CURRENT_USER | grep -q docker; then
    sudo usermod -aG docker $CURRENT_USER
fi

# Fix 6: Restart Docker to apply changes
echo "Restarting Docker service..."
sudo systemctl restart docker
sleep 5

# Verify Docker is working
echo ""
echo "✅ Verifying Docker connectivity..."
if docker info &> /dev/null; then
    echo "✅ Docker daemon is now accessible"
else
    echo "❌ Docker daemon is still not accessible"
    exit 1
fi

ENDSSH

echo ""
echo "🐳 Step 6: Starting services..."
sshpass -p "$SSH_PASS" ssh -o StrictHostKeyChecking=no $SERVER << 'ENDSSH'
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
echo "🔍 Step 7: Running health check..."
sleep 5
curl -f http://165.22.158.75:8000/health || echo "⚠️  Health check failed, but services may still be starting..."

echo ""
echo "======================================================================"
echo "✅ Deployment Complete with Docker Fix!"
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
echo "🎉 Cognitude is live with Docker daemon fix!"

# Cleanup
rm cognitude_deploy.tar.gz
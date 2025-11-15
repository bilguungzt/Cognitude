#!/bin/bash
set -e

# Secure deployment script for Cognitude
# Usage: 
#   1. Source your secrets: source .secrets.env
#   2. Run: ./deploy_cognitude.sh

echo "======================================================================"
echo "🚀 Deploying Cognitude to Production"
echo "======================================================================"

# Check for required environment variables
if [ -z "$PROD_SERVER" ]; then
    echo "❌ Error: PROD_SERVER not set"
    echo "Please source .secrets.env first: source .secrets.env"
    exit 1
fi

if [ -z "$PROD_DATABASE_URL" ]; then
    echo "❌ Error: PROD_DATABASE_URL not set"
    echo "Please source .secrets.env first: source .secrets.env"
    exit 1
fi

# Use SSH key-based auth by default, fall back to password if SSH_PASS is set
if [ -z "$SSH_PASS" ]; then
    echo "📝 Using SSH key-based authentication"
    SSH_CMD="ssh -o StrictHostKeyChecking=no"
    SCP_CMD="scp"
else
    echo "📝 Using password authentication"
    SSH_CMD="sshpass -p $SSH_PASS ssh -o StrictHostKeyChecking=no"
    SCP_CMD="sshpass -p $SSH_PASS scp"
fi

SERVER="$PROD_SERVER"
APP_DIR="/opt/cognitude"

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
  --exclude='.secrets.env' \
  .

echo "✅ Deployment package created"

echo ""
echo "📤 Step 2: Uploading to server..."
$SCP_CMD cognitude_deploy.tar.gz $SERVER:/tmp/

echo ""
echo "🔧 Step 3: Setting up on server..."
$SSH_CMD $SERVER << 'ENDSSH'
set -e

# Stop existing services if any
cd /opt/cognitude 2>/dev/null && docker compose down || true

# Create directory
mkdir -p /opt/cognitude
cd /opt/cognitude

# Extract new code
tar -xzf /tmp/cognitude_deploy.tar.gz
rm /tmp/cognitude_deploy.tar.gz

# Verify extraction
if [ ! -f "app/main.py" ]; then
    echo "❌ Error: Extraction failed - app/main.py not found"
    exit 1
fi

echo "✅ Code deployed to /opt/cognitude"

# Install Docker if not present
if ! command -v docker &> /dev/null; then
    echo "Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    systemctl start docker
    systemctl enable docker
fi

# Install Docker Compose if not present (v2 plugin)
if ! docker compose version &> /dev/null; then
    echo "Installing Docker Compose..."
    mkdir -p /usr/local/lib/docker/cli-plugins
    curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/lib/docker/cli-plugins/docker-compose
    chmod +x /usr/local/lib/docker/cli-plugins/docker-compose
fi

echo "✅ Docker setup complete"
ENDSSH

echo ""
echo "⚙️  Step 4: Configuring environment..."
$SSH_CMD $SERVER << ENDSSH
export PROD_DATABASE_URL="$PROD_DATABASE_URL"
export PROD_REDIS_URL="${PROD_REDIS_URL:-redis://localhost:6379}"
export REDIS_TOKEN="${REDIS_TOKEN:-}"
cd /opt/cognitude

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    cat > .env << EOF
# Database (using Supabase connection pooler)
DATABASE_URL=$PROD_DATABASE_URL

# Redis
REDIS_URL=${PROD_REDIS_URL:-redis://localhost:6379}
REDIS_TOKEN=${REDIS_TOKEN:-}

# API Keys (add your keys here)
# OPENAI_API_KEY=sk-...
# ANTHROPIC_API_KEY=sk-ant-...

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
EOF
    echo "✅ Environment file created"
else
    echo "ℹ️  .env file already exists, skipping..."
fi

# Ensure critical environment variables are up to date
python3 - <<'PY'
import os
from pathlib import Path

env_path = Path(".env")
if env_path.exists():
    target = {
        "DATABASE_URL": os.environ.get("PROD_DATABASE_URL", ""),
        "REDIS_URL": os.environ.get("PROD_REDIS_URL", "redis://localhost:6379"),
        "REDIS_TOKEN": os.environ.get("REDIS_TOKEN", ""),
    }
    lines = env_path.read_text().splitlines()
    updated = []
    seen = set()
    for line in lines:
        if not line or line.lstrip().startswith("#") or "=" not in line:
            updated.append(line)
            continue
        key, val = line.split("=", 1)
        if key in target:
            updated.append(f"{key}={target[key]}")
            seen.add(key)
        else:
            updated.append(line)
    for key, val in target.items():
        if key not in seen:
            updated.append(f"{key}={val}")
    env_path.write_text("\n".join(updated) + "\n")
PY
echo "✅ Environment variables synchronized"


# Update docker-compose.yml for production
cat > docker-compose.prod.yml << 'COMPOSE'
services:
  api:
    build: .
    restart: always
    ports:
      - "8000:8000"
    env_file:
      - .env
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

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
echo "🐳 Step 5: Fixing Docker daemon..."
$SSH_CMD $SERVER << 'ENDSSH'
cd /opt/cognitude

# Create and run Docker diagnostic and fix script
cat > fix_docker.sh << 'DOCKER_SCRIPT'
#!/bin/bash
set -e

echo "🔧 Fixing Docker daemon issues..."

# Ensure Docker is running
if ! systemctl is-active --quiet docker; then
    echo "Starting Docker service..."
    sudo systemctl start docker
    sudo systemctl enable docker
    sleep 5
fi

# Unset DOCKER_HOST to avoid connection issues
unset DOCKER_HOST

# Fix Docker socket permissions
if [ -S /var/run/docker.sock ]; then
    sudo chmod 666 /var/run/docker.sock
fi

# Ensure docker group exists
if ! getent group docker > /dev/null; then
    sudo groupadd docker
fi

# Add user to docker group
CURRENT_USER=$(whoami)
if ! groups $CURRENT_USER | grep -q docker; then
    sudo usermod -aG docker $CURRENT_USER
fi

# Test Docker connectivity
if docker info &> /dev/null; then
    echo "✅ Docker daemon is working"
else
    echo "❌ Docker daemon is not accessible"
    exit 1
fi

DOCKER_SCRIPT

chmod +x fix_docker.sh
./fix_docker.sh
ENDSSH

echo ""
echo "🐳 Step 6: Starting services..."
$SSH_CMD $SERVER << 'ENDSSH'
cd /opt/cognitude

# Unset DOCKER_HOST to avoid connection issues
unset DOCKER_HOST

# Kill any process using port 8000
sudo fuser -k 8000/tcp || true

# Remove any stopped containers
docker ps -aq | xargs docker rm -f 2>/dev/null || true

# Build and start services
docker compose -f docker-compose.prod.yml down --volumes --remove-orphans || true
docker compose -f docker-compose.prod.yml up -d --build

echo "Waiting for services to start..."
sleep 15

# Wait for health check to pass
echo "Waiting for health check..."
for i in {1..30}; do
    if docker compose -f docker-compose.prod.yml ps | grep -q "healthy"; then
        echo "✅ Services are healthy!"
        break
    fi
    echo "Waiting for services to become healthy... ($i/30)"
    sleep 2
done

# Check status
docker compose -f docker-compose.prod.yml ps

echo ""
echo "✅ Services started!"
ENDSSH

echo ""
echo "🔍 Step 7: Running health check..."
sleep 5

# Try health check with timeout
if curl -f --max-time 10 http://${SERVER#*@}:8000/health > /dev/null 2>&1; then
    echo "✅ Health check passed!"
    curl http://${SERVER#*@}:8000/health
else
    echo "⚠️  Health check failed, but services may still be starting..."
    echo "Check logs with: ssh $SERVER 'docker logs cognitude-api-1'"
fi

echo ""
echo "======================================================================"
echo "✅ Deployment Complete!"
echo "======================================================================"
echo ""
echo "🌐 API URL: http://${SERVER#*@}:8000"
echo "📖 Documentation: http://${SERVER#*@}:8000/docs"
echo "💚 Health Check: http://${SERVER#*@}:8000/health"
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

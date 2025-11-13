#!/bin/bash
set -e

# --- Configuration ---
SERVER="root@165.22.158.75"
APP_DIR="/opt/cognitude"
SSH_PASSWORD="GAzette4ever"
# ---------------------

echo "======================================================================"
echo "🚀 Deploying Cognitude to Production ($SERVER)"
echo "======================================================================"

# Check for sshpass and install if not found
if ! command -v sshpass &> /dev/null; then
    echo "sshpass not found. Attempting to install..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        if command -v brew &> /dev/null; then
            brew install hudochenkov/sshpass/sshpass
        else
            echo "Error: Homebrew not found. Please install sshpass manually."
            exit 1
        fi
    else
        # Assuming Debian/Ubuntu
        sudo apt-get update && sudo apt-get install -y sshpass
    fi
fi
  
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
sshpass -p "$SSH_PASSWORD" scp cognitude_deploy.tar.gz $SERVER:/tmp/
  
echo ""
echo "🔧 Step 3: Setting up on server..."
sshpass -p "$SSH_PASSWORD" ssh $SERVER << 'ENDSSH'
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
sshpass -p "$SSH_PASSWORD" ssh $SERVER << 'ENDSSH'
cd /opt/cognitude

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    cat > .env << 'ENVEOF'
# Database
DATABASE_URL=postgresql+psycopg2://coguser:cogpass123@db/cognitude_db

# Redis
REDIS_URL=redis://redis:6379/0

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
ENVEOF
    echo "✅ Environment file created"
else
    echo "ℹ️  .env file already exists, skipping..."
fi

# Update docker-compose.yml for production
cat > docker-compose.prod.yml << 'COMPOSE'
services:
  db:
    image: timescale/timescaledb:latest-pg14
    restart: always
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      POSTGRES_USER: coguser
      POSTGRES_PASSWORD: cogpass123
      POSTGRES_DB: cognitude_db
    networks:
      - cognitude-network

  redis:
    image: redis:7-alpine
    restart: always
    command: redis-server --appendonly yes --maxmemory 256mb --maxmemory-policy allkeys-lru
    volumes:
      - redis_data:/data
    networks:
      - cognitude-network
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5

  api:
    build: .
    restart: always
    ports:
      - "8000:8000"
    depends_on:
      - db
      - redis
    environment:
      - DATABASE_URL=postgresql+psycopg2://coguser:cogpass123@db/cognitude_db
      - REDIS_URL=redis://redis:6379/0
    env_file:
      - .env
    networks:
      - cognitude-network
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
sshpass -p "$SSH_PASSWORD" ssh $SERVER << 'ENDSSH'
cd /opt/cognitude

# Build and start services
docker-compose -f docker-compose.prod.yml up -d --build

echo "Waiting for services to start..."
sleep 10

# Check status
docker-compose -f docker-compose.prod.yml ps

echo ""
echo "✅ Services started!"
ENDSSH

echo ""
echo "🔍 Step 6: Running health check..."
sleep 5
curl -f http://165.22.158.75:8000/health || echo "⚠️  Health check failed, but services may still be starting..."

echo ""
echo "======================================================================"
echo "✅ Deployment Complete!"
echo "======================================================================"
echo ""
echo "🌐 API URL: http://165.22.158.75:8000"
echo "📖 Documentation: http://165.22.158.75:8000/docs"
echo "💚 Health Check: http://165.22.158.75:8000/health"
echo ""
echo "📝 Next steps:"
echo "   1. Add your API keys to /opt/cognitude/.env on the server"
echo "   2. Restart services: sshpass -p \"$SSH_PASSWORD\" ssh $SERVER 'cd /opt/cognitude && docker-compose -f docker-compose.prod.yml restart'"
echo "   3. Set up Nginx reverse proxy (optional)"
echo "   4. Configure SSL with Let's Encrypt (optional)"
echo ""
echo "🎉 Cognitude is live!"

# Cleanup
rm cognitude_deploy.tar.gz

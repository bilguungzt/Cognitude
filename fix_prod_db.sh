#!/bin/bash
# Fix production database connectivity

echo "🔧 Fixing database connectivity..."

cd /opt/cognitude

# Update docker-compose.prod.yml to use correct database config
cat > docker-compose.prod.yml << 'EOF'
services:
  db:
    image: timescale/timescaledb:latest-pg14
    restart: always
    environment:
      POSTGRES_USER: myuser
      POSTGRES_PASSWORD: mypassword
      POSTGRES_DB: mydatabase
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - cognitude-network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U myuser -d mydatabase"]
      interval: 10s
      timeout: 5s
      retries: 5

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
      - DATABASE_URL=postgresql://myuser:mypassword@db:5432/mydatabase
      - REDIS_URL=redis://redis:6379/0
      - SECRET_KEY=${SECRET_KEY}
      - ENVIRONMENT=production
    env_file:
      - .env
    networks:
      - cognitude-network

volumes:
  postgres_data:
  redis_data:

networks:
  cognitude-network:
    driver: bridge
EOF

echo "✅ Updated docker-compose.prod.yml"

# Stop existing containers
docker-compose -f docker-compose.prod.yml down || true

# Start services
docker-compose -f docker-compose.prod.yml up -d

echo "⏳ Waiting for services..."
sleep 30

# Check status
docker-compose -f docker-compose.prod.yml ps

echo "🏥 Health check:"
curl -s http://localhost:8000/health

echo "✅ Database connectivity fixed!"
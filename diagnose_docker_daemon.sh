#!/bin/bash
# Diagnostic script to check Docker daemon status and configuration

set -e

echo "======================================================================"
echo "🔍 Docker Daemon Diagnostic Tool"
echo "======================================================================"
echo ""

# Check if Docker is installed
echo "📦 Checking Docker installation..."
if command -v docker &> /dev/null; then
    echo "✅ Docker is installed"
    docker --version
else
    echo "❌ Docker is NOT installed"
    exit 1
fi
echo ""

# Check if Docker Compose is installed
echo "📦 Checking Docker Compose installation..."
if command -v docker-compose &> /dev/null; then
    echo "✅ Docker Compose is installed"
    docker-compose --version
elif docker compose version &> /dev/null; then
    echo "✅ Docker Compose (v2) is installed"
    docker compose version
else
    echo "❌ Docker Compose is NOT installed"
fi
echo ""

# Check Docker service status
echo "🐳 Checking Docker service status..."
if systemctl is-active --quiet docker; then
    echo "✅ Docker service is running"
    systemctl status docker --no-pager -l | head -10
else
    echo "❌ Docker service is NOT running"
    echo "Attempting to start Docker service..."
    sudo systemctl start docker
    sleep 3
    if systemctl is-active --quiet docker; then
        echo "✅ Docker service started successfully"
    else
        echo "❌ Failed to start Docker service"
    fi
fi
echo ""

# Check Docker socket
echo "🔌 Checking Docker socket..."
if [ -S /var/run/docker.sock ]; then
    echo "✅ Docker socket exists at /var/run/docker.sock"
    ls -la /var/run/docker.sock
else
    echo "❌ Docker socket NOT found at /var/run/docker.sock"
fi
echo ""

# Check DOCKER_HOST environment variable
echo "🌍 Checking DOCKER_HOST environment variable..."
if [ -n "$DOCKER_HOST" ]; then
    echo "⚠️  DOCKER_HOST is set to: $DOCKER_HOST"
    echo "This may cause connection issues. Consider unsetting it."
else
    echo "✅ DOCKER_HOST is not set (good for local Docker)"
fi
echo ""

# Test Docker connectivity
echo "🧪 Testing Docker connectivity..."
if docker info &> /dev/null; then
    echo "✅ Docker daemon is accessible"
    echo "Docker Info:"
    docker info --format 'Server Version: {{.ServerVersion}}' 2>/dev/null || echo "Could not get version"
else
    echo "❌ Cannot connect to Docker daemon"
    echo "Error details:"
    docker info 2>&1 | head -5
fi
echo ""

# Check for common issues
echo "🔍 Checking for common Docker issues..."
echo "User groups:"
groups
echo ""

if groups | grep -q docker; then
    echo "✅ User is in docker group"
else
    echo "⚠️  User is NOT in docker group"
    echo "You may need to run: sudo usermod -aG docker $USER"
fi
echo ""

# Check disk space
echo "💾 Checking disk space..."
df -h /var/lib/docker 2>/dev/null || df -h /
echo ""

# Check Docker logs for errors
echo "📋 Checking recent Docker logs..."
journalctl -u docker.service --no-pager -n 20 2>/dev/null | tail -10 || echo "Could not access Docker logs"
echo ""

echo "======================================================================"
echo "🔧 Recommended fixes based on diagnostics:"
echo "======================================================================"

# Generate recommendations
if ! systemctl is-active --quiet docker; then
    echo "1. Start Docker service: sudo systemctl start docker"
    echo "2. Enable Docker to start on boot: sudo systemctl enable docker"
fi

if [ -n "$DOCKER_HOST" ]; then
    echo "3. Unset DOCKER_HOST: unset DOCKER_HOST"
fi

if ! groups | grep -q docker; then
    echo "4. Add user to docker group: sudo usermod -aG docker $USER"
    echo "   Then log out and back in for changes to take effect"
fi

if [ ! -S /var/run/docker.sock ]; then
    echo "5. Docker socket is missing. Try restarting Docker: sudo systemctl restart docker"
fi

echo ""
echo "======================================================================"
echo "✅ Diagnostic complete!"
echo "======================================================================"
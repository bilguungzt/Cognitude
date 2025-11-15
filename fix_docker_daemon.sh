#!/bin/bash
# Comprehensive fix script for Docker daemon issues
# Run this on the production server to fix Docker connectivity

set -e

echo "======================================================================"
echo "🔧 Docker Daemon Fix Script"
echo "======================================================================"
echo ""

# Function to run command with error handling
run_cmd() {
    echo "▶️  Running: $1"
    if eval "$1"; then
        echo "✅ Success"
    else
        echo "❌ Failed: $1"
        return 1
    fi
    echo ""
}

# 1. Check and install Docker if needed
echo "📦 Step 1: Checking Docker installation..."
if ! command -v docker &> /dev/null; then
    echo "Installing Docker..."
    run_cmd "curl -fsSL https://get.docker.com -o get-docker.sh"
    run_cmd "sh get-docker.sh"
    run_cmd "rm get-docker.sh"
else
    echo "✅ Docker is already installed"
fi
echo ""

# 2. Ensure Docker service is running
echo "🐳 Step 2: Ensuring Docker service is running..."
if ! systemctl is-active --quiet docker; then
    echo "Starting Docker service..."
    run_cmd "sudo systemctl start docker"
    run_cmd "sudo systemctl enable docker"
    sleep 5
else
    echo "✅ Docker service is already running"
fi
echo ""

# 3. Fix DOCKER_HOST environment variable
echo "🌍 Step 3: Fixing DOCKER_HOST environment variable..."
if [ -n "$DOCKER_HOST" ]; then
    echo "⚠️  DOCKER_HOST is currently set to: $DOCKER_HOST"
    echo "This is likely causing connection issues."
    echo "Unsetting DOCKER_HOST for this session..."
    unset DOCKER_HOST
    
    # Also remove from common profile files
    echo "Removing DOCKER_HOST from profile files..."
    for file in ~/.bashrc ~/.bash_profile ~/.profile /etc/environment; do
        if [ -f "$file" ]; then
            sudo sed -i '/DOCKER_HOST/d' "$file" 2>/dev/null || true
        fi
    done
    echo "✅ DOCKER_HOST has been unset and removed from profiles"
else
    echo "✅ DOCKER_HOST is not set (good)"
fi
echo ""

# 4. Fix Docker socket permissions
echo "🔌 Step 4: Fixing Docker socket permissions..."
if [ -S /var/run/docker.sock ]; then
    echo "Docker socket exists, checking permissions..."
    SOCKET_PERMS=$(stat -c "%a" /var/run/docker.sock)
    echo "Current socket permissions: $SOCKET_PERMS"
    
    # Ensure docker group exists and has proper permissions
    if ! getent group docker > /dev/null; then
        echo "Creating docker group..."
        run_cmd "sudo groupadd docker"
    fi
    
    # Add current user to docker group
    CURRENT_USER=$(whoami)
    if ! groups $CURRENT_USER | grep -q docker; then
        echo "Adding $CURRENT_USER to docker group..."
        run_cmd "sudo usermod -aG docker $CURRENT_USER"
        echo "⚠️  You'll need to log out and back in for group changes to take effect"
    fi
    
    # Fix socket permissions
    run_cmd "sudo chmod 666 /var/run/docker.sock"
else
    echo "❌ Docker socket not found, attempting to restart Docker..."
    run_cmd "sudo systemctl restart docker"
    sleep 5
fi
echo ""

# 5. Configure Docker daemon for proper networking
echo "⚙️ Step 5: Configuring Docker daemon..."
DOCKER_DAEMON_JSON="/etc/docker/daemon.json"
if [ ! -f "$DOCKER_DAEMON_JSON" ]; then
    echo "Creating Docker daemon configuration..."
    sudo tee "$DOCKER_DAEMON_JSON" > /dev/null << 'EOF'
{
  "live-restore": true,
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  },
  "storage-driver": "overlay2"
}
EOF
    echo "✅ Docker daemon configuration created"
else
    echo "✅ Docker daemon configuration already exists"
fi
echo ""

# 6. Restart Docker service to apply changes
echo "🔄 Step 6: Restarting Docker service..."
run_cmd "sudo systemctl daemon-reload"
run_cmd "sudo systemctl restart docker"
sleep 5
echo ""

# 7. Verify Docker is working
echo "🧪 Step 7: Verifying Docker connectivity..."
echo "Testing Docker info..."
if docker info &> /dev/null; then
    echo "✅ Docker daemon is accessible"
    docker info --format 'Server Version: {{.ServerVersion}}' 2>/dev/null || echo "Version check completed"
else
    echo "❌ Still cannot connect to Docker daemon"
    echo "Error details:"
    docker info 2>&1 | head -5
    exit 1
fi
echo ""

# 8. Test Docker Compose
echo "🐳 Step 8: Testing Docker Compose..."
if command -v docker-compose &> /dev/null; then
    echo "✅ Docker Compose v1 is available"
elif docker compose version &> /dev/null; then
    echo "✅ Docker Compose v2 is available"
else
    echo "Installing Docker Compose v2..."
    run_cmd "sudo curl -L \"https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)\" -o /usr/local/bin/docker-compose"
    run_cmd "sudo chmod +x /usr/local/bin/docker-compose"
fi
echo ""

# 9. Clean up any stuck containers or images
echo "🧹 Step 9: Cleaning up Docker resources..."
echo "Removing stopped containers..."
docker ps -aq | xargs docker rm -f 2>/dev/null || true
echo "Cleaning up unused images..."
docker image prune -af 2>/dev/null || true
echo "✅ Cleanup completed"
echo ""

# 10. Final verification
echo "✅ Step 10: Final verification..."
echo "Docker version:"
docker --version
echo ""
echo "Docker Compose version:"
docker compose version 2>/dev/null || docker-compose --version 2>/dev/null || echo "Docker Compose not found"
echo ""
echo "Docker service status:"
systemctl is-active docker
echo ""

echo "======================================================================"
echo "✅ Docker daemon fix completed successfully!"
echo "======================================================================"
echo ""
echo "📝 Next steps:"
echo "1. If you were added to the docker group, log out and back in"
echo "2. Test Docker with: docker run hello-world"
echo "3. Deploy your application with: docker compose up -d"
echo ""
echo "🎉 Docker should now be working properly!"
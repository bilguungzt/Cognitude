#!/bin/bash
# DriftGuard Production Deployment Script
# Server: 165.22.158.75
# Run this script on your DigitalOcean droplet

set -e  # Exit on any error

echo "🚀 Starting DriftGuard MVP Deployment..."
echo "========================================"

# 1. Update system and install dependencies
echo "📦 Installing system dependencies..."
sudo apt-get update
sudo apt-get install -y \
    git \
    docker.io \
    docker-compose \
    nginx \
    certbot \
    python3-certbot-nginx

# 2. Start and enable Docker
echo "🐳 Setting up Docker..."
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker $USER

# 3. Clone the repository
echo "📥 Cloning DriftGuard repository..."
cd /home/$USER
if [ -d "driftguard_mvp" ]; then
    echo "⚠️  Directory exists, pulling latest changes..."
    cd driftguard_mvp
    git pull origin main
else
    git clone https://github.com/bilguungzt/Drift_Guard.git driftguard_mvp
    cd driftguard_mvp
fi

# 4. Create production environment file
echo "⚙️  Creating production .env file..."
cat > .env << 'EOF'
# Production Environment Variables
POSTGRES_USER=driftguard_prod
POSTGRES_PASSWORD=$(openssl rand -base64 32)
POSTGRES_DB=driftguard_production

# API Configuration
ENVIRONMENT=production
API_URL=https://api.driftguard.ai

# Encryption Key (generate new one for production)
ENCRYPTION_KEY=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")

# Email Configuration (optional - update with your SMTP)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USER=your-email@gmail.com
EMAIL_PASSWORD=your-app-password

# Slack Configuration (optional)
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
EOF

# Replace placeholders with actual values
POSTGRES_PASSWORD=$(openssl rand -base64 32)
sed -i "s/\$(openssl rand -base64 32)/$POSTGRES_PASSWORD/" .env

# 5. Generate SSL certificates for PostgreSQL
echo "🔐 Generating SSL certificates..."
./generate-postgres-certs.sh

# 6. Build and start services
echo "🏗️  Building Docker containers..."
sudo docker-compose -f docker-compose.prod.yml build --no-cache

echo "🚀 Starting services..."
sudo docker-compose -f docker-compose.prod.yml up -d

# 7. Wait for database to be ready
echo "⏳ Waiting for database to initialize..."
sleep 15

# 8. Run database migrations
echo "📊 Running database migrations..."
sudo docker-compose -f docker-compose.prod.yml exec -T api alembic upgrade head

# 9. Create initial admin organization (optional)
echo "👤 Creating initial admin organization..."
sudo docker-compose -f docker-compose.prod.yml exec -T api python -c "
from app.database import SessionLocal, engine
from app.models import Organization
from app.security import generate_api_key
import secrets

db = SessionLocal()
api_key = secrets.token_urlsafe(32)
org = Organization(
    name='DriftGuard Admin',
    api_key=api_key
)
db.add(org)
db.commit()
print(f'✅ Admin API Key: {api_key}')
print('⚠️  SAVE THIS KEY - It will not be shown again!')
" > /tmp/admin_key.txt

cat /tmp/admin_key.txt

# 10. Configure Nginx reverse proxy
echo "🌐 Configuring Nginx..."
sudo cat > /etc/nginx/sites-available/driftguard << 'EOF'
# API Backend
server {
    listen 80;
    server_name api.driftguard.ai 165.22.158.75;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support (for real-time updates)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}

# Frontend (if serving from same server)
server {
    listen 80;
    server_name app.driftguard.ai;

    root /home/$USER/driftguard_mvp/frontend/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }
}
EOF

# Enable the site
sudo ln -sf /etc/nginx/sites-available/driftguard /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx

# 11. Setup SSL certificates with Let's Encrypt (optional - requires domain)
echo "🔒 SSL Certificate Setup (optional)..."
echo "To enable HTTPS, run:"
echo "sudo certbot --nginx -d api.driftguard.ai -d app.driftguard.ai"

# 12. Setup firewall
echo "🔥 Configuring firewall..."
sudo ufw allow 22/tcp      # SSH
sudo ufw allow 80/tcp      # HTTP
sudo ufw allow 443/tcp     # HTTPS
sudo ufw --force enable

# 13. Display status
echo ""
echo "✅ Deployment Complete!"
echo "========================================"
echo ""
echo "🌐 Services Running:"
sudo docker-compose -f docker-compose.prod.yml ps
echo ""
echo "📝 Important Information:"
echo "  - API Endpoint: http://165.22.158.75:8000"
echo "  - API Docs: http://165.22.158.75:8000/docs"
echo "  - Frontend: Build and deploy separately"
echo "  - Admin API Key: See /tmp/admin_key.txt"
echo ""
echo "🔧 Useful Commands:"
echo "  - View logs: sudo docker-compose -f docker-compose.prod.yml logs -f"
echo "  - Restart: sudo docker-compose -f docker-compose.prod.yml restart"
echo "  - Stop: sudo docker-compose -f docker-compose.prod.yml down"
echo ""
echo "🔒 Next Steps:"
echo "  1. Save your admin API key from /tmp/admin_key.txt"
echo "  2. Configure your domain DNS to point to 165.22.158.75"
echo "  3. Run: sudo certbot --nginx -d api.driftguard.ai"
echo "  4. Update frontend/.env with production API URL"
echo "  5. Build and deploy frontend"
echo ""

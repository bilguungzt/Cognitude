# 🚀 Production Deployment Guide - DigitalOcean

**Server**: 165.22.158.75  
**Date**: November 6, 2025

## Quick Deployment (5 Minutes)

### Step 1: SSH into your server

```bash
ssh root@165.22.158.75
```

### Step 2: Run the automated deployment script

```bash
# Copy deployment script to server
curl -o deploy.sh https://raw.githubusercontent.com/bilguungzt/Drift_Guard/main/deploy-to-server.sh

# Make it executable
chmod +x deploy.sh

# Run deployment
./deploy.sh
```

**OR** manually copy the script:

```bash
# On your local machine (from driftguard_mvp directory)
scp deploy-to-server.sh root@165.22.158.75:~/

# On the server
ssh root@165.22.158.75
chmod +x deploy-to-server.sh
./deploy-to-server.sh
```

---

## Manual Deployment (Step by Step)

If the automated script fails, follow these steps:

### 1. Install Dependencies

```bash
# Update system
sudo apt-get update && sudo apt-get upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo apt-get install docker-compose -y

# Install Nginx
sudo apt-get install nginx -y

# Install Git
sudo apt-get install git -y
```

### 2. Clone Repository

```bash
cd /root
git clone https://github.com/bilguungzt/Drift_Guard.git driftguard_mvp
cd driftguard_mvp
```

### 3. Generate SSL Certificates

```bash
chmod +x generate-postgres-certs.sh
./generate-postgres-certs.sh
```

### 4. Create Production Environment File

```bash
cat > .env << 'EOF'
POSTGRES_USER=driftguard_prod
POSTGRES_PASSWORD=your_secure_password_here
POSTGRES_DB=driftguard_production
ENVIRONMENT=production
EOF
```

### 5. Start Services

```bash
# Build containers
sudo docker-compose -f docker-compose.prod.yml build

# Start services
sudo docker-compose -f docker-compose.prod.yml up -d

# Check status
sudo docker-compose -f docker-compose.prod.yml ps
```

### 6. Run Database Migrations

```bash
# Wait 10 seconds for DB to initialize
sleep 10

# Run migrations
sudo docker-compose -f docker-compose.prod.yml exec api alembic upgrade head
```

### 7. Create Admin API Key

```bash
sudo docker-compose -f docker-compose.prod.yml exec api python << 'PYTHON'
from app.database import SessionLocal
from app.models import Organization
import secrets

db = SessionLocal()
api_key = secrets.token_urlsafe(32)
org = Organization(name='Admin', api_key=api_key)
db.add(org)
db.commit()
print(f"✅ Admin API Key: {api_key}")
print("⚠️  SAVE THIS - It won't be shown again!")
PYTHON
```

### 8. Configure Nginx (Optional - for domain)

```bash
# Create Nginx config
sudo nano /etc/nginx/sites-available/driftguard
```

Paste this configuration:

```nginx
server {
    listen 80;
    server_name 165.22.158.75 api.driftguard.ai;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable and reload:

```bash
sudo ln -s /etc/nginx/sites-available/driftguard /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 9. Configure Firewall

```bash
sudo ufw allow 22    # SSH
sudo ufw allow 80    # HTTP
sudo ufw allow 443   # HTTPS
sudo ufw allow 8000  # API (temporary - remove after Nginx setup)
sudo ufw enable
```

---

## Verification

### Check Services

```bash
# Check Docker containers
sudo docker-compose -f docker-compose.prod.yml ps

# Expected output:
# NAME                   STATUS
# driftguard_mvp-db-1    Up
# driftguard_mvp-api-1   Up
```

### Test API

```bash
# Health check
curl http://165.22.158.75:8000/docs

# Should return Swagger API documentation
```

### View Logs

```bash
# All services
sudo docker-compose -f docker-compose.prod.yml logs -f

# API only
sudo docker-compose -f docker-compose.prod.yml logs -f api

# Database only
sudo docker-compose -f docker-compose.prod.yml logs -f db
```

---

## Post-Deployment

### 1. Save Your Admin API Key

The deployment script creates an admin API key. **SAVE IT IMMEDIATELY**:

```bash
cat /tmp/admin_key.txt
```

### 2. Test API Endpoint

```bash
# Replace YOUR_API_KEY with the key from step 1
curl -H "X-API-Key: YOUR_API_KEY" http://165.22.158.75:8000/models/
```

### 3. Update Frontend Configuration

```bash
# On your local machine
cd frontend
nano .env
```

Update:
```
VITE_API_URL=http://165.22.158.75:8000
```

Build frontend:
```bash
npm run build
```

### 4. Deploy Frontend (Optional - same server)

```bash
# Copy build to server
scp -r dist/* root@165.22.158.75:/var/www/driftguard/

# Or serve via Nginx (see Nginx config above)
```

---

## Domain Setup (Optional)

### 1. Configure DNS

Point your domain to the server:

```
Type: A Record
Name: api
Value: 165.22.158.75
TTL: 3600

Type: A Record  
Name: app
Value: 165.22.158.75
TTL: 3600
```

### 2. Setup SSL with Let's Encrypt

```bash
sudo apt-get install certbot python3-certbot-nginx -y

# Generate certificates
sudo certbot --nginx -d api.driftguard.ai -d app.driftguard.ai

# Auto-renewal (already setup by certbot)
sudo certbot renew --dry-run
```

---

## Troubleshooting

### Services won't start

```bash
# Check logs
sudo docker-compose -f docker-compose.prod.yml logs

# Restart services
sudo docker-compose -f docker-compose.prod.yml restart

# Rebuild if needed
sudo docker-compose -f docker-compose.prod.yml down
sudo docker-compose -f docker-compose.prod.yml build --no-cache
sudo docker-compose -f docker-compose.prod.yml up -d
```

### Database connection errors

```bash
# Check database is running
sudo docker-compose -f docker-compose.prod.yml exec db psql -U driftguard_prod -d driftguard_production -c "SELECT 1;"

# If fails, check password in .env matches docker-compose.prod.yml
```

### Port already in use

```bash
# Check what's using port 8000
sudo lsof -i :8000

# Kill the process if needed
sudo kill -9 <PID>
```

### Out of memory

```bash
# Check memory usage
free -h

# If low, add swap space
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

---

## Maintenance Commands

```bash
# View logs
sudo docker-compose -f docker-compose.prod.yml logs -f

# Restart services
sudo docker-compose -f docker-compose.prod.yml restart

# Stop services
sudo docker-compose -f docker-compose.prod.yml down

# Update code and restart
cd /root/driftguard_mvp
git pull origin main
sudo docker-compose -f docker-compose.prod.yml build
sudo docker-compose -f docker-compose.prod.yml up -d

# Backup database
sudo docker-compose -f docker-compose.prod.yml exec db pg_dump -U driftguard_prod driftguard_production > backup_$(date +%Y%m%d).sql

# Restore database
cat backup_20251106.sql | sudo docker-compose -f docker-compose.prod.yml exec -T db psql -U driftguard_prod driftguard_production
```

---

## URLs After Deployment

| Service | URL | Notes |
|---------|-----|-------|
| **API Docs** | http://165.22.158.75:8000/docs | Interactive API documentation |
| **API Endpoint** | http://165.22.158.75:8000 | Base URL for API calls |
| **Frontend** | Deploy separately | Build and serve via Nginx or Vercel |
| **Database** | localhost:5432 (internal) | Not exposed externally |

---

## Security Checklist

- [ ] Change default PostgreSQL password in `.env`
- [ ] Save admin API key securely
- [ ] Setup firewall (UFW)
- [ ] Configure SSL certificates
- [ ] Enable automatic security updates
- [ ] Setup log rotation
- [ ] Configure backup schedule
- [ ] Monitor resource usage

---

## Support

If you encounter issues:
1. Check logs: `sudo docker-compose -f docker-compose.prod.yml logs`
2. Verify services: `sudo docker-compose -f docker-compose.prod.yml ps`
3. Check firewall: `sudo ufw status`
4. Test API: `curl http://165.22.158.75:8000/docs`

---

**Deployment Time**: ~10 minutes  
**Server**: DigitalOcean Droplet 165.22.158.75  
**Status**: Ready for production use

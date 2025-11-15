# Cognitude Deployment Guide

This guide explains how to use the improved, secure deployment scripts for Cognitude.

## 🔒 Security Setup (REQUIRED)

All deployment scripts now use environment variables for sensitive data instead of hardcoded credentials.

### Step 1: Create your secrets file

```bash
# Copy the example file
cp .secrets.env.example .secrets.env

# Edit with your actual credentials
nano .secrets.env  # or use your preferred editor
```

### Step 2: Fill in your credentials

Edit `.secrets.env` with your actual values:

```bash
# SSH credentials for production deployment
export SSH_PASS="your_actual_ssh_password"

# Production server details
export PROD_SERVER="root@165.22.158.75"

# Organization API key for testing
export ORG_API_KEY="your_actual_org_api_key"

# Production database connection (Supabase)
export PROD_DATABASE_URL="postgresql://user:password@host:5432/database"

# Production Redis URL
export PROD_REDIS_URL="redis://your-redis-url:6379"

# Google API key for testing
export GOOGLE_API_KEY="your_actual_google_api_key"
```

### Step 3: Load secrets before deployment

```bash
# Source the secrets file (loads environment variables)
source .secrets.env

# Now you can run any deployment script
./deploy_cognitude.sh
```

**⚠️ IMPORTANT:** 
- Never commit `.secrets.env` to git (it's already in `.gitignore`)
- Never share your `.secrets.env` file
- Keep backup of your credentials in a secure password manager

---

## 📦 Scripts Overview

### 1. `setup_local_env.sh` - Initial Local Setup

Sets up your local development environment.

**What it does:**
- Creates Python virtual environment
- Installs Python dependencies
- Starts Docker services (PostgreSQL, Redis)
- Runs database migrations
- Sets up frontend (installs npm packages)
- Creates local `.env` files

**Usage:**
```bash
./setup_local_env.sh
```

**Run this once** when you first clone the repo or after a major dependency update.

---

### 2. `start_local_dev.sh` - Start Development Servers

Starts backend and/or frontend for local development.

**Usage:**
```bash
# Start both frontend and backend (default)
./start_local_dev.sh

# Start only backend
./start_local_dev.sh backend

# Start only frontend
./start_local_dev.sh frontend
```

**Features:**
- Auto-detects port conflicts
- Can auto-kill conflicting processes (set `START_LOCAL_DEV_AUTO_KILL=true`)
- Starts Docker services if needed
- Shows backend logs at `/tmp/backend.log`

**Example with auto-kill:**
```bash
START_LOCAL_DEV_AUTO_KILL=true ./start_local_dev.sh
```

---

### 3. `deploy_cognitude.sh` - Production Deployment

Deploys Cognitude to your production server.

**Prerequisites:**
```bash
# Load your secrets first!
source .secrets.env
```

**Usage:**
```bash
./deploy_cognitude.sh
```

**What it does:**
1. Creates deployment package (excludes unnecessary files)
2. Uploads code to production server
3. Installs/updates Docker if needed
4. Sets up production environment
5. Builds and starts Docker containers
6. Runs health checks

**Deployment targets:**
- Server: Value from `$PROD_SERVER` (e.g., root@165.22.158.75)
- Directory: `/opt/cognitude`
- Port: 8000

---

### 4. `redeploy_and_test.sh` - Deploy + Comprehensive Testing

Deploys to production AND runs comprehensive tests.

**Prerequisites:**
```bash
# Load your secrets first!
source .secrets.env
```

**Usage:**
```bash
# Deploy and test with Google API key from environment
./redeploy_and_test.sh

# Or provide Google API key as argument
./redeploy_and_test.sh "your_google_api_key"
```

**What it does:**
1. Runs full deployment (via `deploy_cognitude.sh`)
2. Copies diagnostic scripts to server
3. Updates Google provider API key
4. Tests health endpoint
5. Tests providers endpoint
6. Tests chat completion endpoint
7. Shows comprehensive summary

**Tests performed:**
- ✅ Health check
- ✅ Providers list
- ✅ Google Gemini chat completion
- ✅ Container status
- ✅ API logs

---

## 🔧 Common Workflows

### First Time Setup (Local Development)

```bash
# 1. Set up environment
./setup_local_env.sh

# 2. Start development servers
./start_local_dev.sh

# Access:
# - Backend: http://localhost:8000
# - Frontend: http://localhost:5173
# - API Docs: http://localhost:8000/docs
```

### Deploy to Production

```bash
# 1. Load secrets
source .secrets.env

# 2. Deploy
./deploy_cognitude.sh

# Access your production API at:
# http://165.22.158.75:8000
```

### Deploy and Test Production

```bash
# 1. Load secrets
source .secrets.env

# 2. Deploy with testing
./redeploy_and_test.sh

# Tests will run automatically after deployment
```

### Update API Keys in Production

```bash
# 1. Load secrets
source .secrets.env

# 2. Deploy with new Google API key
./redeploy_and_test.sh "new_google_api_key_here"
```

---

## 🐛 Troubleshooting

### "PROD_SERVER not set" error

```bash
# Make sure you sourced the secrets file
source .secrets.env

# Verify it's loaded
echo $PROD_SERVER
```

### Port already in use (local development)

```bash
# Option 1: Auto-kill conflicting processes
START_LOCAL_DEV_AUTO_KILL=true ./start_local_dev.sh

# Option 2: Manually kill processes
lsof -ti :8000 | xargs kill -9  # Backend
lsof -ti :5173 | xargs kill -9  # Frontend
```

### Docker services not starting

```bash
# Check Docker Desktop is running
docker ps

# Restart Docker services
docker compose -f docker-compose.dev.yml down
docker compose -f docker-compose.dev.yml up -d

# Check logs
docker compose -f docker-compose.dev.yml logs
```

### Health check failing after deployment

```bash
# SSH to server and check logs
ssh root@165.22.158.75
cd /opt/cognitude
docker logs cognitude-api-1

# Check container status
docker ps

# Restart if needed
docker compose -f docker-compose.prod.yml restart
```

---

## 📝 Best Practices

1. **Always source secrets before deployment:**
   ```bash
   source .secrets.env
   ```

2. **Keep `.secrets.env` secure:**
   - Never commit to git
   - Store backup in password manager
   - Don't share with anyone

3. **Use SSH keys instead of passwords (recommended):**
   ```bash
   # Generate SSH key
   ssh-keygen -t ed25519

   # Copy to server
   ssh-copy-id root@165.22.158.75

   # Remove SSH_PASS from .secrets.env
   # Scripts will automatically use SSH keys
   ```

4. **Test locally before deploying:**
   ```bash
   ./start_local_dev.sh
   # Test your changes
   # Then deploy
   source .secrets.env && ./deploy_cognitude.sh
   ```

5. **Monitor deployment:**
   ```bash
   # Watch logs during deployment
   ssh root@165.22.158.75 'docker logs -f cognitude-api-1'
   ```

---

## 🔐 SSH Key Setup (Recommended)

For better security, use SSH keys instead of passwords:

```bash
# 1. Generate SSH key (if you don't have one)
ssh-keygen -t ed25519 -C "your_email@example.com"

# 2. Copy public key to server
ssh-copy-id root@165.22.158.75

# 3. Test connection
ssh root@165.22.158.75

# 4. Remove SSH_PASS from .secrets.env
# Edit .secrets.env and comment out or remove:
# export SSH_PASS="..."

# 5. Scripts will now use key-based auth automatically
source .secrets.env
./deploy_cognitude.sh
```

---

## 📊 Script Comparison

| Feature | setup_local_env.sh | start_local_dev.sh | deploy_cognitude.sh | redeploy_and_test.sh |
|---------|-------------------|-------------------|---------------------|---------------------|
| **Purpose** | Initial setup | Start dev servers | Deploy to prod | Deploy + test |
| **Frequency** | Once | Daily | When deploying | When deploying |
| **Needs Secrets** | No | No | Yes | Yes |
| **Docker** | Starts local | Uses local | Deploys to prod | Deploys to prod |
| **Testing** | No | No | Basic health check | Comprehensive |
| **Duration** | 2-5 min | Instant | 3-5 min | 5-7 min |

---

## 🆘 Getting Help

If you encounter issues:

1. Check this guide first
2. Review error messages carefully
3. Check container logs: `docker logs cognitude-api-1`
4. Verify secrets are loaded: `echo $PROD_SERVER`
5. Test connectivity: `curl http://165.22.158.75:8000/health`

For persistent issues, check:
- `.env` files are correct
- Docker Desktop is running
- Server is accessible: `ping 165.22.158.75`
- Firewall isn't blocking ports 8000, 5432, 6379


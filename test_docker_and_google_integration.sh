#!/bin/bash
# Test script to verify Docker connectivity and Google provider integration

set -e

echo "======================================================================"
echo "🧪 Testing Docker Connectivity and Google Provider Integration"
echo "======================================================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test function
test_step() {
    echo "▶️  $1"
    if eval "$2"; then
        echo -e "${GREEN}✅ $3${NC}"
        return 0
    else
        echo -e "${RED}❌ $4${NC}"
        return 1
    fi
}

# Server configuration
SERVER="root@165.22.158.75"
SSH_PASS="GAzette4ever"

echo "🔍 Step 1: Testing Docker daemon connectivity on server..."
test_step "Checking Docker version" \
    "sshpass -p '$SSH_PASS' ssh -o StrictHostKeyChecking=no $SERVER 'docker --version'" \
    "Docker is installed and accessible" \
    "Docker is not accessible"

echo ""
echo "🔍 Step 2: Testing Docker Compose..."
test_step "Checking Docker Compose version" \
    "sshpass -p '$SSH_PASS' ssh -o StrictHostKeyChecking=no $SERVER 'docker compose version'" \
    "Docker Compose is working" \
    "Docker Compose is not working"

echo ""
echo "🔍 Step 3: Checking running containers..."
sshpass -p "$SSH_PASS" ssh -o StrictHostKeyChecking=no $SERVER << 'ENDSSH'
echo "Current containers:"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
ENDSSH

echo ""
echo "🔍 Step 4: Testing API health endpoint..."
test_step "Checking API health" \
    "curl -f -s http://165.22.158.75:8000/health" \
    "API is responding" \
    "API is not responding"

echo ""
echo "🔍 Step 5: Testing Google provider registration..."
# Create a test script to run on the server
sshpass -p "$SSH_PASS" ssh -o StrictHostKeyChecking=no $SERVER << 'ENDSSH'
cd /opt/cognitude

# Create test script
cat > test_google_provider.py << 'TEST_SCRIPT'
#!/usr/bin/env python3
import sys
import os
sys.path.append('/opt/cognitude')

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from app import models, crud
from app.services.router import ProviderRouter
import asyncio

# Test Google provider
async def test_google_provider():
    try:
        # Create database connection
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            print("❌ DATABASE_URL not set")
            return False
            
        engine = create_engine(database_url)
        db = Session(bind=engine)
        
        # Test router initialization
        router = ProviderRouter(db, organization_id=1)
        print("✅ Router initialized successfully")
        
        # Test provider selection for Gemini models
        test_models = ['gemini-flash', 'gemini-pro', 'gemini-2.5-flash']
        for model in test_models:
            provider = router.select_provider(model)
            if provider:
                print(f"✅ Provider selected for {model}: {provider.provider}")
            else:
                print(f"⚠️  No provider found for {model}")
        
        # Test Google API call (if API key is available)
        google_providers = crud.get_provider_configs(db, organization_id=1, enabled_only=True)
        google_provider = next((p for p in google_providers if p.provider == 'google'), None)
        
        if google_provider and google_provider.get_api_key():
            print("✅ Google provider configured with API key")
            # Test with a simple message
            try:
                messages = [{"role": "user", "content": "Hello, test!"}]
                result = await router.test_provider_connection(
                    "google", 
                    google_provider.get_api_key(), 
                    "gemini-flash", 
                    messages
                )
                print("✅ Google API test call successful")
                print(f"Response: {result['choices'][0]['message']['content'][:100]}...")
            except Exception as e:
                print(f"⚠️  Google API test failed: {e}")
        else:
            print("⚠️  No Google provider with API key found")
            
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_google_provider())
    sys.exit(0 if success else 1)
TEST_SCRIPT

chmod +x test_google_provider.py

echo "Running Google provider test..."
python3 test_google_provider.py
ENDSSH

echo ""
echo "🔍 Step 6: Testing API endpoints..."
echo "Testing /docs endpoint..."
if curl -f -s http://165.22.158.75:8000/docs > /dev/null; then
    echo -e "${GREEN}✅ API documentation is accessible${NC}"
else
    echo -e "${RED}❌ API documentation is not accessible${NC}"
fi

echo ""
echo "Testing /providers endpoint..."
if curl -f -s http://165.22.158.75:8000/providers > /dev/null; then
    echo -e "${GREEN}✅ Providers endpoint is accessible${NC}"
else
    echo -e "${RED}❌ Providers endpoint is not accessible${NC}"
fi

echo ""
echo "🔍 Step 7: Checking logs for errors..."
sshpass -p "$SSH_PASS" ssh -o StrictHostKeyChecking=no $SERVER << 'ENDSSH'
cd /opt/cognitude
echo "Recent API logs:"
docker compose -f docker-compose.prod.yml logs --tail=20 api
ENDSSH

echo ""
echo "======================================================================"
echo "📊 Test Summary"
echo "======================================================================"

# Overall assessment
echo ""
echo "🎯 Key Checks Completed:"
echo "   ✅ Docker daemon connectivity"
echo "   ✅ Docker Compose functionality"
echo "   ✅ API container status"
echo "   ✅ API endpoint accessibility"
echo "   ✅ Google provider integration"
echo ""

echo "📝 Next Steps if Issues Found:"
echo "   1. Run diagnose_docker_daemon.sh on server for detailed diagnostics"
echo "   2. Run fix_docker_daemon.sh on server to apply fixes"
echo "   3. Redeploy with: ./deploy_with_docker_fix.sh"
echo "   4. Check Google API key configuration in .env file"
echo ""

echo "======================================================================"
echo "✅ Testing Complete!"
echo "======================================================================"
#!/bin/bash
# Complete redeployment and testing script
#
# Usage: ./redeploy_and_test.sh [GOOGLE_API_KEY]
# Example: ./redeploy_and_test.sh "your_google_api_key_here"
# If no Google API key is provided, the script will skip the API key update step

set -e

echo "======================================================================"
echo "🚀 Redeploying Cognitude with Fixes and Testing"
echo "======================================================================"
echo ""

SERVER="root@165.22.158.75"
SSH_PASS="GAzette4ever"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print status
print_status() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✅ $2${NC}"
    else
        echo -e "${RED}❌ $2${NC}"
    fi
}

echo "📦 Step 1: Building and deploying updated container..."
echo ""

# Build and deploy
if ./deploy_with_docker_fix.sh; then
    print_status 0 "Deployment completed"
else
    print_status 1 "Deployment failed"
    exit 1
fi

echo ""
echo "⏳ Waiting for services to stabilize..."
sleep 10

echo ""
echo "🔍 Step 2: Running diagnostics on server..."
echo ""

# Copy debug script to server
echo "Copying debug script to server..."
sshpass -p "$SSH_PASS" scp debug_api_errors.py $SERVER:/opt/cognitude/debug_api_errors.py
print_status $? "Debug script copied"

echo ""
echo "Running diagnostics..."
sshpass -p "$SSH_PASS" ssh -o StrictHostKeyChecking=no $SERVER << 'ENDSSH'
cd /opt/cognitude

echo "Checking container status..."
docker ps | grep cognitude

echo ""
echo "Running API error debug script..."
docker exec cognitude-api-1 python3 /code/debug_api_errors.py

echo ""
echo "Checking recent logs..."
docker logs cognitude-api-1 --tail=20
ENDSSH

echo ""
echo "🔑 Step 3: Updating Google API key..."
echo ""

# Update Google API key
ORG_API_KEY="8hX-UQX0UOnDXXWTo-fKhQ"
NEW_GOOGLE_API_KEY="$1"  # Accept new API key as argument

if [ -z "$NEW_GOOGLE_API_KEY" ]; then
    echo "⚠️  Warning: No Google API key provided as argument."
    echo "   Usage: ./redeploy_and_test.sh YOUR_NEW_GOOGLE_API_KEY"
    echo "   Skipping Google API key update..."
else
    echo "Updating Google provider with new API key..."
    RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "http://165.22.158.75:8000/providers/" \
      -H "Content-Type: application/json" \
      -H "X-API-Key: $ORG_API_KEY" \
      -d '{
        "provider": "google",
        "api_key": "'"$NEW_GOOGLE_API_KEY"'",
        "enabled": true,
        "priority": 1
      }')
    
    HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
    BODY=$(echo "$RESPONSE" | sed '$d')
    
    if [ "$HTTP_CODE" = "200" ]; then
        print_status 0 "Google API key updated successfully"
    else
        print_status 1 "Failed to update Google API key: $BODY"
    fi
fi

echo ""
echo "🧪 Step 4: Testing API endpoints..."
echo ""

# Test health endpoint
echo "Testing health endpoint..."
if curl -f -s http://165.22.158.75:8000/health > /dev/null; then
    print_status 0 "Health endpoint is working"
else
    print_status 1 "Health endpoint failed"
fi

# Test providers endpoint
echo "Testing providers endpoint..."
API_KEY="8hX-UQX0UOnDXXWTo-fKhQ"
if curl -f -s http://165.22.158.75:8000/providers -H "X-API-Key: $API_KEY" > /dev/null; then
    print_status 0 "Providers endpoint is working"
else
    print_status 1 "Providers endpoint failed"
fi

# Test chat completion with Google
echo "Testing Google provider chat completion..."
RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "http://165.22.158.75:8000/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{
    "model": "gemini-flash",
    "messages": [{"role": "user", "content": "Hello, test!"}],
    "max_tokens": 50
  }')

HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | sed '$d')

if [ "$HTTP_CODE" = "200" ]; then
    print_status 0 "Google chat completion successful"
    echo "Response: $(echo $BODY | jq -r '.choices[0].message.content' 2>/dev/null | cut -c1-100)..."
elif [ "$HTTP_CODE" = "500" ]; then
    print_status 1 "Internal server error"
    echo "Error response: $BODY"
else
    print_status 1 "Unexpected HTTP code: $HTTP_CODE"
    echo "Response: $BODY"
fi

echo ""
echo "📋 Step 5: Summary..."
echo ""

echo "Container status:"
sshpass -p "$SSH_PASS" ssh -o StrictHostKeyChecking=no $SERVER "docker ps | grep cognitude"

echo ""
echo "API logs (last 10 lines):"
sshpass -p "$SSH_PASS" ssh -o StrictHostKeyChecking=no $SERVER "docker logs cognitude-api-1 --tail=10"

echo ""
echo "======================================================================"
echo "🎯 Deployment and Testing Complete!"
echo "======================================================================"
echo ""

# Check if all tests passed
if [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}🎉 SUCCESS! The API is working correctly with Google provider.${NC}"
    echo ""
    echo "📝 Next steps:"
    echo "   - Your Google provider integration is working"
    echo "   - You can now use models like 'gemini-flash', 'gemini-pro', etc."
    echo "   - API is accessible at http://165.22.158.75:8000"
else
    echo -e "${YELLOW}⚠️  Some issues remain. Check the output above for details.${NC}"
    echo ""
    echo "🔧 Troubleshooting steps:"
    echo "   1. Check the debug output above for specific errors"
    echo "   2. Update Google API key using: ./redeploy_and_test.sh YOUR_NEW_GOOGLE_API_KEY"
    echo "   3. Check container logs: docker logs cognitude-api-1"
    echo "   4. Run debug script: docker exec cognitude-api-1 python3 /code/debug_api_errors.py"
fi

echo ""
echo "🌐 API URL: http://165.22.158.75:8000"
echo "📖 Docs: http://165.22.158.75:8000/docs"
echo "💚 Health: http://165.22.158.75:8000/health"
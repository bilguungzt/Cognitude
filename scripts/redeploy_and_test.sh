#!/bin/bash
# Complete redeployment and testing script
#
# Usage: 
#   1. Source your secrets: source .secrets.env
#   2. Run: ./redeploy_and_test.sh [GOOGLE_API_KEY]
#
# Example: ./redeploy_and_test.sh "your_google_api_key_here"
# If no Google API key is provided, it will use GOOGLE_API_KEY from environment

set -e

echo "======================================================================"
echo "🚀 Redeploying Cognitude with Fixes and Testing"
echo "======================================================================"
echo ""

# Check for required environment variables
if [ -z "$PROD_SERVER" ]; then
    echo "❌ Error: PROD_SERVER not set"
    echo "Please source .secrets.env first: source .secrets.env"
    exit 1
fi

if [ -z "$ORG_API_KEY" ]; then
    echo "❌ Error: ORG_API_KEY not set"
    echo "Please source .secrets.env first: source .secrets.env"
    exit 1
fi

# Use SSH key-based auth by default, fall back to password if SSH_PASS is set
if [ -z "$SSH_PASS" ]; then
    SSH_CMD="ssh -o StrictHostKeyChecking=no"
    SCP_CMD="scp"
else
    SSH_CMD="sshpass -p $SSH_PASS ssh -o StrictHostKeyChecking=no"
    SCP_CMD="sshpass -p $SSH_PASS scp"
fi

SERVER="$PROD_SERVER"

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

# Check if deployment script exists
if [ ! -f "./scripts/deploy_with_docker_fix.sh" ]; then
    echo "⚠️  deploy_with_docker_fix.sh not found, using deploy_cognitude.sh instead"
    DEPLOY_SCRIPT="./scripts/deploy_cognitude.sh"
else
    DEPLOY_SCRIPT="./scripts/deploy_with_docker_fix.sh"
fi

# Build and deploy
if $DEPLOY_SCRIPT; then
    print_status 0 "Deployment completed"
else
    print_status 1 "Deployment failed"
    exit 1
fi

echo ""
echo "⏳ Waiting for services to stabilize..."
sleep 10

echo ""
echo "🔑 Step 2: Updating Google API key..."
echo ""

# Update Google API key - accept as argument or from environment
NEW_GOOGLE_API_KEY="${1:-$GOOGLE_API_KEY}"

if [ -z "$NEW_GOOGLE_API_KEY" ]; then
    echo "⚠️  Warning: No Google API key provided"
    echo "   Usage: ./redeploy_and_test.sh YOUR_NEW_GOOGLE_API_KEY"
    echo "   Or set GOOGLE_API_KEY in .secrets.env"
    echo "   Skipping Google API key update..."
else
    echo "Updating Google provider with new API key..."
    RESPONSE=$(curl -s -w "\n%{http_code}" --max-time 30 -X POST "http://${SERVER#*@}:8000/providers/" \
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
        print_status 1 "Failed to update Google API key (HTTP $HTTP_CODE): $BODY"
    fi
fi

echo ""
echo "🔍 Step 3: Running diagnostics on server..."
echo ""

# Copy debug script to server
echo "Copying debug script to server..."
if [ -f "debug_api_errors.py" ]; then
    $SCP_CMD debug_api_errors.py $SERVER:/opt/cognitude/debug_api_errors.py
    print_status $? "Debug script copied"
else
    echo "⚠️  debug_api_errors.py not found, skipping diagnostics"
fi

echo ""
echo "Running diagnostics..."
$SSH_CMD $SERVER << 'ENDSSH'
cd /opt/cognitude

echo "Checking container status..."
docker ps | grep cognitude || echo "No cognitude containers found"

if [ -f "debug_api_errors.py" ]; then
    echo ""
    echo "Running API error debug script..."
    docker exec cognitude-api-1 python3 /code/debug_api_errors.py || echo "Debug script failed"
fi

echo ""
echo "Checking recent logs..."
docker logs cognitude-api-1 --tail=20 || echo "Failed to get logs"
ENDSSH

echo ""
echo "🧪 Step 4: Testing API endpoints..."
echo ""

# Test health endpoint
echo "Testing health endpoint..."
if curl -f -s --max-time 10 http://${SERVER#*@}:8000/health > /dev/null; then
    print_status 0 "Health endpoint is working"
else
    print_status 1 "Health endpoint failed"
fi

# Test providers endpoint
echo "Testing providers endpoint..."
if curl -f -s --max-time 10 http://${SERVER#*@}:8000/providers -H "X-API-Key: $ORG_API_KEY" > /dev/null; then
    print_status 0 "Providers endpoint is working"
else
    print_status 1 "Providers endpoint failed"
fi

# Test chat completion with Google
echo "Testing Google provider chat completion..."
RESPONSE=$(curl -s -w "\n%{http_code}" --max-time 30 -X POST "http://${SERVER#*@}:8000/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $ORG_API_KEY" \
  -d '{
    "model": "gemini-flash",
    "messages": [{"role": "user", "content": "Hello, test!"}],
    "max_tokens": 50
  }')

HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | sed '$d')

if [ "$HTTP_CODE" = "200" ]; then
    print_status 0 "Google chat completion successful"
    # Try to parse JSON response
    if command -v jq >/dev/null 2>&1; then
        echo "Response: $(echo "$BODY" | jq -r '.choices[0].message.content' 2>/dev/null | cut -c1-100)..."
    else
        echo "Response: $BODY" | cut -c1-200
    fi
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
$SSH_CMD $SERVER "docker ps | grep cognitude || echo 'No cognitude containers running'"

echo ""
echo "API logs (last 10 lines):"
$SSH_CMD $SERVER "docker logs cognitude-api-1 --tail=10 2>&1 || echo 'Failed to get logs'"

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
    echo "   - API is accessible at http://${SERVER#*@}:8000"
else
    echo -e "${YELLOW}⚠️  Some issues remain. Check the output above for details.${NC}"
    echo ""
    echo "🔧 Troubleshooting steps:"
    echo "   1. Check the debug output above for specific errors"
    echo "   2. Update Google API key: ./redeploy_and_test.sh YOUR_NEW_GOOGLE_API_KEY"
    echo "   3. Check container logs: ssh $SERVER 'docker logs cognitude-api-1'"
    echo "   4. Verify environment variables in /opt/cognitude/.env"
fi

echo ""
echo "🌐 API URL: http://${SERVER#*@}:8000"
echo "📖 Docs: http://${SERVER#*@}:8000/docs"
echo "💚 Health: http://${SERVER#*@}:8000/health"

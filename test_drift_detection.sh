#!/bin/bash

# DriftGuard MVP - End-to-End Drift Detection Test Script
# This script demonstrates the complete workflow from model registration to drift visualization

set -e  # Exit on error

echo "🚀 DriftGuard MVP - Drift Detection Test"
echo "=========================================="
echo ""

# Configuration
API_URL="http://localhost:8000"
ORG_NAME="Test Organization $(date +%s)"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Step 1: Register Organization
echo -e "${BLUE}Step 1: Registering organization...${NC}"
REGISTER_RESPONSE=$(curl -s -X POST "$API_URL/auth/register" \
  -H "Content-Type: application/json" \
  -d "{\"name\": \"$ORG_NAME\"}")

API_KEY=$(echo $REGISTER_RESPONSE | grep -o '"api_key":"[^"]*' | grep -o '[^"]*$')

if [ -z "$API_KEY" ]; then
    echo "❌ Failed to get API key"
    echo "Response: $REGISTER_RESPONSE"
    exit 1
fi

echo -e "${GREEN}✓ Organization registered${NC}"
echo "API Key: $API_KEY"
echo ""

# Step 2: Create Model
echo -e "${BLUE}Step 2: Creating ML model...${NC}"
MODEL_RESPONSE=$(curl -s -X POST "$API_URL/models/" \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "customer_churn_model",
    "version": "1.0.0",
    "description": "Predicts customer churn probability",
    "features": [
      {"feature_name": "age", "feature_type": "numeric", "order": 1},
      {"feature_name": "income", "feature_type": "numeric", "order": 2},
      {"feature_name": "tenure_months", "feature_type": "numeric", "order": 3}
    ]
  }')

MODEL_ID=$(echo $MODEL_RESPONSE | grep -o '"id":[0-9]*' | grep -o '[0-9]*' | head -1)

if [ -z "$MODEL_ID" ]; then
    echo "❌ Failed to create model"
    echo "Response: $MODEL_RESPONSE"
    exit 1
fi

echo -e "${GREEN}✓ Model created (ID: $MODEL_ID)${NC}"
echo ""

# Step 3: Set Baseline
echo -e "${BLUE}Step 3: Setting baseline data...${NC}"
BASELINE_RESPONSE=$(curl -s -X POST "$API_URL/drift/baseline" \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d "{
    \"model_id\": $MODEL_ID,
    \"features\": {
      \"age\": [25, 30, 35, 40, 45, 50, 28, 32, 38, 42, 27, 33, 39, 44, 29],
      \"income\": [50000, 60000, 70000, 80000, 90000, 55000, 65000, 75000, 85000, 95000, 52000, 62000, 72000, 82000, 92000],
      \"tenure_months\": [12, 24, 36, 48, 60, 18, 30, 42, 54, 66, 15, 27, 39, 51, 63]
    }
  }")

echo -e "${GREEN}✓ Baseline configured${NC}"
echo ""

# Step 4: Log Normal Predictions (similar to baseline)
echo -e "${BLUE}Step 4: Logging normal predictions (no drift expected)...${NC}"
for i in {1..35}; do
  AGE=$((25 + RANDOM % 30))
  INCOME=$((50000 + RANDOM % 50000))
  TENURE=$((12 + RANDOM % 60))
  PREDICTION=$(echo "scale=2; $RANDOM % 100 / 100" | bc)
  
  curl -s -X POST "$API_URL/predictions/" \
    -H "X-API-Key: $API_KEY" \
    -H "Content-Type: application/json" \
    -d "{
      \"model_id\": $MODEL_ID,
      \"predictions\": [{
        \"features\": {
          \"age\": $AGE,
          \"income\": $INCOME,
          \"tenure_months\": $TENURE
        },
        \"prediction\": $PREDICTION
      }]
    }" > /dev/null
done

echo -e "${GREEN}✓ Logged 35 normal predictions${NC}"
echo ""

# Step 5: Check Drift (should be NO drift)
echo -e "${BLUE}Step 5: Checking for drift...${NC}"
DRIFT_RESPONSE=$(curl -s -X GET "$API_URL/drift/models/$MODEL_ID/current" \
  -H "X-API-Key: $API_KEY")

echo "Drift Status: $DRIFT_RESPONSE"
echo ""

# Step 6: Log Drifted Predictions (very different from baseline)
echo -e "${YELLOW}Step 6: Logging drifted predictions (drift expected)...${NC}"
for i in {1..35}; do
  AGE=$((60 + RANDOM % 20))  # Much older age range
  INCOME=$((150000 + RANDOM % 100000))  # Much higher income
  TENURE=$((80 + RANDOM % 30))  # Much longer tenure
  PREDICTION=$(echo "scale=2; 0.8 + $RANDOM % 20 / 100" | bc)  # Higher predictions
  
  curl -s -X POST "$API_URL/predictions/" \
    -H "X-API-Key: $API_KEY" \
    -H "Content-Type: application/json" \
    -d "{
      \"model_id\": $MODEL_ID,
      \"predictions\": [{
        \"features\": {
          \"age\": $AGE,
          \"income\": $INCOME,
          \"tenure_months\": $TENURE
        },
        \"prediction\": $PREDICTION
      }]
    }" > /dev/null
done

echo -e "${GREEN}✓ Logged 35 drifted predictions${NC}"
echo ""

# Step 7: Check Drift Again (should detect drift)
echo -e "${BLUE}Step 7: Checking for drift again...${NC}"
DRIFT_RESPONSE2=$(curl -s -X GET "$API_URL/drift/models/$MODEL_ID/current" \
  -H "X-API-Key: $API_KEY")

echo "Drift Status: $DRIFT_RESPONSE2"
echo ""

# Step 8: Get Drift History
echo -e "${BLUE}Step 8: Fetching drift history...${NC}"
HISTORY_RESPONSE=$(curl -s -X GET "$API_URL/drift/models/$MODEL_ID/history?limit=10" \
  -H "X-API-Key: $API_KEY")

echo "Drift History: $HISTORY_RESPONSE"
echo ""

# Step 9: Configure Email Alert
echo -e "${BLUE}Step 9: Configuring email alert channel...${NC}"
ALERT_RESPONSE=$(curl -s -X POST "$API_URL/alert-channels/" \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "channel_type": "email",
    "configuration": {"email": "alerts@example.com"}
  }')

echo -e "${GREEN}✓ Email alert configured${NC}"
echo ""

# Summary
echo "=========================================="
echo -e "${GREEN}✅ Test Complete!${NC}"
echo ""
echo "Test Summary:"
echo "  • Organization: $ORG_NAME"
echo "  • API Key: $API_KEY"
echo "  • Model ID: $MODEL_ID"
echo "  • Predictions logged: 70 (35 normal + 35 drifted)"
echo "  • Drift checks: 2"
echo ""
echo "Next Steps:"
echo "  1. Open http://localhost:5173/ in your browser"
echo "  2. Login with API Key: $API_KEY"
echo "  3. Go to Dashboard"
echo "  4. Click 'Drift History' on model #$MODEL_ID"
echo "  5. View the drift chart with real data!"
echo ""
echo "To check drift again:"
echo "  curl -X GET '$API_URL/drift/models/$MODEL_ID/current' -H 'X-API-Key: $API_KEY'"
echo ""

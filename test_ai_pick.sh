#!/bin/bash

# Test script for AI draft picks
# Usage: ./test_ai_pick.sh [simulation_id] [username] [password]

BASE_URL="http://localhost:5000"
# Try 5001 if 5000 doesn't work
if ! curl -s "${BASE_URL}/api/health" > /dev/null 2>&1; then
    BASE_URL="http://localhost:5001"
fi

echo "============================================================"
echo "AI Draft Pick Test Script"
echo "============================================================"
echo ""

# Get credentials
USERNAME="${2:-admin}"
PASSWORD="${3:-admin}"

echo "Logging in as ${USERNAME}..."
LOGIN_RESPONSE=$(curl -s -X POST "${BASE_URL}/api/auth/login" \
    -H "Content-Type: application/json" \
    -d "{\"username\":\"${USERNAME}\",\"password\":\"${PASSWORD}\"}")

TOKEN=$(echo "$LOGIN_RESPONSE" | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
    echo "❌ Login failed"
    echo "Response: $LOGIN_RESPONSE"
    exit 1
fi

echo "✓ Login successful"
echo ""

# Get simulations
echo "Fetching simulations..."
SIMULATIONS=$(curl -s -X GET "${BASE_URL}/api/simulations" \
    -H "Authorization: Bearer ${TOKEN}")

# Extract draft simulations
DRAFT_SIMS=$(echo "$SIMULATIONS" | grep -o '"status":"draft"' | wc -l | tr -d ' ')

if [ "$DRAFT_SIMS" -eq 0 ]; then
    echo "No simulations in draft status found."
    echo "Available simulations:"
    echo "$SIMULATIONS" | grep -o '"id":[0-9]*,"name":"[^"]*","status":"[^"]*"' | head -5
    exit 1
fi

# Get simulation ID
if [ -n "$1" ]; then
    SIMULATION_ID="$1"
else
    # Try to get first draft simulation ID
    SIMULATION_ID=$(echo "$SIMULATIONS" | grep -o '"id":[0-9]*' | head -1 | cut -d':' -f2)
    if [ -z "$SIMULATION_ID" ]; then
        echo "Please provide a simulation ID as first argument"
        exit 1
    fi
fi

echo "Using simulation ID: ${SIMULATION_ID}"
echo ""

# Get current pick
echo "============================================================"
echo "Current Draft State"
echo "============================================================"
CURRENT=$(curl -s -X GET "${BASE_URL}/api/simulations/${SIMULATION_ID}/draft/current" \
    -H "Authorization: Bearer ${TOKEN}")

echo "$CURRENT" | grep -o '"round":[0-9]*' | head -1
echo "$CURRENT" | grep -o '"pick":[0-9]*' | head -1
echo "$CURRENT" | grep -o '"team_name":"[^"]*"' | head -1
echo ""

# Get draft history
HISTORY=$(curl -s -X GET "${BASE_URL}/api/simulations/${SIMULATION_ID}/draft/history" \
    -H "Authorization: Bearer ${TOKEN}")

HISTORY_COUNT=$(echo "$HISTORY" | grep -o '"round":[0-9]*' | wc -l | tr -d ' ')
echo "Total picks made: ${HISTORY_COUNT}"
echo ""

# Test AI pick
echo "============================================================"
echo "Testing AI Pick"
echo "============================================================"
echo ""

RESPONSE=$(curl -s -X POST "${BASE_URL}/api/simulations/${SIMULATION_ID}/draft/sim-next-ai" \
    -H "Authorization: Bearer ${TOKEN}" \
    -w "\nHTTP_STATUS:%{http_code}")

HTTP_STATUS=$(echo "$RESPONSE" | grep "HTTP_STATUS" | cut -d':' -f2)
BODY=$(echo "$RESPONSE" | sed '/HTTP_STATUS/d')

echo "Response Status: ${HTTP_STATUS}"
echo "Response Body:"
echo "$BODY" | python3 -m json.tool 2>/dev/null || echo "$BODY"
echo ""

# Check for errors
if echo "$BODY" | grep -q '"error"'; then
    ERROR=$(echo "$BODY" | grep -o '"error":"[^"]*' | cut -d'"' -f4)
    echo "❌ Error: ${ERROR}"
else
    echo "✓ AI pick request completed"
fi

# Get updated history
echo ""
echo "============================================================"
echo "Updated Draft History"
echo "============================================================"
HISTORY=$(curl -s -X GET "${BASE_URL}/api/simulations/${SIMULATION_ID}/draft/history" \
    -H "Authorization: Bearer ${TOKEN}")

HISTORY_COUNT=$(echo "$HISTORY" | grep -o '"round":[0-9]*' | wc -l | tr -d ' ')
echo "Total picks made: ${HISTORY_COUNT}"

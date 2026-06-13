#!/bin/bash
# Quick test script for Xephy-AI API

echo "🧪 Testing Xephy-AI Trading System API"
echo "========================================"
echo ""

API="http://localhost:5000"

echo "1️⃣  Health Check"
curl -s $API/ | jq '.' || echo "❌ Server not running"
echo ""

echo "2️⃣  System Status"
curl -s $API/api/status | jq '.'
echo ""

echo "3️⃣  Run Analysis"
curl -s -X POST $API/api/analyze | jq '.'
echo ""

echo "4️⃣  Check Positions"
curl -s $API/api/positions | jq '.'
echo ""

echo "5️⃣  Get Settings"
curl -s $API/api/settings | jq '.'
echo ""

echo "6️⃣  Account Info"
curl -s $API/api/account | jq '.'
echo ""

echo "✅ Test complete!"

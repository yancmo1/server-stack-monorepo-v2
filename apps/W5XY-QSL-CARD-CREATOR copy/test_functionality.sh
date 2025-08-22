#!/bin/bash

# QSL Card Creator - JavaScript Functionality Test
# Test various functionality to ensure everything works

echo "🧪 QSL Card Creator - JavaScript Functionality Test"
echo "====================================================="

BASE_URL="http://localhost:5001"

# Test 1: Check if container is running
echo "📋 Test 1: Container Status"
if docker ps | grep -q qsl-card-creator; then
    echo "✅ Docker container is running"
else
    echo "❌ Docker container is not running"
    exit 1
fi

# Test 2: Test basic API
echo ""
echo "📋 Test 2: QSO API Test"
API_RESULT=$(curl -s "$BASE_URL/qso/KI8N")
if echo "$API_RESULT" | grep -q "KI8N"; then
    echo "✅ QSO API is working"
    echo "   Data: $(echo "$API_RESULT" | python3 -c "import sys, json; data=json.load(sys.stdin); print(f'Call: {data[\"callsign\"]}, Date: {data[\"date\"]}, Mode: {data[\"mode\"]}')")"
else
    echo "❌ QSO API failed"
    echo "   Response: $API_RESULT"
fi

# Test 3: Test database info
echo ""
echo "📋 Test 3: Database Status"
DB_RESULT=$(curl -s "$BASE_URL/api/database-info")
if echo "$DB_RESULT" | grep -q "exists"; then
    echo "✅ Database API is working"
    echo "   Info: $(echo "$DB_RESULT" | python3 -c "import sys, json; data=json.load(sys.stdin); print(f'QSOs: {data[\"qso_count\"]}, Size: {data[\"size_mb\"]}MB')")"
else
    echo "❌ Database API failed"
    echo "   Response: $DB_RESULT"
fi

# Test 4: Test create page loading
echo ""
echo "📋 Test 4: Create Page Loading"
CREATE_RESULT=$(curl -s "$BASE_URL/create?callsign=KI8N")
if echo "$CREATE_RESULT" | grep -q "id=\"callsign\""; then
    echo "✅ Create page loads correctly"
    if echo "$CREATE_RESULT" | grep -q "loadQSOData"; then
        echo "✅ JavaScript functions are included"
    else
        echo "❌ JavaScript functions missing"
    fi
else
    echo "❌ Create page failed to load"
fi

# Test 5: Test QSOs page loading
echo ""
echo "📋 Test 5: QSOs Page Loading"
QSOS_RESULT=$(curl -s "$BASE_URL/qsos")
if echo "$QSOS_RESULT" | grep -q "Create QSL"; then
    echo "✅ QSOs page loads with Create QSL buttons"
else
    echo "❌ QSOs page failed to load properly"
fi

echo ""
echo "🌐 Manual Testing:"
echo "   1. Open: $BASE_URL/create?callsign=KI8N"
echo "   2. Check if callsign field shows 'KI8N'"
echo "   3. Check if other fields are populated"
echo "   4. Open: $BASE_URL/qsos"
echo "   5. Click any 'Create QSL' button"
echo ""
echo "📝 Expected Behavior:"
echo "   - URL parameters should auto-populate callsign field"
echo "   - loadQSOData should auto-fill date, time, frequency, mode, RST"
echo "   - 'Load from Log' button should work manually"
echo "   - 'Create QSL' buttons in QSOs page should open new tabs"

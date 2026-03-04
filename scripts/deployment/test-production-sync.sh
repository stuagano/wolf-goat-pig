#!/bin/bash
# Test Production Google Sheets Sync
# This script verifies that the Google Sheets sync is working in production

set -e

PROD_URL="https://wolf-goat-pig.onrender.com"
SHEET_CSV_URL="https://docs.google.com/spreadsheets/d/1PWhi5rJ4ZGhTwySZh-D_9lo_GKJcHb1Q5MEkNasHLgM/export?format=csv&gid=0"

echo "🔍 Testing Production Google Sheets Sync"
echo "========================================"
echo ""

# Step 1: Check backend health
echo "1️⃣ Checking backend health..."
if curl -s -f "$PROD_URL/health" > /dev/null 2>&1; then
    echo "   ✅ Backend is healthy"
else
    echo "   ⏳ Backend is cold starting, waiting 15 seconds..."
    sleep 15
    if curl -s -f "$PROD_URL/health" > /dev/null 2>&1; then
        echo "   ✅ Backend is now healthy"
    else
        echo "   ❌ Backend is not responding. Please check Render.com dashboard."
        exit 1
    fi
fi
echo ""

# Step 2: Check scheduler status
echo "2️⃣ Checking scheduled sync status..."
SCHEDULER_STATUS=$(curl -s "$PROD_URL/email/scheduler-status")
echo "   Status: $SCHEDULER_STATUS"
echo ""

# Step 3: Check current leaderboard data
echo "3️⃣ Checking current leaderboard data..."
LEADERBOARD_DATA=$(curl -s "$PROD_URL/leaderboard/total_earnings")
if echo "$LEADERBOARD_DATA" | grep -q "leaderboard"; then
    PLAYER_COUNT=$(echo "$LEADERBOARD_DATA" | grep -o '"player_name"' | wc -l)
    echo "   ✅ Found $PLAYER_COUNT players in leaderboard"
    echo ""
    echo "   Top 3 Players:"
    echo "$LEADERBOARD_DATA" | python3 -m json.tool 2>/dev/null | grep -A 1 "player_name" | head -12 || echo "   (Unable to parse)"
else
    echo "   ⚠️  No leaderboard data found or backend error"
fi
echo ""

# Step 4: Trigger manual sync
echo "4️⃣ Triggering manual Google Sheets sync..."
SYNC_RESPONSE=$(curl -s -X POST "$PROD_URL/sheet-integration/sync-wgp-sheet" \
    -H "Content-Type: application/json" \
    -H "X-Scheduled-Job: true" \
    -d "{\"csv_url\":\"$SHEET_CSV_URL\"}")

if echo "$SYNC_RESPONSE" | grep -q "players_synced\|players_processed"; then
    echo "   ✅ Sync triggered successfully!"
    echo ""
    echo "   Sync Results:"
    echo "$SYNC_RESPONSE" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(f'   - Players Processed: {data.get(\"sync_results\", {}).get(\"players_processed\", 0)}')
    print(f'   - Players Created: {data.get(\"sync_results\", {}).get(\"players_created\", 0)}')
    print(f'   - Players Updated: {data.get(\"sync_results\", {}).get(\"players_updated\", 0)}')
    print(f'   - Total Players: {data.get(\"player_count\", 0)}')

    if 'players_synced' in data:
        print(f'   - Synced Players: {', '.join(data['players_synced'][:5])}...')

    if data.get('sync_results', {}).get('errors'):
        print(f'   ⚠️  Errors: {len(data[\"sync_results\"][\"errors\"])}')
except Exception as e:
    print(f'   (Unable to parse sync results: {e})')
" 2>/dev/null || echo "$SYNC_RESPONSE" | head -20
else
    echo "   ❌ Sync failed or backend error"
    echo "   Response: $SYNC_RESPONSE"
fi
echo ""

# Step 5: Verify updated leaderboard
echo "5️⃣ Verifying updated leaderboard data..."
sleep 2  # Give the database a moment to update
UPDATED_LEADERBOARD=$(curl -s "$PROD_URL/leaderboard/total_earnings")
if echo "$UPDATED_LEADERBOARD" | grep -q "leaderboard"; then
    UPDATED_COUNT=$(echo "$UPDATED_LEADERBOARD" | grep -o '"player_name"' | wc -l)
    echo "   ✅ Leaderboard now has $UPDATED_COUNT players"

    echo ""
    echo "   Updated Top 5:"
    echo "$UPDATED_LEADERBOARD" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    for i, player in enumerate(data.get('leaderboard', [])[:5], 1):
        name = player.get('player_name', 'Unknown')
        value = player.get('value', 0)
        print(f'   {i}. {name}: \${value:.2f}')
except Exception as e:
    print(f'   (Unable to parse leaderboard)')
" 2>/dev/null || echo "   (Unable to parse)"
else
    echo "   ❌ Failed to retrieve updated leaderboard"
fi
echo ""

echo "========================================"
echo "✅ Production sync test complete!"
echo ""
echo "📊 To view the leaderboard in browser:"
echo "   https://wolf-goat-pig.onrender.com/leaderboard/total_earnings"
echo ""
echo "🔄 To view the sync UI:"
echo "   https://your-frontend-url.vercel.app/live-sync"

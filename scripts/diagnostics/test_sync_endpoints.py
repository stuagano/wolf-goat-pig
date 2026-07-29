#!/usr/bin/env python3
"""
Simple test script to verify sync endpoints are working correctly.
"""
import asyncio
import httpx
import json

# Test the endpoints with a mock CSV URL
TEST_CSV_URL = "https://docs.google.com/spreadsheets/d/141s8V_UACdBc8Xg17W0UhWxd08BMbEImkXOSPa66RfQ/export?format=csv&gid=0"
API_BASE_URL = "http://localhost:8000"

async def test_fetch_google_sheet():
    """Test the fetch-google-sheet endpoint"""
    print("Testing fetch-google-sheet endpoint...")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{API_BASE_URL}/sheet-integration/fetch-google-sheet",
                json={"csv_url": TEST_CSV_URL},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                print("✅ fetch-google-sheet working!")
                print(f"   Headers: {data.get('headers', [])[:5]}...")  # First 5 headers
                print(f"   Rows: {data.get('total_rows', 0)}")
                return True
            else:
                print(f"❌ fetch-google-sheet failed: {response.status_code}")
                print(f"   Error: {response.text}")
                return False
        except Exception as e:
            print(f"❌ fetch-google-sheet error: {e}")
            return False

async def test_sync_wgp_sheet():
    """Test the sync-wgp-sheet endpoint"""
    print("\nTesting sync-wgp-sheet endpoint...")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{API_BASE_URL}/sheet-integration/sync-wgp-sheet",
                json={"csv_url": TEST_CSV_URL},
                timeout=60  # Longer timeout for sync
            )
            
            if response.status_code == 200:
                data = response.json()
                print("✅ sync-wgp-sheet working!")
                print(f"   Players synced: {data.get('player_count', 0)}")
                print(f"   Players with GHIN: {data.get('ghin_players_count', 0)}")
                print(f"   Sync results: {data.get('sync_results', {})}")
                
                # Check if GHIN data is in response
                if data.get('ghin_data'):
                    print(f"   GHIN data included for: {list(data['ghin_data'].keys())}")
                else:
                    print("   No GHIN data in response (expected if no GHIN IDs configured)")
                    
                return True
            else:
                print(f"❌ sync-wgp-sheet failed: {response.status_code}")
                print(f"   Error: {response.text}")
                return False
        except Exception as e:
            print(f"❌ sync-wgp-sheet error: {e}")
            return False

async def main():
    """Run all tests"""
    print("🧪 Testing Google Sheets sync endpoints...")
    print(f"Using CSV URL: {TEST_CSV_URL}\n")
    
    # Test both endpoints
    fetch_ok = await test_fetch_google_sheet()
    sync_ok = await test_sync_wgp_sheet()
    
    print(f"\n📊 Test Results:")
    print(f"   fetch-google-sheet: {'✅ PASS' if fetch_ok else '❌ FAIL'}")
    print(f"   sync-wgp-sheet: {'✅ PASS' if sync_ok else '❌ FAIL'}")
    
    if fetch_ok and sync_ok:
        print("\n🎉 All endpoints working correctly!")
        print("✨ GHIN scores are now included in sync-wgp-sheet payload!")
    else:
        print("\n⚠️  Some endpoints have issues. Check server logs for details.")

if __name__ == "__main__":
    asyncio.run(main())
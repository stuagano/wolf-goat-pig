"""
Test script to verify the sheet sync transaction fix.
This test verifies that errors on individual players don't abort the entire transaction.
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from backend.app.database import SessionLocal, init_db
from backend.app.services.sheet_integration_service import SheetIntegrationService
from backend.app.models import PlayerProfile, PlayerStatistics

def test_sheet_sync_with_errors():
    """Test that sheet sync handles errors on individual players gracefully."""
    print("🧪 Testing sheet sync transaction handling...")

    # Initialize database
    init_db()
    db = SessionLocal()

    try:
        # Clean up any existing test players
        test_names = ["Test Player 1", "Test Player 2", "Test Player 3"]
        for name in test_names:
            player = db.query(PlayerProfile).filter_by(name=name).first()
            if player:
                # Delete related statistics first
                db.query(PlayerStatistics).filter_by(player_id=player.id).delete()
                db.delete(player)
        db.commit()

        # Create test sheet data with one invalid row
        sheet_data = [
            {
                "Player Name": "Test Player 1",
                "Games Played": "10",
                "Games Won": "5",
                "Total Earnings": "$100.00"
            },
            {
                "Player Name": "Test Player 2",
                "Games Played": "invalid_data",  # This will cause an error
                "Games Won": "3",
                "Total Earnings": "$50.00"
            },
            {
                "Player Name": "Test Player 3",
                "Games Played": "15",
                "Games Won": "8",
                "Total Earnings": "$200.00"
            }
        ]

        # Run sheet sync
        service = SheetIntegrationService(db)
        headers = list(sheet_data[0].keys())
        mappings = service.create_column_mappings(headers)
        results = service.sync_sheet_data_to_database(sheet_data, mappings)

        print(f"\n📊 Sync Results:")
        print(f"  Players processed: {results['players_processed']}")
        print(f"  Players created: {results['players_created']}")
        print(f"  Players updated: {results['players_updated']}")
        print(f"  Errors: {len(results['errors'])}")

        if results['errors']:
            print(f"\n⚠️  Errors encountered:")
            for error in results['errors']:
                print(f"  - {error}")

        # Verify that players 1 and 3 were created despite player 2 having an error
        player1 = db.query(PlayerProfile).filter_by(name="Test Player 1").first()
        player2 = db.query(PlayerProfile).filter_by(name="Test Player 2").first()
        player3 = db.query(PlayerProfile).filter_by(name="Test Player 3").first()

        print(f"\n✅ Verification:")
        print(f"  Test Player 1 created: {player1 is not None}")
        print(f"  Test Player 2 created: {player2 is not None}")
        print(f"  Test Player 3 created: {player3 is not None}")

        # Check if the fix worked
        if player1 and player3:
            print(f"\n🎉 SUCCESS! Transaction isolation working correctly.")
            print(f"   Players 1 and 3 were created even though Player 2 had an error.")
            return True
        else:
            print(f"\n❌ FAILED! Transaction isolation not working.")
            print(f"   Expected Players 1 and 3 to be created, but they weren't.")
            return False

    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        # Clean up test data
        try:
            for name in test_names:
                player = db.query(PlayerProfile).filter_by(name=name).first()
                if player:
                    db.query(PlayerStatistics).filter_by(player_id=player.id).delete()
                    db.delete(player)
            db.commit()
        except:
            pass
        finally:
            db.close()

if __name__ == "__main__":
    success = test_sheet_sync_with_errors()
    sys.exit(0 if success else 1)

import httpx
import asyncio

async def test_ghin_sync():
    try:
        async with httpx.AsyncClient() as client:
            # Get all players
            response = await client.get("http://localhost:8000/players/all")
            response.raise_for_status()
            players = response.json()

            # Find a player with a ghin_id
            player_to_sync = None
            for player in players:
                if player.get("ghin_id"):
                    player_to_sync = player
                    break
            
            if not player_to_sync:
                print("No player with a ghin_id found. Please add one to test the sync.")
                return

            player_id = player_to_sync["id"]
            print(f"Found player to sync: {player_to_sync['name']} (ID: {player_id}, GHIN ID: {player_to_sync['ghin_id']})")

            # Sync the player's handicap
            print(f"Syncing handicap for player {player_id}...")
            sync_response = await client.post(f"http://localhost:8000/ghin/sync-player-handicap/{player_id}")
            sync_response.raise_for_status()
            sync_data = sync_response.json()

            print("Sync successful!")
            print(sync_data)

    except httpx.HTTPStatusError as e:
        print(f"HTTP error occurred: {e.response.status_code} - {e.response.text}")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    asyncio.run(test_ghin_sync())

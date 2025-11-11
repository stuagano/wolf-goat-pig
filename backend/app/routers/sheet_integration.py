"""
Sheet Integration Router

Google Sheets integration endpoints for syncing player data and leaderboards.

Rate limited to prevent excessive API calls.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Header
from sqlalchemy.orm import Session
from typing import List, Dict, Optional
from datetime import datetime
import logging
import httpx

from ..database import get_db
from .. import models, schemas
from ..services.player_service import PlayerService
from ..middleware.rate_limiting import rate_limiter
from ..middleware.caching import sheet_sync_cache

logger = logging.getLogger("app.routers.sheet_integration")

router = APIRouter(
    prefix="/sheet-integration",
    tags=["sheet_integration"],
    responses={404: {"description": "Not found"}},
)


@router.post("/analyze-structure")
async def analyze_sheet_structure(
    sheet_headers: List[str],
    db: Session = Depends(get_db)
):
    """
    Analyze Google Sheets structure and suggest column mappings.

    Takes a list of sheet headers and returns suggested mappings to database fields.
    """
    try:
        # Common column name variations
        column_mappings = []

        for header in sheet_headers:
            header_lower = header.lower()
            mapping = {"sheet_column": header}

            if any(name in header_lower for name in ['member', 'player', 'name', 'golfer']):
                mapping["db_field"] = "player_name"
            elif any(name in header_lower for name in ['score', 'quarters', 'total']):
                mapping["db_field"] = "total_earnings"
            elif 'average' in header_lower:
                mapping["db_field"] = "avg_earnings_per_game"
            elif any(name in header_lower for name in ['rounds', 'games']):
                mapping["db_field"] = "games_played"
            elif 'qb' in header_lower:
                mapping["db_field"] = "qb_count"
            elif 'date' in header_lower:
                mapping["db_field"] = "last_played"
            else:
                mapping["db_field"] = None

            column_mappings.append(mapping)

        return {
            "column_mappings": column_mappings,
            "total_columns": len(sheet_headers),
            "mapped_columns": len([m for m in column_mappings if m["db_field"] is not None])
        }

    except Exception as e:
        logger.error(f"Error analyzing sheet structure: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to analyze sheet structure: {str(e)}")
    finally:
        db.close()


@router.post("/create-leaderboard")
async def create_leaderboard_from_sheet(
    sheet_data: List[Dict],
    db: Session = Depends(get_db)
):
    """
    Transform Google Sheets data into leaderboard format.

    Takes raw sheet data and creates a structured leaderboard.
    """
    try:
        from ..services.leaderboard_service import LeaderboardService

        leaderboard_service = LeaderboardService(db)
        leaderboard = leaderboard_service.create_from_sheet_data(sheet_data)

        return {
            "leaderboard": leaderboard,
            "player_count": len(leaderboard),
            "created_at": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error creating leaderboard from sheet: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create leaderboard: {str(e)}")
    finally:
        db.close()


@router.post("/sync-data")
async def sync_sheet_data(
    request: Dict,
    db: Session = Depends(get_db)
):
    """
    Generic sheet data sync endpoint.

    Syncs data from Google Sheets to database.
    """
    try:
        from ..services.sheet_integration_service import SheetIntegrationService

        sheet_service = SheetIntegrationService(db)
        result = await sheet_service.sync_data(request)

        return result

    except Exception as e:
        logger.error(f"Error syncing sheet data: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to sync sheet data: {str(e)}")
    finally:
        db.close()


@router.get("/export-current-data")
def export_current_data_for_sheet(
    sheet_headers: List[str] = Query(...),
    db: Session = Depends(get_db)
):
    """
    Export current database data in sheet format.

    Returns current player statistics formatted for Google Sheets export.
    """
    try:
        from ..services.leaderboard_service import LeaderboardService

        leaderboard_service = LeaderboardService(db)
        export_data = leaderboard_service.export_for_sheets(sheet_headers)

        return {
            "data": export_data,
            "headers": sheet_headers,
            "row_count": len(export_data),
            "exported_at": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error exporting current data: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to export current data: {str(e)}")
    finally:
        db.close()


@router.post("/sync-wgp-sheet")
async def sync_wgp_sheet_data(
    request: Dict[str, str],
    db: Session = Depends(get_db),
    x_scheduled_job: Optional[str] = Header(None)
):
    """
    Sync Wolf Goat Pig specific sheet data format.

    Rate limited to once per hour to prevent excessive API calls from external sources.
    Results are cached for 1 hour.

    Scheduled jobs (with X-Scheduled-Job header) bypass rate limiting.

    Uses isolated sessions per player to ensure failures are isolated and
    don't cascade to other players' data.
    """
    try:
        # Rate limit: max once per hour (but bypass for scheduled jobs)
        is_scheduled_job = x_scheduled_job == "true"
        if not is_scheduled_job:
            rate_limiter.check_limit("sheet_sync", min_interval_seconds=3600)
        else:
            logger.info("Scheduled job detected - bypassing rate limit")

        csv_url = request.get("csv_url")
        if not csv_url:
            raise HTTPException(status_code=400, detail="CSV URL is required")

        # Check cache first
        cache_key = f"sheet_sync:{csv_url}"
        cached_result = sheet_sync_cache.get(cache_key)
        if cached_result:
            logger.info(f"Returning cached sheet sync data (CSV: {csv_url[:50]}...)")
            return cached_result

        from collections import defaultdict

        # Fetch the CSV data (follow redirects for Google Sheets export URLs)
        async with httpx.AsyncClient(follow_redirects=True) as client:
            response = await client.get(csv_url, timeout=30)
            response.raise_for_status()
        csv_text = response.text

        # Parse CSV
        lines = csv_text.strip().split('\n')
        if not lines:
            raise HTTPException(status_code=400, detail="Empty sheet data")

        # Find the actual header row (looking for "Member" column)
        header_line_index = -1
        headers = []

        for i, line in enumerate(lines):
            temp_headers = [h.strip().strip('"') for h in line.split(',')]
            # Check if this line contains the actual column headers
            if any('member' in h.lower() for h in temp_headers if h) and \
               any('quarters' in h.lower() for h in temp_headers if h):
                header_line_index = i
                headers = temp_headers
                logger.info(f"Found headers at row {i + 1}: {headers}")
                break

        if header_line_index == -1:
            # Fallback: assume headers are in the first non-empty row with multiple values
            for i, line in enumerate(lines):
                temp_headers = [h.strip().strip('"') for h in line.split(',')]
                if len([h for h in temp_headers if h]) >= 3:  # At least 3 non-empty columns
                    header_line_index = i
                    headers = temp_headers
                    logger.info(f"Using row {i + 1} as headers (fallback): {headers}")
                    break

        if not headers:
            raise HTTPException(status_code=400, detail="Could not find valid headers in sheet")

        # Create header index mapping for flexible column handling
        header_map = {header.lower(): idx for idx, header in enumerate(headers) if header}

        # Process each row based on detected columns
        player_stats = {}

        # Start processing from the row after headers
        for line in lines[header_line_index + 1:]:
            if line.strip():
                values = [v.strip().strip('"') for v in line.split(',')]

                # Skip empty rows or rows with too few values
                if len(values) < 2 or not any(v for v in values[:5]):  # Check first 5 columns
                    continue

                # Extract player name (try different column names)
                player_name = None
                for name_key in ['member', 'player', 'name', 'golfer']:
                    if name_key in header_map and header_map[name_key] < len(values):
                        player_name = values[header_map[name_key]]
                        break

                # Skip if no player name, or if it's a header/summary row
                if not player_name or player_name.lower() in ['member', 'player', 'name', '', 'total', 'average', 'grand total']:
                    logger.info(f"Skipping non-player row: {player_name}")
                    continue

                # Stop if we hit summary sections (like "Most Rounds Played")
                if any(keyword in player_name.lower() for keyword in ['most rounds', 'top 5', 'best score', 'worst score', 'group size']):
                    logger.info(f"Stopping at summary section: {player_name}")
                    break

                # Initialize player stats if not exists
                if player_name not in player_stats:
                    player_stats[player_name] = {
                        "quarters": 0,
                        "average": 0,
                        "rounds": 0,
                        "qb": 0,
                        "games_won": 0,
                        "total_earnings": 0
                    }

                # Map the sheet columns to our data model
                # Score column (total earnings - can be negative)
                score_value = None
                for score_key in ['score', 'sum score', 'total score', 'quarters']:
                    if score_key in header_map and header_map[score_key] < len(values):
                        score_value = values[header_map[score_key]]
                        break

                if score_value and score_value != '':
                    try:
                        # Handle negative values (e.g., "-155")
                        score_int = int(float(score_value))  # Handle decimal values too
                        # Accumulate total earnings across multiple games
                        player_stats[player_name]["quarters"] += score_int
                        player_stats[player_name]["total_earnings"] += float(score_int)
                        logger.debug(f"Added {score_value} to {player_name}, total now: {player_stats[player_name]['total_earnings']}")
                    except (ValueError, IndexError) as e:
                        logger.warning(f"Error parsing score for {player_name}: {e}")
                        pass

                # Average column
                if 'average' in header_map and header_map['average'] < len(values):
                    try:
                        avg_value = values[header_map['average']]
                        if avg_value and avg_value != '':
                            player_stats[player_name]["average"] = float(avg_value)
                            logger.debug(f"Set {player_name} average to {avg_value}")
                    except (ValueError, IndexError) as e:
                        logger.warning(f"Error parsing average for {player_name}: {e}")
                        pass

                # Count rounds/games played (increment for each row)
                player_stats[player_name]["rounds"] += 1
                logger.debug(f"Incremented {player_name} rounds to {player_stats[player_name]['rounds']}")

                # Check if they won this game (positive score)
                if score_value and score_value != '':
                    try:
                        if float(score_value) > 0:
                            player_stats[player_name]["games_won"] += 1
                    except (ValueError, TypeError):
                        pass

                # QB column
                if 'qb' in header_map and header_map['qb'] < len(values):
                    try:
                        qb_value = values[header_map['qb']]
                        if qb_value and qb_value != '':
                            player_stats[player_name]["qb"] = int(qb_value)
                            logger.debug(f"Set {player_name} QB to {qb_value}")
                    except (ValueError, IndexError) as e:
                        logger.warning(f"Error parsing QB for {player_name}: {e}")
                        pass

                # Log successful player data extraction
                if player_stats[player_name]["quarters"] != 0 or player_stats[player_name]["rounds"] > 0:
                    logger.info(f"Extracted data for {player_name}: {player_stats[player_name]}")

        # Calculate averages for all players after processing all rows
        for player_name, stats in player_stats.items():
            if stats["rounds"] > 0:
                stats["average"] = stats["total_earnings"] / stats["rounds"]
                logger.debug(f"Calculated average for {player_name}: {stats['average']}")

        # Create/update players in database
        player_service = PlayerService(db)
        sync_results = {
            "players_processed": 0,
            "players_created": 0,
            "players_updated": 0,
            "errors": []
        }

        # Track GHIN data for response payload
        ghin_data_collection = {}

        for player_name, stats in player_stats.items():
            try:
                # Check if player exists
                existing_player = db.query(models.PlayerProfile).filter(
                    models.PlayerProfile.name == player_name
                ).first()

                if not existing_player:
                    # Create new player
                    player_data = schemas.PlayerProfileCreate(
                        name=player_name,
                        handicap=10.0,  # Default handicap
                        email=f"{player_name.lower().replace(' ', '.')}@wgp.com"
                    )
                    new_player = player_service.create_player_profile(player_data)
                    sync_results["players_created"] += 1
                    player_id = new_player.id
                else:
                    player_id = existing_player.id
                    sync_results["players_updated"] += 1

                # Update or create statistics record
                player_stats_record = db.query(models.PlayerStatistics).filter(
                    models.PlayerStatistics.player_id == player_id
                ).first()

                if not player_stats_record:
                    # Create new statistics record
                    player_stats_record = models.PlayerStatistics(player_id=player_id)
                    db.add(player_stats_record)

                # Update statistics with sheet data
                player_stats_record.games_played = stats.get("rounds", 0)
                player_stats_record.total_earnings = stats.get("total_earnings", 0)

                # Calculate win percentage based on average earnings per game
                if stats.get("rounds", 0) > 0 and stats.get("average", 0) > 0:
                    # If average is positive, estimate wins based on that
                    # Assuming positive average means winning more often
                    estimated_win_rate = min(100, max(0, (stats.get("average", 0) + 50) / 100 * 50))
                    player_stats_record.win_percentage = estimated_win_rate
                    player_stats_record.games_won = int(stats.get("rounds", 0) * estimated_win_rate / 100)
                else:
                    player_stats_record.win_percentage = 0
                    player_stats_record.games_won = 0

                # Store additional metrics
                player_stats_record.avg_earnings_per_game = stats.get("average", 0)

                # Update timestamp
                player_stats_record.last_updated = datetime.now().isoformat()

                # Try to fetch GHIN data if player has GHIN ID
                ghin_data = None
                if existing_player and existing_player.ghin_id:
                    try:
                        from ..services.ghin_service import GHINService
                        ghin_service = GHINService(db)

                        # Check if GHIN service is available
                        if await ghin_service.initialize():
                            ghin_data = await ghin_service.sync_player_handicap(player_id)
                            if ghin_data:
                                # Update handicap from GHIN
                                existing_player.handicap = ghin_data.get('handicap_index', existing_player.handicap)
                                logger.info(f"Updated GHIN data for {player_name}: handicap={ghin_data.get('handicap_index')}")
                        else:
                            # Fall back to stored GHIN data
                            ghin_data = ghin_service.get_player_ghin_data(player_id)
                            if ghin_data:
                                logger.info(f"Using stored GHIN data for {player_name}")
                    except Exception as ghin_error:
                        logger.warning(f"Failed to fetch GHIN data for {player_name}: {ghin_error}")

                # Store GHIN data for response payload
                if ghin_data:
                    ghin_data_collection[player_name] = {
                        "ghin_id": ghin_data.get("ghin_id"),
                        "current_handicap": ghin_data.get("current_handicap"),
                        "recent_scores": ghin_data.get("recent_scores", [])[:5],  # Last 5 scores
                        "last_updated": ghin_data.get("last_updated")
                    }

                db.commit()

                sync_results["players_processed"] += 1

            except Exception as e:
                db.rollback()  # CRITICAL: Roll back the failed transaction
                sync_results["errors"].append(f"Error processing {player_name}: {str(e)}")
                logger.error(f"Failed to process {player_name}, rolled back transaction: {e}")
                continue

        # Log summary of synced data
        logger.info(f"Synced {len(player_stats)} players from sheet")
        logger.info(f"Sync results: {sync_results}")

        # Return detailed sync information including the data that was synced
        result = {
            "sync_results": sync_results,
            "player_count": len(player_stats),
            "synced_at": datetime.now().isoformat(),
            "headers_found": headers,
            "players_synced": list(player_stats.keys()),
            "sample_data": {name: stats for name, stats in list(player_stats.items())[:3]},  # First 3 players as sample
            "ghin_data": ghin_data_collection,  # GHIN scores and handicap data
            "ghin_players_count": len(ghin_data_collection)
        }

        # Cache the result for 1 hour
        sheet_sync_cache.set(cache_key, result)
        logger.info(f"Sheet sync data cached for 1 hour (key: {cache_key})")

        return result

    except HTTPException:
        # Re-raise HTTPExceptions (like 429 from rate limiter) without modifying them
        raise
    except httpx.RequestError as e:
        logger.error(f"Error fetching Google Sheet: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to fetch sheet: {str(e)}")
    except Exception as e:
        logger.error(f"Error syncing WGP sheet data: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to sync data: {str(e)}")


@router.post("/fetch-google-sheet")
async def fetch_google_sheet(request: Dict[str, str]):
    """
    Fetch raw data from Google Sheets.

    Downloads CSV data from a Google Sheets export URL.
    """
    try:
        csv_url = request.get("csv_url")
        if not csv_url:
            raise HTTPException(status_code=400, detail="CSV URL is required")

        # Fetch the CSV data (follow redirects for Google Sheets export URLs)
        async with httpx.AsyncClient(follow_redirects=True) as client:
            response = await client.get(csv_url, timeout=30)
            response.raise_for_status()

        csv_text = response.text

        # Parse CSV into structured data
        lines = csv_text.strip().split('\n')
        if not lines:
            raise HTTPException(status_code=400, detail="Empty sheet data")

        # First line is headers
        headers = [h.strip().strip('"') for h in lines[0].split(',')]

        # Parse data rows
        data = []
        for line in lines[1:]:
            if line.strip():
                values = [v.strip().strip('"') for v in line.split(',')]
                row = {}
                for i, header in enumerate(headers):
                    if i < len(values):
                        row[header] = values[i]
                data.append(row)

        return {
            "headers": headers,
            "data": data,
            "row_count": len(data),
            "fetched_at": datetime.now().isoformat()
        }

    except httpx.RequestError as e:
        logger.error(f"Error fetching Google Sheet: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to fetch sheet: {str(e)}")
    except Exception as e:
        logger.error(f"Error processing sheet data: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process sheet: {str(e)}")


@router.post("/compare-data")
async def compare_sheet_to_db_data(request: Dict, db: Session = Depends(get_db)):
    """
    Compare Google Sheets data with current database data.

    Generates a comparison report showing differences between sheet and DB.
    """
    try:
        from ..services.leaderboard_service import LeaderboardService

        sheet_data = request.get("sheet_data", [])
        if not sheet_data:
            raise HTTPException(status_code=400, detail="Sheet data is required")

        leaderboard_service = LeaderboardService(db)
        comparison = leaderboard_service.compare_with_sheet(sheet_data)

        return {
            "comparison": comparison,
            "differences_found": len(comparison.get("differences", [])),
            "compared_at": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error comparing sheet data: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to compare data: {str(e)}")
    finally:
        db.close()

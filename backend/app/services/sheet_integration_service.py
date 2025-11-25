"""
Sheet Integration Service

This service provides functionality to integrate with Google Sheets data
and create a read replica of spreadsheet-based metrics and leaderboards.

Features:
- Data mapping from sheet structure to database models
- Batch data import/sync utilities
- Custom metric calculation for sheet compatibility
- Export functionality for migration validation
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from ..models import PlayerProfile, PlayerStatistics
from .statistics_service import StatisticsService

logger = logging.getLogger(__name__)

@dataclass
class SheetColumnMapping:
    """Maps Google Sheet columns to database fields."""
    sheet_column: str
    db_field: str
    data_type: str  # 'text', 'number', 'percentage', 'currency', 'date'
    transformation: Optional[str] = None  # Optional transformation function name

@dataclass
class SheetDataRow:
    """Represents a row of data from the Google Sheet."""
    raw_data: Dict[str, Any]
    mapped_data: Dict[str, Any]
    validation_errors: List[str] = field(default_factory=list)

class SheetIntegrationService:
    """Service for integrating Google Sheets data with the application."""

    def __init__(self, db: Session):
        self.db = db
        self.stats_service = StatisticsService(db)

        # Default column mappings (can be customized based on actual sheet structure)
        self.default_column_mappings = [
            SheetColumnMapping("Player Name", "player_name", "text"),
            SheetColumnMapping("Games Played", "games_played", "number"),
            SheetColumnMapping("Games Won", "games_won", "number"),
            SheetColumnMapping("Win Rate", "win_rate", "percentage", "percentage_to_decimal"),
            SheetColumnMapping("Total Earnings", "total_earnings", "currency", "currency_to_float"),
            SheetColumnMapping("Avg Earnings Per Game", "avg_earnings_per_game", "currency", "currency_to_float"),
            SheetColumnMapping("Best Finish", "best_finish", "number"),
            SheetColumnMapping("Holes Won", "holes_won", "number"),
            SheetColumnMapping("Partnerships", "partnerships_formed", "number"),
            SheetColumnMapping("Partnership Success", "partnership_success_rate", "percentage", "percentage_to_decimal"),
            SheetColumnMapping("Betting Success", "betting_success_rate", "percentage", "percentage_to_decimal"),
            SheetColumnMapping("Solo Attempts", "solo_attempts", "number"),
            SheetColumnMapping("Solo Wins", "solo_wins", "number"),
        ]

    def create_column_mappings(self, sheet_headers: List[str]) -> List[SheetColumnMapping]:
        """Create column mappings based on sheet headers."""
        mappings = []

        # Try to match sheet headers to known patterns
        for header in sheet_headers:
            header_lower = header.lower().strip()

            # Player identification
            if any(pattern in header_lower for pattern in ["player", "name", "golfer"]):
                mappings.append(SheetColumnMapping(header, "player_name", "text"))

            # Game counts
            elif any(pattern in header_lower for pattern in ["games played", "rounds played", "total games"]):
                mappings.append(SheetColumnMapping(header, "games_played", "number"))
            elif any(pattern in header_lower for pattern in ["games won", "wins", "victories"]):
                mappings.append(SheetColumnMapping(header, "games_won", "number"))

            # Win rates
            elif any(pattern in header_lower for pattern in ["win rate", "win %", "win percentage"]):
                mappings.append(SheetColumnMapping(header, "win_rate", "percentage", "percentage_to_decimal"))

            # Earnings
            elif any(pattern in header_lower for pattern in ["total earnings", "total winnings", "earnings"]):
                mappings.append(SheetColumnMapping(header, "total_earnings", "currency", "currency_to_float"))
            elif any(pattern in header_lower for pattern in ["avg earnings", "average earnings", "earnings per game"]):
                mappings.append(SheetColumnMapping(header, "avg_earnings_per_game", "currency", "currency_to_float"))

            # Performance metrics
            elif any(pattern in header_lower for pattern in ["best finish", "best position"]):
                mappings.append(SheetColumnMapping(header, "best_finish", "number"))
            elif any(pattern in header_lower for pattern in ["holes won", "holes victory"]):
                mappings.append(SheetColumnMapping(header, "holes_won", "number"))

            # Partnership data
            elif any(pattern in header_lower for pattern in ["partnerships", "team ups"]):
                mappings.append(SheetColumnMapping(header, "partnerships_formed", "number"))
            elif any(pattern in header_lower for pattern in ["partnership success", "team success"]):
                mappings.append(SheetColumnMapping(header, "partnership_success_rate", "percentage", "percentage_to_decimal"))

            # Betting data
            elif any(pattern in header_lower for pattern in ["betting success", "bet success", "betting %"]):
                mappings.append(SheetColumnMapping(header, "betting_success_rate", "percentage", "percentage_to_decimal"))

            # Solo play
            elif any(pattern in header_lower for pattern in ["solo attempts", "solo tries"]):
                mappings.append(SheetColumnMapping(header, "solo_attempts", "number"))
            elif any(pattern in header_lower for pattern in ["solo wins", "solo victories"]):
                mappings.append(SheetColumnMapping(header, "solo_wins", "number"))

            # If no match found, create a generic mapping
            else:
                # Determine data type based on header patterns
                if any(pattern in header_lower for pattern in ["%", "rate", "percentage"]):
                    data_type = "percentage"
                    transformation = "percentage_to_decimal"
                elif any(pattern in header_lower for pattern in ["$", "earnings", "winnings", "money"]):
                    data_type = "currency"
                    transformation = "currency_to_float"
                elif any(pattern in header_lower for pattern in ["date", "time", "when"]):
                    data_type = "date"
                    transformation = "string_to_date"
                else:
                    data_type = "text"
                    transformation = None

                mappings.append(SheetColumnMapping(
                    header,
                    header.lower().replace(" ", "_").replace("-", "_"),
                    data_type,
                    transformation
                ))

        return mappings

    def transform_data_value(self, value: Any, transformation: Optional[str]) -> Any:
        """Apply data transformation based on transformation type."""
        if value is None or value == "":
            return None

        try:
            if transformation == "percentage_to_decimal":
                # Handle percentage strings like "85%" or "0.85" or 85
                if isinstance(value, str):
                    value = value.strip().replace("%", "")
                    return float(value) / 100 if float(value) > 1 else float(value)
                return float(value) / 100 if value > 1 else float(value)

            elif transformation == "currency_to_float":
                # Handle currency strings like "$123.45" or "123.45"
                if isinstance(value, str):
                    value = value.strip().replace("$", "").replace(",", "")
                return float(value)

            elif transformation == "string_to_date":
                # Handle date strings
                if isinstance(value, str):
                    return datetime.strptime(value, "%Y-%m-%d").isoformat()
                return value

            elif transformation == "number":
                return int(float(value))

            else:
                return value

        except (ValueError, TypeError) as e:
            logger.warning(f"Failed to transform value {value} with {transformation}: {e}")
            return value

    def validate_sheet_row(self, row_data: Dict[str, Any], mappings: List[SheetColumnMapping]) -> SheetDataRow:
        """Validate and transform a row of sheet data."""
        errors = []
        mapped_data = {}

        for mapping in mappings:
            if mapping.sheet_column in row_data:
                raw_value = row_data[mapping.sheet_column]

                try:
                    transformed_value = self.transform_data_value(raw_value, mapping.transformation)
                    mapped_data[mapping.db_field] = transformed_value
                except Exception as e:
                    errors.append(f"Error transforming {mapping.sheet_column}: {e}")
                    mapped_data[mapping.db_field] = raw_value
            else:
                errors.append(f"Missing column: {mapping.sheet_column}")

        return SheetDataRow(
            raw_data=row_data,
            mapped_data=mapped_data,
            validation_errors=errors if errors else []
        )

    def create_leaderboard_from_sheet_data(self, sheet_data: List[Dict[str, Any]],
                                         mappings: List[SheetColumnMapping]) -> List[Dict[str, Any]]:
        """Create a leaderboard from sheet data."""
        validated_rows = []

        for row in sheet_data:
            validated_row = self.validate_sheet_row(row, mappings)
            if not validated_row.validation_errors:
                validated_rows.append(validated_row.mapped_data)
            else:
                logger.warning(f"Row validation errors: {validated_row.validation_errors}")

        # Sort by total earnings (or primary metric)
        if validated_rows and "total_earnings" in validated_rows[0]:
            validated_rows.sort(key=lambda x: x.get("total_earnings", 0), reverse=True)

        # Add ranks
        for rank, row in enumerate(validated_rows, 1):
            row["rank"] = rank

        return validated_rows

    def sync_sheet_data_to_database(self, sheet_data: List[Dict[str, Any]],
                                   mappings: List[SheetColumnMapping]) -> Dict[str, Any]:
        """Sync sheet data to the database (create/update player profiles and statistics)."""
        results: Dict[str, Any] = {
            "players_processed": 0,
            "players_created": 0,
            "players_updated": 0,
            "errors": []
        }

        try:
            for row in sheet_data:
                # Use savepoint for each player to isolate errors
                savepoint = self.db.begin_nested()

                try:
                    validated_row = self.validate_sheet_row(row, mappings)

                    if validated_row.validation_errors:
                        results["errors"].append({
                            "row": row,
                            "errors": validated_row.validation_errors
                        })
                        savepoint.rollback()
                        continue

                    data = validated_row.mapped_data
                    player_name = data.get("player_name")

                    if not player_name:
                        results["errors"].append({"row": row, "errors": ["Missing player name"]})
                        savepoint.rollback()
                        continue

                    # Find or create player profile
                    player = self.db.query(PlayerProfile).filter(
                        PlayerProfile.name == player_name
                    ).first()

                    if not player:
                        # Create new player profile
                        player = PlayerProfile(
                            name=player_name,
                            handicap=data.get("handicap", 18.0),
                            created_date=datetime.now().isoformat(),
                            is_active=1
                        )
                        self.db.add(player)
                        self.db.flush()  # Get the ID
                        results["players_created"] += 1

                    # Find or create player statistics
                    stats = self.db.query(PlayerStatistics).filter(
                        PlayerStatistics.player_id == player.id
                    ).first()

                    if not stats:
                        stats = PlayerStatistics(player_id=player.id)
                        self.db.add(stats)
                        self.db.flush()

                    # Update statistics from sheet data
                    for field, value in data.items():
                        if field != "player_name" and hasattr(stats, field) and value is not None:
                            setattr(stats, field, value)

                    setattr(stats, 'last_updated', datetime.now().isoformat())
                    results["players_updated"] += 1
                    results["players_processed"] += 1

                    # Commit this player's changes
                    savepoint.commit()

                except Exception as e:
                    # Rollback just this player's changes and continue with others
                    savepoint.rollback()
                    logger.error(f"Error processing player from row {row}: {e}")
                    results["errors"].append({
                        "row": row,
                        "errors": [f"Database error: {str(e)}"]
                    })
                    continue

            # Final commit for the entire transaction
            self.db.commit()
            logger.info(f"Sheet sync completed: {results}")

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error syncing sheet data: {e}")
            results["errors"].append({"general_error": str(e)})

        return results

    def export_current_data_to_sheet_format(self, mappings: List[SheetColumnMapping]) -> List[Dict[str, Any]]:
        """Export current database data in sheet format for comparison."""
        try:
            # Get all active players with statistics
            query = self.db.query(PlayerProfile, PlayerStatistics).join(
                PlayerStatistics, PlayerProfile.id == PlayerStatistics.player_id
            ).filter(PlayerProfile.is_active == 1)

            results = query.all()
            sheet_data = []

            for player, stats in results:
                row = {}

                # Map database fields back to sheet columns
                for mapping in mappings:
                    if mapping.db_field == "player_name":
                        row[mapping.sheet_column] = player.name
                    elif hasattr(stats, mapping.db_field):
                        value = getattr(stats, mapping.db_field)

                        # Apply reverse transformation for display
                        if mapping.transformation == "percentage_to_decimal" and value:
                            row[mapping.sheet_column] = f"{value * 100:.1f}%"
                        elif mapping.transformation == "currency_to_float" and value:
                            row[mapping.sheet_column] = f"${value:.2f}"
                        else:
                            row[mapping.sheet_column] = value
                    else:
                        row[mapping.sheet_column] = None

                sheet_data.append(row)

            # Sort by total earnings or primary metric
            sheet_data.sort(key=lambda x: float(str(x.get("Total Earnings", "0")).replace("$", "").replace(",", "")),
                          reverse=True)

            return sheet_data

        except Exception as e:
            logger.error(f"Error exporting data to sheet format: {e}")
            return []

    def generate_sheet_comparison_report(self,
                                       current_data: List[Dict[str, Any]],
                                       sheet_data: List[Dict[str, Any]],
                                       mappings: List[SheetColumnMapping]) -> Dict[str, Any]:
        """Generate a comparison report between current database and sheet data."""
        report: Dict[str, Any] = {
            "summary": {
                "database_players": len(current_data),
                "sheet_players": len(sheet_data),
                "common_players": 0,
                "database_only": [],
                "sheet_only": [],
                "data_differences": []
            },
            "detailed_comparison": []
        }

        try:
            # Create lookup dictionaries
            db_players = {row.get("Player Name", "").lower(): row for row in current_data}
            sheet_players = {row.get("Player Name", "").lower(): row for row in sheet_data}

            # Find common players and differences
            all_players = set(db_players.keys()) | set(sheet_players.keys())

            for player_name in all_players:
                if player_name in db_players and player_name in sheet_players:
                    report["summary"]["common_players"] += 1

                    # Compare data for common players
                    db_row = db_players[player_name]
                    sheet_row = sheet_players[player_name]
                    differences = []

                    for mapping in mappings:
                        db_value = db_row.get(mapping.sheet_column)
                        sheet_value = sheet_row.get(mapping.sheet_column)

                        if str(db_value) != str(sheet_value):
                            differences.append({
                                "field": mapping.sheet_column,
                                "database_value": db_value,
                                "sheet_value": sheet_value
                            })

                    if differences:
                        report["detailed_comparison"].append({
                            "player": player_name,
                            "differences": differences
                        })

                elif player_name in db_players:
                    report["summary"]["database_only"].append(player_name)
                else:
                    report["summary"]["sheet_only"].append(player_name)

            return report

        except Exception as e:
            logger.error(f"Error generating comparison report: {e}")
            report["error"] = str(e)
            return report

"""
Comprehensive data seeding script for Wolf-Goat-Pig application.
Initializes database with all required data for proper simulation bootstrapping.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import text

from .database import SessionLocal, init_db
from .models import Course, Rule, PlayerProfile, GameRecord, GamePlayerResult
from .seed_courses import DEFAULT_COURSES
from .seed_rules import RULES

logger = logging.getLogger(__name__)

# Default AI player personalities with different playing styles and characteristics
DEFAULT_AI_PERSONALITIES = [
    {
        "name": "Bob",
        "handicap": 10.5,
        "playing_style": "aggressive",
        "description": "Aggressive player who takes risks for potential big rewards",
        "personality_traits": {
            "risk_tolerance": 0.8,
            "partnership_frequency": 0.7,
            "double_frequency": 0.6,
            "strategic_thinking": 0.7
        },
        "strengths": ["Long drives", "Risk assessment", "Pressure situations"],
        "weaknesses": ["Short game consistency", "Conservative play"]
    },
    {
        "name": "Scott",
        "handicap": 15.0,
        "playing_style": "steady",
        "description": "Reliable player who focuses on consistent performance",
        "personality_traits": {
            "risk_tolerance": 0.4,
            "partnership_frequency": 0.8,
            "double_frequency": 0.3,
            "strategic_thinking": 0.8
        },
        "strengths": ["Course management", "Steady putting", "Partnership play"],
        "weaknesses": ["Distance", "Aggressive play under pressure"]
    },
    {
        "name": "Vince",
        "handicap": 8.0,
        "playing_style": "strategic",
        "description": "Strategic player who analyzes every situation carefully",
        "personality_traits": {
            "risk_tolerance": 0.6,
            "partnership_frequency": 0.6,
            "double_frequency": 0.7,
            "strategic_thinking": 0.9
        },
        "strengths": ["Shot selection", "Reading opponents", "Betting strategy"],
        "weaknesses": ["Overthinking", "Time management"]
    },
    {
        "name": "Mike",
        "handicap": 20.5,
        "playing_style": "unpredictable",
        "description": "Wild card player with surprising shot-making ability",
        "personality_traits": {
            "risk_tolerance": 0.9,
            "partnership_frequency": 0.5,
            "double_frequency": 0.8,
            "strategic_thinking": 0.5
        },
        "strengths": ["Clutch shots", "Unpredictability", "Entertainment value"],
        "weaknesses": ["Consistency", "Course management", "Handicap control"]
    },
    {
        "name": "Sarah",
        "handicap": 12.0,
        "playing_style": "analytical",
        "description": "Data-driven player who uses statistics to make decisions",
        "personality_traits": {
            "risk_tolerance": 0.5,
            "partnership_frequency": 0.7,
            "double_frequency": 0.4,
            "strategic_thinking": 0.9
        },
        "strengths": ["Statistical analysis", "Probability assessment", "Long-term strategy"],
        "weaknesses": ["Gut decisions", "Adapting to unexpected situations"]
    },
    {
        "name": "Dave",
        "handicap": 16.5,
        "playing_style": "social",
        "description": "Social player who enjoys the camaraderie and banter",
        "personality_traits": {
            "risk_tolerance": 0.6,
            "partnership_frequency": 0.9,
            "double_frequency": 0.5,
            "strategic_thinking": 0.6
        },
        "strengths": ["Team play", "Morale boosting", "Reading group dynamics"],
        "weaknesses": ["Solo play", "High-pressure situations"]
    }
]

# Sample game data for testing and demonstration
SAMPLE_GAME_SCENARIOS = [
    {
        "scenario_name": "Close Championship Finish",
        "description": "Tight competition with multiple lead changes",
        "player_count": 4,
        "course_name": "Wing Point Golf & Country Club",
        "total_holes": 18,
        "final_scores": {
            "Bob": {"quarters": 2.5, "holes_won": 5},
            "Scott": {"quarters": 1.0, "holes_won": 3},
            "Vince": {"quarters": -1.5, "holes_won": 4},
            "Mike": {"quarters": -2.0, "holes_won": 6}
        }
    },
    {
        "scenario_name": "Dominant Performance",
        "description": "One player runs away with the competition",
        "player_count": 4,
        "course_name": "Championship Links",
        "total_holes": 18,
        "final_scores": {
            "Bob": {"quarters": 8.5, "holes_won": 12},
            "Scott": {"quarters": -2.5, "holes_won": 2},
            "Vince": {"quarters": -3.0, "holes_won": 3},
            "Mike": {"quarters": -3.0, "holes_won": 1}
        }
    }
]

def verify_database_connection(db: Session) -> bool:
    """Verify database connection is working."""
    try:
        db.execute(text("SELECT 1"))
        db.commit()
        return True
    except Exception as e:
        logger.error(f"Database connection verification failed: {e}")
        return False

def seed_courses(db: Session) -> int:
    """Seed database with default golf courses."""
    courses_added = 0
    
    try:
        for course_data in DEFAULT_COURSES:
            # Check if course already exists
            existing_course = db.query(Course).filter_by(name=course_data["name"]).first()
            
            if existing_course:
                logger.info(f"Course '{course_data['name']}' already exists, skipping...")
                continue
            
            # Create new course
            course = Course(
                name=course_data["name"],
                description=course_data["description"],
                total_par=course_data["total_par"],
                total_yards=course_data["total_yards"],
                course_rating=course_data.get("course_rating"),
                slope_rating=course_data.get("slope_rating"),
                holes_data=course_data["holes_data"],
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat()
            )
            
            db.add(course)
            courses_added += 1
            logger.info(f"Added course: {course_data['name']} ({course_data['total_par']} par, {course_data['total_yards']} yards)")
        
        db.commit()
        logger.info(f"Successfully seeded {courses_added} courses!")
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error seeding courses: {e}")
        raise
    
    return courses_added

def seed_rules(db: Session) -> int:
    """Seed database with Wolf-Goat-Pig rules."""
    rules_added = 0
    
    try:
        for rule_data in RULES:
            # Check if rule already exists
            existing_rule = db.query(Rule).filter_by(title=rule_data["title"]).first()
            
            if existing_rule:
                logger.debug(f"Rule '{rule_data['title']}' already exists, skipping...")
                continue
            
            # Create new rule
            rule = Rule(
                title=rule_data["title"],
                description=rule_data["description"]
            )
            
            db.add(rule)
            rules_added += 1
            logger.debug(f"Added rule: {rule_data['title']}")
        
        db.commit()
        logger.info(f"Successfully seeded {rules_added} rules!")
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error seeding rules: {e}")
        raise
    
    return rules_added

def seed_ai_personalities(db: Session) -> int:
    """Seed database with AI player personalities."""
    personalities_added = 0
    
    try:
        for personality in DEFAULT_AI_PERSONALITIES:
            # Check if player profile already exists
            existing_player = db.query(PlayerProfile).filter_by(name=personality["name"]).first()
            
            if existing_player:
                logger.debug(f"Player '{personality['name']}' already exists, skipping...")
                continue
            
            # Create new AI player profile
            player = PlayerProfile(
                name=personality["name"],
                handicap=personality["handicap"],
                playing_style=personality["playing_style"],
                is_ai=1,
                is_active=1,
                description=personality["description"],
                personality_traits=personality["personality_traits"],
                strengths=personality["strengths"],
                weaknesses=personality["weaknesses"],
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            db.add(player)
            personalities_added += 1
            logger.info(f"Added AI personality: {personality['name']} ({personality['playing_style']} style)")
        
        db.commit()
        logger.info(f"Successfully seeded {personalities_added} AI personalities!")
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error seeding AI personalities: {e}")
        raise
    
    return personalities_added

def seed_sample_games(db: Session) -> int:
    """Seed database with sample game data for testing."""
    games_added = 0
    
    try:
        for scenario in SAMPLE_GAME_SCENARIOS:
            # Create sample game record
            game_date = datetime.now() - timedelta(days=games_added * 7)  # Space games a week apart
            
            game_record = GameRecord(
                game_date=game_date,
                course_name=scenario["course_name"],
                player_count=scenario["player_count"],
                total_holes=scenario["total_holes"],
                game_mode="wolf_goat_pig",
                notes=scenario["description"],
                created_at=game_date
            )
            
            db.add(game_record)
            db.flush()  # Get the game_record_id
            
            # Add player results for this game
            for player_name, results in scenario["final_scores"].items():
                try:
                    # Find the player profile
                    player_profile = db.query(PlayerProfile).filter_by(name=player_name).first()
                    if not player_profile:
                        logger.warning(f"Player '{player_name}' not found for sample game, skipping...")
                        continue

                    player_result = GamePlayerResult(
                        game_record_id=game_record.id,
                        player_profile_id=player_profile.id,
                        final_score=results["quarters"],
                        holes_won=results["holes_won"],
                        holes_played=scenario["total_holes"],
                        partnerships_formed=max(1, results["holes_won"] // 4),  # Estimate
                        solo_attempts=max(0, results["holes_won"] // 8),  # Estimate
                        successful_bets=results["holes_won"],
                        total_bets=scenario["total_holes"],
                        created_at=game_date
                    )

                    db.add(player_result)
                except Exception as player_error:
                    logger.warning(f"Failed to add player result for '{player_name}': {player_error}")
                    # Continue with next player instead of aborting entire transaction
                    continue
            
            games_added += 1
            logger.info(f"Added sample game: {scenario['scenario_name']}")
        
        db.commit()
        logger.info(f"Successfully seeded {games_added} sample games!")
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error seeding sample games: {e}")
        raise
    
    return games_added

def create_default_human_player(db: Session) -> Optional[PlayerProfile]:
    """Create a default human player profile if none exists."""
    try:
        # Check if any human players exist
        human_players = (
            db.query(PlayerProfile)
            .filter(PlayerProfile.is_ai == 0)
            .count()
        )
        
        if human_players > 0:
            logger.info("Human players already exist, skipping default creation...")
            return None
        
        # Create default human player
        default_human = PlayerProfile(
            name="Player",
            handicap=18.0,
            playing_style="balanced",
            is_ai=0,
            is_active=1,
            description="Default human player profile",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        db.add(default_human)
        db.commit()
        
        logger.info("Created default human player profile")
        return default_human
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating default human player: {e}")
        raise

def verify_seeded_data(db: Session) -> dict:
    """Verify that all essential data has been seeded correctly."""
    verification_results = {}
    
    try:
        # Check courses
        course_count = db.query(Course).count()
        verification_results["courses"] = {
            "count": course_count,
            "status": "success" if course_count >= 3 else "warning",
            "message": f"Found {course_count} courses" if course_count >= 3 else f"Only {course_count} courses found, expected at least 3"
        }
        
        # Check rules
        rule_count = db.query(Rule).count()
        verification_results["rules"] = {
            "count": rule_count,
            "status": "success" if rule_count >= 10 else "warning",
            "message": f"Found {rule_count} rules" if rule_count >= 10 else f"Only {rule_count} rules found, expected at least 10"
        }
        
        # Check AI personalities
        ai_player_count = (
            db.query(PlayerProfile)
            .filter(PlayerProfile.is_ai == 1)
            .count()
        )
        verification_results["ai_personalities"] = {
            "count": ai_player_count,
            "status": "success" if ai_player_count >= 4 else "warning",
            "message": f"Found {ai_player_count} AI personalities" if ai_player_count >= 4 else f"Only {ai_player_count} AI personalities found, expected at least 4"
        }
        
        # Check human players
        human_player_count = (
            db.query(PlayerProfile)
            .filter(PlayerProfile.is_ai == 0)
            .count()
        )
        verification_results["human_players"] = {
            "count": human_player_count,
            "status": "success" if human_player_count >= 1 else "info",
            "message": f"Found {human_player_count} human players" if human_player_count >= 1 else "No human players found (will use default)"
        }
        
        # Check sample games
        game_count = db.query(GameRecord).count()
        verification_results["sample_games"] = {
            "count": game_count,
            "status": "success" if game_count >= 1 else "info",
            "message": f"Found {game_count} sample games" if game_count >= 1 else "No sample games found"
        }
        
        # Overall status
        all_critical_success = all(
            result["status"] in ["success", "info"] 
            for key, result in verification_results.items()
            if key in ["courses", "rules", "ai_personalities"]
        )
        
        verification_results["overall"] = {
            "status": "success" if all_critical_success else "warning",
            "message": "All critical data seeded successfully" if all_critical_success else "Some critical data may be missing"
        }
        
    except Exception as e:
        logger.error(f"Error verifying seeded data: {e}")
        verification_results["overall"] = {
            "status": "error",
            "message": f"Verification failed: {str(e)}"
        }
    
    return verification_results

def seed_all_data(force_reseed: bool = False) -> dict:
    """
    Main seeding function that initializes all required data.
    
    Args:
        force_reseed: If True, will reseed data even if it already exists
    
    Returns:
        Dictionary with seeding results and statistics
    """
    logger.info("Starting comprehensive data seeding...")
    
    # Initialize database
    try:
        init_db()
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        return {"status": "error", "message": f"Database initialization failed: {str(e)}"}
    
    db = SessionLocal()
    seeding_results = {
        "status": "success",
        "timestamp": datetime.now().isoformat(),
        "results": {}
    }
    
    try:
        # Verify database connection
        if not verify_database_connection(db):
            raise Exception("Database connection verification failed")
        
        logger.info("Database connection verified successfully")
        
        # Seed courses
        logger.info("Seeding courses...")
        courses_added = seed_courses(db)
        seeding_results["results"]["courses"] = {
            "added": courses_added,
            "status": "success"
        }
        
        # Seed rules
        logger.info("Seeding rules...")
        rules_added = seed_rules(db)
        seeding_results["results"]["rules"] = {
            "added": rules_added,
            "status": "success"
        }
        
        # Seed AI personalities
        logger.info("Seeding AI personalities...")
        personalities_added = seed_ai_personalities(db)
        seeding_results["results"]["ai_personalities"] = {
            "added": personalities_added,
            "status": "success"
        }
        
        # Create default human player if needed
        logger.info("Creating default human player if needed...")
        default_human = create_default_human_player(db)
        seeding_results["results"]["default_human"] = {
            "created": default_human is not None,
            "status": "success"
        }
        
        # Seed sample games (optional)
        logger.info("Seeding sample games...")
        try:
            games_added = seed_sample_games(db)
            seeding_results["results"]["sample_games"] = {
                "added": games_added,
                "status": "success"
            }
        except Exception as e:
            logger.warning(f"Failed to seed sample games (non-critical): {e}")
            seeding_results["results"]["sample_games"] = {
                "added": 0,
                "status": "warning",
                "error": str(e)
            }
        
        # Verify all seeded data
        logger.info("Verifying seeded data...")
        verification_results = verify_seeded_data(db)
        seeding_results["verification"] = verification_results
        
        # Set overall status based on verification
        if verification_results["overall"]["status"] == "error":
            seeding_results["status"] = "error"
            seeding_results["message"] = "Critical seeding failures detected"
        elif verification_results["overall"]["status"] == "warning":
            seeding_results["status"] = "warning"
            seeding_results["message"] = "Seeding completed with warnings"
        else:
            seeding_results["message"] = "All data seeded successfully"
        
        logger.info(f"Data seeding completed with status: {seeding_results['status']}")
        
    except Exception as e:
        db.rollback()
        logger.error(f"Critical error during data seeding: {e}")
        seeding_results = {
            "status": "error",
            "message": f"Seeding failed: {str(e)}",
            "timestamp": datetime.now().isoformat(),
            "results": {}
        }
    
    finally:
        db.close()
    
    return seeding_results

def get_seeding_status() -> dict:
    """Get the current status of seeded data without re-seeding."""
    logger.debug("Checking seeding status...")
    
    db = SessionLocal()
    try:
        if not verify_database_connection(db):
            return {"status": "error", "message": "Database connection failed"}
        
        verification_results = verify_seeded_data(db)
        
        return {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "verification": verification_results
        }
        
    except Exception as e:
        logger.error(f"Error checking seeding status: {e}")
        return {
            "status": "error",
            "message": f"Status check failed: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }
    
    finally:
        db.close()

def main():
    """Command-line entry point for seeding script."""
    import sys
    
    # Configure logging for command-line usage
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    force_reseed = "--force" in sys.argv
    
    if "--status" in sys.argv:
        # Just check status
        status = get_seeding_status()
        print(f"Seeding Status: {status['status']}")
        if "verification" in status:
            for component, result in status["verification"].items():
                if component != "overall":
                    print(f"  {component}: {result['message']}")
        sys.exit(0 if status["status"] == "success" else 1)
    
    # Run full seeding
    results = seed_all_data(force_reseed=force_reseed)
    
    print(f"Seeding Results: {results['status']}")
    print(f"Message: {results.get('message', 'No message')}")
    
    if "results" in results:
        print("\nComponent Results:")
        for component, result in results["results"].items():
            print(f"  {component}: {result.get('added', 0)} added, status: {result['status']}")
    
    if "verification" in results:
        print("\nVerification Results:")
        for component, result in results["verification"].items():
            if component != "overall":
                print(f"  {component}: {result['message']}")
    
    sys.exit(0 if results["status"] in ["success", "warning"] else 1)

if __name__ == "__main__":
    main()

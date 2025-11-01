"""
Badge System Seeds - Initialize all badges in the database
Run this script to populate the badge system with all available badges.
"""

from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from .models import NFTBadge, BadgeSeries, SeasonalBadge
from .database import SessionLocal

def seed_badges(db: Session):
    """Seed all badges into the database"""

    # Clear existing badges if reseeding
    # db.query(NFTBadge).delete()
    # db.query(BadgeSeries).delete()
    # db.query(SeasonalBadge).delete()
    # db.commit()

    badge_id_counter = 1
    created_at = datetime.utcnow().isoformat()

    # ====================================================================================
    # ACHIEVEMENT BADGES - One-Time Unlocks
    # ====================================================================================

    achievement_badges = []

    # Solo Mastery Series
    achievement_badges.append({
        'badge_id': badge_id_counter,
        'name': 'Lone Wolf',
        'description': 'Win your first solo hole (1v3)',
        'category': 'achievement',
        'rarity': 'common',
        'image_url': '/badges/lone-wolf.png',
        'trigger_condition': {'type': 'first_solo_win'},
        'trigger_type': 'one_time',
        'max_supply': None,
        'points_value': 10,
        'is_active': True,
        'created_at': created_at
    })
    badge_id_counter += 1

    achievement_badges.append({
        'badge_id': badge_id_counter,
        'name': 'Alpha Predator',
        'description': 'Win 3 consecutive solo holes in one game',
        'category': 'achievement',
        'rarity': 'rare',
        'image_url': '/badges/alpha-predator.png',
        'trigger_condition': {'type': 'triple_solo_streak'},
        'trigger_type': 'one_time',
        'max_supply': None,
        'points_value': 50,
        'is_active': True,
        'created_at': created_at
    })
    badge_id_counter += 1

    achievement_badges.append({
        'badge_id': badge_id_counter,
        'name': 'Wolf Pack Leader',
        'description': 'Win 50 solo holes (career)',
        'category': 'achievement',
        'rarity': 'epic',
        'image_url': '/badges/wolf-pack-leader.png',
        'trigger_condition': {'type': 'career_solo_50'},
        'trigger_type': 'one_time',
        'max_supply': 10000,
        'points_value': 100,
        'is_active': True,
        'created_at': created_at
    })
    badge_id_counter += 1

    achievement_badges.append({
        'badge_id': badge_id_counter,
        'name': 'Apex Lone Wolf',
        'description': 'Win a game going solo on every hole',
        'category': 'achievement',
        'rarity': 'legendary',
        'image_url': '/badges/apex-lone-wolf.png',
        'trigger_condition': {'type': 'solo_all_18'},
        'trigger_type': 'one_time',
        'max_supply': 1000,
        'points_value': 500,
        'is_active': True,
        'created_at': created_at
    })
    badge_id_counter += 1

    # Partnership Excellence
    achievement_badges.append({
        'badge_id': badge_id_counter,
        'name': 'Dynamic Duo',
        'description': 'Win 5 partnership holes with same partner',
        'category': 'achievement',
        'rarity': 'common',
        'image_url': '/badges/dynamic-duo.png',
        'trigger_condition': {'type': 'first_partnership'},
        'trigger_type': 'one_time',
        'max_supply': None,
        'points_value': 10,
        'is_active': True,
        'created_at': created_at
    })
    badge_id_counter += 1

    achievement_badges.append({
        'badge_id': badge_id_counter,
        'name': 'Perfect Partnership',
        'description': '100% partnership success rate (minimum 10 holes)',
        'category': 'achievement',
        'rarity': 'rare',
        'image_url': '/badges/perfect-partnership.png',
        'trigger_condition': {'type': 'perfect_partnership_rate'},
        'trigger_type': 'one_time',
        'max_supply': None,
        'points_value': 50,
        'is_active': True,
        'created_at': created_at
    })
    badge_id_counter += 1

    # Betting Brilliance
    achievement_badges.append({
        'badge_id': badge_id_counter,
        'name': 'High Roller',
        'description': 'Accept 5 doubles in a single game',
        'category': 'achievement',
        'rarity': 'common',
        'image_url': '/badges/high-roller.png',
        'trigger_condition': {'type': 'high_roller'},
        'trigger_type': 'one_time',
        'max_supply': None,
        'points_value': 20,
        'is_active': True,
        'created_at': created_at
    })
    badge_id_counter += 1

    achievement_badges.append({
        'badge_id': badge_id_counter,
        'name': 'Pressure Player',
        'description': 'Win a redoubled hole (4x+ wager)',
        'category': 'achievement',
        'rarity': 'rare',
        'image_url': '/badges/pressure-player.png',
        'trigger_condition': {'type': 'win_redoubled'},
        'trigger_type': 'one_time',
        'max_supply': None,
        'points_value': 50,
        'is_active': True,
        'created_at': created_at
    })
    badge_id_counter += 1

    achievement_badges.append({
        'badge_id': badge_id_counter,
        'name': 'The Gambler',
        'description': 'Win 100 quarters in a single game',
        'category': 'achievement',
        'rarity': 'epic',
        'image_url': '/badges/the-gambler.png',
        'trigger_condition': {'type': 'big_earner_100'},
        'trigger_type': 'one_time',
        'max_supply': 10000,
        'points_value': 100,
        'is_active': True,
        'created_at': created_at
    })
    badge_id_counter += 1

    achievement_badges.append({
        'badge_id': badge_id_counter,
        'name': "Karl Marx's Favorite",
        'description': 'Receive 50 quarters via Karl Marx rule (career)',
        'category': 'achievement',
        'rarity': 'rare',
        'image_url': '/badges/karl-marx-favorite.png',
        'trigger_condition': {'type': 'karl_marx_50', 'target': 50},
        'trigger_type': 'one_time',
        'max_supply': None,
        'points_value': 75,
        'is_active': True,
        'created_at': created_at
    })
    badge_id_counter += 1

    # Rare Events
    achievement_badges.append({
        'badge_id': badge_id_counter,
        'name': 'Unicorn',
        'description': 'Make a hole-in-one',
        'category': 'rare_event',
        'rarity': 'mythic',
        'image_url': '/badges/unicorn.png',
        'trigger_condition': {'type': 'hole_in_one'},
        'trigger_type': 'one_time',
        'max_supply': 100,
        'points_value': 1000,
        'is_active': True,
        'created_at': created_at
    })
    badge_id_counter += 1

    achievement_badges.append({
        'badge_id': badge_id_counter,
        'name': 'Perfect Game',
        'description': 'Win every hole in a game',
        'category': 'rare_event',
        'rarity': 'legendary',
        'image_url': '/badges/perfect-game.png',
        'trigger_condition': {'type': 'perfect_game'},
        'trigger_type': 'one_time',
        'max_supply': 1000,
        'points_value': 500,
        'is_active': True,
        'created_at': created_at
    })
    badge_id_counter += 1

    achievement_badges.append({
        'badge_id': badge_id_counter,
        'name': 'Lazarus',
        'description': 'Come back from 20+ quarters down to win',
        'category': 'rare_event',
        'rarity': 'epic',
        'image_url': '/badges/lazarus.png',
        'trigger_condition': {'type': 'comeback_20'},
        'trigger_type': 'one_time',
        'max_supply': 5000,
        'points_value': 200,
        'is_active': True,
        'created_at': created_at
    })
    badge_id_counter += 1

    # Add all achievement badges
    for badge_data in achievement_badges:
        badge = NFTBadge(**badge_data)
        db.add(badge)

    # ====================================================================================
    # PROGRESSION BADGES - Career Milestones
    # ====================================================================================

    # Career Earnings Tiers
    earnings_tiers = [
        {'tier': 0, 'name': 'Bronze Earner', 'threshold': 100, 'rarity': 'common'},
        {'tier': 1, 'name': 'Silver Earner', 'threshold': 500, 'rarity': 'rare'},
        {'tier': 2, 'name': 'Gold Earner', 'threshold': 2000, 'rarity': 'epic'},
        {'tier': 3, 'name': 'Platinum Earner', 'threshold': 10000, 'rarity': 'legendary'},
        {'tier': 4, 'name': 'Diamond Earner', 'threshold': 50000, 'rarity': 'mythic'},
    ]

    for tier_data in earnings_tiers:
        badge = NFTBadge(
            badge_id=badge_id_counter,
            name=tier_data['name'],
            description=f"Earn {tier_data['threshold']} quarters (career)",
            category='progression',
            rarity=tier_data['rarity'],
            image_url=f"/badges/earnings-{tier_data['tier']}.png",
            trigger_condition={
                'type': 'earnings_milestone',
                'earnings_threshold': tier_data['threshold']
            },
            trigger_type='career_milestone',
            max_supply=None,
            points_value=tier_data['threshold'] // 10,
            tier=tier_data['tier'],
            is_active=True,
            created_at=created_at
        )
        db.add(badge)
        badge_id_counter += 1

    # Games Played Tiers
    games_tiers = [
        {'tier': 0, 'name': 'Rookie', 'threshold': 10, 'rarity': 'common'},
        {'tier': 1, 'name': 'Journeyman', 'threshold': 50, 'rarity': 'rare'},
        {'tier': 2, 'name': 'Veteran', 'threshold': 200, 'rarity': 'epic'},
        {'tier': 3, 'name': 'Legend', 'threshold': 500, 'rarity': 'legendary'},
        {'tier': 4, 'name': 'Immortal', 'threshold': 1000, 'rarity': 'mythic'},
    ]

    for tier_data in games_tiers:
        badge = NFTBadge(
            badge_id=badge_id_counter,
            name=tier_data['name'],
            description=f"Play {tier_data['threshold']} games",
            category='progression',
            rarity=tier_data['rarity'],
            image_url=f"/badges/games-{tier_data['tier']}.png",
            trigger_condition={
                'type': 'games_played_milestone',
                'games_threshold': tier_data['threshold']
            },
            trigger_type='career_milestone',
            max_supply=None,
            points_value=tier_data['threshold'] * 2,
            tier=tier_data['tier'],
            is_active=True,
            created_at=created_at
        )
        db.add(badge)
        badge_id_counter += 1

    # Holes Won Tiers
    holes_tiers = [
        {'tier': 0, 'name': 'Scrapper', 'threshold': 50, 'rarity': 'common'},
        {'tier': 1, 'name': 'Competitor', 'threshold': 250, 'rarity': 'rare'},
        {'tier': 2, 'name': 'Champion', 'threshold': 1000, 'rarity': 'epic'},
        {'tier': 3, 'name': 'Dominator', 'threshold': 5000, 'rarity': 'legendary'},
        {'tier': 4, 'name': 'Untouchable', 'threshold': 20000, 'rarity': 'mythic'},
    ]

    for tier_data in holes_tiers:
        badge = NFTBadge(
            badge_id=badge_id_counter,
            name=tier_data['name'],
            description=f"Win {tier_data['threshold']} holes",
            category='progression',
            rarity=tier_data['rarity'],
            image_url=f"/badges/holes-{tier_data['tier']}.png",
            trigger_condition={
                'type': 'holes_won_milestone',
                'holes_threshold': tier_data['threshold']
            },
            trigger_type='career_milestone',
            max_supply=None,
            points_value=tier_data['threshold'] // 5,
            tier=tier_data['tier'],
            is_active=True,
            created_at=created_at
        )
        db.add(badge)
        badge_id_counter += 1

    # Win Rate Badges
    winrate_badges = [
        {'name': 'Iron Will', 'rate': 0.40, 'rarity': 'rare'},
        {'name': 'Consistent Crusher', 'rate': 0.50, 'rarity': 'epic'},
        {'name': 'Dominance', 'rate': 0.60, 'rarity': 'legendary'},
        {'name': 'Godlike', 'rate': 0.70, 'rarity': 'mythic'},
    ]

    for wr_data in winrate_badges:
        badge = NFTBadge(
            badge_id=badge_id_counter,
            name=wr_data['name'],
            description=f"{int(wr_data['rate']*100)}% win rate (minimum 100 holes played)",
            category='progression',
            rarity=wr_data['rarity'],
            image_url=f"/badges/winrate-{int(wr_data['rate']*100)}.png",
            trigger_condition={
                'type': 'win_rate_badge',
                'win_rate': wr_data['rate']
            },
            trigger_type='career_milestone',
            max_supply=None,
            points_value=int(wr_data['rate'] * 1000),
            is_active=True,
            created_at=created_at
        )
        db.add(badge)
        badge_id_counter += 1

    # ====================================================================================
    # COLLECTIBLE SERIES - Four Horsemen
    # ====================================================================================

    # Create the series first
    four_horsemen_series = BadgeSeries(
        name='Four Horsemen',
        description='Collect all four badges to unlock Apocalypse Master',
        category='collectible',
        badge_count=4,
        completion_badge_id=None,  # Will set after creating badges
        image_url='/badges/series-four-horsemen.png',
        is_active=True,
        created_at=created_at
    )
    db.add(four_horsemen_series)
    db.commit()
    db.refresh(four_horsemen_series)

    # Four Horsemen Badges
    horsemen_badges = []

    horsemen_badges.append(NFTBadge(
        badge_id=badge_id_counter,
        name='War',
        description='Win 10 redoubled holes (career)',
        category='collectible_series',
        rarity='epic',
        image_url='/badges/horseman-war.png',
        trigger_condition={'type': 'four_horsemen_war', 'target': 10},
        trigger_type='one_time',
        max_supply=None,
        points_value=150,
        series_id=four_horsemen_series.id,
        is_active=True,
        created_at=created_at
    ))
    badge_id_counter += 1

    horsemen_badges.append(NFTBadge(
        badge_id=badge_id_counter,
        name='Famine',
        description='Bankrupt an opponent (reduce to -50 quarters)',
        category='collectible_series',
        rarity='epic',
        image_url='/badges/horseman-famine.png',
        trigger_condition={'type': 'four_horsemen_famine'},
        trigger_type='one_time',
        max_supply=None,
        points_value=150,
        series_id=four_horsemen_series.id,
        is_active=True,
        created_at=created_at
    ))
    badge_id_counter += 1

    horsemen_badges.append(NFTBadge(
        badge_id=badge_id_counter,
        name='Pestilence',
        description='Win 5 games in a row',
        category='collectible_series',
        rarity='epic',
        image_url='/badges/horseman-pestilence.png',
        trigger_condition={'type': 'four_horsemen_pestilence'},
        trigger_type='one_time',
        max_supply=None,
        points_value=150,
        series_id=four_horsemen_series.id,
        is_active=True,
        created_at=created_at
    ))
    badge_id_counter += 1

    horsemen_badges.append(NFTBadge(
        badge_id=badge_id_counter,
        name='Death',
        description='Eliminate all 3 opponents in solo mode',
        category='collectible_series',
        rarity='epic',
        image_url='/badges/horseman-death.png',
        trigger_condition={'type': 'four_horsemen_death'},
        trigger_type='one_time',
        max_supply=None,
        points_value=150,
        series_id=four_horsemen_series.id,
        is_active=True,
        created_at=created_at
    ))
    badge_id_counter += 1

    for badge in horsemen_badges:
        db.add(badge)

    # Create completion badge
    apocalypse_master = NFTBadge(
        badge_id=badge_id_counter,
        name='Apocalypse Master',
        description='Completed the Four Horsemen collection',
        category='collectible_series',
        rarity='legendary',
        image_url='/badges/apocalypse-master.png',
        trigger_condition={'type': 'series_completion', 'series_id': four_horsemen_series.id},
        trigger_type='series_completion',
        max_supply=None,
        points_value=750,
        series_id=four_horsemen_series.id,
        is_active=True,
        created_at=created_at
    )
    db.add(apocalypse_master)
    db.commit()
    db.refresh(apocalypse_master)

    # Update series with completion badge
    four_horsemen_series.completion_badge_id = apocalypse_master.id
    db.commit()
    badge_id_counter += 1

    # ====================================================================================
    # SEASONAL BADGES
    # ====================================================================================

    # Example: New Year Dominator (January 2026)
    new_year_badge = NFTBadge(
        badge_id=badge_id_counter,
        name='New Year Dominator',
        description='Win 15 games during January 2026',
        category='seasonal',
        rarity='rare',
        image_url='/badges/new-year-2026.png',
        trigger_condition={'type': 'monthly_challenge', 'games_won': 15, 'month': 1, 'year': 2026},
        trigger_type='seasonal',
        max_supply=1000,
        points_value=100,
        is_active=True,
        created_at=created_at
    )
    db.add(new_year_badge)
    db.commit()
    db.refresh(new_year_badge)

    # Create seasonal badge entry
    seasonal_entry = SeasonalBadge(
        badge_id=new_year_badge.id,
        season_name='January 2026',
        start_date='2026-01-01',
        end_date='2026-01-31',
        is_active=False,  # Activate when ready
        max_earners=1000,
        current_earners=0,
        created_at=created_at
    )
    db.add(seasonal_entry)
    badge_id_counter += 1

    db.commit()

    print(f"✅ Successfully seeded {badge_id_counter - 1} badges!")
    print(f"   - Achievement badges: {len(achievement_badges)}")
    print(f"   - Progression badges: {len(earnings_tiers) + len(games_tiers) + len(holes_tiers) + len(winrate_badges)}")
    print(f"   - Four Horsemen series: 5 badges (4 + completion)")
    print(f"   - Seasonal badges: 1")


def run_seed():
    """Standalone function to run the seed"""
    db = SessionLocal()
    try:
        seed_badges(db)
    except Exception as e:
        print(f"❌ Error seeding badges: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    run_seed()

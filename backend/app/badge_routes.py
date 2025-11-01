"""
API Routes for NFT Badge System
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime

from .database import get_db
from .models import (
    NFTBadge, PlayerBadgeEarned, BadgeProgress, BadgeSeries,
    PlayerSeriesProgress, SeasonalBadge, WalletConnection,
    PlayerProfile, PlayerStatistics
)
from .badge_engine import BadgeEngine

router = APIRouter(prefix="/api/badges", tags=["badges"])


# ====================================================================================
# PYDANTIC MODELS (Request/Response Schemas)
# ====================================================================================

class BadgeResponse(BaseModel):
    id: int
    badge_id: int
    name: str
    description: str
    category: str
    rarity: str
    image_url: Optional[str]
    max_supply: Optional[int]
    current_supply: int
    points_value: int
    tier: Optional[int]
    series_id: Optional[int]

    class Config:
        from_attributes = True


class EarnedBadgeResponse(BaseModel):
    id: int
    badge: BadgeResponse
    earned_at: str
    serial_number: int
    is_minted: bool
    transaction_hash: Optional[str]
    wallet_address: Optional[str]
    game_record_id: Optional[int]

    class Config:
        from_attributes = True


class BadgeProgressResponse(BaseModel):
    badge: BadgeResponse
    current_progress: int
    target_progress: int
    progress_percentage: float
    last_progress_date: Optional[str]

    class Config:
        from_attributes = True


class SeriesResponse(BaseModel):
    id: int
    name: str
    description: str
    badge_count: int
    badges_earned: int
    is_completed: bool
    completion_badge: Optional[BadgeResponse]

    class Config:
        from_attributes = True


class WalletConnectRequest(BaseModel):
    wallet_address: str
    wallet_type: str = "metamask"
    verification_signature: str


class MintBadgeRequest(BaseModel):
    badge_earned_id: int
    wallet_address: str


class BadgeLeaderboardEntry(BaseModel):
    player_id: int
    player_name: str
    serial_number: int
    earned_at: str
    is_minted: bool


# ====================================================================================
# BADGE DISCOVERY ENDPOINTS
# ====================================================================================

@router.get("/available", response_model=List[BadgeResponse])
def get_available_badges(
    category: Optional[str] = None,
    rarity: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get all available badges with optional filtering.
    Query params:
    - category: achievement, progression, seasonal, rare_event, collectible_series
    - rarity: common, rare, epic, legendary, mythic
    """
    query = db.query(NFTBadge).filter(NFTBadge.is_active == True)

    if category:
        query = query.filter(NFTBadge.category == category)

    if rarity:
        query = query.filter(NFTBadge.rarity == rarity)

    badges = query.order_by(
        # Sort by rarity tier, then by name
        func.case(
            (NFTBadge.rarity == 'mythic', 5),
            (NFTBadge.rarity == 'legendary', 4),
            (NFTBadge.rarity == 'epic', 3),
            (NFTBadge.rarity == 'rare', 2),
            else_=1
        ).desc(),
        NFTBadge.name
    ).all()

    return badges


@router.get("/player/{player_id}/earned", response_model=List[EarnedBadgeResponse])
def get_player_earned_badges(
    player_id: int,
    showcase_only: bool = False,
    db: Session = Depends(get_db)
):
    """
    Get all badges earned by a player.
    - showcase_only: Return only badges in player's showcase (top 6)
    """
    query = db.query(PlayerBadgeEarned).filter(
        PlayerBadgeEarned.player_profile_id == player_id
    )

    if showcase_only:
        query = query.filter(PlayerBadgeEarned.showcase_position.isnot(None))

    earned_badges = query.order_by(
        PlayerBadgeEarned.earned_at.desc()
    ).all()

    # Enrich with badge details
    result = []
    for earned in earned_badges:
        badge = db.query(NFTBadge).filter_by(id=earned.badge_id).first()
        if badge:
            result.append({
                **earned.__dict__,
                'badge': badge
            })

    return result


@router.get("/player/{player_id}/progress", response_model=List[BadgeProgressResponse])
def get_player_badge_progress(
    player_id: int,
    include_completed: bool = False,
    db: Session = Depends(get_db)
):
    """
    Get player's progress toward unearned badges.
    - include_completed: Include badges already earned
    """
    # Get all progression badges
    progress_records = db.query(BadgeProgress).filter(
        BadgeProgress.player_profile_id == player_id
    ).all()

    result = []
    for progress in progress_records:
        # Check if already earned
        if not include_completed:
            has_badge = db.query(PlayerBadgeEarned).filter(
                and_(
                    PlayerBadgeEarned.player_profile_id == player_id,
                    PlayerBadgeEarned.badge_id == progress.badge_id
                )
            ).first()
            if has_badge:
                continue

        badge = db.query(NFTBadge).filter_by(id=progress.badge_id).first()
        if badge:
            result.append({
                'badge': badge,
                'current_progress': progress.current_progress,
                'target_progress': progress.target_progress,
                'progress_percentage': progress.progress_percentage,
                'last_progress_date': progress.last_progress_date
            })

    return result


@router.get("/player/{player_id}/stats")
def get_player_badge_stats(player_id: int, db: Session = Depends(get_db)):
    """Get summary statistics about player's badge collection"""
    earned_count = db.query(PlayerBadgeEarned).filter(
        PlayerBadgeEarned.player_profile_id == player_id
    ).count()

    # Count by rarity
    rarity_counts = db.query(
        NFTBadge.rarity,
        func.count(PlayerBadgeEarned.id)
    ).join(
        PlayerBadgeEarned,
        NFTBadge.id == PlayerBadgeEarned.badge_id
    ).filter(
        PlayerBadgeEarned.player_profile_id == player_id
    ).group_by(NFTBadge.rarity).all()

    # Count by category
    category_counts = db.query(
        NFTBadge.category,
        func.count(PlayerBadgeEarned.id)
    ).join(
        PlayerBadgeEarned,
        NFTBadge.id == PlayerBadgeEarned.badge_id
    ).filter(
        PlayerBadgeEarned.player_profile_id == player_id
    ).group_by(NFTBadge.category).all()

    # Count minted badges
    minted_count = db.query(PlayerBadgeEarned).filter(
        and_(
            PlayerBadgeEarned.player_profile_id == player_id,
            PlayerBadgeEarned.is_minted == True
        )
    ).count()

    # Total badges available
    total_available = db.query(NFTBadge).filter(NFTBadge.is_active == True).count()

    return {
        'total_earned': earned_count,
        'total_available': total_available,
        'completion_percentage': (earned_count / total_available * 100) if total_available > 0 else 0,
        'minted_count': minted_count,
        'by_rarity': {r: c for r, c in rarity_counts},
        'by_category': {cat: c for cat, c in category_counts}
    }


# ====================================================================================
# SERIES / COLLECTION ENDPOINTS
# ====================================================================================

@router.get("/series", response_model=List[SeriesResponse])
def get_badge_series(db: Session = Depends(get_db)):
    """Get all badge series/collections"""
    series_list = db.query(BadgeSeries).filter(
        BadgeSeries.is_active == True
    ).all()

    result = []
    for series in series_list:
        # Get completion badge if exists
        completion_badge = None
        if series.completion_badge_id:
            completion_badge = db.query(NFTBadge).filter_by(
                id=series.completion_badge_id
            ).first()

        result.append({
            **series.__dict__,
            'badges_earned': 0,  # Will be filled by player-specific endpoint
            'is_completed': False,
            'completion_badge': completion_badge
        })

    return result


@router.get("/series/player/{player_id}", response_model=List[SeriesResponse])
def get_player_series_progress(player_id: int, db: Session = Depends(get_db)):
    """Get player's progress on all badge series"""
    series_list = db.query(BadgeSeries).filter(
        BadgeSeries.is_active == True
    ).all()

    result = []
    for series in series_list:
        # Get player's progress
        progress = db.query(PlayerSeriesProgress).filter(
            and_(
                PlayerSeriesProgress.player_profile_id == player_id,
                PlayerSeriesProgress.series_id == series.id
            )
        ).first()

        # Get completion badge
        completion_badge = None
        if series.completion_badge_id:
            completion_badge = db.query(NFTBadge).filter_by(
                id=series.completion_badge_id
            ).first()

        result.append({
            **series.__dict__,
            'badges_earned': progress.badges_earned if progress else 0,
            'is_completed': progress.is_completed if progress else False,
            'completion_badge': completion_badge
        })

    return result


# ====================================================================================
# LEADERBOARD ENDPOINTS
# ====================================================================================

@router.get("/leaderboard/badge/{badge_id}", response_model=List[BadgeLeaderboardEntry])
def get_badge_leaderboard(badge_id: int, limit: int = 100, db: Session = Depends(get_db)):
    """
    Get leaderboard for a specific badge (who has it, serial numbers).
    Useful for rare badges to see who the elite owners are.
    """
    badge = db.query(NFTBadge).filter_by(id=badge_id).first()
    if not badge:
        raise HTTPException(status_code=404, detail="Badge not found")

    earned_records = db.query(
        PlayerBadgeEarned, PlayerProfile.name
    ).join(
        PlayerProfile,
        PlayerBadgeEarned.player_profile_id == PlayerProfile.id
    ).filter(
        PlayerBadgeEarned.badge_id == badge_id
    ).order_by(
        PlayerBadgeEarned.serial_number.asc()
    ).limit(limit).all()

    result = []
    for earned, player_name in earned_records:
        result.append({
            'player_id': earned.player_profile_id,
            'player_name': player_name,
            'serial_number': earned.serial_number,
            'earned_at': earned.earned_at,
            'is_minted': earned.is_minted
        })

    return result


@router.get("/leaderboard/top-collectors")
def get_top_collectors(limit: int = 50, db: Session = Depends(get_db)):
    """Get players with most badges earned"""
    top_collectors = db.query(
        PlayerProfile.id,
        PlayerProfile.name,
        func.count(PlayerBadgeEarned.id).label('badge_count')
    ).join(
        PlayerBadgeEarned,
        PlayerProfile.id == PlayerBadgeEarned.player_profile_id
    ).group_by(
        PlayerProfile.id,
        PlayerProfile.name
    ).order_by(
        desc('badge_count')
    ).limit(limit).all()

    result = []
    for player_id, player_name, badge_count in top_collectors:
        # Get rarity breakdown
        rarity_counts = db.query(
            NFTBadge.rarity,
            func.count(PlayerBadgeEarned.id)
        ).join(
            PlayerBadgeEarned,
            NFTBadge.id == PlayerBadgeEarned.badge_id
        ).filter(
            PlayerBadgeEarned.player_profile_id == player_id
        ).group_by(NFTBadge.rarity).all()

        result.append({
            'player_id': player_id,
            'player_name': player_name,
            'total_badges': badge_count,
            'by_rarity': {r: c for r, c in rarity_counts}
        })

    return result


# ====================================================================================
# WALLET & MINTING ENDPOINTS
# ====================================================================================

@router.post("/wallet/connect")
def connect_wallet(request: WalletConnectRequest, db: Session = Depends(get_db)):
    """
    Connect a Web3 wallet to a player profile.
    Requires signature verification.
    """
    # Note: In production, verify the signature here
    # For now, we'll accept the request

    # Check if wallet already connected
    existing = db.query(WalletConnection).filter_by(
        wallet_address=request.wallet_address.lower()
    ).first()

    if existing:
        if not existing.is_active:
            existing.is_active = True
            existing.updated_at = datetime.utcnow().isoformat()
            db.commit()
        return {"message": "Wallet already connected", "wallet_connection": existing}

    # Create new wallet connection
    # Note: player_profile_id should come from authenticated session
    # For now, we'll leave it to be set later
    connection = WalletConnection(
        wallet_address=request.wallet_address.lower(),
        wallet_type=request.wallet_type,
        is_verified=True,  # Would verify signature in production
        verification_signature=request.verification_signature,
        last_verified_at=datetime.utcnow().isoformat(),
        connected_at=datetime.utcnow().isoformat(),
        is_active=True,
        created_at=datetime.utcnow().isoformat()
    )

    db.add(connection)
    db.commit()
    db.refresh(connection)

    return {"message": "Wallet connected successfully", "wallet_connection": connection}


@router.get("/wallet/player/{player_id}")
def get_player_wallet(player_id: int, db: Session = Depends(get_db)):
    """Get wallet connection for a player"""
    wallet = db.query(WalletConnection).filter_by(
        player_profile_id=player_id,
        is_active=True
    ).first()

    if not wallet:
        return {"connected": False, "wallet_address": None}

    return {
        "connected": True,
        "wallet_address": wallet.wallet_address,
        "wallet_type": wallet.wallet_type,
        "connected_at": wallet.connected_at
    }


@router.post("/mint")
def mint_badge(request: MintBadgeRequest, db: Session = Depends(get_db)):
    """
    Mint an earned badge to the blockchain.
    This endpoint would be called by the frontend after wallet transaction completes.
    """
    earned_badge = db.query(PlayerBadgeEarned).filter_by(
        id=request.badge_earned_id
    ).first()

    if not earned_badge:
        raise HTTPException(status_code=404, detail="Badge not found")

    if earned_badge.is_minted:
        raise HTTPException(status_code=400, detail="Badge already minted")

    # In production, this would:
    # 1. Call smart contract to mint NFT
    # 2. Wait for transaction confirmation
    # 3. Update database with transaction hash

    # For now, we'll just mark as minted
    earned_badge.is_minted = True
    earned_badge.wallet_address = request.wallet_address.lower()
    earned_badge.transaction_hash = "0x" + "0" * 64  # Placeholder
    earned_badge.updated_at = datetime.utcnow().isoformat()

    db.commit()

    return {
        "message": "Badge minted successfully",
        "transaction_hash": earned_badge.transaction_hash
    }


# ====================================================================================
# ADMIN ENDPOINTS (Badge Management)
# ====================================================================================

@router.post("/admin/check-achievements/{player_id}")
def manually_check_achievements(
    player_id: int,
    game_record_id: int,
    db: Session = Depends(get_db)
):
    """
    Manually trigger badge achievement check for a player/game.
    Useful for testing or retroactive badge awards.
    """
    engine = BadgeEngine(db)
    earned_badges = engine.check_post_game_achievements(game_record_id, player_id)

    return {
        "message": f"Found {len(earned_badges)} new badges",
        "badges": [
            {
                "badge_id": b.badge_id,
                "serial_number": b.serial_number,
                "earned_at": b.earned_at
            }
            for b in earned_badges
        ]
    }


@router.get("/admin/badge/{badge_id}/holders")
def get_badge_holders(badge_id: int, db: Session = Depends(get_db)):
    """Get detailed information about who holds a specific badge"""
    holders = db.query(
        PlayerBadgeEarned, PlayerProfile.name, PlayerProfile.email
    ).join(
        PlayerProfile,
        PlayerBadgeEarned.player_profile_id == PlayerProfile.id
    ).filter(
        PlayerBadgeEarned.badge_id == badge_id
    ).order_by(
        PlayerBadgeEarned.serial_number.asc()
    ).all()

    return {
        "badge_id": badge_id,
        "total_holders": len(holders),
        "holders": [
            {
                "player_id": h[0].player_profile_id,
                "player_name": h[1],
                "player_email": h[2],
                "serial_number": h[0].serial_number,
                "earned_at": h[0].earned_at,
                "is_minted": h[0].is_minted,
                "transaction_hash": h[0].transaction_hash
            }
            for h in holders
        ]
    }

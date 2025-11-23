"""
Simple in-memory caching for expensive operations.

For production, consider using Redis for distributed caching.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

logger = logging.getLogger("app.caching")


class SimpleCache:
    """
    Time-based in-memory cache.

    Each cached item has a TTL (time-to-live) and is automatically invalidated
    after that period.
    """

    def __init__(self, default_ttl_seconds: int = 3600):
        """
        Initialize cache.

        Args:
            default_ttl_seconds: Default time-to-live in seconds (default: 1 hour)
        """
        self.cache: Dict[str, tuple[Any, datetime]] = {}
        self.default_ttl = timedelta(seconds=default_ttl_seconds)
        self.hits = 0
        self.misses = 0

    def get(self, key: str) -> Optional[Any]:
        """
        Retrieve value from cache if not expired.

        Args:
            key: Cache key

        Returns:
            Cached value if exists and not expired, None otherwise
        """
        if key not in self.cache:
            self.misses += 1
            logger.debug(f"Cache MISS for key: {key}")
            return None

        value, timestamp = self.cache[key]
        age = datetime.now() - timestamp

        if age >= self.default_ttl:
            # Expired, remove from cache
            del self.cache[key]
            self.misses += 1
            logger.debug(f"Cache EXPIRED for key: {key} (age: {age.seconds}s)")
            return None

        self.hits += 1
        remaining_ttl = self.default_ttl - age
        logger.debug(
            f"Cache HIT for key: {key} "
            f"(age: {age.seconds}s, remaining TTL: {remaining_ttl.seconds}s)"
        )
        return value

    def set(self, key: str, value: Any) -> None:
        """
        Store value in cache with current timestamp.

        Args:
            key: Cache key
            value: Value to cache
        """
        self.cache[key] = (value, datetime.now())
        logger.debug(f"Cache SET for key: {key}")

    def invalidate(self, key: str) -> None:
        """
        Manually invalidate a cache entry.

        Args:
            key: Cache key to invalidate
        """
        if key in self.cache:
            del self.cache[key]
            logger.info(f"Cache INVALIDATED for key: {key}")

    def clear(self):
        """Clear all cache entries."""
        count = len(self.cache)
        self.cache.clear()
        self.hits = 0
        self.misses = 0
        logger.info(f"Cache CLEARED ({count} entries removed)")

    def cleanup_expired(self):
        """Remove all expired entries from cache."""
        now = datetime.now()
        expired_keys = [
            key for key, (_, timestamp) in self.cache.items()
            if now - timestamp >= self.default_ttl
        ]

        for key in expired_keys:
            del self.cache[key]

        if expired_keys:
            logger.info(f"Cache cleanup: removed {len(expired_keys)} expired entries")

    def get_stats(self) -> Dict:
        """Get cache statistics."""
        total_requests = self.hits + self.misses
        hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0

        return {
            "total_entries": len(self.cache),
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate_percent": round(hit_rate, 2),
            "ttl_seconds": self.default_ttl.seconds,
            "entries": list(self.cache.keys())
        }


# Global cache instances for different use cases
sheet_sync_cache = SimpleCache(default_ttl_seconds=3600)  # 1 hour for sheet sync
analytics_cache = SimpleCache(default_ttl_seconds=300)    # 5 minutes for analytics
leaderboard_cache = SimpleCache(default_ttl_seconds=600)  # 10 minutes for leaderboards

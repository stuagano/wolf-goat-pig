"""Time helpers."""

from datetime import UTC, date, datetime
from zoneinfo import ZoneInfo

# The club plays on Bainbridge Island, WA; "today" for sign-ups is Pacific time.
CLUB_TZ = ZoneInfo("America/Los_Angeles")


def club_today() -> date:
    """Today's date at the club (Pacific), not the UTC server's date."""
    return datetime.now(CLUB_TZ).date()


def utc_now() -> datetime:
    # Naive UTC datetime. Naive (no tzinfo) so .isoformat() produces the
    # `YYYY-MM-DDTHH:MM:SS.ffffff` format that existing stored timestamps
    # use, keeping lexicographic comparisons against historical records
    # correct. Always returns UTC regardless of host timezone, replacing
    # callers of the bare datetime.now() / datetime.utcnow() that drifted
    # with the server's local TZ.
    return datetime.now(UTC).replace(tzinfo=None)

"""Time helpers."""

from datetime import UTC, datetime


def utc_now() -> datetime:
    # Naive UTC datetime. Naive (no tzinfo) so .isoformat() produces the
    # `YYYY-MM-DDTHH:MM:SS.ffffff` format that existing stored timestamps
    # use, keeping lexicographic comparisons against historical records
    # correct. Always returns UTC regardless of host timezone, replacing
    # callers of the bare datetime.now() / datetime.utcnow() that drifted
    # with the server's local TZ.
    return datetime.now(UTC).replace(tzinfo=None)

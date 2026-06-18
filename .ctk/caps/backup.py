from __future__ import annotations

import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Union


KEEP_BACKUPS = 5


def _prune_backups(path: Path, keep: int = KEEP_BACKUPS) -> None:
    """Delete all but the `keep` most recent `path.bak.*` backups."""
    backups = sorted(
        path.parent.glob(path.name + ".bak.*"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    for stale in backups[keep:]:
        stale.unlink(missing_ok=True)


def backup_file(path: Union[str, Path]) -> Path:
    """Copy `path` to `path.bak.<YYYYMMDD>`, adding a -2, -3, ... suffix if a
    backup for today already exists. Keeps only the most recent KEEP_BACKUPS
    backups per file. Returns the backup path."""
    path = Path(path)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d")
    candidate = path.with_suffix(path.suffix + f".bak.{stamp}")
    n = 2
    while candidate.exists():
        candidate = path.with_suffix(path.suffix + f".bak.{stamp}-{n}")
        n += 1
    shutil.copy2(path, candidate)
    _prune_backups(path)
    return candidate

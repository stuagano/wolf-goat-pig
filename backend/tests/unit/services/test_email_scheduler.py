"""Scheduler has one UUID-bound queue processor, no approximate identity path."""

from unittest.mock import Mock

import pytest

from app.services.email_scheduler import EmailScheduler


@pytest.mark.parametrize("fails", [False, True])
def test_sheet_job_delegates_once_and_closes_session(monkeypatch, fails):
    from app.services import round_sheet_delivery

    scheduler = EmailScheduler()
    db = Mock()
    processor = Mock(side_effect=RuntimeError("fixture failure") if fails else None)
    monkeypatch.setattr(scheduler, "_get_db", lambda: db)
    monkeypatch.setattr(round_sheet_delivery, "process_pending_sheet_syncs", processor)
    if fails:
        with pytest.raises(RuntimeError, match="fixture failure"):
            scheduler._process_pending_sheet_syncs()
    else:
        scheduler._process_pending_sheet_syncs()
    processor.assert_called_once_with(db.get_bind.return_value)
    db.close.assert_called_once()
    assert not hasattr(scheduler, "_dedup_action")

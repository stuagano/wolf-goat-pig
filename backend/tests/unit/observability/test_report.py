"""Unit tests for Cloud Logging report helpers."""

from app.observability import report


def test_report_exception_logs(caplog):
    with caplog.at_level("ERROR", logger="app.observability.report"):
        try:
            raise RuntimeError("boom")
        except RuntimeError as exc:
            report.report_exception(exc)
    assert any("boom" in r.message for r in caplog.records)


def test_report_message_logs(caplog):
    with caplog.at_level("ERROR", logger="app.observability.report"):
        report.report_message("signup email failed")
    assert any("signup email failed" in r.message for r in caplog.records)

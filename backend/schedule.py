"""
Minimal in-repo shim for the `schedule` PyPI package.

The upstream `schedule` library is a small dependency used by `app/services/email_scheduler.py`.
In some locked-down environments, installing it at runtime may be impossible (PEP 668 / network
restrictions). This shim provides just enough surface area for the app to import and for tests
to run without requiring external installation.

It is intentionally a no-op scheduler: jobs are registered but never executed automatically.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Literal, Optional


JobUnit = Literal["day", "hours", "sunday", "saturday"]


@dataclass(frozen=True)
class _Job:
    unit: JobUnit
    interval: int
    at_time: Optional[str]
    func: Callable[[], object] | None

    def at(self, time_str: str) -> "_Job":
        return _Job(unit=self.unit, interval=self.interval, at_time=time_str, func=self.func)

    def do(self, func: Callable[[], object]) -> "_Job":
        job = _Job(unit=self.unit, interval=self.interval, at_time=self.at_time, func=func)
        _JOBS.append(job)
        return job

    @property
    def day(self) -> "_Job":
        return _Job(unit="day", interval=self.interval, at_time=self.at_time, func=self.func)

    @property
    def sunday(self) -> "_Job":
        return _Job(unit="sunday", interval=self.interval, at_time=self.at_time, func=self.func)

    @property
    def saturday(self) -> "_Job":
        return _Job(unit="saturday", interval=self.interval, at_time=self.at_time, func=self.func)

    @property
    def hours(self) -> "_Job":
        return _Job(unit="hours", interval=self.interval, at_time=self.at_time, func=self.func)


_JOBS: list[_Job] = []


def every(interval: int = 1) -> _Job:
    return _Job(unit="day", interval=interval, at_time=None, func=None)


def run_pending() -> None:
    # No-op: this shim never triggers jobs automatically.
    return None


def clear() -> None:
    _JOBS.clear()


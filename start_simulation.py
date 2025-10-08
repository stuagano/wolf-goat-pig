#!/usr/bin/env python3
"""Wolf Goat Pig Simulation Startup Script."""

from __future__ import annotations

import logging
import os
import subprocess
import sys
from importlib import metadata
from pathlib import Path
from typing import Iterable

REPO_ROOT = Path(__file__).resolve().parent
BACKEND_PATH = REPO_ROOT / "backend"
REQUIREMENTS_FILE = BACKEND_PATH / "requirements.txt"
ENV_FILE = REPO_ROOT / ".env"
ENV_TEMPLATE = REPO_ROOT / ".env.example"
DEFAULT_SQLITE_PATH = REPO_ROOT / "reports" / "wolf_goat_pig.db"


def setup_logging() -> logging.Logger:
    """Configure a repository-wide logger."""

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )
    return logging.getLogger("start_simulation")


def _strip_requirement_specifier(requirement: str) -> str:
    """Return the distribution name portion of a requirement string."""

    separators = ["[", "==", ">=", "<=", "~=", "!=", ">", "<"]
    name = requirement
    for separator in separators:
        if separator in name:
            name = name.split(separator, 1)[0]
    return name.strip()


def _parse_requirements() -> list[str]:
    """Read backend requirements, ignoring comments and blank lines."""

    if not REQUIREMENTS_FILE.exists():
        return []

    requirements: list[str] = []
    for raw_line in REQUIREMENTS_FILE.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        # Remove inline comments while preserving version specifiers.
        if " #" in line:
            line = line.split(" #", 1)[0].strip()
        requirements.append(line)
    return requirements


def _find_missing_distributions(requirements: Iterable[str]) -> list[str]:
    """Return the subset of requirement distributions that are not installed."""

    missing: list[str] = []
    for requirement in requirements:
        distribution = _strip_requirement_specifier(requirement)
        if not distribution:
            continue
        try:
            metadata.version(distribution)
        except metadata.PackageNotFoundError:
            missing.append(distribution)
    return missing


def ensure_dependencies(logger: logging.Logger) -> bool:
    """Install backend requirements when missing."""

    requirements = _parse_requirements()
    if not requirements:
        logger.warning("⚠️ backend/requirements.txt not found; skipping dependency check")
        return True

    missing = _find_missing_distributions(requirements)
    if not missing:
        logger.info("✅ Backend dependencies already satisfied")
        return True

    logger.warning("⚠️ Missing backend dependencies: %s", ", ".join(sorted(missing)))

    if not REQUIREMENTS_FILE.exists():
        logger.error("❌ Cannot install dependencies automatically; backend/requirements.txt is missing")
        logger.info("Run `python -m pip install -r backend/requirements.txt` and retry.")
        return False

    logger.info(
        "📦 Installing backend requirements from %s",
        REQUIREMENTS_FILE.relative_to(REPO_ROOT),
    )

    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "-r", str(REQUIREMENTS_FILE)]
        )
    except subprocess.CalledProcessError as exc:
        logger.error("❌ Failed to install backend requirements: %s", exc)
        logger.info("Run `python -m pip install -r backend/requirements.txt` manually.")
        return False

    remaining = _find_missing_distributions(requirements)
    if remaining:
        logger.error("❌ Dependencies still missing after installation: %s", ", ".join(sorted(remaining)))
        return False

    logger.info("✅ Backend requirements installed successfully")
    return True


def _parse_env_file(path: Path) -> dict[str, str]:
    """Parse a dotenv file into a dictionary."""

    try:
        contents = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return {}

    values: dict[str, str] = {}
    for raw_line in contents.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "#" in line:
            line = line.split("#", 1)[0].strip()
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def _ensure_sqlite_database(logger: logging.Logger) -> None:
    """Guarantee that the SQLite database directory exists when configured."""

    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        DEFAULT_SQLITE_PATH.parent.mkdir(parents=True, exist_ok=True)
        resolved = DEFAULT_SQLITE_PATH.resolve()
        os.environ["DATABASE_URL"] = f"sqlite:///{resolved}"
        logger.info("🔧 DATABASE_URL not set; defaulting to %s", resolved)
        return

    if not database_url.startswith("sqlite:///"):
        logger.info("ℹ️ Using non-SQLite database configured via DATABASE_URL")
        return

    raw_path = database_url.replace("sqlite:///", "", 1)
    db_path = Path(raw_path).expanduser()
    if not db_path.is_absolute():
        db_path = (REPO_ROOT / db_path).resolve()
    else:
        db_path = db_path.resolve()

    db_path.parent.mkdir(parents=True, exist_ok=True)
    os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"
    logger.info("🔧 Using SQLite database at %s", db_path)


def load_environment(logger: logging.Logger) -> None:
    """Load environment variables from .env files without overriding shell exports."""

    merged: dict[str, str] = {}
    merged.update(_parse_env_file(ENV_TEMPLATE))
    merged.update(_parse_env_file(ENV_FILE))

    applied: list[str] = []
    for key, value in merged.items():
        if key not in os.environ:
            os.environ[key] = value
            applied.append(key)

    if applied:
        logger.info("✅ Loaded %d environment variables from .env files", len(applied))
    else:
        logger.info("ℹ️ Environment variables already set; .env files not applied")

    _ensure_sqlite_database(logger)


def _ensure_backend_on_path() -> None:
    backend_str = str(BACKEND_PATH)
    if backend_str not in sys.path:
        sys.path.insert(0, backend_str)


def test_basic_imports() -> bool:
    """Validate that the core simulation modules can be imported."""

    logger = logging.getLogger("start_simulation")
    logger.info("🔍 Testing backend imports...")
    _ensure_backend_on_path()

    try:
        import app.database  # noqa: F401
        from app.wolf_goat_pig_simulation import WolfGoatPigSimulation
    except ModuleNotFoundError as exc:
        logger.error("❌ Missing dependency while importing backend modules: %s", exc)
        logger.info("Run `python -m pip install -r backend/requirements.txt` and retry.")
        return False
    except Exception as exc:  # pragma: no cover - diagnostics only
        logger.error("❌ Unexpected error while importing backend modules: %s", exc)
        return False

    try:
        WolfGoatPigSimulation(player_count=4)
    except Exception as exc:  # pragma: no cover - diagnostics only
        logger.error("❌ Failed to instantiate WolfGoatPigSimulation: %s", exc)
        return False

    logger.info("✅ Backend simulation imports verified")
    return True


def start_backend_server() -> bool:
    """Launch the FastAPI application with Uvicorn."""

    logger = logging.getLogger("start_simulation")
    _ensure_backend_on_path()

    try:
        import uvicorn
    except ModuleNotFoundError:
        logger.error("❌ Uvicorn is not installed. Run `python -m pip install -r backend/requirements.txt`.")
        return False

    host = os.environ.get("WGP_API_HOST", "0.0.0.0")
    port_raw = os.environ.get("WGP_API_PORT", "8000")

    try:
        port = int(port_raw)
    except ValueError:
        logger.warning("⚠️ Invalid WGP_API_PORT=%s; defaulting to 8000", port_raw)
        port = 8000

    logger.info("🚀 Starting backend server at http://%s:%d", host, port)
    logger.info("📖 API Docs: http://%s:%d/docs", "localhost" if host in {"0.0.0.0", "127.0.0.1"} else host, port)

    try:
        uvicorn.run(
            "app.main:app",
            host=host,
            port=port,
            reload=True,
            log_level=os.environ.get("UVICORN_LOG_LEVEL", "info"),
        )
    except Exception as exc:  # pragma: no cover - diagnostics only
        logger.error("❌ Failed to start Uvicorn: %s", exc)
        return False

    return True


def main() -> int:
    """Main entry point for the simulation bootstrap."""

    logger = setup_logging()
    logger.info("🐺 Wolf Goat Pig Simulation Startup")
    logger.info("=" * 60)

    if not ensure_dependencies(logger):
        return 1

    load_environment(logger)

    if not test_basic_imports():
        return 1

    logger.info("✅ All checks passed - starting server...")

    try:
        if not start_backend_server():
            return 1
    except KeyboardInterrupt:
        logger.info("👋 Server stopped by user")
    except Exception as exc:  # pragma: no cover - diagnostics only
        logger.error("❌ Server error: %s", exc)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())

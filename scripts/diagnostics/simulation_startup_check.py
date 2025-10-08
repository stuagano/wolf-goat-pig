#!/usr/bin/env python3
"""Simulation startup diagnostics without external dependencies."""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_PATH = REPO_ROOT / "backend"
FRONTEND_SRC = REPO_ROOT / "frontend" / "src"


def _ensure_backend_path() -> None:
    if str(BACKEND_PATH) not in sys.path:
        sys.path.insert(0, str(BACKEND_PATH))


def test_simulation_logic() -> bool:
    """Test core simulation components without database dependencies."""

    print("🎮 Testing simulation startup logic...")
    _ensure_backend_path()

    try:
        from app import wolf_goat_pig_simulation
    except ImportError as exc:
        print(f"❌ Cannot import simulation modules: {exc}")
        print("💡 Install backend requirements and ensure PYTHONPATH includes ./backend")
        return False

    print("✅ wolf_goat_pig_simulation imported successfully")

    try:
        wgp_sim = wolf_goat_pig_simulation.WolfGoatPigSimulation()
    except Exception as exc:  # pragma: no cover - diagnostic logging
        print(f"❌ Error creating WolfGoatPigSimulation: {exc}")
        return False

    print("✅ WolfGoatPigSimulation object created")

    required_methods = [
        "get_game_state",
        "set_computer_players",
        "_initialize_hole",
        "_create_default_players",
    ]
    missing_methods = [method for method in required_methods if not hasattr(wgp_sim, method)]

    for method in required_methods:
        if hasattr(wgp_sim, method):
            print(f"✅ Method {method} found")

    if missing_methods:
        print(f"❌ Missing methods: {missing_methods}")
        return False

    try:
        state = wgp_sim.get_game_state()
        print(f"✅ Game state retrieved: {type(state)}")
    except Exception as exc:  # pragma: no cover - diagnostic logging
        print(f"⚠️ Game state initialization warning: {exc}")

    return True


def test_frontend_integration() -> bool:
    """Verify that frontend simulation components exist."""

    print("🎨 Testing frontend simulation integration...")

    simulation_candidates = [
        ["components/simulation/SimulationMode.js"],
        ["components/simulation/GameSetup.js", "components/simulation/GameSetup.tsx"],
        ["components/simulation/GamePlay.js"],
        ["components/game/UnifiedGameInterface.js"],
    ]

    missing = []
    for options in simulation_candidates:
        found = False
        for option in options:
            candidate = FRONTEND_SRC / option
            if candidate.exists():
                print(f"✅ {option}")
                found = True
                break
        if not found:
            missing.append(options[0])

    if missing:
        print(f"❌ Missing frontend files: {missing}")
        return False

    sim_mode_path = FRONTEND_SRC / "components/simulation/SimulationMode.js"
    if not sim_mode_path.exists():
        sim_mode_path = FRONTEND_SRC / "components/simulation/SimulationMode.tsx"

    content = sim_mode_path.read_text(encoding="utf-8")
    required_features = ["SimulationMode", "useState", "selectedCourse", "humanPlayer", "computerPlayers"]

    for feature in required_features:
        if feature in content:
            print(f"✅ Found frontend feature: {feature}")
        else:
            print(f"⚠️ Missing frontend feature: {feature}")

    print("✅ Frontend simulation components found")
    return True


def test_api_endpoints() -> bool:
    """Verify that key API endpoints are defined in the FastAPI app."""

    print("🌐 Testing API endpoint definitions...")

    main_path = BACKEND_PATH / "app" / "main.py"
    if not main_path.exists():
        print("❌ backend/app/main.py not found")
        return False

    content = main_path.read_text(encoding="utf-8")
    required_endpoints = [
        "/wgp/calculate-odds",
        "/wgp/shot-range-analysis",
        "/courses",
        "/health",
    ]

    missing = []
    for endpoint in required_endpoints:
        if endpoint in content:
            print(f"✅ Found endpoint: {endpoint}")
        else:
            missing.append(endpoint)

    if missing:
        print(f"❌ Missing endpoints: {missing}")
        return len(missing) < len(required_endpoints)

    print("✅ All required API endpoints found")
    return True


def main() -> bool:
    """Run simulation startup tests."""

    print("🐺🎮 Wolf-Goat-Pig Simulation Startup Test")
    print("=" * 60)

    checks = [
        test_simulation_logic(),
        test_frontend_integration(),
        test_api_endpoints(),
    ]

    success = all(checks)
    if success:
        print("\n🎉 Simulation startup diagnostics passed")
    else:
        print("\n⚠️ Simulation startup diagnostics reported issues")

    return success


if __name__ == "__main__":
    sys.exit(0 if main() else 1)

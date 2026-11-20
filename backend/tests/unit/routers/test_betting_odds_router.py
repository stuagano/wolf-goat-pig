"""Unit tests for betting_odds router — shot analysis, odds calculation, quick odds, history."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


# ── POST /wgp/shot-range-analysis ──────────────────────────────────────────


class TestShotRangeAnalysis:
    def _valid_payload(self, **overrides):
        base = {
            "lie_type": "fairway",
            "distance_to_pin": 150.0,
            "player_handicap": 15.0,
            "hole_number": 7,
        }
        base.update(overrides)
        return base

    def test_shot_analysis_returns_200(self):
        resp = client.post("/wgp/shot-range-analysis", json=self._valid_payload())
        assert resp.status_code == 200

    def test_shot_analysis_response_shape(self):
        resp = client.post("/wgp/shot-range-analysis", json=self._valid_payload())
        data = resp.json()
        assert data["status"] == "success"
        assert "analysis" in data
        assert "timestamp" in data

    def test_shot_analysis_with_all_optional_fields(self):
        payload = self._valid_payload(
            team_situation="partners",
            score_differential=-2,
            opponent_styles=["aggressive", "conservative"],
        )
        resp = client.post("/wgp/shot-range-analysis", json=payload)
        assert resp.status_code == 200

    def test_shot_analysis_bunker_lie(self):
        resp = client.post(
            "/wgp/shot-range-analysis",
            json=self._valid_payload(lie_type="bunker", distance_to_pin=30.0),
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "success"

    def test_shot_analysis_rough_lie(self):
        resp = client.post(
            "/wgp/shot-range-analysis",
            json=self._valid_payload(lie_type="rough", distance_to_pin=180.0),
        )
        assert resp.status_code == 200

    def test_shot_analysis_green_lie(self):
        resp = client.post(
            "/wgp/shot-range-analysis",
            json=self._valid_payload(lie_type="green", distance_to_pin=15.0),
        )
        assert resp.status_code == 200

    def test_shot_analysis_missing_required_field_returns_422(self):
        # Missing lie_type
        resp = client.post(
            "/wgp/shot-range-analysis",
            json={"distance_to_pin": 150.0, "player_handicap": 15.0, "hole_number": 7},
        )
        assert resp.status_code == 422

    def test_shot_analysis_missing_distance_returns_422(self):
        resp = client.post(
            "/wgp/shot-range-analysis",
            json={"lie_type": "fairway", "player_handicap": 15.0, "hole_number": 7},
        )
        assert resp.status_code == 422

    def test_shot_analysis_missing_handicap_returns_422(self):
        resp = client.post(
            "/wgp/shot-range-analysis",
            json={"lie_type": "fairway", "distance_to_pin": 150.0, "hole_number": 7},
        )
        assert resp.status_code == 422

    def test_shot_analysis_missing_hole_number_returns_422(self):
        resp = client.post(
            "/wgp/shot-range-analysis",
            json={"lie_type": "fairway", "distance_to_pin": 150.0, "player_handicap": 15.0},
        )
        assert resp.status_code == 422

    def test_shot_analysis_low_handicap_player(self):
        resp = client.post(
            "/wgp/shot-range-analysis",
            json=self._valid_payload(player_handicap=2.0),
        )
        assert resp.status_code == 200

    def test_shot_analysis_high_handicap_player(self):
        resp = client.post(
            "/wgp/shot-range-analysis",
            json=self._valid_payload(player_handicap=36.0),
        )
        assert resp.status_code == 200

    def test_shot_analysis_late_hole(self):
        resp = client.post(
            "/wgp/shot-range-analysis",
            json=self._valid_payload(hole_number=18, score_differential=5),
        )
        assert resp.status_code == 200


# ── POST /wgp/calculate-odds ──────────────────────────────────────────────


class TestCalculateOdds:
    def _valid_payload(self, **overrides):
        base = {
            "players": [
                {
                    "id": "p1",
                    "name": "Alice",
                    "handicap": 12,
                    "distance_to_pin": 150,
                    "lie_type": "fairway",
                },
                {
                    "id": "p2",
                    "name": "Bob",
                    "handicap": 18,
                    "distance_to_pin": 160,
                    "lie_type": "rough",
                },
            ],
            "hole_state": {
                "hole_number": 5,
                "par": 4,
                "teams": "pending",
            },
        }
        base.update(overrides)
        return base

    def test_calculate_odds_returns_200(self):
        resp = client.post("/wgp/calculate-odds", json=self._valid_payload())
        assert resp.status_code == 200

    def test_calculate_odds_response_shape(self):
        resp = client.post("/wgp/calculate-odds", json=self._valid_payload())
        data = resp.json()
        assert "timestamp" in data
        assert "calculation_time_ms" in data
        assert "player_probabilities" in data
        assert "team_probabilities" in data
        assert "betting_scenarios" in data
        assert "optimal_strategy" in data
        assert "confidence_level" in data

    def test_calculate_odds_monte_carlo_always_false(self):
        """Monte Carlo removed — response always has monte_carlo_used=False."""
        resp = client.post("/wgp/calculate-odds", json=self._valid_payload())
        if resp.status_code == 200:
            data = resp.json()
            assert data["monte_carlo_used"] is False

    def test_calculate_odds_four_players(self):
        payload = self._valid_payload()
        payload["players"] = [
            {"id": f"p{i}", "name": f"Player{i}", "handicap": 10 + i * 3, "distance_to_pin": 140 + i * 10}
            for i in range(4)
        ]
        resp = client.post("/wgp/calculate-odds", json=payload)
        assert resp.status_code == 200

    def test_calculate_odds_missing_players_returns_422(self):
        resp = client.post(
            "/wgp/calculate-odds",
            json={"hole_state": {"hole_number": 1, "par": 4}},
        )
        assert resp.status_code == 422

    def test_calculate_odds_missing_hole_state_returns_422(self):
        resp = client.post(
            "/wgp/calculate-odds",
            json={"players": [{"id": "p1", "name": "A", "handicap": 10}]},
        )
        assert resp.status_code == 422

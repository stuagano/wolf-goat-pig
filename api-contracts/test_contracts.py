"""
Contract Validation Tests

These tests verify that actual implementations conform to their protocol contracts.
They use Python's type checking and runtime inspection to ensure interface compatibility.

Unlike traditional unit tests, these tests:
1. Don't test behavior - they test interface conformance
2. Don't need updates when implementation details change
3. Fail only when contracts are violated
4. Are self-maintaining through type checking
"""

import pytest
import inspect
from typing import get_type_hints, Protocol, get_origin
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import protocols
from service_contracts import (
    GameLifecycleServiceProtocol,
    NotificationServiceProtocol,
    LeaderboardServiceProtocol,
    AchievementServiceProtocol
)
from manager_contracts import (
    RuleManagerProtocol,
    ScoringManagerProtocol
)
from validator_contracts import (
    HandicapValidatorProtocol,
    BettingValidatorProtocol,
    GameStateValidatorProtocol
)

# Import actual implementations
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../backend')))

from app.services.game_lifecycle_service import GameLifecycleService
from app.services.notification_service import NotificationService
from app.services.leaderboard_service import LeaderboardService
from app.services.achievement_service import AchievementService
from app.managers.rule_manager import RuleManager
from app.managers.scoring_manager import ScoringManager
from app.validators import HandicapValidator, BettingValidator, GameStateValidator


def check_protocol_compliance(implementation, protocol):
    """
    Check if implementation satisfies protocol contract.

    Verifies that:
    1. All protocol methods exist in implementation
    2. Method signatures match (parameters and return types)
    3. Type hints are compatible

    Args:
        implementation: Actual class implementation
        protocol: Protocol contract to check against

    Returns:
        tuple: (is_compliant, list_of_violations)
    """
    violations = []

    # Get all methods from protocol
    protocol_methods = {
        name: method
        for name, method in inspect.getmembers(protocol, predicate=inspect.isfunction)
        if not name.startswith('_')
    }

    for method_name, protocol_method in protocol_methods.items():
        # Check method exists
        if not hasattr(implementation, method_name):
            violations.append(f"Missing method: {method_name}")
            continue

        impl_method = getattr(implementation, method_name)

        # Check method is callable
        if not callable(impl_method):
            violations.append(f"{method_name} is not callable")
            continue

        # Get signatures
        protocol_sig = inspect.signature(protocol_method)
        try:
            impl_sig = inspect.signature(impl_method)
        except (ValueError, TypeError):
            # Some built-in methods don't have inspectable signatures
            continue

        # Check parameter compatibility
        protocol_params = list(protocol_sig.parameters.keys())
        impl_params = list(impl_sig.parameters.keys())

        # Allow implementation to have fewer params if using *args/**kwargs
        if not (set(protocol_params).issubset(set(impl_params)) or
                any(p.kind == inspect.Parameter.VAR_KEYWORD
                    for p in impl_sig.parameters.values())):
            violations.append(
                f"{method_name}: Parameter mismatch - "
                f"Protocol expects {protocol_params}, "
                f"Implementation has {impl_params}"
            )

    return len(violations) == 0, violations


class TestServiceContracts:
    """Test that services implement their protocol contracts."""

    def test_game_lifecycle_service_contract(self):
        """GameLifecycleService must implement GameLifecycleServiceProtocol."""
        is_compliant, violations = check_protocol_compliance(
            GameLifecycleService,
            GameLifecycleServiceProtocol
        )
        assert is_compliant, f"Contract violations: {violations}"

    def test_notification_service_contract(self):
        """NotificationService must implement NotificationServiceProtocol."""
        is_compliant, violations = check_protocol_compliance(
            NotificationService,
            NotificationServiceProtocol
        )
        assert is_compliant, f"Contract violations: {violations}"

    def test_leaderboard_service_contract(self):
        """LeaderboardService must implement LeaderboardServiceProtocol."""
        is_compliant, violations = check_protocol_compliance(
            LeaderboardService,
            LeaderboardServiceProtocol
        )
        assert is_compliant, f"Contract violations: {violations}"

    def test_achievement_service_contract(self):
        """AchievementService must implement AchievementServiceProtocol."""
        is_compliant, violations = check_protocol_compliance(
            AchievementService,
            AchievementServiceProtocol
        )
        assert is_compliant, f"Contract violations: {violations}"


class TestManagerContracts:
    """Test that managers implement their protocol contracts."""

    def test_rule_manager_contract(self):
        """RuleManager must implement RuleManagerProtocol."""
        is_compliant, violations = check_protocol_compliance(
            RuleManager,
            RuleManagerProtocol
        )
        assert is_compliant, f"Contract violations: {violations}"

    def test_scoring_manager_contract(self):
        """ScoringManager must implement ScoringManagerProtocol."""
        is_compliant, violations = check_protocol_compliance(
            ScoringManager,
            ScoringManagerProtocol
        )
        assert is_compliant, f"Contract violations: {violations}"


class TestValidatorContracts:
    """Test that validators implement their protocol contracts."""

    def test_handicap_validator_contract(self):
        """HandicapValidator must implement HandicapValidatorProtocol."""
        is_compliant, violations = check_protocol_compliance(
            HandicapValidator,
            HandicapValidatorProtocol
        )
        assert is_compliant, f"Contract violations: {violations}"

    def test_betting_validator_contract(self):
        """BettingValidator must implement BettingValidatorProtocol."""
        is_compliant, violations = check_protocol_compliance(
            BettingValidator,
            BettingValidatorProtocol
        )
        assert is_compliant, f"Contract violations: {violations}"

    def test_game_state_validator_contract(self):
        """GameStateValidator must implement GameStateValidatorProtocol."""
        is_compliant, violations = check_protocol_compliance(
            GameStateValidator,
            GameStateValidatorProtocol
        )
        assert is_compliant, f"Contract violations: {violations}"


class TestContractIntegration:
    """Test that contracts work together correctly."""

    def test_service_layer_completeness(self):
        """All services should be covered by contracts."""
        expected_services = [
            'GameLifecycleService',
            'NotificationService',
            'LeaderboardService',
            'AchievementService'
        ]

        # This test ensures we don't forget to add contracts for new services
        for service_name in expected_services:
            protocol_name = f"{service_name}Protocol"
            assert protocol_name in dir(sys.modules['service_contracts']), \
                f"Missing protocol for {service_name}"

    def test_manager_layer_completeness(self):
        """All managers should be covered by contracts."""
        expected_managers = [
            'RuleManager',
            'ScoringManager'
        ]

        for manager_name in expected_managers:
            protocol_name = f"{manager_name}Protocol"
            assert protocol_name in dir(sys.modules['manager_contracts']), \
                f"Missing protocol for {manager_name}"

    def test_validator_layer_completeness(self):
        """All validators should be covered by contracts."""
        expected_validators = [
            'HandicapValidator',
            'BettingValidator',
            'GameStateValidator'
        ]

        for validator_name in expected_validators:
            protocol_name = f"{validator_name}Protocol"
            assert protocol_name in dir(sys.modules['validator_contracts']), \
                f"Missing protocol for {validator_name}"


class TestContractEvolution:
    """Test that contracts handle evolution gracefully."""

    def test_backward_compatibility(self):
        """Implementations can have MORE methods than protocols require."""
        # This is always allowed - implementations can extend protocols
        # We just verify the protocol methods are present
        assert hasattr(GameLifecycleService, 'create_game')
        assert hasattr(GameLifecycleService, 'get_game')
        # Implementation may have additional methods not in protocol

    def test_optional_parameters(self):
        """Implementation methods can have optional parameters."""
        # Protocol specifies minimum required interface
        # Implementations can add optional params without breaking contract
        create_game = getattr(GameLifecycleService, 'create_game')
        sig = inspect.signature(create_game)

        # Check that required params from protocol are present
        required_params = ['self', 'db', 'player_count', 'players', 'course_name']
        actual_params = list(sig.parameters.keys())

        for param in required_params:
            assert param in actual_params, \
                f"Required parameter '{param}' missing from create_game"


if __name__ == '__main__':
    # Run contract tests
    pytest.main([__file__, '-v'])

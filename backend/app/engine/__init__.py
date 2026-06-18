"""Wolf Goat Pig game-engine mixins.

WolfGoatPigGame (app/wolf_goat_pig.py) is composed from these mixins —
each file owns one functional area of the engine. They are not reusable
outside the game class: methods freely call across mixin boundaries via
``self``, resolved by the composed class's MRO (same informal-contract
pattern as app/mixins/persistence_mixin.py).
"""

from .aardvark import AardvarkMixin
from .analytics import AnalyticsMixin
from .betting_actions import BettingActionsMixin
from .hole_setup import HoleSetupMixin
from .partnership import PartnershipMixin
from .scoring import ScoringMixin
from .serialization import SerializationMixin
from .shot_progression import ShotProgressionMixin
from .simulation_api import SimulationMixin
from .state_views import StateViewsMixin

__all__ = [
    "AardvarkMixin",
    "AnalyticsMixin",
    "BettingActionsMixin",
    "HoleSetupMixin",
    "PartnershipMixin",
    "ScoringMixin",
    "SerializationMixin",
    "ShotProgressionMixin",
    "StateViewsMixin",
    "SimulationMixin",
]

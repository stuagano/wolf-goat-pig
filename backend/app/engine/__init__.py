"""Wolf Goat Pig game-engine mixins.

WolfGoatPigGame (app/wolf_goat_pig.py) is composed from these mixins —
each file owns one functional area of the engine. They are not reusable
outside the game class: methods freely call across mixin boundaries via
``self``, resolved by the composed class's MRO (same informal-contract
pattern as app/mixins/persistence_mixin.py).
"""

from .analytics import AnalyticsMixin
from .partnership import PartnershipMixin
from .serialization import SerializationMixin
from .shot_progression import ShotProgressionMixin
from .simulation_api import SimulationMixin

__all__ = [
    "AnalyticsMixin",
    "PartnershipMixin",
    "SerializationMixin",
    "ShotProgressionMixin",
    "SimulationMixin",
]

from sqlalchemy import Column, Integer, String
from .database import Base
from sqlalchemy.types import JSON

class Rule(Base):
    __tablename__ = "rules"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(String)

# For MVP: store the entire game state as a JSON blob
class GameStateModel(Base):
    __tablename__ = "game_state"
    id = Column(Integer, primary_key=True, index=True)
    state = Column(JSON) 
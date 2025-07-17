from sqlalchemy import Column, Integer, String, Float
from .database import Base
from sqlalchemy.types import JSON

class Rule(Base):
    __tablename__ = "rules"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(String)

# Enhanced Course model for proper course management
class Course(Base):
    __tablename__ = "courses"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    description = Column(String, nullable=True)
    total_par = Column(Integer)
    total_yards = Column(Integer)
    course_rating = Column(Float, nullable=True)
    slope_rating = Column(Float, nullable=True)
    holes_data = Column(JSON)  # Store hole details as JSON
    created_at = Column(String)
    updated_at = Column(String)

class Hole(Base):
    __tablename__ = "holes"
    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, index=True)
    hole_number = Column(Integer)
    par = Column(Integer)
    yards = Column(Integer)
    handicap = Column(Integer)  # Stroke index (1-18)
    description = Column(String, nullable=True)
    tee_box = Column(String, default="regular")  # regular, championship, forward, etc.

# For MVP: store the entire game state as a JSON blob
class GameStateModel(Base):
    __tablename__ = "game_state"
    id = Column(Integer, primary_key=True, index=True)
    state = Column(JSON)

# Store simulation results for analysis
class SimulationResult(Base):
    __tablename__ = "simulation_results"
    id = Column(Integer, primary_key=True, index=True)
    course_name = Column(String, nullable=True)
    player_count = Column(Integer)
    simulation_count = Column(Integer)
    results_data = Column(JSON)
    created_at = Column(String) 
from sqlalchemy import Column, Integer, String
from .database import Base

class Rule(Base):
    __tablename__ = "rules"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(String) 
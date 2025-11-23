"""
Database session management helpers.

Provides utilities for proper database session lifecycle management in FastAPI.
"""

import logging
from functools import wraps
from typing import Callable

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


def with_db_session(func: Callable) -> Callable:
    """
    Decorator to ensure database session is properly closed after function execution.

    Use this ONLY for functions that create their own SessionLocal() manually.
    DO NOT use for FastAPI endpoints with db: Session = Depends(database.get_db).

    Example:
        @with_db_session
        def my_function():
            db = SessionLocal()
            # do work with db
            return result
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        db = kwargs.get('db')
        created_session = False

        # If db not provided, create one
        if db is None:
            from .database import SessionLocal
            db = SessionLocal()
            kwargs['db'] = db
            created_session = True

        try:
            result = func(*args, **kwargs)
            return result
        except Exception:
            if created_session:
                db.rollback()
            raise
        finally:
            if created_session:
                db.close()

    return wrapper


# Alternative: Context manager approach (preferred)
def get_db_session() -> Session:
    """
    Context manager for database sessions.

    This is the PREFERRED approach for manual session management.

    Example:
        with get_db_session() as db:
            player = db.query(Player).filter_by(id=1).first()
            # session automatically closed after with block
    """
    from .database import get_isolated_session
    return get_isolated_session()

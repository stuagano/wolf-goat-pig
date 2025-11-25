"""
API Helper Utilities

Provides decorators and utilities for consistent API error handling,
database session management, and response formatting.
"""

import logging
from contextlib import contextmanager
from datetime import datetime, timezone
from functools import wraps
from typing import Any, Callable, Dict, Generator, Optional, TypeVar, Union
import asyncio

from fastapi import HTTPException
from sqlalchemy.orm import Session

logger = logging.getLogger("app.utils.api_helpers")

T = TypeVar("T")


def handle_api_errors(
    operation_name: str = "operation",
    log_errors: bool = True,
    reraise_http_exceptions: bool = True
) -> Callable:
    """
    Decorator for consistent API error handling.

    Eliminates the need to write try-except-finally blocks in every route handler.
    Automatically handles:
    - ValueError -> 400 Bad Request
    - HTTPException -> re-raised as-is
    - Other exceptions -> 500 Internal Server Error

    Args:
        operation_name: Human-readable name for logging (e.g., "create player profile")
        log_errors: Whether to log errors (default True)
        reraise_http_exceptions: Whether to re-raise HTTPExceptions (default True)

    Usage:
        @router.post("")
        @handle_api_errors(operation_name="create player profile")
        def create_player(profile: PlayerCreate, db: Session = Depends(get_db)):
            return player_service.create(profile)
    """
    def decorator(func: Callable[..., T]) -> Union[Callable[..., T], Callable[..., Any]]:
        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> T:
            try:
                return func(*args, **kwargs)
            except ValueError as e:
                if log_errors:
                    logger.error(f"Validation error in {operation_name}: {e}")
                raise HTTPException(status_code=400, detail=str(e))
            except HTTPException:
                if reraise_http_exceptions:
                    raise
                if log_errors:
                    logger.error(f"HTTP error in {operation_name}")
                raise
            except Exception as e:
                if log_errors:
                    logger.error(f"Error in {operation_name}: {e}", exc_info=True)
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to {operation_name}: {str(e)}"
                )

        @wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> T:
            try:
                result = await func(*args, **kwargs)  # type: ignore
                return result  # type: ignore
            except ValueError as e:
                if log_errors:
                    logger.error(f"Validation error in {operation_name}: {e}")
                raise HTTPException(status_code=400, detail=str(e))
            except HTTPException:
                if reraise_http_exceptions:
                    raise
                if log_errors:
                    logger.error(f"HTTP error in {operation_name}")
                raise
            except Exception as e:
                if log_errors:
                    logger.error(f"Error in {operation_name}: {e}", exc_info=True)
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to {operation_name}: {str(e)}"
                )

        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


def with_db_session(func: Callable[..., T]) -> Callable[..., T]:
    """
    Decorator that provides automatic database session management.

    Creates a session, passes it to the function, and ensures cleanup.
    Use this for functions that need a database session but aren't using
    FastAPI's dependency injection.

    Usage:
        @with_db_session
        def my_function(db: Session):
            return db.query(Model).all()
    """
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> T:
        from ..database import SessionLocal

        db = kwargs.get('db')
        created_session = False

        if db is None:
            db = SessionLocal()
            kwargs['db'] = db
            created_session = True

        try:
            result = func(*args, **kwargs)
            if created_session:
                db.commit()
            return result
        except Exception:
            if created_session:
                db.rollback()
            raise
        finally:
            if created_session:
                db.close()

    return wrapper


@contextmanager
def managed_session() -> Generator[Session, None, None]:
    """
    Context manager for database sessions.

    Usage:
        with managed_session() as db:
            player = db.query(Player).filter_by(id=1).first()
    """
    from ..database import SessionLocal

    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


class ApiResponse:
    """
    Utility class for consistent API response formatting.

    Provides standard response structures for success and error cases.
    """

    @staticmethod
    def success(
        data: Any = None,
        message: str = "Success",
        meta: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a success response.

        Args:
            data: The response payload
            message: Human-readable success message
            meta: Optional metadata (pagination, etc.)

        Returns:
            Standardized success response dict
        """
        response: Dict[str, Any] = {
            "success": True,
            "message": message,
            "data": data,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        if meta:
            response["meta"] = meta
        return response

    @staticmethod
    def error(
        message: str,
        code: str = "ERROR",
        details: Optional[Dict[str, Any]] = None,
        status_code: int = 500
    ) -> Dict[str, Any]:
        """
        Create an error response.

        Args:
            message: Human-readable error message
            code: Machine-readable error code
            details: Additional error details
            status_code: HTTP status code (for reference)

        Returns:
            Standardized error response dict
        """
        return {
            "success": False,
            "message": message,
            "code": code,
            "details": details or {},
            "status_code": status_code,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    @staticmethod
    def paginated(
        data: list,
        total: int,
        page: int = 1,
        page_size: int = 20,
        message: str = "Success"
    ) -> Dict[str, Any]:
        """
        Create a paginated response.

        Args:
            data: List of items for current page
            total: Total number of items
            page: Current page number
            page_size: Items per page
            message: Success message

        Returns:
            Standardized paginated response dict
        """
        total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0
        return ApiResponse.success(
            data=data,
            message=message,
            meta={
                "pagination": {
                    "page": page,
                    "page_size": page_size,
                    "total_items": total,
                    "total_pages": total_pages,
                    "has_next": page < total_pages,
                    "has_prev": page > 1
                }
            }
        )


def require_not_none(value: Optional[T], entity_name: str, entity_id: Any) -> T:
    """
    Utility to check for None and raise 404 if not found.

    Args:
        value: The value to check
        entity_name: Name of entity for error message (e.g., "Player")
        entity_id: ID of entity for error message

    Returns:
        The value if not None

    Raises:
        HTTPException: 404 if value is None
    """
    if value is None:
        raise HTTPException(
            status_code=404,
            detail=f"{entity_name} {entity_id} not found"
        )
    return value

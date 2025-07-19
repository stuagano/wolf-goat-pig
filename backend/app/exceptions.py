"""
Custom exception handlers and HTTP exception utilities
"""
from fastapi import HTTPException
from typing import Optional


class APIException:
    """Centralized HTTP exception factory to eliminate DRY violations"""
    
    @staticmethod
    def bad_request(detail: str) -> HTTPException:
        """Return a 400 Bad Request exception"""
        return HTTPException(status_code=400, detail=detail)
    
    @staticmethod
    def not_found(detail: str) -> HTTPException:
        """Return a 404 Not Found exception"""
        return HTTPException(status_code=404, detail=detail)
    
    @staticmethod
    def validation_error(field: str, value: any, constraint: str) -> HTTPException:
        """Return a validation error with standardized format"""
        return HTTPException(
            status_code=400, 
            detail=f"Validation error for '{field}': {value} {constraint}"
        )
    
    @staticmethod
    def missing_required_field(field: str) -> HTTPException:
        """Return a missing required field error"""
        return HTTPException(status_code=400, detail=f"Missing required field: {field}")
    
    @staticmethod
    def resource_not_found(resource_type: str, identifier: str) -> HTTPException:
        """Return a resource not found error"""
        return HTTPException(
            status_code=404, 
            detail=f"{resource_type} '{identifier}' not found"
        )
    
    @staticmethod
    def invalid_range(field: str, min_val: int, max_val: int) -> HTTPException:
        """Return an invalid range error"""
        return HTTPException(
            status_code=400,
            detail=f"{field} must be between {min_val} and {max_val}"
        )


class GameStateException(Exception):
    """Custom exception for game state related errors"""
    pass


class ValidationException(Exception):
    """Custom exception for validation errors"""
    pass


class CourseException(Exception):
    """Custom exception for course-related errors"""
    pass


def handle_game_exception(e: Exception) -> HTTPException:
    """Convert game exceptions to appropriate HTTP exceptions"""
    if isinstance(e, GameStateException):
        return APIException.bad_request(str(e))
    elif isinstance(e, ValidationException):
        return APIException.bad_request(str(e))
    elif isinstance(e, CourseException):
        return APIException.not_found(str(e))
    else:
        return APIException.bad_request(str(e))
"""
Custom exceptions for the SIDRA API integration.
"""
from typing import Dict, Any, Optional, Type, TypeVar, Generic

# Define type variable for exception chaining
E = TypeVar('E', bound=Exception)


class SidraApiError(Exception, Generic[E]):
    """
    Base exception for SIDRA API integration errors.

    This exception is raised when there's an error interacting with the SIDRA API,
    including validation errors, API errors, and data processing errors.
    """


    def __init__(
        self,
        message: str,
        *,
        table_code: Optional[str] = None,
        error_code: Optional[str] = None,
        original_error: Optional[Exception] = None,
        params: Optional[Dict[str, Any]] = None
    ):
        self.table_code = table_code
        self.error_code = error_code or "UNKNOWN_ERROR"
        self.original_error = original_error
        self.params = params or {}

        # Build a detailed, log-friendly error message
        full_message = message
        details = []

        if table_code:
            details.append(f"Table: {table_code}")

        if params:
            details.append(f"Parameters: {params}")

        if original_error:
            details.append(f"Original error: {str(original_error)}")

        if details:
            full_message = f"{message} ({'; '.join(details)})"

        super().__init__(full_message)

    @classmethod


    def from_exception(
        cls: Type['SidraApiError'],
        exc: Exception,
        message: Optional[str] = None,
        **kwargs: Any
    ) -> 'SidraApiError':
        """Create a SidraApiError from another exception.

        Args:
            exc: The original exception to wrap.
            message: Custom message (defaults to str(exc)).
            **kwargs: Additional arguments to pass to SidraApiError.

        Returns:
            A new SidraApiError instance.
        """
        return cls(
            message=message or str(exc),
            original_error=exc,
            **kwargs
        )


# Common error codes as class variables for consistency


class ErrorCodes:
    """Standard error codes for SIDRA API errors."""
    TABLE_NOT_FOUND = "TABLE_NOT_FOUND"
    INVALID_PARAMETER = "INVALID_PARAMETER"
    API_ERROR = "API_ERROR"
    NETWORK_ERROR = "NETWORK_ERROR"
    TIMEOUT = "TIMEOUT"
    NO_DATA = "NO_DATA"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    CACHE_ERROR = "CACHE_ERROR"

# Set error codes as class attributes for easy access
SidraApiError.ErrorCodes = ErrorCodes  # type: ignore


class SidraTableNotFoundError(SidraApiError):
    """Raised when a specified SIDRA table is not found."""
    pass


class SidraVariableNotFoundError(SidraApiError):
    """Raised when a specified variable is not found in a table."""
    pass


class SidraClassificationNotFoundError(SidraApiError):
    """Raised when a specified classification is not found in a table."""
    pass


class SidraCategoryNotFoundError(SidraApiError):
    """Raised when a specified category is not found in a classification."""
    pass


class SidraLocationNotFoundError(SidraApiError):
    """Raised when a specified location is not found or invalid."""
    pass


class SidraApiValidationError(SidraApiError):
    """Raised when there's a validation error in the API request parameters."""
    pass


class SidraApiRateLimitError(SidraApiError):
    """Raised when the SIDRA API rate limit has been exceeded."""
    pass

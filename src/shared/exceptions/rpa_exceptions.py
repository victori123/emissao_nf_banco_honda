class RPAException(Exception):
    """Base exception for all RPA errors."""

class LoginFailedException(RPAException):
    """Raised when login attempt fails."""

class ElementNotFoundException(RPAException):
    """Raised when a required element is not found on the page."""

class NavigationException(RPAException):
    """Raised when page navigation fails or lands on an unexpected URL."""

class DataExtractionException(RPAException):
    """Raised when expected data cannot be extracted from the page."""

class TimeoutException(RPAException):
    """Raised when an operation exceeds the allowed time."""

class MaxRetriesExceededException(RPAException):
    """Raised when all retry attempts are exhausted."""
    def __init__(self, operation: str, attempts: int):
        super().__init__(f"Operation '{operation}' failed after {attempts} attempt(s).")

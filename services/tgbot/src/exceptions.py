class TaskNotFoundError(ValueError):
    """Exception raised when a task is not found."""


class UnauthorizedAccessError(Exception):
    """Exception raised when a service is not authorized to perform a task."""

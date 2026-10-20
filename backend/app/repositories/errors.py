"""Errors shared by the MongoDB repositories."""


class DatabaseConnectionError(Exception):
    """Raised when MongoDB is unreachable or an operation fails because of the connection."""

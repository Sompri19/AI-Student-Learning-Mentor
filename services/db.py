"""
Database connection service for AI Student Learning Mentor.
Maintains backward-compatible interface by delegating to canonical database.db_connection.
"""
from database.db_connection import (
    REQUIRED_TABLES,
    sanitize_db_error,
    get_db_connection,
    get_db_cursor,
    check_db_health,
    initialize_database,
)

__all__ = [
    'REQUIRED_TABLES',
    'sanitize_db_error',
    'get_db_connection',
    'get_db_cursor',
    'check_db_health',
    'initialize_database',
]

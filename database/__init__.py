"""
Database package for AI Student Learning Mentor.
Exposes connection management, health verification, and database setup utilities.
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

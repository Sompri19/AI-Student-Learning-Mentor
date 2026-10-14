"""
User Model for AI Student Learning Mentor.
Encapsulates SQL operations for the 'users' table.
"""
import logging
from typing import Optional, Dict, Any, Tuple
import pymysql
from database.db_connection import get_db_connection, sanitize_db_error

logger = logging.getLogger(__name__)


def find_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    """
    Retrieves user record by email address.
    Returns row dict or None.
    """
    if not email:
        return None
    cleaned = email.strip().lower()
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, name, email, password_hash, role, created_at 
                FROM users 
                WHERE email = %s
                """,
                (cleaned,)
            )
            return cursor.fetchone()
    finally:
        conn.close()


def find_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    """
    Retrieves safe user information by ID (excluding password hash).
    """
    if not user_id:
        return None
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, name, email, role, created_at 
                FROM users 
                WHERE id = %s
                """,
                (user_id,)
            )
            return cursor.fetchone()
    finally:
        conn.close()


def insert_user(name: str, email: str, password_hash: str, role: str = 'student') -> Tuple[bool, str, Optional[int]]:
    """
    Inserts a new user record into the 'users' table.
    
    Returns:
        (success, message, new_user_id)
    """
    cleaned_name = name.strip()
    cleaned_email = email.strip().lower()
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO users (name, email, password_hash, role)
                VALUES (%s, %s, %s, %s)
                """,
                (cleaned_name, cleaned_email, password_hash, role)
            )
            new_id = cursor.lastrowid
            return True, "User registered successfully.", new_id
    except pymysql.IntegrityError:
        return False, "An account with this email address already exists.", None
    except Exception as exc:
        logger.error("Database error inserting user: %s", sanitize_db_error(exc))
        return False, "Database error during registration.", None
    finally:
        conn.close()


def update_user_password(user_id: int, new_password_hash: str) -> bool:
    """
    Updates the password hash for a given user ID.
    """
    if not user_id or not new_password_hash:
        return False
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                UPDATE users 
                SET password_hash = %s 
                WHERE id = %s
                """,
                (new_password_hash, user_id)
            )
            return cursor.rowcount > 0
    finally:
        conn.close()

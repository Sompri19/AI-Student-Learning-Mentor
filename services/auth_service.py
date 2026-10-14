"""
Authentication Service for AI Student Learning Mentor.
Handles user registration, credential validation, secure password hashing,
and database queries for user records.
"""
import re
import logging
from typing import Optional, Tuple, Dict, Any
from werkzeug.security import generate_password_hash, check_password_hash
import pymysql

from services.db import get_db_connection, sanitize_db_error

logger = logging.getLogger(__name__)

# Basic RFC 5322 compatible email pattern
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$')


def validate_registration_input(name: str, email: str, password: str) -> Tuple[bool, Optional[str]]:
    """
    Validates registration form inputs.
    
    Returns:
        (is_valid, error_message_if_any)
    """
    if not name or not name.strip():
        return False, "Full name is required."
    
    if len(name.strip()) < 2 or len(name.strip()) > 100:
        return False, "Name must be between 2 and 100 characters."
        
    if not email or not email.strip():
        return False, "Email address is required."
        
    cleaned_email = email.strip().lower()
    if not EMAIL_REGEX.match(cleaned_email):
        return False, "Please enter a valid email address."
        
    if not password:
        return False, "Password is required."
        
    if len(password) < 6:
        return False, "Password must be at least 6 characters long."
        
    if len(password) > 128:
        return False, "Password exceeds maximum allowable length."
        
    return True, None


from models.user_model import find_user_by_email, find_user_by_id, insert_user


def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    """
    Retrieves user record by email address via user_model.
    Never returns password_hash outside authentication scope.
    """
    if not email:
        return None
    return find_user_by_email(email)


def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    """
    Retrieves safe user information by ID via user_model.
    """
    if not user_id:
        return None
    return find_user_by_id(user_id)


def register_user(name: str, email: str, password: str, role: str = 'student') -> Tuple[bool, str, Optional[int]]:
    """
    Registers a new user with secure password hashing.
    Enforces unique email constraints.
    
    Returns:
        (success, message, user_id_if_created)
    """
    is_valid, validation_err = validate_registration_input(name, email, password)
    if not is_valid:
        return False, validation_err, None

    cleaned_email = email.strip().lower()
    cleaned_name = name.strip()

    # Check for duplicate email
    existing_user = get_user_by_email(cleaned_email)
    if existing_user:
        return False, "An account with this email address already exists.", None

    # Securely hash password using Werkzeug's default scrypt/pbkdf2
    password_hash = generate_password_hash(password)

    return insert_user(cleaned_name, cleaned_email, password_hash, role)


def authenticate_user(email: str, password: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """
    Authenticates user credentials against the stored password hash.
    
    Returns:
        (success, message, safe_user_dict_without_password)
    """
    if not email or not password:
        return False, "Email and password are required.", None

    user = get_user_by_email(email.strip().lower())
    if not user:
        # Uniform failure message to prevent email enumeration
        return False, "Invalid email or password.", None

    if not check_password_hash(user['password_hash'], password):
        return False, "Invalid email or password.", None

    # Return safe user dictionary without password_hash
    safe_user = {
        'id': user['id'],
        'name': user['name'],
        'email': user['email'],
        'role': user['role'],
        'created_at': user['created_at']
    }

    return True, "Authentication successful.", safe_user

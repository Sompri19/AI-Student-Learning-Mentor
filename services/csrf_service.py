"""
Cross-Site Request Forgery (CSRF) Protection Service.
AI Student Learning Mentor - Phase 8 System Polish & Security.

Provides lightweight, session-backed CSRF token generation and validation
without introducing heavy external framework dependencies.
"""
import secrets
import hmac
from flask import session


def generate_csrf_token() -> str:
    """
    Generates or retrieves the active session-bound CSRF token.
    Uses cryptographically strong pseudorandom hex generation (32 bytes = 64 hex chars).
    """
    if '_csrf_token' not in session:
        session['_csrf_token'] = secrets.token_hex(32)
    return session['_csrf_token']


def validate_csrf_token(token: str) -> bool:
    """
    Validates a submitted CSRF token against the active session's token.
    Uses timing-attack resistant comparison (hmac.compare_digest).
    """
    if not token or not isinstance(token, str):
        return False
    session_token = session.get('_csrf_token')
    if not session_token or not isinstance(session_token, str):
        return False
    return hmac.compare_digest(token.strip(), session_token.strip())


def rotate_csrf_token() -> str:
    """
    Rotates the session CSRF token, e.g. upon user login or logout.
    """
    session['_csrf_token'] = secrets.token_hex(32)
    return session['_csrf_token']

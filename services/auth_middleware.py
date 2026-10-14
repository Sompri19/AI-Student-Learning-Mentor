"""
Authentication Middleware and Decorators.
Provides reusable access-control decorators for Flask routes.
"""
from functools import wraps
from flask import session, redirect, url_for, flash, request, jsonify


def login_required(f):
    """
    Decorator to ensure a user is logged in before accessing a route.
    For standard browser requests, redirects unauthenticated users to /login with next-URL.
    For API endpoints (/api/*), returns a 401 Unauthorized JSON response.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            if request.path.startswith('/api/'):
                return jsonify({
                    "status": "error",
                    "message": "Authentication required. Please sign in to access this resource."
                }), 401
            flash("Please log in to access this page.", "warning")
            # Store the requested URL in query string for post-login redirect
            return redirect(url_for('login', next=request.path))
        return f(*args, **kwargs)
    return decorated_function

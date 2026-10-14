"""
Authentication Routes for AI Student Learning Mentor.
Handles user registration, login, logout, and session lifecycle.
"""
from urllib.parse import urlparse, urljoin
from flask import (
    Blueprint, render_template, request,
    redirect, url_for, flash, session
)
from services.auth_service import register_user, authenticate_user
from services.csrf_service import rotate_csrf_token

auth_bp = Blueprint('auth', __name__)


def is_safe_redirect_url(target: str) -> bool:
    """
    Validates redirect URL to prevent Open Redirect attacks.
    Only allows relative local paths.
    """
    if not target:
        return False
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc


def _get_auth_fn(name: str, default_fn):
    """
    Retrieves auth function from app module if monkey-patched (e.g. by unit tests),
    falling back to the standard service function.
    """
    import sys
    app_mod = sys.modules.get('app')
    if app_mod and hasattr(app_mod, name):
        return getattr(app_mod, name)
    return default_fn


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """
    User registration with input validation and password hashing.
    """
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        # Validate password match
        if password != confirm_password:
            flash("Passwords do not match. Please verify and retype.", "danger")
            return render_template('auth/register.html', name=name, email=email), 400

        auth_fn = _get_auth_fn('register_user', register_user)
        success, message, new_user_id = auth_fn(name, email, password)
        if not success:
            flash(message, "danger")
            return render_template('auth/register.html', name=name, email=email), 400

        flash("Registration successful! You may now sign in.", "success")
        return redirect(url_for('login'))

    return render_template('auth/register.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    User authentication with email and password.
    Manages secure session creation.
    """
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    next_page = request.args.get('next', '')

    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        next_target = request.form.get('next', '')

        auth_fn = _get_auth_fn('authenticate_user', authenticate_user)
        success, message, user = auth_fn(email, password)
        if not success or not user:
            flash("Invalid email or password.", "danger")
            return render_template('auth/login.html', email=email, next=next_target), 401

        # Initialize user session
        session.clear()
        rotate_csrf_token()
        session['user_id'] = user['id']
        session['user_name'] = user['name']
        session['user_email'] = user['email']
        session['user_role'] = user['role']

        flash(f"Welcome back, {user['name']}!", "success")

        if next_target and is_safe_redirect_url(next_target):
            return redirect(next_target)
        return redirect(url_for('dashboard'))

    return render_template('auth/login.html', next=next_page)


@auth_bp.route('/logout', methods=['GET'])
def logout():
    """
    Clears session and logs out user.
    """
    session.clear()
    rotate_csrf_token()
    flash("You have been signed out successfully.", "info")
    return redirect(url_for('login'))

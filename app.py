"""
AI Student Learning Mentor - Application Entry Point
Flask web application for personalized student mentorship.
Provides application factory, middleware, blueprints registration, and root routing.
"""
import os
from urllib.parse import urlparse, urljoin
from flask import (
    Flask, jsonify, render_template, request,
    url_for, abort, session
)
from config import Config
from services.db import check_db_health
from services.auth_service import register_user, authenticate_user, get_user_by_id
from services.csrf_service import generate_csrf_token, validate_csrf_token
from services.markdown_service import render_markdown
from routes import (
    auth_bp, dashboard_bp, profile_bp, study_plan_bp,
    resource_bp, quiz_bp, progress_bp, ai_bp
)
from routes.auth_routes import is_safe_redirect_url


def create_app(config_class=Config):
    """
    Application factory for AI Student Learning Mentor.
    """
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Enforce that production cannot silently run with empty or default dev SECRET_KEY
    env = str(app.config.get('ENV', os.getenv('FLASK_ENV', 'development'))).lower().strip()
    secret_key = app.config.get('SECRET_KEY')
    if env in ('production', 'prod'):
        if not secret_key or secret_key == 'change-this-secret-key':
            raise ValueError(
                "CRITICAL SECURITY CONFIGURATION: A secure, random SECRET_KEY must be "
                "provided via environment variable in production environments. "
                "The default development fallback is forbidden."
            )

    # Register session-backed CSRF generator globally for all Jinja templates
    app.jinja_env.globals['csrf_token'] = generate_csrf_token

    # Render AI Mentor answers (Markdown) as sanitised HTML in templates
    app.jinja_env.filters['markdown'] = render_markdown

    # Register feature blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(study_plan_bp)
    app.register_blueprint(resource_bp)
    app.register_blueprint(quiz_bp)
    app.register_blueprint(progress_bp)
    app.register_blueprint(ai_bp)

    # Blueprint url_for endpoint fallback for backward compatibility
    # Allows both flat url_for('login') and blueprint-scoped url_for('auth.login') to resolve seamlessly
    def url_build_fallback(error, endpoint, values):
        for bp_name in app.blueprints:
            candidate = f'{bp_name}.{endpoint}'
            if candidate in app.view_functions:
                return url_for(candidate, **values)
        raise error

    app.url_build_error_handlers.append(url_build_fallback)

    @app.before_request
    def verify_csrf():
        """
        Lightweight CSRF and Origin protection verification hook.
        Safely enforces CSRF checks on state-modifying HTTP requests.
        """
        if request.method in ('GET', 'HEAD', 'OPTIONS', 'TRACE'):
            return None

        if not app.config.get('CSRF_ENABLED', True):
            return None

        # Cross-origin protection
        origin = request.headers.get('Origin')
        if origin:
            origin_netloc = urlparse(origin).netloc
            host_netloc = urlparse(request.host_url).netloc
            if origin_netloc and host_netloc and origin_netloc != host_netloc:
                abort(403, description="Cross-origin request forbidden.")
        elif request.headers.get('Referer'):
            referer_netloc = urlparse(request.headers.get('Referer')).netloc
            host_netloc = urlparse(request.host_url).netloc
            if referer_netloc and host_netloc and referer_netloc != host_netloc:
                abort(403, description="Cross-origin referer forbidden.")

        # CSRF token check
        token = (
            request.form.get('csrf_token') or 
            request.headers.get('X-CSRF-Token') or 
            request.headers.get('X-CSRFToken')
        )
        if token:
            if not validate_csrf_token(token):
                abort(400, description="Invalid or expired CSRF token.")
        elif app.config.get('CSRF_STRICT', False):
            abort(400, description="CSRF token missing from request.")

        return None

    @app.after_request
    def set_security_headers(response):
        """
        Injects application-level security headers for defense-in-depth:
        - X-Content-Type-Options: nosniff
        - X-Frame-Options: SAMEORIGIN
        - Referrer-Policy: strict-origin-when-cross-origin
        """
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        return response

    @app.context_processor
    def inject_user_context():
        """
        Injects current authenticated user info into all template contexts.
        """
        current_user = None
        if 'user_id' in session:
            current_user = {
                'id': session.get('user_id'),
                'name': session.get('user_name'),
                'email': session.get('user_email'),
                'role': session.get('user_role')
            }
        return dict(current_user=current_user)

    # -------------------------------------------------------------------------
    # Public Routes (Landing & Health)
    # -------------------------------------------------------------------------
    @app.route('/', methods=['GET'])
    def index():
        """
        Landing page showcasing project overview and feature previews.
        All preview items are informational placeholders for future modules.
        """
        features = [
            {
                "title": "Personalized Study Plan",
                "icon": "📚",
                "description": "Custom day-by-day learning schedules tailored to your target subjects, available study hours, and academic deadlines."
            },
            {
                "title": "Quiz & Practice",
                "icon": "📝",
                "description": "Topic-based multiple choice assessments to validate knowledge retention and identify concept gaps."
            },
            {
                "title": "AI Doubt Assistant",
                "icon": "🤖",
                "description": "Interactive academic mentor providing step-by-step conceptual explanations without generating fabricated answers."
            },
            {
                "title": "Progress Tracking",
                "icon": "📊",
                "description": "Real-time topic mastery dashboards and milestone trackers reflecting honest academic progress."
            },
            {
                "title": "Learning Goals",
                "icon": "🎯",
                "description": "Set educational targets, specify target skill levels, and monitor curriculum coverage systematically."
            },
            {
                "title": "Integrated Mentorship Platform",
                "icon": "🎓",
                "description": "Seamless cross-feature learning workflow with unified navigation, student dashboard, and security."
            }
        ]
        
        return render_template(
            'index.html',
            project_name=app.config.get('PROJECT_NAME', Config.PROJECT_NAME),
            phase=app.config.get('CURRENT_PHASE', Config.CURRENT_PHASE),
            features=features
        )

    @app.route('/api/health', methods=['GET'])
    def health_check():
        """
        Health endpoint reporting application and database connectivity status.
        Does not report 'healthy' if database is unavailable.
        """
        db_health = check_db_health()
        
        is_healthy = db_health["connected"] and db_health["database_exists"]
        overall_status = "healthy" if is_healthy else "unhealthy"
        status_code = 200 if is_healthy else 503

        response = {
            "status": overall_status,
            "project": app.config.get('PROJECT_NAME', Config.PROJECT_NAME),
            "phase": app.config.get('CURRENT_PHASE', Config.CURRENT_PHASE),
            "database": {
                "connected": db_health["connected"],
                "database_exists": db_health["database_exists"],
                "database_name": db_health["database_name"]
            }
        }
        
        if not is_healthy and db_health.get("error"):
            response["database"]["message"] = db_health["error"]

        return jsonify(response), status_code

    # -------------------------------------------------------------------------
    # Custom Error Handlers
    # -------------------------------------------------------------------------
    @app.errorhandler(400)
    def bad_request(e):
        msg = getattr(e, 'description', 'Bad Request')
        if request.path.startswith('/api/'):
            return jsonify({"status": "error", "message": msg}), 400
        return render_template(
            'error.html',
            error_code=400,
            error_title="Bad Request",
            message=msg
        ), 400

    @app.errorhandler(401)
    def unauthorized(e):
        msg = getattr(e, 'description', 'Authentication Required')
        if request.path.startswith('/api/'):
            return jsonify({"status": "error", "message": msg}), 401
        return render_template(
            'error.html',
            error_code=401,
            error_title="Authentication Required",
            message=msg
        ), 401

    @app.errorhandler(403)
    def access_forbidden(e):
        msg = getattr(e, 'description', 'Access Forbidden')
        if request.path.startswith('/api/'):
            return jsonify({"status": "error", "message": msg}), 403
        return render_template(
            'error.html',
            error_code=403,
            error_title="Access Forbidden",
            message=msg
        ), 403

    @app.errorhandler(404)
    def page_not_found(e):
        msg = getattr(e, 'description', 'Resource not found.')
        if request.path.startswith('/api/'):
            return jsonify({
                "status": "error",
                "message": msg
            }), 404
        return render_template('404.html', message=msg), 404

    @app.errorhandler(405)
    def method_not_allowed(e):
        msg = getattr(e, 'description', 'Method Not Allowed')
        if request.path.startswith('/api/'):
            return jsonify({"status": "error", "message": msg}), 405
        return render_template(
            'error.html',
            error_code=405,
            error_title="Method Not Allowed",
            message=msg
        ), 405

    @app.errorhandler(429)
    def too_many_requests(e):
        msg = getattr(e, 'description', 'Too Many Requests')
        if request.path.startswith('/api/'):
            return jsonify({"status": "error", "message": msg}), 429
        return render_template(
            'error.html',
            error_code=429,
            error_title="Too Many Requests",
            message=msg
        ), 429

    @app.errorhandler(500)
    def internal_server_error(e):
        msg = "An unexpected server error occurred. Please try again shortly."
        if request.path.startswith('/api/'):
            return jsonify({"status": "error", "message": msg}), 500
        return render_template(
            '500.html',
            error_code=500,
            error_title="Internal Server Error",
            message=msg
        ), 500

    return app


# Root application instance for direct execution / WSGI
app = create_app()

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)

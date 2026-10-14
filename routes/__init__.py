"""
Routes package for AI Student Learning Mentor.
Exports all feature blueprints for application registration.
"""
from routes.auth_routes import auth_bp
from routes.dashboard_routes import dashboard_bp
from routes.profile_routes import profile_bp
from routes.study_plan_routes import study_plan_bp
from routes.resource_routes import resource_bp
from routes.quiz_routes import quiz_bp
from routes.progress_routes import progress_bp
from routes.ai_routes import ai_bp

__all__ = [
    'auth_bp',
    'dashboard_bp',
    'profile_bp',
    'study_plan_bp',
    'resource_bp',
    'quiz_bp',
    'progress_bp',
    'ai_bp',
]

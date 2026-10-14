"""
Dashboard Routes for AI Student Learning Mentor.
Handles student dashboard presentation, learning progress overview, and activity metrics.
"""
from flask import Blueprint, render_template, session
from services.auth_middleware import login_required
from services.auth_service import get_user_by_id
from services.profile_service import get_student_profile, calculate_profile_completion
from services.study_plan_service import get_user_study_plans, get_user_study_stats
from services.quiz_service import get_user_quiz_stats
from services.progress_service import (
    get_overall_progress, get_subject_progress, get_weak_topics,
    get_learning_statistics, get_recent_activity
)

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/dashboard', methods=['GET'])
@login_required
def dashboard():
    """
    Student Dashboard Foundation.
    Displays student name, profile status, selected course, skill level, and goals.
    Does NOT show fabricated progress, fake quiz scores, or fake AI metrics.
    """
    user_id = session['user_id']
    user = get_user_by_id(user_id)
    profile = get_student_profile(user_id)
    completion = calculate_profile_completion(profile)
    study_plans = get_user_study_plans(user_id)
    study_stats = get_user_study_stats(user_id)
    quiz_stats = get_user_quiz_stats(user_id)
    overall_progress = get_overall_progress(user_id)
    subject_progress = get_subject_progress(user_id)
    weak_topics = get_weak_topics(user_id)
    learning_stats = get_learning_statistics(user_id)
    recent_activity = get_recent_activity(user_id, limit=6)

    return render_template(
        'dashboard/dashboard.html',
        user=user,
        profile=profile,
        completion=completion,
        study_plans=study_plans,
        study_stats=study_stats,
        quiz_stats=quiz_stats,
        overall_progress=overall_progress,
        subject_progress=subject_progress,
        weak_topics=weak_topics,
        learning_stats=learning_stats,
        recent_activity=recent_activity
    )

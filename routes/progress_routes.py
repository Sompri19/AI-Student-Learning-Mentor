"""
Progress Tracking & Student Dashboard Routes for AI Student Learning Mentor.
Handles progress summary, subject mastery, topic analytics, learning statistics, and activity timeline APIs.
Strictly requires authentication; student progress is strictly isolated.
"""
from flask import Blueprint, render_template, request, session, jsonify
from services.auth_middleware import login_required
from services.auth_service import get_user_by_id
from services.profile_service import get_student_profile
from services.content_service import get_all_subjects
from services.progress_service import (
    get_topic_progress, get_subject_progress, get_overall_progress,
    get_weak_topics, get_learning_statistics, get_recent_activity
)

progress_bp = Blueprint('progress', __name__)


# -------------------------------------------------------------------------
# Web Template Routes
# -------------------------------------------------------------------------

@progress_bp.route('/progress', methods=['GET'])
@login_required
def progress_page():
    """
    Dedicated Student Progress & Mastery Center.
    Displays overall progress, subject progress breakdown, topic-by-topic
    mastery metrics, weak areas needing practice, and recent activity timeline.
    """
    user_id = session['user_id']
    user = get_user_by_id(user_id)
    profile = get_student_profile(user_id)
    subjects = get_all_subjects()
    selected_subject_id = request.args.get('subject_id', type=int)

    overall_progress = get_overall_progress(user_id)
    subject_progress = get_subject_progress(user_id)
    topic_progress = get_topic_progress(user_id, subject_id=selected_subject_id)
    weak_topics = get_weak_topics(user_id)
    learning_stats = get_learning_statistics(user_id)
    recent_activity = get_recent_activity(user_id, limit=15)

    return render_template(
        'progress/progress.html',
        user=user,
        profile=profile,
        subjects=subjects,
        selected_subject_id=selected_subject_id,
        overall_progress=overall_progress,
        subject_progress=subject_progress,
        topic_progress=topic_progress,
        weak_topics=weak_topics,
        learning_stats=learning_stats,
        recent_activity=recent_activity
    )


# -------------------------------------------------------------------------
# Progress Analytics APIs
# -------------------------------------------------------------------------

@progress_bp.route('/api/progress', methods=['GET'])
@login_required
def api_progress_summary():
    """
    API: Returns comprehensive progress summary for authenticated student.
    """
    user_id = session['user_id']
    overall = get_overall_progress(user_id)
    stats = get_learning_statistics(user_id)
    subjects = get_subject_progress(user_id)
    weak = get_weak_topics(user_id)
    activity = get_recent_activity(user_id, limit=10)

    # Format datetimes for JSON serialization
    for item in activity:
        if item.get("timestamp") and hasattr(item["timestamp"], "isoformat"):
            item["timestamp"] = item["timestamp"].isoformat()
    for s in subjects:
        if s.get("last_activity") and hasattr(s["last_activity"], "isoformat"):
            s["last_activity"] = s["last_activity"].isoformat()

    return jsonify({
        "status": "success",
        "overall_progress": overall["overall_percentage"],
        "overall_status": overall["status"],
        "statistics": stats,
        "subjects": subjects,
        "weak_topics": weak,
        "recent_activity": activity
    }), 200


@progress_bp.route('/api/progress/subjects', methods=['GET'])
@login_required
def api_progress_subjects():
    """
    API: Returns subject-level progress metrics for authenticated student.
    """
    user_id = session['user_id']
    subjects = get_subject_progress(user_id)
    for s in subjects:
        if s.get("last_activity") and hasattr(s["last_activity"], "isoformat"):
            s["last_activity"] = s["last_activity"].isoformat()
    return jsonify({
        "status": "success",
        "subjects": subjects
    }), 200


@progress_bp.route('/api/progress/topics', methods=['GET'])
@login_required
def api_progress_topics():
    """
    API: Returns granular topic-level progress metrics for authenticated student.
    Optionally filters by ?subject_id=<int>.
    """
    user_id = session['user_id']
    subject_id = request.args.get('subject_id', type=int)
    topics = get_topic_progress(user_id, subject_id=subject_id)
    for t in topics:
        if t.get("last_activity") and hasattr(t["last_activity"], "isoformat"):
            t["last_activity"] = t["last_activity"].isoformat()
    return jsonify({
        "status": "success",
        "topics": topics
    }), 200


@progress_bp.route('/api/progress/statistics', methods=['GET'])
@login_required
def api_progress_statistics():
    """
    API: Returns aggregate learning statistics for authenticated student.
    """
    user_id = session['user_id']
    stats = get_learning_statistics(user_id)
    return jsonify({
        "status": "success",
        "statistics": stats
    }), 200


@progress_bp.route('/api/progress/activity', methods=['GET'])
@login_required
def api_progress_activity():
    """
    API: Returns chronological learning activity feed for authenticated student.
    Optionally accepts ?limit=<int> (default 10, max 50).
    """
    user_id = session['user_id']
    limit = request.args.get('limit', default=10, type=int)
    limit = max(1, min(limit, 50))
    activity = get_recent_activity(user_id, limit=limit)
    for item in activity:
        if item.get("timestamp") and hasattr(item["timestamp"], "isoformat"):
            item["timestamp"] = item["timestamp"].isoformat()
    return jsonify({
        "status": "success",
        "activity": activity
    }), 200

"""
Resource & Educational Content Routes for AI Student Learning Mentor.
Handles browsing subjects, topics, learning materials, and content discovery APIs.
Publicly accessible to both guests and authenticated students.
"""
from flask import (
    Blueprint, render_template, request,
    abort, jsonify
)
from services.content_service import (
    get_all_subjects, get_subject_by_id, get_topics_by_subject,
    get_topic_by_id, get_resources_by_topic, search_content,
    get_filter_meta
)

resource_bp = Blueprint('resource', __name__)


# -------------------------------------------------------------------------
# Web Template Routes
# -------------------------------------------------------------------------

@resource_bp.route('/subjects', methods=['GET'])
def subjects_list():
    """
    Browse all subjects and search/filter across the curriculum.
    """
    search_query = request.args.get('q', '').strip()
    selected_subject = request.args.get('subject_id', type=int)
    selected_difficulty = request.args.get('difficulty', '').strip()
    selected_resource_type = request.args.get('resource_type', '').strip()

    is_searching = bool(
        search_query or selected_subject or selected_difficulty or selected_resource_type
    )

    filter_meta = get_filter_meta()

    if is_searching:
        search_results = search_content(
            query=search_query,
            subject_id=selected_subject,
            difficulty=selected_difficulty if selected_difficulty else None,
            resource_type=selected_resource_type if selected_resource_type else None
        )
        return render_template(
            'resources/resources.html',
            subjects=search_results["subjects"],
            topics=search_results["topics"],
            resources=search_results["resources"],
            total_matches=search_results["total_matches"],
            is_searching=True,
            search_query=search_query,
            selected_subject=selected_subject,
            selected_difficulty=selected_difficulty,
            selected_resource_type=selected_resource_type,
            filter_meta=filter_meta
        )
    else:
        subjects = get_all_subjects()
        return render_template(
            'resources/resources.html',
            subjects=subjects,
            is_searching=False,
            filter_meta=filter_meta
        )


@resource_bp.route('/subjects/<int:subject_id>', methods=['GET'])
def subject_detail(subject_id: int):
    """
    View details and all syllabus topics for a specific subject.
    """
    subject = get_subject_by_id(subject_id)
    if not subject:
        abort(404, description=f"Subject with ID {subject_id} not found.")

    selected_difficulty = request.args.get('difficulty', '').strip()
    topics = get_topics_by_subject(
        subject_id, 
        difficulty=selected_difficulty if selected_difficulty else None
    )

    return render_template(
        'resources/subject_detail.html',
        subject=subject,
        topics=topics,
        selected_difficulty=selected_difficulty,
        allowed_difficulties=['Beginner', 'Intermediate', 'Advanced']
    )


@resource_bp.route('/topics/<int:topic_id>', methods=['GET'])
def topic_detail(topic_id: int):
    """
    View syllabus topic details and verified educational resources.
    """
    topic = get_topic_by_id(topic_id)
    if not topic:
        abort(404, description=f"Topic with ID {topic_id} not found.")

    selected_type = request.args.get('resource_type', '').strip()
    selected_difficulty = request.args.get('difficulty', '').strip()

    resources = get_resources_by_topic(
        topic_id,
        resource_type=selected_type if selected_type else None,
        difficulty=selected_difficulty if selected_difficulty else None
    )

    return render_template(
        'resources/topic_detail.html',
        topic=topic,
        resources=resources,
        selected_type=selected_type,
        selected_difficulty=selected_difficulty,
        allowed_types=['Notes', 'Video', 'Documentation', 'Article', 'Practice'],
        allowed_difficulties=['Beginner', 'Intermediate', 'Advanced']
    )


# -------------------------------------------------------------------------
# Read-Only Educational Content APIs
# -------------------------------------------------------------------------

@resource_bp.route('/api/subjects', methods=['GET'])
def api_get_subjects():
    """
    API: Retrieve all subjects with topic counts.
    """
    q = request.args.get('q', '')
    subjects = get_all_subjects(search_query=q)
    return jsonify({
        "status": "success",
        "count": len(subjects),
        "subjects": subjects
    }), 200


@resource_bp.route('/api/subjects/<int:subject_id>', methods=['GET'])
def api_get_subject_detail(subject_id: int):
    """
    API: Retrieve subject details and its syllabus topics.
    """
    subject = get_subject_by_id(subject_id)
    if not subject:
        return jsonify({"status": "error", "message": "Subject not found."}), 404

    topics = get_topics_by_subject(subject_id)
    return jsonify({
        "status": "success",
        "subject": subject,
        "topics": topics
    }), 200


@resource_bp.route('/api/topics/<int:topic_id>', methods=['GET'])
def api_get_topic_detail(topic_id: int):
    """
    API: Retrieve topic details and verified educational resources.
    """
    topic = get_topic_by_id(topic_id)
    if not topic:
        return jsonify({"status": "error", "message": "Topic not found."}), 404

    resources = get_resources_by_topic(topic_id)
    return jsonify({
        "status": "success",
        "topic": topic,
        "resources": resources
    }), 200


@resource_bp.route('/api/resources', methods=['GET'])
def api_get_resources():
    """
    API: Search and filter educational resources.
    """
    q = request.args.get('q', '').strip()
    subject_id = request.args.get('subject_id', type=int)
    difficulty = request.args.get('difficulty', '').strip() or None
    resource_type = request.args.get('resource_type', '').strip() or None

    results = search_content(
        query=q,
        subject_id=subject_id,
        difficulty=difficulty,
        resource_type=resource_type
    )

    return jsonify({
        "status": "success",
        "total_matches": results["total_matches"],
        "resources": results["resources"]
    }), 200


@resource_bp.route('/api/subjects/<int:subject_id>/topics', methods=['GET'])
def api_get_subject_topics(subject_id: int):
    """
    API: Retrieve syllabus topics for a specific subject.
    """
    subject = get_subject_by_id(subject_id)
    if not subject:
        return jsonify({"status": "error", "message": "Subject not found."}), 404

    topics = get_topics_by_subject(subject_id)
    return jsonify({
        "status": "success",
        "subject_id": subject_id,
        "topics": topics
    }), 200

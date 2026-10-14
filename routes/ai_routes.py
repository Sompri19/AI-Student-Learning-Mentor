"""
AI Doubt Assistant Routes for AI Student Learning Mentor.
Handles conceptual academic queries, rate limiting, conversation history, and AI mentor APIs.
Strictly requires authentication; student dialogue is strictly isolated.
"""
from flask import (
    Blueprint, render_template, request, session,
    flash, jsonify, current_app
)
from services.auth_middleware import login_required
from services.content_service import get_all_subjects, get_topics_by_subject
from services.ai_service import (
    validate_academic_question, check_rate_limit, ask_ai,
    save_ai_chat, get_user_ai_history, get_ai_chat_detail
)

ai_bp = Blueprint('ai', __name__)


# -------------------------------------------------------------------------
# Web Template Routes
# -------------------------------------------------------------------------

@ai_bp.route('/ai', methods=['GET'])
@login_required
def ai_assistant():
    """
    AI Doubt Assistant interface.
    Allows student to ask conceptual questions directly with optional subject context.
    """
    subjects = get_all_subjects()
    subject_id = request.args.get('subject_id', type=int)

    return render_template(
        'ai_assistant/chat.html',
        subjects=subjects,
        selected_subject_id=subject_id
    )


@ai_bp.route('/ai/ask', methods=['POST'])
@login_required
def ai_ask():
    """
    Processes academic question submission from the web form.
    Validates question, applies cooldown rate limit, calls AI provider,
    and saves genuine responses to chat history.
    """
    user_id = session['user_id']
    question = request.form.get('question', '')

    # Parse optional subject (topic selection has been removed from UI)
    subject_id_raw = request.form.get('subject_id')
    topic_id_raw = request.form.get('topic_id')
    subject_id = int(subject_id_raw) if subject_id_raw and subject_id_raw.isdigit() else None
    topic_id = int(topic_id_raw) if topic_id_raw and topic_id_raw.isdigit() else None

    subjects = get_all_subjects()

    # Server-side input validation
    is_valid, err_msg, validated = validate_academic_question(
        question=question,
        subject_id=subject_id,
        topic_id=topic_id
    )
    if not is_valid:
        flash(err_msg, "danger")
        return render_template(
            'ai_assistant/chat.html',
            subjects=subjects,
            selected_subject_id=subject_id,
            question=question
        ), 400

    # Rate limiting / abuse protection
    cooldown = current_app.config.get('AI_RATE_LIMIT_SECONDS', 5)
    allowed, wait_msg = check_rate_limit(user_id, cooldown_seconds=cooldown)
    if not allowed:
        flash(wait_msg, "warning")
        return render_template(
            'ai_assistant/chat.html',
            subjects=subjects,
            selected_subject_id=subject_id,
            question=question
        ), 429

    # Query AI mentor provider
    success, answer_or_msg = ask_ai(
        question=validated["question"],
        subject_name=validated["subject_name"],
        topic_name=validated.get("topic_name")
    )

    if not success:
        flash(answer_or_msg, "warning")
        return render_template(
            'ai_assistant/chat.html',
            subjects=subjects,
            selected_subject_id=subject_id,
            question=question
        ), 503

    # Save successful dialogue to database
    save_ai_chat(user_id, validated["question"], answer_or_msg)

    return render_template(
        'ai_assistant/chat.html',
        subjects=subjects,
        selected_subject_id=subject_id,
        question=validated["question"],
        answer=answer_or_msg,
        subject_name=validated["subject_name"],
        topic_name=validated.get("topic_name")
    )


@ai_bp.route('/ai/history', methods=['GET'])
@login_required
def ai_history():
    """
    Student's AI conversation history.
    Strictly isolates dialogue to authenticated user.
    """
    user_id = session['user_id']
    chats = get_user_ai_history(user_id)
    return render_template('ai_assistant/ai_history.html', chats=chats)


# -------------------------------------------------------------------------
# AI Doubt Assistant API Endpoints
# -------------------------------------------------------------------------

@ai_bp.route('/api/ai/ask', methods=['POST'])
@login_required
def api_ai_ask():
    """
    API: Ask academic question to AI Mentor.
    JSON format: {"question": "...", "subject_id": 1, "topic_id": 5}
    Returns: {"success": true, "answer": "...", "chat_id": 123}
    """
    user_id = session['user_id']
    req_json = request.get_json(silent=True) or {}
    question = req_json.get('question')
    subject_id = req_json.get('subject_id')
    topic_id = req_json.get('topic_id')

    try:
        subject_id = int(subject_id) if subject_id is not None else None
    except (ValueError, TypeError):
        subject_id = None

    try:
        topic_id = int(topic_id) if topic_id is not None else None
    except (ValueError, TypeError):
        topic_id = None

    is_valid, err_msg, validated = validate_academic_question(
        question=question,
        subject_id=subject_id,
        topic_id=topic_id
    )
    if not is_valid:
        return jsonify({"success": False, "message": err_msg}), 400

    cooldown = current_app.config.get('AI_RATE_LIMIT_SECONDS', 5)
    allowed, wait_msg = check_rate_limit(user_id, cooldown_seconds=cooldown)
    if not allowed:
        return jsonify({"success": False, "message": wait_msg}), 429

    success, answer_or_msg = ask_ai(
        question=validated["question"],
        subject_name=validated["subject_name"],
        topic_name=validated["topic_name"]
    )

    if not success:
        return jsonify({"success": False, "message": answer_or_msg}), 503

    save_success, save_msg, chat_id = save_ai_chat(
        user_id, validated["question"], answer_or_msg
    )

    return jsonify({
        "success": True,
        "answer": answer_or_msg,
        "chat_id": chat_id
    }), 201


@ai_bp.route('/api/ai/history', methods=['GET'])
@login_required
def api_ai_history():
    """
    API: Returns authenticated student's AI chat history.
    """
    user_id = session['user_id']
    chats = get_user_ai_history(user_id)
    return jsonify({
        "status": "success",
        "chats": chats
    }), 200


@ai_bp.route('/api/ai/history/<int:chat_id>', methods=['GET'])
@login_required
def api_ai_chat_detail(chat_id: int):
    """
    API: Returns specific chat dialogue with ownership check.
    """
    user_id = session['user_id']
    chat = get_ai_chat_detail(chat_id, user_id)
    if not chat:
        return jsonify({
            "status": "error",
            "message": "Chat conversation not found or you do not have permission to view it."
        }), 404

    return jsonify({
        "status": "success",
        "chat": chat
    }), 200

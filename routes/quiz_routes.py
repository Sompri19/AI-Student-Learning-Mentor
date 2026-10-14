"""
Quiz & Practice Engine Routes for AI Student Learning Mentor.
Handles topic quizzes, question generation, answer evaluation, scoring, attempt history, and quiz APIs.
"""
from flask import (
    Blueprint, render_template, request,
    redirect, url_for, flash, session, abort, jsonify
)
from services.auth_middleware import login_required
from services.quiz_service import (
    get_available_quizzes_catalog, get_topic_quiz_info,
    get_quiz_questions_for_topic, submit_quiz_attempt,
    get_quiz_attempt_result, get_quiz_attempt_review,
    get_user_quiz_history, get_user_quiz_stats
)

quiz_bp = Blueprint('quiz', __name__)


# -------------------------------------------------------------------------
# Web Template Routes
# -------------------------------------------------------------------------

@quiz_bp.route('/quizzes', methods=['GET'])
@login_required
def quizzes_catalog():
    """
    Practice Quizzes Catalog.
    Displays all available topic-level practice quizzes grouped by subject.
    """
    user_id = session['user_id']
    catalog = get_available_quizzes_catalog()
    stats = get_user_quiz_stats(user_id)
    return render_template(
        'quiz/quizzes.html',
        catalog=catalog,
        subjects=catalog,
        stats=stats
    )


@quiz_bp.route('/quizzes/topic/<int:topic_id>', methods=['GET'])
@login_required
def quiz_topic_preview(topic_id: int):
    """
    Topic Quiz Briefing / Instructions page.
    Prepares the student before starting the timed practice session.
    """
    info = get_topic_quiz_info(topic_id)
    if not info:
        abort(404, description="Topic not found.")

    topic = {
        'id': info['topic_id'],
        'topic_id': info['topic_id'],
        'topic_name': info['topic_name'],
        'description': info['topic_description'],
        'topic_description': info['topic_description'],
        'difficulty': info['topic_difficulty'],
        'topic_difficulty': info['topic_difficulty'],
        'subject_name': info['subject_name'],
        'subject_id': info['subject_id'],
        'question_count': info['question_count']
    }
    subject = {
        'id': info['subject_id'],
        'name': info['subject_name']
    }
    return render_template(
        'quiz/quiz_start.html',
        topic=topic,
        subject=subject,
        total_questions=info['question_count']
    )


@quiz_bp.route('/quiz/<int:topic_id>/start', methods=['GET'])
@quiz_bp.route('/quiz/topic/<int:topic_id>/start', methods=['GET'])
@login_required
def quiz_start(topic_id: int):
    """
    Active Practice Quiz Interface.
    Fetches genuine questions from MySQL without exposing correct answers.
    """
    info = get_topic_quiz_info(topic_id)
    if not info:
        abort(404, description="Topic not found.")

    if info['question_count'] == 0:
        flash("No practice questions are currently available for this topic.", "info")
        return redirect(url_for('quizzes_catalog'))

    questions = get_quiz_questions_for_topic(
        topic_id,
        limit=10,
        randomize=True,
        include_correct=False
    )
    topic = {
        'id': info['topic_id'],
        'topic_id': info['topic_id'],
        'topic_name': info['topic_name'],
        'description': info['topic_description'],
        'difficulty': info['topic_difficulty'],
        'subject_name': info['subject_name'],
        'subject_id': info['subject_id']
    }
    subject = {
        'id': info['subject_id'],
        'name': info['subject_name']
    }
    return render_template(
        'quiz/quiz.html',
        topic=topic,
        subject=subject,
        questions=questions
    )


@quiz_bp.route('/quiz/<int:topic_id>/submit', methods=['POST'])
@quiz_bp.route('/quiz/submit', methods=['POST'])
@login_required
def quiz_submit(topic_id: int = None):
    """
    Submits student answers, evaluates score against database, and saves attempt.
    """
    user_id = session['user_id']
    if topic_id is None:
        try:
            topic_id = int(request.form.get('topic_id') or 0)
        except (ValueError, TypeError):
            topic_id = 0

    if not topic_id:
        abort(404, description="Topic identifier is required.")

    info = get_topic_quiz_info(topic_id)
    if not info:
        abort(404, description="Topic not found.")

    # Extract submitted answers: form inputs named 'question_<id>'
    submitted_answers = {}
    for key, val in request.form.items():
        if key.startswith('question_'):
            try:
                qid = int(key.replace('question_', ''))
                submitted_answers[qid] = val.strip().upper()
            except (ValueError, TypeError):
                pass

    success, message, attempt_id = submit_quiz_attempt(
        user_id=user_id,
        topic_id=topic_id,
        submitted_answers=submitted_answers
    )

    if not success:
        flash(message, "warning")
        return redirect(url_for('quiz_start', topic_id=topic_id))

    flash("Quiz submitted successfully! Here is your performance breakdown.", "success")
    return redirect(url_for('quiz_result', attempt_id=attempt_id))


@quiz_bp.route('/quiz/results/<int:attempt_id>', methods=['GET'])
@login_required
def quiz_result(attempt_id: int):
    """
    Quiz Result Scorecard.
    Displays calculated percentage, score summary, and performance feedback.
    Enforces user ownership.
    """
    user_id = session['user_id']
    attempt = get_quiz_attempt_result(attempt_id, user_id)
    if not attempt:
        abort(404, description="Quiz attempt not found or you do not have permission to view it.")

    return render_template('quiz/result.html', attempt=attempt)


@quiz_bp.route('/quiz/results/<int:attempt_id>/review', methods=['GET'])
@login_required
def quiz_review(attempt_id: int):
    """
    Detailed Question-by-Question Review.
    Shows question text, student's selected answer, and correct answers.
    Enforces user ownership.
    """
    user_id = session['user_id']
    review_data = get_quiz_attempt_review(attempt_id, user_id)
    if not review_data:
        abort(404, description="Quiz review not found or you do not have permission to view it.")

    return render_template(
        'quiz/quiz_review.html',
        attempt=review_data['attempt'],
        answers=review_data['answers'],
        total_questions=review_data['total_questions'],
        correct_answers=review_data['correct_answers'],
        incorrect_answers=review_data['incorrect_answers']
    )


@quiz_bp.route('/quiz/history', methods=['GET'])
@login_required
def quiz_history():
    """
    Student Practice Quiz History.
    Displays previous attempts with real scores, percentages, and review links.
    """
    user_id = session['user_id']
    attempts = get_user_quiz_history(user_id)
    stats = get_user_quiz_stats(user_id)
    return render_template(
        'quiz/quiz_history.html',
        history=attempts,
        attempts=attempts,
        stats=stats
    )


# -------------------------------------------------------------------------
# Quiz API Endpoints
# -------------------------------------------------------------------------

@quiz_bp.route('/api/quizzes/topic/<int:topic_id>', methods=['GET'])
@login_required
def api_get_topic_quizzes(topic_id: int):
    """
    API: Retrieves questions for a topic.
    Guarantees correct_answer is never exposed.
    """
    info = get_topic_quiz_info(topic_id)
    if not info:
        return jsonify({"status": "error", "message": "Topic not found."}), 404

    limit = request.args.get('limit', default=10, type=int)
    questions = get_quiz_questions_for_topic(
        topic_id,
        limit=limit,
        randomize=False,
        include_correct=False
    )
    return jsonify({
        "status": "success",
        "topic": {
            "id": info["topic_id"],
            "name": info["topic_name"],
            "difficulty": info["topic_difficulty"],
            "subject_name": info["subject_name"]
        },
        "total_questions": len(questions),
        "questions": questions
    }), 200


@quiz_bp.route('/api/quizzes/topic/<int:topic_id>/submit', methods=['POST'])
@quiz_bp.route('/api/quizzes/<int:topic_id>/submit', methods=['POST'])
@login_required
def api_submit_quiz(topic_id: int):
    """
    API: Submits student answers, evaluates score against database, and saves attempt.
    Expected JSON: {"answers": {1: "A", 2: "B"}} or direct mapping {"1": "A", "2": "B"}
    """
    user_id = session['user_id']
    info = get_topic_quiz_info(topic_id)
    if not info:
        return jsonify({"status": "error", "message": "Topic not found."}), 404

    req_json = request.get_json(silent=True) or {}
    answers_payload = req_json.get("answers", req_json)
    if not isinstance(answers_payload, dict):
        return jsonify({
            "status": "error",
            "message": "Invalid answers payload. Expected a dictionary of question IDs to options."
        }), 400

    success, message, attempt_id = submit_quiz_attempt(
        user_id=user_id,
        topic_id=topic_id,
        submitted_answers=answers_payload
    )
    if not success:
        return jsonify({"status": "error", "message": message}), 400

    result = get_quiz_attempt_result(attempt_id, user_id)
    return jsonify({
        "status": "success",
        "message": message,
        "attempt_id": attempt_id,
        "result": result
    }), 201


@quiz_bp.route('/api/quiz-attempts', methods=['GET'])
@login_required
def api_get_quiz_attempts():
    """
    API: Returns student's quiz attempt history and aggregate statistics.
    """
    user_id = session['user_id']
    history = get_user_quiz_history(user_id)
    stats = get_user_quiz_stats(user_id)
    return jsonify({
        "status": "success",
        "stats": stats,
        "attempts": history
    }), 200


@quiz_bp.route('/api/quiz-attempts/<int:attempt_id>', methods=['GET'])
@login_required
def api_get_quiz_attempt_detail(attempt_id: int):
    """
    API: Returns full review and breakdown of a specific attempt with answers.
    Enforces user ownership.
    """
    user_id = session['user_id']
    review_data = get_quiz_attempt_review(attempt_id, user_id)
    if not review_data:
        return jsonify({
            "status": "error",
            "message": "Quiz attempt not found or you do not have permission to view it."
        }), 404

    return jsonify({
        "status": "success",
        "attempt": review_data["attempt"],
        "answers": review_data["answers"]
    }), 200

"""
Quiz & Practice Engine Service for AI Student Learning Mentor.
Manages practice question retrieval, secure quiz submissions,
deterministic score calculation, attempt review, history, and student stats.

Academic Integrity & Security Principles:
- Uses real database records from `quizzes`, `quiz_attempts`, and `quiz_attempt_answers`.
- Never exposes correct answers before submission.
- Re-reads correct answers from MySQL on the server upon submission.
- Strictly enforces student isolation: attempts can only be viewed by their owner.
- Zero fake attempts, synthetic scores, or artificial AI responses.
- Delegates database operations to models.quiz_model and models.subject_model.
"""
import logging
import random
from typing import List, Dict, Any, Optional, Tuple

from models.quiz_model import (
    find_quiz_catalog_grouped,
    find_topic_quiz_info,
    find_quizzes_by_topic,
    find_quiz_questions_by_ids,
    insert_quiz_attempt_with_answers,
    find_quiz_attempt_by_id,
    find_quiz_attempt_answers,
    find_quiz_attempts_by_user,
    find_user_quiz_stats,
    has_quiz_for_topic,
)
from models.subject_model import find_topic_by_id
from services.db import get_db_connection, sanitize_db_error

logger = logging.getLogger(__name__)

ALLOWED_OPTIONS = {'A', 'B', 'C', 'D'}
DEFAULT_QUIZ_SIZE = 10


def get_performance_feedback(score_pct: float) -> Dict[str, str]:
    """
    Returns deterministic, rule-based performance message and badge class
    based on the student's actual score percentage.
    """
    if score_pct >= 90.0:
        return {
            "tier": "Excellent",
            "title": "Excellent Performance!",
            "message": "Outstanding mastery of this topic. You have demonstrated comprehensive understanding.",
            "badge_class": "badge-success",
            "grade": "A+"
        }
    elif score_pct >= 75.0:
        return {
            "tier": "Good",
            "title": "Good Performance!",
            "message": "You have a solid grasp of key concepts. A little more revision will help you achieve mastery.",
            "badge_class": "badge-info",
            "grade": "B"
        }
    elif score_pct >= 50.0:
        return {
            "tier": "Average",
            "title": "Keep Practicing!",
            "message": "You understand the basics, but some concepts need reinforcement. Review incorrect answers below.",
            "badge_class": "badge-warning",
            "grade": "C"
        }
    else:
        return {
            "tier": "Needs Practice",
            "title": "More Practice Recommended",
            "message": "Foundational review recommended. Revisit topic study notes and learning resources before re-attempting.",
            "badge_class": "badge-danger",
            "grade": "D"
        }


def get_available_quizzes_catalog() -> List[Dict[str, Any]]:
    """
    Retrieves all subjects and topics with question counts from MySQL.
    Groups topics under their respective subjects for catalog display.
    Delegates to models.quiz_model.find_quiz_catalog_grouped.
    """
    return find_quiz_catalog_grouped()


def get_topic_quiz_info(topic_id: int) -> Optional[Dict[str, Any]]:
    """
    Retrieves syllabus topic details, parent subject, and available question counts.
    Returns None if topic does not exist.
    Delegates to models.quiz_model.find_topic_quiz_info.
    """
    if not topic_id:
        return None
    return find_topic_quiz_info(topic_id)


def get_quiz_questions_for_topic(
    topic_id: int,
    limit: int = DEFAULT_QUIZ_SIZE,
    randomize: bool = True,
    include_correct: bool = False
) -> List[Dict[str, Any]]:
    """
    Fetches genuine static questions for a given topic from the quizzes table.
    
    Security:
    - By default (include_correct=False), strictly strips `correct_answer`
      so correct answers are never sent to client/browser prior to submission.
    - Limits to min(limit, available_count).
    - Prevents duplicates.
    """
    if not topic_id:
        return []

    questions = find_quizzes_by_topic(topic_id, include_correct=include_correct)
    if not questions:
        return []

    # Determine quiz size (never invent missing questions)
    quiz_size = min(limit, len(questions))

    if randomize:
        selected = random.sample(questions, quiz_size)
    else:
        selected = questions[:quiz_size]

    # Security sanitization: strip correct_answer if not explicitly authorized
    sanitized: List[Dict[str, Any]] = []
    for q in selected:
        item = {
            "id": q["id"],
            "topic_id": q["topic_id"],
            "question": q["question"],
            "option_a": q["option_a"],
            "option_b": q["option_b"],
            "option_c": q["option_c"],
            "option_d": q["option_d"],
            "difficulty": q["difficulty"]
        }
        if include_correct and "correct_answer" in q:
            item["correct_answer"] = q["correct_answer"]
        sanitized.append(item)

    return sanitized


def submit_quiz_attempt(
    user_id: int,
    topic_id: int,
    submitted_answers: Dict[int, str]
) -> Tuple[bool, str, Optional[int]]:
    """
    Submits student responses for a topic quiz, calculates the real score,
    and stores the attempt in `quiz_attempts` and `quiz_attempt_answers`.

    Security & Correctness:
    - Re-reads correct answers directly from MySQL via models.quiz_model.
    - Never trusts client-sent correct answer values.
    - Verifies all submitted question IDs belong to the topic.
    - Atomic database transaction managed by model layer.

    Returns:
        (success: bool, message: str, attempt_id: Optional[int])
    """
    if not user_id:
        return False, "Authentication required to submit quiz.", None

    if not topic_id:
        return False, "Valid topic identifier required.", None

    if not submitted_answers or not isinstance(submitted_answers, dict):
        return False, "No answers were submitted for this quiz.", None

    # Clean and validate submitted answers
    cleaned_answers: Dict[int, str] = {}
    for qid_raw, ans_raw in submitted_answers.items():
        try:
            qid_int = int(qid_raw)
            if qid_int <= 0:
                continue
        except (ValueError, TypeError):
            continue

        if not ans_raw or not isinstance(ans_raw, str):
            continue

        ans_clean = ans_raw.strip().upper()
        if ans_clean in ALLOWED_OPTIONS:
            cleaned_answers[qid_int] = ans_clean

    if not cleaned_answers:
        return False, "Please select at least one answer before submitting.", None

    # Verify topic exists
    topic_row = find_topic_by_id(topic_id)
    if not topic_row:
        return False, f"Topic #{topic_id} does not exist.", None

    # Fetch the real questions and correct answers from MySQL via model
    try:
        question_ids = [int(qid) for qid in cleaned_answers.keys()]
    except (ValueError, TypeError):
        return False, "Invalid question identifiers submitted.", None

    real_questions = find_quiz_questions_by_ids(question_ids, topic_id=topic_id)
    if not real_questions:
        return False, "None of the submitted questions belong to this topic.", None

    # Create lookup of correct answers
    real_answers_map = {
        q["id"]: q["correct_answer"].strip().upper() 
        for q in real_questions
    }

    # Evaluate each submitted question
    detailed_results: List[Dict[str, Any]] = []
    correct_count = 0

    for qid, real_correct in real_answers_map.items():
        student_choice = cleaned_answers.get(qid, "")
        is_correct = (student_choice == real_correct)
        if is_correct:
            correct_count += 1

        detailed_results.append({
            "quiz_id": qid,
            "selected_answer": student_choice,
            "correct_answer": real_correct,
            "is_correct": 1 if is_correct else 0
        })

    total_questions = len(detailed_results)
    score_pct = round((correct_count / total_questions) * 100, 2) if total_questions > 0 else 0.0

    # Atomically persist attempt and answers via model
    success, msg, attempt_id = insert_quiz_attempt_with_answers(
        user_id=user_id,
        topic_id=topic_id,
        total_questions=total_questions,
        correct_answers=correct_count,
        score_percentage=score_pct,
        answers=detailed_results
    )

    if not success:
        return False, msg, None

    # Automatically update topic progress for the student
    try:
        from services.progress_service import update_topic_progress
        update_topic_progress(user_id, topic_id)
    except Exception as prog_exc:
        logger.warning(f"Could not update progress after quiz: {prog_exc}")

    return True, "Quiz completed and scored successfully!", attempt_id


def get_quiz_attempt_result(attempt_id: int, user_id: int) -> Optional[Dict[str, Any]]:
    """
    Retrieves high-level summary results of a completed quiz attempt.
    Enforces student isolation: attempt must belong to user_id.

    Returns:
        Dict with attempt summary, score, performance feedback, or None.
    """
    if not attempt_id or not user_id:
        return None

    attempt = find_quiz_attempt_by_id(attempt_id, user_id=user_id)
    if not attempt:
        return None

    score_pct = float(attempt.get("score_percentage") or 0.0)
    total = int(attempt.get("total_questions") or 0)
    correct = int(attempt.get("correct_answers") or 0)
    incorrect = max(0, total - correct)

    attempt["score_percentage"] = score_pct
    attempt["total_questions"] = total
    attempt["correct_answers"] = correct
    attempt["incorrect_answers"] = incorrect
    attempt["feedback"] = get_performance_feedback(score_pct)

    return attempt


def get_quiz_attempt_review(attempt_id: int, user_id: int) -> Optional[Dict[str, Any]]:
    """
    Retrieves full question-by-question breakdown of an attempt,
    including student's selected answer and the correct answer.
    Enforces student isolation: attempt must belong to user_id.
    """
    if not attempt_id or not user_id:
        return None

    attempt = get_quiz_attempt_result(attempt_id, user_id)
    if not attempt:
        return None

    rows = find_quiz_attempt_answers(attempt_id)
    for row in rows:
        row["is_correct"] = bool(row.get("is_correct"))

    return {
        "attempt": attempt,
        "answers": rows,
        "total_questions": attempt["total_questions"],
        "correct_answers": attempt["correct_answers"],
        "incorrect_answers": attempt["incorrect_answers"]
    }


def get_user_quiz_history(user_id: int) -> List[Dict[str, Any]]:
    """
    Retrieves all quiz attempts made by the authenticated student.
    Ordered by attempted_at DESC.
    """
    if not user_id:
        return []

    rows = find_quiz_attempts_by_user(user_id, limit=50)
    for r in rows:
        r["score_percentage"] = float(r.get("score_percentage") or 0.0)
        r["feedback"] = get_performance_feedback(r["score_percentage"])
    return rows


def get_user_quiz_stats(user_id: int) -> Dict[str, Any]:
    """
    Calculates aggregated authentic quiz statistics for student dashboard.
    Uses real database values only; zero synthetic metrics.
    Delegates to models.quiz_model.find_user_quiz_stats.
    """
    if not user_id:
        return {
            "total_attempts": 0,
            "avg_score": 0.0,
            "best_score": 0.0,
            "total_questions_answered": 0,
            "total_correct_answers": 0,
            "recent_attempts": []
        }

    return find_user_quiz_stats(user_id)


def check_topic_has_quiz(topic_id: int) -> bool:
    """
    Checks if a given topic has at least one real question in quizzes.
    Used for Study Plan practice links.
    Delegates to models.quiz_model.has_quiz_for_topic.
    """
    if not topic_id:
        return False
    return has_quiz_for_topic(topic_id)

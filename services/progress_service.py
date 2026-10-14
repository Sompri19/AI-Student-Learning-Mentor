"""
Progress Tracking Service.
AI Student Learning Mentor - Phase 7.

Provides deterministic, evidence-based academic progress tracking.
Calculates topic, subject, and overall progress from authentic database records:
- Study Plan Task Completion
- Quiz Attempts and Real Test Scores
- Academic Inquiries in AI Mentoring

No synthetic progress metrics or fabricated numbers are generated.
Delegates database queries to models.progress_model.
"""
import logging
from typing import Dict, Any, List, Optional, Tuple

from models.progress_model import (
    find_topic_progress as model_find_topic_progress,
    upsert_topic_progress,
    find_topic_learning_evidence,
    find_user_topic_progress_matrix,
    find_learning_stats_aggregates,
    find_recent_activity_records,
)
from services.db import get_db_connection, sanitize_db_error

logger = logging.getLogger(__name__)

# Constants & Thresholds
TOPIC_COMPLETION_THRESHOLD = 80.0  # Topic considered 'Completed' at >= 80%
WEAK_TOPIC_THRESHOLD = 60.0        # Topic considered 'Needs Practice' if quiz avg < 60%


def calculate_topic_progress_value(
    user_id: int,
    topic_id: int,
    cursor=None
) -> float:
    """
    Deterministically computes a student's mastery percentage (0.0 to 100.0)
    for a single topic based on authentic learning evidence in MySQL:
    
    1. Study Plan Tasks:
       - Measures theoretical curriculum coverage.
       - Task ratio = (completed_tasks / total_tasks) * 100%
    2. Quiz Performance:
       - Measures validated practical mastery.
       - Best quiz score and average score.

    Transparent Formula:
    - If both study tasks and quiz attempts exist:
      Progress = (0.40 * Task Ratio) + (0.60 * Best Quiz Score)
    - If only quiz attempts exist:
      Progress = Best Quiz Score
    - If only study tasks exist:
      Progress = 0.75 * Task Ratio (capped at 75% without quiz validation)
    - If neither exist:
      Progress = 0.0%

    Bounded strictly between 0.0% and 100.0%.
    """
    if not user_id or not topic_id:
        return 0.0

    if cursor is not None:
        # Legacy/direct cursor support
        cursor.execute(
            """
            SELECT 
                COUNT(spi.id) AS total_tasks,
                COALESCE(SUM(CASE WHEN spi.completed = 1 THEN 1 ELSE 0 END), 0) AS completed_tasks
            FROM study_plan_items spi
            JOIN study_plans sp ON spi.study_plan_id = sp.id
            WHERE sp.user_id = %s AND spi.topic_id = %s
            """,
            (user_id, topic_id)
        )
        task_data = cursor.fetchone() or {}
        total_tasks = int(task_data.get("total_tasks") or 0)
        completed_tasks = int(task_data.get("completed_tasks") or 0)

        cursor.execute(
            """
            SELECT 
                COUNT(id) AS attempts_count,
                COALESCE(MAX(score_percentage), 0) AS best_score,
                COALESCE(AVG(score_percentage), 0) AS avg_score
            FROM quiz_attempts
            WHERE user_id = %s AND topic_id = %s
            """,
            (user_id, topic_id)
        )
        quiz_data = cursor.fetchone() or {}
        quiz_attempts = int(quiz_data.get("attempts_count") or 0)
        best_score = float(quiz_data.get("best_score") or 0.0)
    else:
        evidence = find_topic_learning_evidence(user_id, topic_id)
        total_tasks = evidence.get("total_tasks", 0)
        completed_tasks = evidence.get("completed_tasks", 0)
        quiz_attempts = evidence.get("attempts_count", 0)
        best_score = float(evidence.get("best_score", 0.0))

    # Apply Deterministic Progress Formula
    has_tasks = (total_tasks > 0)
    has_quizzes = (quiz_attempts > 0)

    if has_tasks and has_quizzes:
        task_ratio = (completed_tasks / total_tasks) * 100.0 if total_tasks > 0 else 0.0
        calc_val = (0.40 * task_ratio) + (0.60 * best_score)
    elif has_quizzes:
        calc_val = best_score
    elif has_tasks:
        task_ratio = (completed_tasks / total_tasks) * 100.0 if total_tasks > 0 else 0.0
        calc_val = 0.75 * task_ratio
    else:
        calc_val = 0.0

    # Boundary clamping: 0.0% to 100.0%
    return max(0.0, min(100.0, round(calc_val, 2)))


def update_topic_progress(user_id: int, topic_id: int) -> float:
    """
    Recalculates and updates the authentic mastery percentage in the `progress` table
    for a given user and topic.
    Avoids duplicate rows by utilizing the existing unique constraint `uq_user_topic`.
    Delegates persistence to models.progress_model.upsert_topic_progress.
    """
    if not user_id or not topic_id:
        return 0.0

    progress_val = calculate_topic_progress_value(user_id, topic_id)
    success = upsert_topic_progress(user_id, topic_id, progress_val)
    if not success:
        logger.error(f"Failed to upsert progress for user {user_id}, topic {topic_id}")
    return progress_val


def get_topic_progress(user_id: int, subject_id: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Retrieves granular topic-by-topic progress for the authenticated student.
    Includes completion status, quiz metrics, and weak-topic flags.
    Filtered optionally by `subject_id`.
    Delegates SQL aggregation to models.progress_model.find_user_topic_progress_matrix.
    """
    if not user_id:
        return []

    rows = find_user_topic_progress_matrix(user_id, subject_id=subject_id)

    topic_results = []
    for r in rows:
        pct = float(r.get("completion_percentage") or 0.0)
        q_attempts = int(r.get("quiz_attempts") or 0)
        avg_score = float(r.get("avg_quiz_score") or 0.0)
        best_score = float(r.get("best_quiz_score") or 0.0)

        is_completed = (pct >= TOPIC_COMPLETION_THRESHOLD)
        is_weak = (q_attempts > 0 and avg_score < WEAK_TOPIC_THRESHOLD)

        if is_completed:
            status = "Completed"
        elif pct > 0:
            status = "In Progress"
        else:
            status = "Not Started"

        topic_results.append({
            "topic_id": r["topic_id"],
            "topic_name": r["topic_name"],
            "difficulty": r["topic_difficulty"],
            "subject_id": r["subject_id"],
            "subject_name": r["subject_name"],
            "completion_percentage": round(pct, 1),
            "is_completed": is_completed,
            "is_weak": is_weak,
            "status": status,
            "quiz_attempts": q_attempts,
            "best_quiz_score": round(best_score, 1),
            "avg_quiz_score": round(avg_score, 1),
            "total_tasks": int(r.get("total_tasks") or 0),
            "completed_tasks": int(r.get("completed_tasks") or 0),
            "last_activity": r.get("last_updated")
        })

    return topic_results


def get_subject_progress(user_id: int) -> List[Dict[str, Any]]:
    """
    Computes subject-level academic progress by aggregating topics belonging
    to each subject for the authenticated student.
    Returns subject cards with real percentages, started/completed counts,
    and quiz metrics.
    """
    if not user_id:
        return []

    # Get topic progress for all topics
    all_topics = get_topic_progress(user_id)
    if not all_topics:
        return []

    # Group by subject
    subjects_map: Dict[int, Dict[str, Any]] = {}
    for t in all_topics:
        sid = t["subject_id"]
        if sid not in subjects_map:
            subjects_map[sid] = {
                "subject_id": sid,
                "subject_name": t["subject_name"],
                "total_topics": 0,
                "topics_started": 0,
                "topics_completed": 0,
                "total_percentage_sum": 0.0,
                "quiz_attempts": 0,
                "quiz_scores_sum": 0.0,
                "quiz_scored_count": 0,
                "last_activity": None
            }

        s_entry = subjects_map[sid]
        s_entry["total_topics"] += 1
        pct = t["completion_percentage"]
        s_entry["total_percentage_sum"] += pct

        if pct > 0:
            s_entry["topics_started"] += 1
        if t["is_completed"]:
            s_entry["topics_completed"] += 1

        if t["quiz_attempts"] > 0:
            s_entry["quiz_attempts"] += t["quiz_attempts"]
            s_entry["quiz_scores_sum"] += (t["avg_quiz_score"] * t["quiz_attempts"])
            s_entry["quiz_scored_count"] += t["quiz_attempts"]

        # Track latest activity
        t_act = t.get("last_activity")
        if t_act:
            if s_entry["last_activity"] is None or t_act > s_entry["last_activity"]:
                s_entry["last_activity"] = t_act

    # Finalize subject summaries
    results = []
    for sid, s in subjects_map.items():
        total_t = s["total_topics"]
        subj_pct = round(s["total_percentage_sum"] / total_t, 1) if total_t > 0 else 0.0
        avg_quiz = round(s["quiz_scores_sum"] / s["quiz_scored_count"], 1) if s["quiz_scored_count"] > 0 else 0.0

        if subj_pct >= TOPIC_COMPLETION_THRESHOLD:
            status = "Completed"
        elif subj_pct > 0:
            status = "In Progress"
        else:
            status = "Not Started"

        results.append({
            "subject_id": sid,
            "subject_name": s["subject_name"],
            "total_topics": total_t,
            "topics_started": s["topics_started"],
            "topics_completed": s["topics_completed"],
            "progress_percentage": subj_pct,
            "quiz_attempts": s["quiz_attempts"],
            "avg_quiz_score": avg_quiz,
            "status": status,
            "last_activity": s["last_activity"]
        })

    return results


def get_overall_progress(user_id: int) -> Dict[str, Any]:
    """
    Computes global learning progress across the entire student curriculum.
    Formula: Average of topic progress across all syllabus topics.
    Zero synthetic progress.
    """
    if not user_id:
        return {
            "overall_percentage": 0.0,
            "total_topics": 0,
            "topics_started": 0,
            "topics_completed": 0,
            "status": "Not Started"
        }

    all_topics = get_topic_progress(user_id)
    total_topics = len(all_topics)
    if total_topics == 0:
        return {
            "overall_percentage": 0.0,
            "total_topics": 0,
            "topics_started": 0,
            "topics_completed": 0,
            "status": "Not Started"
        }

    total_sum = sum(t["completion_percentage"] for t in all_topics)
    started_count = sum(1 for t in all_topics if t["completion_percentage"] > 0)
    completed_count = sum(1 for t in all_topics if t["is_completed"])
    overall_pct = round(total_sum / total_topics, 1)

    if overall_pct >= TOPIC_COMPLETION_THRESHOLD:
        status = "Completed"
    elif overall_pct > 0:
        status = "In Progress"
    else:
        status = "Not Started"

    return {
        "overall_percentage": overall_pct,
        "total_topics": total_topics,
        "topics_started": started_count,
        "topics_completed": completed_count,
        "status": status
    }


def get_weak_topics(user_id: int) -> List[Dict[str, Any]]:
    """
    Identifies academic topics requiring reinforcement based on real data.
    Rule: A topic is marked as weak if:
    - The student has attempted quizzes for the topic (`quiz_attempts > 0`)
    - The average quiz score is below 60.0% (`avg_quiz_score < 60.0%`)
    Sorted ascending by average quiz score (most critical weak areas first).
    """
    if not user_id:
        return []

    all_topics = get_topic_progress(user_id)
    weak = [t for t in all_topics if t["is_weak"]]
    weak.sort(key=lambda x: x["avg_quiz_score"])
    return weak


def get_learning_statistics(user_id: int) -> Dict[str, Any]:
    """
    Aggregates comprehensive authentic student learning metrics from MySQL:
    - Study Plan Task Counts & Percentage
    - Quiz Attempts, Accuracy, and Scores
    - Topics Progress & Weak Areas
    - AI Mentoring Questions Asked
    Delegates data aggregation to models.progress_model.find_learning_stats_aggregates.
    """
    if not user_id:
        return {
            "overall_progress_percentage": 0.0,
            "total_study_tasks": 0,
            "completed_study_tasks": 0,
            "study_plan_completion_percentage": 0.0,
            "total_quiz_attempts": 0,
            "total_questions_answered": 0,
            "total_correct_answers": 0,
            "overall_quiz_accuracy": 0.0,
            "avg_quiz_score": 0.0,
            "best_quiz_score": 0.0,
            "topics_started": 0,
            "topics_completed": 0,
            "weak_topics_count": 0,
            "total_ai_doubts_asked": 0
        }

    aggs = find_learning_stats_aggregates(user_id)
    total_tasks = aggs["total_tasks"]
    completed_tasks = aggs["completed_tasks"]
    sp_pct = round((completed_tasks / total_tasks) * 100.0, 1) if total_tasks > 0 else 0.0

    total_attempts = aggs["total_attempts"]
    total_questions = aggs["total_questions"]
    total_correct = aggs["total_correct"]
    avg_quiz = aggs["avg_quiz_score"]
    best_quiz = aggs["best_quiz_score"]
    accuracy = round((total_correct / total_questions) * 100.0, 1) if total_questions > 0 else 0.0
    total_ai = aggs["total_ai_doubts"]

    # Overall & Topic Progress Stats
    overall = get_overall_progress(user_id)
    weak_topics = get_weak_topics(user_id)

    return {
        "overall_progress_percentage": overall["overall_percentage"],
        "total_study_tasks": total_tasks,
        "completed_study_tasks": completed_tasks,
        "study_plan_completion_percentage": sp_pct,
        "total_quiz_attempts": total_attempts,
        "total_questions_answered": total_questions,
        "total_correct_answers": total_correct,
        "overall_quiz_accuracy": accuracy,
        "avg_quiz_score": avg_quiz,
        "best_quiz_score": best_quiz,
        "topics_started": overall["topics_started"],
        "topics_completed": overall["topics_completed"],
        "weak_topics_count": len(weak_topics),
        "total_ai_doubts_asked": total_ai
    }


def get_recent_activity(user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Builds a unified real learning activity timeline for the student.
    Aggregates:
    - Quiz Submissions
    - Study Plan Task Completions
    - AI Doubt Inquiries
    - Topic Progress Updates
    Sorted chronologically descending (newest first).
    Zero synthetic events.
    Delegates database records fetch to models.progress_model.find_recent_activity_records.
    """
    if not user_id:
        return []

    records = find_recent_activity_records(user_id, limit=limit)
    activities: List[Dict[str, Any]] = []

    # 1. Quizzes
    for row in records.get("quizzes", []):
        score = round(float(row["score_percentage"]), 1)
        activities.append({
            "type": "quiz",
            "icon": "🎯",
            "title": f"Completed practice quiz on '{row['topic_name']}'",
            "description": f"Scored {score}% ({row['subject_name']})",
            "timestamp": row["attempted_at"],
            "url": f"/quiz/results/{row['attempt_id']}"
        })

    # 2. Study Plan Tasks
    for row in records.get("study_tasks", []):
        task_snippet = row["task"][:75] + ("..." if len(row["task"]) > 75 else "")
        activities.append({
            "type": "study_plan",
            "icon": "✓",
            "title": f"Completed task for '{row.get('topic_name') or 'Study Plan'}'",
            "description": task_snippet,
            "timestamp": row["created_at"],
            "url": f"/study-plans/{row['plan_id']}"
        })

    # 3. AI Doubts
    for row in records.get("ai_chats", []):
        q_snippet = row["question"][:70] + ("..." if len(row["question"]) > 70 else "")
        activities.append({
            "type": "ai_chat",
            "icon": "🤖",
            "title": "Asked AI Mentor a question",
            "description": q_snippet,
            "timestamp": row["created_at"],
            "url": "/ai/history"
        })

    # Sort combined activity timeline newest first
    activities.sort(
        key=lambda x: str(x["timestamp"]) if x["timestamp"] else "",
        reverse=True
    )

    return activities[:limit]

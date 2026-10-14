"""
Recommendation Service for AI Student Learning Mentor.
Generates personalized, data-driven academic study recommendations
based on authentic student learning records:
1. Weak Topics: Topics where the student struggles (low quiz averages or incomplete progress)
2. Pending Tasks: Next scheduled study plan tasks in active study plans
3. Curriculum Progression: Next uncompleted syllabus topics in active subjects
4. Learning Goals: Alignment with student profile learning goals

Principles:
- Purely evidence-based: zero synthetic metrics, fake scores, or hallucinated content.
- Graceful empty states: clear, helpful onboarding guidance for new students with no activity.
- Complete student isolation: strictly enforces user_id boundaries.
"""
import logging
from typing import Dict, Any, List, Optional

from models.progress_model import find_weak_topics_by_user, find_user_topic_progress_matrix
from models.study_plan_model import find_pending_study_tasks, find_study_plans_by_user
from models.subject_model import find_all_subjects, find_topics_by_subject
from models.learning_goal_model import find_student_profile

logger = logging.getLogger(__name__)

DEFAULT_WEAK_THRESHOLD = 60.0
DEFAULT_COMPLETION_THRESHOLD = 80.0


def _build_topic_url(topic_id: int) -> str:
    """
    Constructs the topic detail study URL.
    Uses Flask url_for() if within an active request context,
    otherwise falls back to the canonical /topics/<id> path.
    """
    try:
        from flask import has_request_context, url_for
        if has_request_context():
            return url_for('resource.topic_detail', topic_id=topic_id)
    except Exception:
        pass
    return f"/topics/{topic_id}"


def get_weak_topic_recommendations(
    user_id: int,
    threshold: float = DEFAULT_WEAK_THRESHOLD
) -> List[Dict[str, Any]]:
    """
    Identifies academic topics where the student has demonstrated difficulty.
    Uses real quiz scores and completion percentages from MySQL.
    
    A topic is recommended for review if:
    - The student has attempted quizzes with average score < threshold, OR
    - Progress completion percentage < threshold after starting
    """
    if not user_id:
        return []

    weak_rows = find_weak_topics_by_user(user_id, threshold=threshold)
    recommendations: List[Dict[str, Any]] = []

    for row in weak_rows:
        avg_score = round(float(row.get("avg_quiz_score") or 0.0), 1)
        completion_pct = round(float(row.get("completion_percentage") or 0.0), 1)
        attempts = int(row.get("quiz_attempts_count") or 0)
        topic_id = row["topic_id"]

        if attempts > 0 and avg_score < 40.0:
            priority = "Critical"
            action = f"Review foundational concepts in '{row['topic_name']}' and retake practice quiz."
            reason = f"Quiz average is {avg_score}% across {attempts} attempt(s) (target: {threshold}%)."
        elif attempts > 0:
            priority = "High"
            action = f"Revise key notes for '{row['topic_name']}' to improve mastery."
            reason = f"Quiz average is {avg_score}% (target: {threshold}%)."
        else:
            priority = "Medium"
            action = f"Continue studying '{row['topic_name']}' and take a practice test."
            reason = f"Topic completion is only {completion_pct}% with no practice quiz attempts."

        recommendations.append({
            "topic_id": topic_id,
            "topic_name": row["topic_name"],
            "subject_id": row["subject_id"],
            "subject_name": row["subject_name"],
            "difficulty": row.get("difficulty", "Medium"),
            "avg_quiz_score": avg_score,
            "quiz_attempts": attempts,
            "completion_percentage": completion_pct,
            "priority": priority,
            "recommended_action": action,
            "reason": reason,
            "practice_url": f"/quiz/{topic_id}/start",
            "study_url": _build_topic_url(topic_id)
        })

    return recommendations


def get_pending_task_recommendations(
    user_id: int,
    limit: int = 5
) -> List[Dict[str, Any]]:
    """
    Retrieves the next pending study plan tasks for the student.
    Ordered by scheduled day number.
    """
    if not user_id:
        return []

    pending_items = find_pending_study_tasks(user_id, limit=limit)
    recommendations: List[Dict[str, Any]] = []

    for item in pending_items:
        day_num = item.get("day_number", 1)
        plan_id = item["study_plan_id"]
        topic_id = item.get("topic_id")

        if day_num <= 2:
            priority = "High"
        elif day_num <= 5:
            priority = "Medium"
        else:
            priority = "Normal"

        recommendations.append({
            "item_id": item["item_id"],
            "plan_id": plan_id,
            "day_number": day_num,
            "task": item["task"],
            "topic_id": topic_id,
            "topic_name": item.get("topic_name", "Topic"),
            "subject_id": item.get("subject_id"),
            "subject_name": item.get("subject_name", "Subject"),
            "difficulty": item.get("topic_difficulty", "Medium"),
            "priority": priority,
            "recommended_action": f"Complete Day {day_num} study task",
            "action_url": f"/study-plans/{plan_id}",
            "practice_url": f"/quiz/{topic_id}/start" if topic_id else None
        })

    return recommendations


def get_next_topic_recommendations(
    user_id: int,
    limit: int = 3
) -> List[Dict[str, Any]]:
    """
    Suggests the next sequential curriculum topics to study.
    Prioritizes:
    1. Uncompleted topics in subjects the student has active study plans for.
    2. Next syllabus topics in general if no active plans exist.
    Never suggests topics already mastered (completion >= 80%).
    """
    if not user_id:
        return []

    # Get student's current topic mastery matrix
    matrix = find_user_topic_progress_matrix(user_id)
    progress_by_topic = {
        row["topic_id"]: float(row.get("completion_percentage") or 0.0)
        for row in matrix
    }

    # Find subjects the student is actively studying (from plans)
    active_plans = find_study_plans_by_user(user_id)
    active_subject_ids = [p["subject_id"] for p in active_plans if "subject_id" in p]

    recommendations: List[Dict[str, Any]] = []
    seen_topic_ids = set()

    # Priority 1: Check active subjects first
    for sid in active_subject_ids:
        subject_topics = find_topics_by_subject(sid)
        for top in subject_topics:
            tid = top["id"]
            pct = progress_by_topic.get(tid, 0.0)
            if pct < DEFAULT_COMPLETION_THRESHOLD and tid not in seen_topic_ids:
                seen_topic_ids.add(tid)
                recommendations.append({
                    "topic_id": tid,
                    "topic_name": top["topic_name"],
                    "subject_id": top["subject_id"],
                    "subject_name": top.get("subject_name", ""),
                    "difficulty": top.get("difficulty", "Medium"),
                    "completion_percentage": pct,
                    "reason": "Next topic in your active study plan syllabus",
                    "priority": "Medium",
                    "study_url": _build_topic_url(tid),
                    "practice_url": f"/quiz/{tid}/start"
                })
                if len(recommendations) >= limit:
                    return recommendations

    # Priority 2: General syllabus topics
    if len(recommendations) < limit:
        all_subjects = find_all_subjects()
        for subj in all_subjects:
            sid = subj["id"]
            if sid in active_subject_ids:
                continue  # Already checked
            topics = find_topics_by_subject(sid)
            for top in topics:
                tid = top["id"]
                pct = progress_by_topic.get(tid, 0.0)
                if pct < DEFAULT_COMPLETION_THRESHOLD and tid not in seen_topic_ids:
                    seen_topic_ids.add(tid)
                    recommendations.append({
                        "topic_id": tid,
                        "topic_name": top["topic_name"],
                        "subject_id": sid,
                        "subject_name": subj.get("name", ""),
                        "difficulty": top.get("difficulty", "Medium"),
                        "completion_percentage": pct,
                        "reason": f"Explore syllabus in '{subj.get('name', 'Subject')}'",
                        "priority": "Normal",
                        "study_url": _build_topic_url(tid),
                        "practice_url": f"/quiz/{tid}/start"
                    })
                    if len(recommendations) >= limit:
                        return recommendations

    return recommendations


def get_comprehensive_recommendations(user_id: int) -> Dict[str, Any]:
    """
    Aggregates all student recommendation streams into a unified advisory object.
    Gracefully handles empty states for new students without inventing fake data.
    """
    if not user_id:
        return {
            "user_id": None,
            "has_activity": False,
            "weak_topics": [],
            "pending_tasks": [],
            "next_topics": [],
            "learning_goal": None,
            "summary": {
                "weak_topics_count": 0,
                "pending_tasks_count": 0,
                "next_topics_count": 0,
                "primary_focus": "Get Started"
            },
            "empty_state_message": "Sign in to view personalized recommendations."
        }

    weak_topics = get_weak_topic_recommendations(user_id)
    pending_tasks = get_pending_task_recommendations(user_id)
    next_topics = get_next_topic_recommendations(user_id)

    profile = find_student_profile(user_id) or {}
    learning_goal = (
        profile.get("learning_goal")
        or profile.get("learning_goals")
        or profile.get("goal")
        or None
    )

    has_activity = bool(weak_topics or pending_tasks or profile.get("created_at"))

    if weak_topics:
        primary_focus = f"Reinforce {len(weak_topics)} weak topic(s) with practice quizzes"
    elif pending_tasks:
        primary_focus = f"Complete scheduled study plan tasks (next: Day {pending_tasks[0]['day_number']})"
    elif next_topics:
        primary_focus = f"Start new topics in '{next_topics[0]['subject_name']}'"
    else:
        primary_focus = "Explore subjects and create your first study plan"

    empty_msg = None
    if not has_activity and not pending_tasks and not weak_topics:
        empty_msg = (
            "Welcome! No learning history found yet. "
            "Start by browsing subjects, generating a study plan, or taking a diagnostic practice quiz."
        )

    return {
        "user_id": user_id,
        "has_activity": has_activity,
        "weak_topics": weak_topics,
        "pending_tasks": pending_tasks,
        "next_topics": next_topics,
        "learning_goal": learning_goal,
        "summary": {
            "weak_topics_count": len(weak_topics),
            "pending_tasks_count": len(pending_tasks),
            "next_topics_count": len(next_topics),
            "primary_focus": primary_focus
        },
        "empty_state_message": empty_msg
    }

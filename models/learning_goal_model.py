"""
Learning Goal Model for AI Student Learning Mentor.
Encapsulates operations for academic learning goals and student profiles.
Interacts with the verified schema:
- 'student_profiles.learning_goal' (primary student learning objective)
- 'study_plans.goal' (goal attached to active student study plans)
Does NOT invent a separate learning_goals table.
"""
import logging
from typing import Optional, Dict, Any, List, Tuple
from database.db_connection import get_db_connection, sanitize_db_error

logger = logging.getLogger(__name__)


def find_student_profile(user_id: int) -> Optional[Dict[str, Any]]:
    """
    Retrieves the student profile (including learning_goal) for a user ID.
    Enforces authorization check by scoping queries to user_id.
    """
    if not user_id:
        return None
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, user_id, education_level, course, semester, 
                       skill_level, learning_goal, preferred_study_time,
                       created_at, updated_at
                FROM student_profiles
                WHERE user_id = %s
                """,
                (user_id,)
            )
            return cursor.fetchone()
    finally:
        conn.close()


def upsert_student_profile(user_id: int, data: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Atomically creates or updates student profile and learning goal.
    Uses INSERT ... ON DUPLICATE KEY UPDATE.
    """
    if not user_id:
        return False, "User ID is required."

    education_level = (data.get('education_level') or '').strip() or None
    course = (data.get('course') or '').strip() or None
    semester = (data.get('semester') or '').strip() or None
    skill_level = (data.get('skill_level') or '').strip() or None
    learning_goal = (data.get('learning_goal') or '').strip() or None
    preferred_study_time = (data.get('preferred_study_time') or '').strip() or None

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO student_profiles 
                    (user_id, education_level, course, semester, skill_level, learning_goal, preferred_study_time)
                VALUES 
                    (%s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    education_level = VALUES(education_level),
                    course = VALUES(course),
                    semester = VALUES(semester),
                    skill_level = VALUES(skill_level),
                    learning_goal = VALUES(learning_goal),
                    preferred_study_time = VALUES(preferred_study_time),
                    updated_at = CURRENT_TIMESTAMP
                """,
                (
                    user_id,
                    education_level,
                    course,
                    semester,
                    skill_level,
                    learning_goal,
                    preferred_study_time
                )
            )
        return True, "Profile and learning goal saved successfully."
    except Exception as exc:
        logger.error("Database error upserting profile for user %s: %s", user_id, sanitize_db_error(exc))
        return False, "Unable to save profile due to a database error."
    finally:
        conn.close()


def find_student_learning_goal(user_id: int) -> Optional[str]:
    """
    Retrieves the primary learning goal text from student_profiles.
    """
    profile = find_student_profile(user_id)
    return profile.get('learning_goal') if profile else None


def update_student_learning_goal(user_id: int, learning_goal: str) -> bool:
    """
    Updates the learning goal in student_profiles.
    """
    if not user_id:
        return False
    goal_clean = (learning_goal or '').strip() or None
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO student_profiles (user_id, learning_goal)
                VALUES (%s, %s)
                ON DUPLICATE KEY UPDATE
                    learning_goal = VALUES(learning_goal),
                    updated_at = CURRENT_TIMESTAMP
                """,
                (user_id, goal_clean)
            )
            return True
    except Exception as exc:
        logger.error("Error updating learning goal for user %s: %s", user_id, sanitize_db_error(exc))
        return False
    finally:
        conn.close()


def find_study_plan_goals(user_id: int) -> List[Dict[str, Any]]:
    """
    Retrieves study plan goals associated with active study plans for the student.
    """
    if not user_id:
        return []
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT sp.id AS plan_id, sp.goal, sp.duration_days, sp.skill_level,
                       s.name AS subject_name, sp.created_at
                FROM study_plans sp
                JOIN subjects s ON sp.subject_id = s.id
                WHERE sp.user_id = %s
                ORDER BY sp.created_at DESC
                """,
                (user_id,)
            )
            return cursor.fetchall()
    finally:
        conn.close()

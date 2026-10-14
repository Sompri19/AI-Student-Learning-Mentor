"""
Student Profile Service for AI Student Learning Mentor.
Handles student academic profile creation, retrieval, updates, and completion checks.
"""
import logging
from typing import Optional, Dict, Any, Tuple
from services.db import get_db_connection, sanitize_db_error

logger = logging.getLogger(__name__)

PROFILE_FIELDS = [
    'education_level',
    'course',
    'semester',
    'skill_level',
    'learning_goal',
    'preferred_study_time'
]


from models.learning_goal_model import (
    find_student_profile,
    upsert_student_profile as model_upsert_profile
)


def get_student_profile(user_id: int) -> Optional[Dict[str, Any]]:
    """
    Retrieves the student profile associated with a specific user ID via learning_goal_model.
    Enforces authorization boundary: user_id must be the authenticated user's ID.
    
    Returns:
        Dict of profile record or None if not yet created.
    """
    if not user_id:
        return None
    return find_student_profile(user_id)


def upsert_student_profile(user_id: int, data: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Creates or updates the student profile for the authenticated student via learning_goal_model.
    Uses INSERT ... ON DUPLICATE KEY UPDATE to handle both creation and updates atomically.
    
    Returns:
        (success, message)
    """
    if not user_id:
        return False, "User ID is required."

    education_level = (data.get('education_level') or '').strip() or None
    course = (data.get('course') or '').strip() or None
    semester = (data.get('semester') or '').strip() or None
    skill_level = (data.get('skill_level') or '').strip() or None
    learning_goal = (data.get('learning_goal') or '').strip() or None
    preferred_study_time = (data.get('preferred_study_time') or '').strip() or None

    # Length constraints matching database schema
    if education_level and len(education_level) > 50:
        return False, "Education level must be at most 50 characters."
    if course and len(course) > 100:
        return False, "Course must be at most 100 characters."
    if semester and len(semester) > 20:
        return False, "Semester must be at most 20 characters."
    if skill_level and len(skill_level) > 30:
        return False, "Skill level must be at most 30 characters."
    if preferred_study_time and len(preferred_study_time) > 50:
        return False, "Preferred study time must be at most 50 characters."

    return model_upsert_profile(user_id, data)


def calculate_profile_completion(profile: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Computes profile completion status honestly based on whether fields are filled.
    Does not invent or fake student progress.
    
    Returns:
        Dict containing percentage, status_label, is_complete, and missing fields.
    """
    if not profile:
        return {
            "is_complete": False,
            "percentage": 0,
            "status_label": "Not Started",
            "filled_count": 0,
            "total_count": len(PROFILE_FIELDS),
            "missing_fields": PROFILE_FIELDS.copy()
        }

    filled = []
    missing = []
    for field in PROFILE_FIELDS:
        val = profile.get(field)
        if val is not None and str(val).strip():
            filled.append(field)
        else:
            missing.append(field)

    pct = int((len(filled) / len(PROFILE_FIELDS)) * 100)
    is_complete = (len(missing) == 0)

    if is_complete:
        label = "Complete"
    elif pct > 0:
        label = "Incomplete"
    else:
        label = "Not Started"

    return {
        "is_complete": is_complete,
        "percentage": pct,
        "status_label": label,
        "filled_count": len(filled),
        "total_count": len(PROFILE_FIELDS),
        "missing_fields": missing
    }

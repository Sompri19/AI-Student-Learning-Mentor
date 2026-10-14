"""
Learning Content and Resource Engine Service for AI Student Learning Mentor.
Manages database operations for subjects, syllabus topics, learning resources,
database-driven search, filtering, and URL safety validation.
"""
import logging
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse
from services.db import get_db_connection

logger = logging.getLogger(__name__)

ALLOWED_DIFFICULTIES = ['Beginner', 'Intermediate', 'Advanced']
ALLOWED_RESOURCE_TYPES = ['Notes', 'Video', 'Documentation', 'Article', 'Practice']


def is_safe_resource_url(url: str) -> bool:
    """
    Validates that an external educational resource URL is safe to display/link.
    Rejects unsafe pseudo-schemes (e.g. javascript:, data:, vbscript:, file:).
    Only allows valid http:// and https:// links.
    """
    if not url or not isinstance(url, str):
        return False

    cleaned = url.strip()
    lower = cleaned.lower()

    # Disallow dangerous schemes
    dangerous_schemes = ('javascript:', 'data:', 'vbscript:', 'file:', 'about:')
    if any(lower.startswith(scheme) for scheme in dangerous_schemes):
        return False

    try:
        parsed = urlparse(cleaned)
        # Scheme must be either http or https
        if parsed.scheme.lower() not in ('http', 'https'):
            return False
        # Must possess a valid network location (hostname/domain)
        if not parsed.netloc:
            return False
        return True
    except Exception:
        return False


from models.subject_model import (
    find_all_subjects,
    find_subject_by_id,
    find_topics_by_subject,
    find_topic_by_id,
    find_resources_by_topic,
)


def get_all_subjects(search_query: str = None) -> List[Dict[str, Any]]:
    """
    Retrieves all academic subjects from MySQL with topic counts via subject_model.
    Supports optional search filtering.
    """
    return find_all_subjects(search_query)


def get_subject_by_id(subject_id: int) -> Optional[Dict[str, Any]]:
    """
    Retrieves a single subject by its primary key via subject_model.
    """
    if not subject_id:
        return None
    return find_subject_by_id(subject_id)


def get_topics_by_subject(subject_id: int, difficulty: str = None) -> List[Dict[str, Any]]:
    """
    Retrieves syllabus topics belonging to a specific subject with resource counts via subject_model.
    Supports optional difficulty filtering.
    """
    if not subject_id:
        return []

    diff_filter = difficulty.strip() if difficulty and difficulty.strip() in ALLOWED_DIFFICULTIES else None
    return find_topics_by_subject(subject_id, difficulty=diff_filter)


def get_topic_by_id(topic_id: int) -> Optional[Dict[str, Any]]:
    """
    Retrieves topic details joined with the parent subject name via subject_model.
    """
    if not topic_id:
        return None
    return find_topic_by_id(topic_id)


def get_resources_by_topic(
    topic_id: int, 
    resource_type: str = None, 
    difficulty: str = None
) -> List[Dict[str, Any]]:
    """
    Retrieves verified learning resources associated with a topic via subject_model.
    Validates URL safety for each resource.
    """
    if not topic_id:
        return []

    r_type = resource_type.strip() if resource_type and resource_type.strip() in ALLOWED_RESOURCE_TYPES else None
    diff = difficulty.strip() if difficulty and difficulty.strip() in ALLOWED_DIFFICULTIES else None

    records = find_resources_by_topic(topic_id, resource_type=r_type, difficulty=diff)
    for r in records:
        r["is_safe_url"] = is_safe_resource_url(r["url"])

    return records


def search_content(
    query: str = '',
    subject_id: Optional[int] = None,
    difficulty: Optional[str] = None,
    resource_type: Optional[str] = None
) -> Dict[str, Any]:
    """
    Database-driven search and filtering across subjects, topics, and resources.
    Uses strictly parameterized queries to prevent SQL injection.
    
    Returns:
        {
            "subjects": [...],
            "topics": [...],
            "resources": [...],
            "total_matches": int
        }
    """
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            q_clean = (query or '').strip()
            pattern = f"%{q_clean}%" if q_clean else None

            # 1. Search Subjects (if no topic/resource type specific filter requested)
            subjects = []
            if not resource_type:
                subj_sql = """
                    SELECT 
                        s.id, 
                        s.name, 
                        s.description, 
                        COUNT(t.id) AS topic_count
                    FROM subjects s
                    LEFT JOIN topics t ON s.id = t.subject_id
                """
                subj_conditions = []
                subj_params = []

                if subject_id:
                    subj_conditions.append("s.id = %s")
                    subj_params.append(subject_id)

                if pattern:
                    subj_conditions.append("(s.name LIKE %s OR s.description LIKE %s)")
                    subj_params.extend([pattern, pattern])

                if subj_conditions:
                    subj_sql += " WHERE " + " AND ".join(subj_conditions)

                subj_sql += " GROUP BY s.id ORDER BY s.name ASC"
                cursor.execute(subj_sql, tuple(subj_params))
                subjects = cursor.fetchall()

            # 2. Search Topics
            topic_sql = """
                SELECT 
                    t.id, 
                    t.subject_id, 
                    t.topic_name, 
                    t.description, 
                    t.difficulty, 
                    s.name AS subject_name,
                    COUNT(r.id) AS resource_count
                FROM topics t
                JOIN subjects s ON t.subject_id = s.id
                LEFT JOIN resources r ON t.id = r.topic_id
            """
            topic_conditions = []
            topic_params = []

            if subject_id:
                topic_conditions.append("t.subject_id = %s")
                topic_params.append(subject_id)

            if difficulty and difficulty in ALLOWED_DIFFICULTIES:
                topic_conditions.append("t.difficulty = %s")
                topic_params.append(difficulty)

            if pattern:
                topic_conditions.append("(t.topic_name LIKE %s OR t.description LIKE %s OR s.name LIKE %s)")
                topic_params.extend([pattern, pattern, pattern])

            if topic_conditions:
                topic_sql += " WHERE " + " AND ".join(topic_conditions)

            topic_sql += " GROUP BY t.id ORDER BY s.name ASC, t.id ASC"
            cursor.execute(topic_sql, tuple(topic_params))
            topics = cursor.fetchall()

            # 3. Search Resources
            res_sql = """
                SELECT 
                    r.id, 
                    r.topic_id, 
                    r.title, 
                    r.resource_type, 
                    r.url, 
                    r.description, 
                    r.difficulty, 
                    t.topic_name, 
                    s.id AS subject_id, 
                    s.name AS subject_name
                FROM resources r
                JOIN topics t ON r.topic_id = t.id
                JOIN subjects s ON t.subject_id = s.id
            """
            res_conditions = []
            res_params = []

            if subject_id:
                res_conditions.append("s.id = %s")
                res_params.append(subject_id)

            if difficulty and difficulty in ALLOWED_DIFFICULTIES:
                res_conditions.append("r.difficulty = %s")
                res_params.append(difficulty)

            if resource_type and resource_type in ALLOWED_RESOURCE_TYPES:
                res_conditions.append("r.resource_type = %s")
                res_params.append(resource_type)

            if pattern:
                res_conditions.append(
                    "(r.title LIKE %s OR r.description LIKE %s OR r.resource_type LIKE %s OR t.topic_name LIKE %s OR s.name LIKE %s)"
                )
                res_params.extend([pattern, pattern, pattern, pattern, pattern])

            if res_conditions:
                res_sql += " WHERE " + " AND ".join(res_conditions)

            res_sql += " ORDER BY s.name ASC, t.id ASC, r.id ASC"
            cursor.execute(res_sql, tuple(res_params))
            resources = cursor.fetchall()

            for r in resources:
                r["is_safe_url"] = is_safe_resource_url(r["url"])

            total = len(subjects) + len(topics) + len(resources)

            return {
                "subjects": subjects,
                "topics": topics,
                "resources": resources,
                "total_matches": total
            }
    finally:
        conn.close()


def get_filter_meta() -> Dict[str, Any]:
    """
    Returns available filter choices for frontend dropdown menus.
    """
    subjects = get_all_subjects()
    return {
        "subjects": subjects,
        "difficulties": ALLOWED_DIFFICULTIES,
        "resource_types": ALLOWED_RESOURCE_TYPES
    }

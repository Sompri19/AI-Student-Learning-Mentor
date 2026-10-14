"""
Subject & Curriculum Model for AI Student Learning Mentor.
Encapsulates SQL operations for 'subjects', 'topics', and 'resources' tables.
"""
import logging
from typing import Optional, Dict, Any, List
from database.db_connection import get_db_connection, sanitize_db_error

logger = logging.getLogger(__name__)


def find_all_subjects(search_query: str = None) -> List[Dict[str, Any]]:
    """
    Retrieves all curriculum subjects with their associated topic counts.
    Supports optional search filtering across name and description.
    """
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            base_sql = """
                SELECT 
                    s.id, 
                    s.name, 
                    s.description, 
                    s.created_at, 
                    COUNT(t.id) AS topic_count
                FROM subjects s
                LEFT JOIN topics t ON s.id = t.subject_id
            """
            params = []
            if search_query and search_query.strip():
                base_sql += " WHERE s.name LIKE %s OR s.description LIKE %s"
                pattern = f"%{search_query.strip()}%"
                params.extend([pattern, pattern])

            base_sql += " GROUP BY s.id ORDER BY s.name ASC"
            cursor.execute(base_sql, tuple(params))
            return cursor.fetchall()
    finally:
        conn.close()


def find_subject_by_id(subject_id: int) -> Optional[Dict[str, Any]]:
    """
    Retrieves a single subject by its primary key.
    """
    if not subject_id:
        return None
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, name, description, created_at
                FROM subjects
                WHERE id = %s
                """,
                (subject_id,)
            )
            return cursor.fetchone()
    finally:
        conn.close()


def find_topics_by_subject(subject_id: int, difficulty: str = None) -> List[Dict[str, Any]]:
    """
    Retrieves syllabus topics belonging to a specific subject with resource counts.
    Supports optional difficulty filtering.
    """
    if not subject_id:
        return []
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            sql = """
                SELECT 
                    t.id, 
                    t.subject_id, 
                    t.topic_name, 
                    t.description, 
                    t.difficulty, 
                    t.created_at,
                    COUNT(r.id) AS resource_count
                FROM topics t
                LEFT JOIN resources r ON t.id = r.topic_id
                WHERE t.subject_id = %s
            """
            params = [subject_id]
            if difficulty and difficulty.strip():
                sql += " AND t.difficulty = %s"
                params.append(difficulty.strip())

            sql += " GROUP BY t.id ORDER BY t.id ASC"
            cursor.execute(sql, tuple(params))
            return cursor.fetchall()
    finally:
        conn.close()


def find_topic_by_id(topic_id: int) -> Optional[Dict[str, Any]]:
    """
    Retrieves topic details joined with the parent subject name.
    """
    if not topic_id:
        return None
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT 
                    t.id, 
                    t.subject_id, 
                    t.topic_name, 
                    t.description, 
                    t.difficulty, 
                    t.created_at,
                    s.name AS subject_name
                FROM topics t
                JOIN subjects s ON t.subject_id = s.id
                WHERE t.id = %s
                """,
                (topic_id,)
            )
            return cursor.fetchone()
    finally:
        conn.close()


def find_resources_by_topic(
    topic_id: int, 
    resource_type: str = None, 
    difficulty: str = None
) -> List[Dict[str, Any]]:
    """
    Retrieves verified learning resources associated with a topic.
    """
    if not topic_id:
        return []
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            sql = """
                SELECT 
                    id, 
                    topic_id, 
                    title, 
                    resource_type, 
                    url, 
                    description, 
                    difficulty, 
                    created_at
                FROM resources
                WHERE topic_id = %s
            """
            params = [topic_id]

            if resource_type and resource_type.strip():
                sql += " AND resource_type = %s"
                params.append(resource_type.strip())

            if difficulty and difficulty.strip():
                sql += " AND difficulty = %s"
                params.append(difficulty.strip())

            sql += " ORDER BY id ASC"
            cursor.execute(sql, tuple(params))
            return cursor.fetchall()
    finally:
        conn.close()


def search_resources(query: str, resource_type: str = None) -> List[Dict[str, Any]]:
    """
    Searches resources across titles and descriptions.
    """
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            sql = """
                SELECT 
                    r.id, 
                    r.topic_id, 
                    r.title, 
                    r.resource_type, 
                    r.url, 
                    r.description, 
                    r.difficulty,
                    t.topic_name,
                    s.name AS subject_name
                FROM resources r
                JOIN topics t ON r.topic_id = t.id
                JOIN subjects s ON t.subject_id = s.id
                WHERE (r.title LIKE %s OR r.description LIKE %s)
            """
            pattern = f"%{query.strip()}%"
            params = [pattern, pattern]

            if resource_type and resource_type.strip():
                sql += " AND r.resource_type = %s"
                params.append(resource_type.strip())

            sql += " ORDER BY s.name ASC, t.topic_name ASC, r.title ASC LIMIT 100"
            cursor.execute(sql, tuple(params))
            return cursor.fetchall()
    finally:
        conn.close()


def find_topics_by_ids(subject_id: int, topic_ids: List[int]) -> List[Dict[str, Any]]:
    """
    Retrieves topic records for a given subject matching a list of topic IDs.
    """
    if not subject_id or not topic_ids:
        return []
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            format_strings = ','.join(['%s'] * len(topic_ids))
            sql = f"""
                SELECT id, subject_id, topic_name, description, difficulty
                FROM topics
                WHERE subject_id = %s AND id IN ({format_strings})
                ORDER BY id ASC
            """
            cursor.execute(sql, (subject_id, *topic_ids))
            return cursor.fetchall()
    finally:
        conn.close()

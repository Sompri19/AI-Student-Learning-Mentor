"""
Progress Model for AI Student Learning Mentor.
Encapsulates SQL operations for 'progress' and 'ai_chats' tables, as well as
evidence-based student mastery calculations across quizzes and study plans.
"""
import logging
from typing import Optional, Dict, Any, List
from database.db_connection import get_db_connection, sanitize_db_error

logger = logging.getLogger(__name__)


def find_topic_progress(user_id: int, topic_id: int = None) -> List[Dict[str, Any]]:
    """
    Retrieves records from the 'progress' table for a user.
    Optionally filters by topic_id.
    """
    if not user_id:
        return []
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            sql = """
                SELECT 
                    p.id, p.user_id, p.topic_id, p.completion_percentage, p.last_updated,
                    t.topic_name, t.difficulty, s.name AS subject_name, s.id AS subject_id
                FROM progress p
                JOIN topics t ON p.topic_id = t.id
                JOIN subjects s ON t.subject_id = s.id
                WHERE p.user_id = %s
            """
            params = [user_id]
            if topic_id is not None:
                sql += " AND p.topic_id = %s"
                params.append(topic_id)

            sql += " ORDER BY s.name ASC, t.topic_name ASC"
            cursor.execute(sql, tuple(params))
            return cursor.fetchall()
    finally:
        conn.close()


def upsert_topic_progress(user_id: int, topic_id: int, completion_pct: float) -> bool:
    """
    Inserts or updates topic mastery percentage in the 'progress' table.
    Uses the unique key (user_id, topic_id).
    """
    if not user_id or not topic_id:
        return False
    pct = max(0.0, min(100.0, float(completion_pct)))
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO progress (user_id, topic_id, completion_percentage)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    completion_percentage = VALUES(completion_percentage),
                    last_updated = CURRENT_TIMESTAMP
                """,
                (user_id, topic_id, pct)
            )
            return True
    except Exception as exc:
        logger.error("Error updating progress for user %s, topic %s: %s", user_id, topic_id, sanitize_db_error(exc))
        return False
    finally:
        conn.close()


def find_user_quiz_summary(user_id: int) -> Dict[str, Any]:
    """
    Calculates aggregated quiz metrics from real quiz_attempts records.
    """
    if not user_id:
        return {"total_attempts": 0, "avg_score": 0.0, "passed_quizzes": 0}
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT 
                    COUNT(id) AS total_attempts,
                    COALESCE(AVG(score_percentage), 0) AS avg_score,
                    SUM(CASE WHEN score_percentage >= 70.0 THEN 1 ELSE 0 END) AS passed_quizzes
                FROM quiz_attempts
                WHERE user_id = %s
                """,
                (user_id,)
            )
            row = cursor.fetchone() or {}
            return {
                "total_attempts": int(row.get("total_attempts") or 0),
                "avg_score": round(float(row.get("avg_score") or 0.0), 1),
                "passed_quizzes": int(row.get("passed_quizzes") or 0)
            }
    finally:
        conn.close()


def find_user_task_summary(user_id: int) -> Dict[str, Any]:
    """
    Calculates aggregated study plan task metrics from real study_plan_items records.
    """
    if not user_id:
        return {"total_tasks": 0, "completed_tasks": 0, "active_plans": 0}
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT 
                    COUNT(spi.id) AS total_tasks,
                    SUM(CASE WHEN spi.completed = 1 THEN 1 ELSE 0 END) AS completed_tasks,
                    COUNT(DISTINCT sp.id) AS active_plans
                FROM study_plans sp
                LEFT JOIN study_plan_items spi ON sp.id = spi.study_plan_id
                WHERE sp.user_id = %s
                """,
                (user_id,)
            )
            row = cursor.fetchone() or {}
            total = int(row.get("total_tasks") or 0)
            completed = int(row.get("completed_tasks") or 0)
            pct = int(round((completed / total) * 100)) if total > 0 else 0
            return {
                "total_tasks": total,
                "completed_tasks": completed,
                "task_completion_pct": pct,
                "active_plans": int(row.get("active_plans") or 0)
            }
    finally:
        conn.close()


def find_recent_activity(user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Aggregates recent student actions (quiz attempts and study tasks) ordered by date.
    """
    if not user_id:
        return []
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            sql = """
                SELECT 
                    'quiz' AS activity_type,
                    t.topic_name AS title,
                    CONCAT('Scored ', ROUND(qa.score_percentage, 0), '%') AS details,
                    qa.attempted_at AS timestamp
                FROM quiz_attempts qa
                JOIN topics t ON qa.topic_id = t.id
                WHERE qa.user_id = %s
                
                UNION ALL
                
                SELECT 
                    'study_plan' AS activity_type,
                    spi.task AS title,
                    CONCAT('Completed task in ', s.name) AS details,
                    spi.created_at AS timestamp
                FROM study_plan_items spi
                JOIN study_plans sp ON spi.study_plan_id = sp.id
                JOIN subjects s ON sp.subject_id = s.id
                WHERE sp.user_id = %s AND spi.completed = 1
                
                ORDER BY timestamp DESC
                LIMIT %s
            """
            cursor.execute(sql, (user_id, user_id, limit))
            return cursor.fetchall()
    finally:
        conn.close()


def insert_ai_chat_log(user_id: int, question: str, answer: str) -> Optional[int]:
    """
    Logs an academic interaction with the AI Mentor in the 'ai_chats' table.
    """
    if not user_id:
        return None
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO ai_chats (user_id, question, answer)
                VALUES (%s, %s, %s)
                """,
                (user_id, question, answer)
            )
            return cursor.lastrowid
    except Exception as exc:
        logger.error("Error logging AI chat: %s", sanitize_db_error(exc))
        return None
    finally:
        conn.close()


def find_ai_chats_by_user(user_id: int, limit: int = 50) -> List[Dict[str, Any]]:
    """
    Retrieves AI chat interaction history for a student.
    """
    if not user_id:
        return []
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, user_id, question, answer, created_at
                FROM ai_chats
                WHERE user_id = %s
                ORDER BY created_at DESC
                LIMIT %s
                """,
                (user_id, limit)
            )
            return cursor.fetchall()
    finally:
        conn.close()


def find_ai_chat_by_id(chat_id: int, user_id: int) -> Optional[Dict[str, Any]]:
    """
    Retrieves a specific AI chat dialogue with student ownership verification.
    """
    if not chat_id or not user_id:
        return None
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, user_id, question, answer, created_at
                FROM ai_chats
                WHERE id = %s AND user_id = %s
                """,
                (chat_id, user_id)
            )
            return cursor.fetchone()
    finally:
        conn.close()


def find_weak_topics_by_user(user_id: int, threshold: float = 60.0) -> List[Dict[str, Any]]:
    """
    Identifies topics with real evidence of student struggle (low quiz scores or low progress mastery).
    """
    if not user_id:
        return []
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT 
                    p.topic_id,
                    p.completion_percentage,
                    p.last_updated,
                    t.topic_name,
                    t.difficulty,
                    s.id AS subject_id,
                    s.name AS subject_name,
                    COALESCE(AVG(qa.score_percentage), 0.0) AS avg_quiz_score,
                    COUNT(qa.id) AS quiz_attempts_count
                FROM progress p
                JOIN topics t ON p.topic_id = t.id
                JOIN subjects s ON t.subject_id = s.id
                LEFT JOIN quiz_attempts qa ON p.topic_id = qa.topic_id AND qa.user_id = p.user_id
                WHERE p.user_id = %s AND (p.completion_percentage < %s OR (qa.score_percentage IS NOT NULL AND qa.score_percentage < %s))
                GROUP BY p.topic_id, p.completion_percentage, p.last_updated, t.topic_name, t.difficulty, s.id, s.name
                ORDER BY p.completion_percentage ASC, avg_quiz_score ASC
                """,
                (user_id, threshold, threshold)
            )
            return cursor.fetchall()
    finally:
        conn.close()


def find_topic_learning_evidence(user_id: int, topic_id: int) -> Dict[str, Any]:
    """
    Retrieves authentic study plan tasks and quiz attempt statistics for a single topic.
    Used for calculating topic mastery percentage.
    """
    if not user_id or not topic_id:
        return {"total_tasks": 0, "completed_tasks": 0, "attempts_count": 0, "best_score": 0.0, "avg_score": 0.0}

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # Study tasks
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

            # Quizzes
            cursor.execute(
                """
                SELECT 
                    COUNT(id) AS attempts_count,
                    COALESCE(MAX(score_percentage), 0.0) AS best_score,
                    COALESCE(AVG(score_percentage), 0.0) AS avg_score
                FROM quiz_attempts
                WHERE user_id = %s AND topic_id = %s
                """,
                (user_id, topic_id)
            )
            quiz_data = cursor.fetchone() or {}

            return {
                "total_tasks": int(task_data.get("total_tasks") or 0),
                "completed_tasks": int(task_data.get("completed_tasks") or 0),
                "attempts_count": int(quiz_data.get("attempts_count") or 0),
                "best_score": float(quiz_data.get("best_score") or 0.0),
                "avg_score": float(quiz_data.get("avg_score") or 0.0)
            }
    finally:
        conn.close()


def find_user_topic_progress_matrix(user_id: int, subject_id: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Queries all topics joined with progress, quiz metrics, and study plan metrics for a user.
    Optionally filters by subject_id.
    """
    if not user_id:
        return []

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            params: List[Any] = [user_id, user_id, user_id]
            subject_filter = ""
            if subject_id:
                subject_filter = "WHERE t.subject_id = %s"
                params.append(subject_id)

            sql = f"""
                SELECT 
                    t.id AS topic_id,
                    t.topic_name,
                    t.difficulty AS topic_difficulty,
                    s.id AS subject_id,
                    s.name AS subject_name,
                    COALESCE(p.completion_percentage, 0.0) AS completion_percentage,
                    p.last_updated,
                    COALESCE(q_stat.attempts_count, 0) AS quiz_attempts,
                    COALESCE(q_stat.best_score, 0.0) AS best_quiz_score,
                    COALESCE(q_stat.avg_score, 0.0) AS avg_quiz_score,
                    COALESCE(task_stat.total_tasks, 0) AS total_tasks,
                    COALESCE(task_stat.completed_tasks, 0) AS completed_tasks
                FROM topics t
                JOIN subjects s ON t.subject_id = s.id
                LEFT JOIN progress p 
                    ON t.id = p.topic_id AND p.user_id = %s
                LEFT JOIN (
                    SELECT 
                        topic_id,
                        COUNT(id) AS attempts_count,
                        MAX(score_percentage) AS best_score,
                        AVG(score_percentage) AS avg_score
                    FROM quiz_attempts
                    WHERE user_id = %s
                    GROUP BY topic_id
                ) q_stat ON t.id = q_stat.topic_id
                LEFT JOIN (
                    SELECT 
                        spi.topic_id,
                        COUNT(spi.id) AS total_tasks,
                        SUM(CASE WHEN spi.completed = 1 THEN 1 ELSE 0 END) AS completed_tasks
                    FROM study_plan_items spi
                    JOIN study_plans sp ON spi.study_plan_id = sp.id
                    WHERE sp.user_id = %s
                    GROUP BY spi.topic_id
                ) task_stat ON t.id = task_stat.topic_id
                {subject_filter}
                ORDER BY s.id ASC, t.id ASC
            """
            cursor.execute(sql, tuple(params))
            return cursor.fetchall()
    finally:
        conn.close()


def find_learning_stats_aggregates(user_id: int) -> Dict[str, Any]:
    """
    Gathers raw learning statistics (study plan tasks, quiz attempts, and AI inquiries).
    """
    empty = {
        "total_tasks": 0,
        "completed_tasks": 0,
        "total_attempts": 0,
        "total_questions": 0,
        "total_correct": 0,
        "avg_quiz_score": 0.0,
        "best_quiz_score": 0.0,
        "total_ai_doubts": 0
    }
    if not user_id:
        return empty

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # 1. Study Plan Stats
            cursor.execute(
                """
                SELECT 
                    COUNT(spi.id) AS total_tasks,
                    COALESCE(SUM(CASE WHEN spi.completed = 1 THEN 1 ELSE 0 END), 0) AS completed_tasks
                FROM study_plan_items spi
                JOIN study_plans sp ON spi.study_plan_id = sp.id
                WHERE sp.user_id = %s
                """,
                (user_id,)
            )
            sp_data = cursor.fetchone() or {}

            # 2. Quiz Stats
            cursor.execute(
                """
                SELECT 
                    COUNT(id) AS total_attempts,
                    COALESCE(SUM(total_questions), 0) AS total_questions,
                    COALESCE(SUM(correct_answers), 0) AS total_correct,
                    COALESCE(AVG(score_percentage), 0.0) AS avg_score,
                    COALESCE(MAX(score_percentage), 0.0) AS best_score
                FROM quiz_attempts
                WHERE user_id = %s
                """,
                (user_id,)
            )
            q_data = cursor.fetchone() or {}

            # 3. AI Chats Count
            cursor.execute(
                "SELECT COUNT(id) AS total_chats FROM ai_chats WHERE user_id = %s",
                (user_id,)
            )
            ai_data = cursor.fetchone() or {}

            return {
                "total_tasks": int(sp_data.get("total_tasks") or 0),
                "completed_tasks": int(sp_data.get("completed_tasks") or 0),
                "total_attempts": int(q_data.get("total_attempts") or 0),
                "total_questions": int(q_data.get("total_questions") or 0),
                "total_correct": int(q_data.get("total_correct") or 0),
                "avg_quiz_score": round(float(q_data.get("avg_score") or 0.0), 1),
                "best_quiz_score": round(float(q_data.get("best_score") or 0.0), 1),
                "total_ai_doubts": int(ai_data.get("total_chats") or 0)
            }
    finally:
        conn.close()


def find_recent_activity_records(user_id: int, limit: int = 10) -> Dict[str, List[Dict[str, Any]]]:
    """
    Fetches raw activity records across quizzes, study tasks, and AI doubts.
    """
    if not user_id:
        return {"quizzes": [], "study_tasks": [], "ai_chats": []}

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # Recent Quizzes
            cursor.execute(
                """
                SELECT 
                    a.id AS attempt_id,
                    a.score_percentage,
                    a.attempted_at,
                    t.id AS topic_id,
                    t.topic_name,
                    s.name AS subject_name
                FROM quiz_attempts a
                JOIN topics t ON a.topic_id = t.id
                JOIN subjects s ON t.subject_id = s.id
                WHERE a.user_id = %s
                ORDER BY a.attempted_at DESC
                LIMIT %s
                """,
                (user_id, limit)
            )
            quizzes = cursor.fetchall()

            # Recent Study Tasks
            cursor.execute(
                """
                SELECT 
                    spi.id AS item_id,
                    spi.task,
                    spi.created_at,
                    sp.id AS plan_id,
                    sp.goal,
                    t.topic_name
                FROM study_plan_items spi
                JOIN study_plans sp ON spi.study_plan_id = sp.id
                LEFT JOIN topics t ON spi.topic_id = t.id
                WHERE sp.user_id = %s AND spi.completed = 1
                ORDER BY spi.id DESC
                LIMIT %s
                """,
                (user_id, limit)
            )
            study_tasks = cursor.fetchall()

            # Recent AI Doubts
            cursor.execute(
                """
                SELECT 
                    id,
                    question,
                    created_at
                FROM ai_chats
                WHERE user_id = %s
                ORDER BY created_at DESC
                LIMIT %s
                """,
                (user_id, limit)
            )
            ai_chats = cursor.fetchall()

            return {
                "quizzes": quizzes,
                "study_tasks": study_tasks,
                "ai_chats": ai_chats
            }
    finally:
        conn.close()

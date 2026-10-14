"""
Study Plan Model for AI Student Learning Mentor.
Encapsulates SQL operations for 'study_plans' and 'study_plan_items' tables.
Enforces parameterized queries, atomic transactions, and student authorization checks.
"""
import logging
from typing import Optional, Dict, Any, List, Tuple
from database.db_connection import get_db_connection, sanitize_db_error

logger = logging.getLogger(__name__)


def insert_study_plan_with_items(
    user_id: int,
    subject_id: int,
    goal: str,
    duration_days: int,
    skill_level: str,
    preferred_study_time: str,
    items: List[Dict[str, Any]]
) -> Tuple[bool, str, Optional[int]]:
    """
    Atomically inserts a new study plan and its day-by-day task items in a single transaction.
    Rolls back completely if any item insertion fails.
    """
    conn = get_db_connection(autocommit=False)
    try:
        with conn.cursor() as cursor:
            # 1. Insert parent study plan
            cursor.execute(
                """
                INSERT INTO study_plans 
                    (user_id, subject_id, goal, duration_days, skill_level, preferred_study_time)
                VALUES 
                    (%s, %s, %s, %s, %s, %s)
                """,
                (user_id, subject_id, goal, duration_days, skill_level, preferred_study_time)
            )
            plan_id = cursor.lastrowid

            # 2. Bulk insert daily items
            if items:
                items_sql = """
                    INSERT INTO study_plan_items 
                        (study_plan_id, day_number, topic_id, task, completed)
                    VALUES 
                        (%s, %s, %s, %s, %s)
                """
                item_tuples = [
                    (
                        plan_id,
                        item['day_number'],
                        item['topic_id'],
                        item['task'],
                        item.get('completed', False)
                    )
                    for item in items
                ]
                cursor.executemany(items_sql, item_tuples)

            conn.commit()
            return True, "Study plan created successfully.", plan_id
    except Exception as exc:
        conn.rollback()
        logger.error("Transaction error creating study plan: %s", sanitize_db_error(exc))
        return False, "Database error creating study plan.", None
    finally:
        conn.close()


def find_study_plans_by_user(user_id: int) -> List[Dict[str, Any]]:
    """
    Retrieves all study plans created by a user, with computed task completion metrics.
    """
    if not user_id:
        return []
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT 
                    sp.id,
                    sp.user_id,
                    sp.subject_id,
                    sp.goal,
                    sp.duration_days,
                    sp.skill_level,
                    sp.preferred_study_time,
                    sp.created_at,
                    s.name AS subject_name,
                    COUNT(spi.id) AS total_items,
                    SUM(CASE WHEN spi.completed = 1 THEN 1 ELSE 0 END) AS completed_items
                FROM study_plans sp
                JOIN subjects s ON sp.subject_id = s.id
                LEFT JOIN study_plan_items spi ON sp.id = spi.study_plan_id
                WHERE sp.user_id = %s
                GROUP BY sp.id
                ORDER BY sp.created_at DESC
                """,
                (user_id,)
            )
            plans = cursor.fetchall()
            for p in plans:
                total = p.get('total_items') or 0
                completed = p.get('completed_items') or 0
                p['progress_pct'] = int(round((completed / total) * 100)) if total > 0 else 0
            return plans
    finally:
        conn.close()


def find_study_plan_by_id(plan_id: int, user_id: int = None) -> Optional[Dict[str, Any]]:
    """
    Retrieves a study plan by ID, optionally verifying ownership with user_id.
    """
    if not plan_id:
        return None
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            sql = """
                SELECT 
                    sp.id,
                    sp.user_id,
                    sp.subject_id,
                    sp.goal,
                    sp.duration_days,
                    sp.skill_level,
                    sp.preferred_study_time,
                    sp.created_at,
                    s.name AS subject_name,
                    COUNT(spi.id) AS total_items,
                    SUM(CASE WHEN spi.completed = 1 THEN 1 ELSE 0 END) AS completed_items
                FROM study_plans sp
                JOIN subjects s ON sp.subject_id = s.id
                LEFT JOIN study_plan_items spi ON sp.id = spi.study_plan_id
                WHERE sp.id = %s
            """
            params = [plan_id]
            if user_id is not None:
                sql += " AND sp.user_id = %s"
                params.append(user_id)

            sql += " GROUP BY sp.id"
            cursor.execute(sql, tuple(params))
            plan = cursor.fetchone()
            if plan:
                total = plan.get('total_items') or 0
                completed = plan.get('completed_items') or 0
                plan['progress_pct'] = int(round((completed / total) * 100)) if total > 0 else 0
            return plan
    finally:
        conn.close()


def find_study_plan_items(plan_id: int) -> List[Dict[str, Any]]:
    """
    Retrieves daily tasks for a study plan ordered by day number.
    """
    if not plan_id:
        return []
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT 
                    spi.id,
                    spi.study_plan_id,
                    spi.day_number,
                    spi.topic_id,
                    spi.task,
                    spi.completed,
                    spi.created_at,
                    t.topic_name,
                    t.difficulty AS topic_difficulty
                FROM study_plan_items spi
                JOIN topics t ON spi.topic_id = t.id
                WHERE spi.study_plan_id = %s
                ORDER BY spi.day_number ASC, spi.id ASC
                """,
                (plan_id,)
            )
            return cursor.fetchall()
    finally:
        conn.close()


def toggle_plan_item_status(item_id: int, plan_id: int, user_id: int, state: bool = None) -> Tuple[bool, str, Optional[bool]]:
    """
    Toggles or explicitly sets completion boolean of a task item.
    Enforces authorization check ensuring user owns the parent study plan.
    """
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # Verify ownership
            cursor.execute(
                """
                SELECT spi.completed 
                FROM study_plan_items spi
                JOIN study_plans sp ON spi.study_plan_id = sp.id
                WHERE spi.id = %s AND spi.study_plan_id = %s AND sp.user_id = %s
                """,
                (item_id, plan_id, user_id)
            )
            row = cursor.fetchone()
            if not row:
                return False, "Item not found or unauthorized.", None

            new_status = bool(state) if state is not None else not bool(row['completed'])
            cursor.execute(
                """
                UPDATE study_plan_items 
                SET completed = %s 
                WHERE id = %s AND study_plan_id = %s
                """,
                (new_status, item_id, plan_id)
            )
            return True, "Item status updated.", new_status
    finally:
        conn.close()


def delete_study_plan_record(plan_id: int, user_id: int) -> Tuple[bool, str]:
    """
    Deletes a study plan and associated items (via foreign key CASCADE) with ownership check.
    """
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT id FROM study_plans WHERE id = %s AND user_id = %s",
                (plan_id, user_id)
            )
            if not cursor.fetchone():
                return False, "Study plan not found or unauthorized."

            cursor.execute(
                "DELETE FROM study_plans WHERE id = %s AND user_id = %s",
                (plan_id, user_id)
            )
            return True, "Study plan deleted successfully."
    finally:
        conn.close()


def update_study_plan_record(
    plan_id: int, 
    user_id: int, 
    goal: str, 
    preferred_study_time: str,
    duration_days: int = None,
    skill_level: str = None
) -> Tuple[bool, str]:
    """
    Updates the goal and preferred study time for a student study plan.
    """
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            fields = ["goal = %s", "preferred_study_time = %s"]
            params = [goal, preferred_study_time]
            if duration_days is not None:
                fields.append("duration_days = %s")
                params.append(duration_days)
            if skill_level is not None:
                fields.append("skill_level = %s")
                params.append(skill_level)

            params.extend([plan_id, user_id])
            sql = f"UPDATE study_plans SET {', '.join(fields)} WHERE id = %s AND user_id = %s"
            cursor.execute(sql, tuple(params))
            if cursor.rowcount == 0:
                cursor.execute(
                    "SELECT id FROM study_plans WHERE id = %s AND user_id = %s",
                    (plan_id, user_id)
                )
                if not cursor.fetchone():
                    return False, "Study plan not found or unauthorized."
            return True, "Study plan updated successfully."
    finally:
        conn.close()


def find_user_study_stats(user_id: int) -> Dict[str, Any]:
    """
    Retrieves aggregated study plan statistics for a user.
    """
    if not user_id:
        return {
            "total_plans": 0,
            "completed_plans": 0,
            "total_tasks": 0,
            "completed_tasks": 0,
            "completion_rate": 0
        }
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT 
                    COUNT(DISTINCT sp.id) AS total_plans,
                    COUNT(spi.id) AS total_tasks,
                    SUM(CASE WHEN spi.completed = 1 THEN 1 ELSE 0 END) AS completed_tasks
                FROM study_plans sp
                LEFT JOIN study_plan_items spi ON sp.id = spi.study_plan_id
                WHERE sp.user_id = %s
                """,
                (user_id,)
            )
            row = cursor.fetchone() or {}
            total_plans = int(row.get("total_plans") or 0)
            total_tasks = int(row.get("total_tasks") or 0)
            completed_tasks = int(row.get("completed_tasks") or 0)
            rate = int(round((completed_tasks / total_tasks) * 100)) if total_tasks > 0 else 0

            # Count plans where all items are completed
            cursor.execute(
                """
                SELECT sp.id, 
                       COUNT(spi.id) AS total_items, 
                       SUM(CASE WHEN spi.completed = 1 THEN 1 ELSE 0 END) AS completed_items
                FROM study_plans sp
                JOIN study_plan_items spi ON sp.id = spi.study_plan_id
                WHERE sp.user_id = %s
                GROUP BY sp.id
                HAVING total_items > 0 AND total_items = completed_items
                """,
                (user_id,)
            )
            completed_plans = len(cursor.fetchall())

            return {
                "total_plans": total_plans,
                "completed_plans": completed_plans,
                "total_tasks": total_tasks,
                "completed_tasks": completed_tasks,
                "completion_rate": rate
            }
    finally:
        conn.close()


def find_pending_study_tasks(user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Retrieves uncompleted study plan tasks for active study plans of a user,
    ordered by day_number ascending.
    """
    if not user_id:
        return []
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT 
                    spi.id AS item_id,
                    spi.study_plan_id,
                    spi.day_number,
                    spi.topic_id,
                    spi.task,
                    spi.completed,
                    sp.subject_id,
                    s.name AS subject_name,
                    t.topic_name,
                    t.difficulty AS topic_difficulty
                FROM study_plan_items spi
                JOIN study_plans sp ON spi.study_plan_id = sp.id
                JOIN subjects s ON sp.subject_id = s.id
                JOIN topics t ON spi.topic_id = t.id
                WHERE sp.user_id = %s AND spi.completed = 0
                ORDER BY spi.day_number ASC, spi.id ASC
                LIMIT %s
                """,
                (user_id, limit)
            )
            return cursor.fetchall()
    finally:
        conn.close()

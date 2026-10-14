"""
Quiz Model for AI Student Learning Mentor.
Encapsulates SQL operations for 'quizzes', 'quiz_attempts', and 'quiz_attempt_answers' tables.
Enforces parameterized queries, atomic multi-question grading transactions, and student authorization.
"""
import logging
from typing import Optional, Dict, Any, List, Tuple
from database.db_connection import get_db_connection, sanitize_db_error

logger = logging.getLogger(__name__)


def find_quiz_catalog() -> List[Dict[str, Any]]:
    """
    Retrieves topics that have practice questions available, with question counts.
    """
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            sql = """
                SELECT 
                    t.id AS topic_id,
                    t.topic_name,
                    t.difficulty,
                    s.id AS subject_id,
                    s.name AS subject_name,
                    COUNT(q.id) AS question_count
                FROM topics t
                JOIN subjects s ON t.subject_id = s.id
                JOIN quizzes q ON t.id = q.topic_id
                GROUP BY t.id
                ORDER BY s.name ASC, t.topic_name ASC
            """
            cursor.execute(sql)
            return cursor.fetchall()
    finally:
        conn.close()


def find_quiz_catalog_raw() -> List[Dict[str, Any]]:
    """
    Retrieves all subjects and topics with question counts from MySQL.
    """
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            sql = """
                SELECT 
                    s.id AS subject_id,
                    s.name AS subject_name,
                    s.description AS subject_description,
                    t.id AS topic_id,
                    t.topic_name,
                    t.difficulty AS topic_difficulty,
                    COUNT(q.id) AS question_count
                FROM subjects s
                JOIN topics t ON s.id = t.subject_id
                LEFT JOIN quizzes q ON t.id = q.topic_id
                GROUP BY s.id, t.id
                ORDER BY s.name ASC, t.id ASC
            """
            cursor.execute(sql)
            return cursor.fetchall()
    finally:
        conn.close()


def find_quiz_catalog_grouped() -> List[Dict[str, Any]]:
    """
    Retrieves all subjects and topics with question counts, grouped by subject.
    """
    rows = find_quiz_catalog_raw()
    subjects_map: Dict[int, Dict[str, Any]] = {}
    for row in rows:
        sid = row["subject_id"]
        if sid not in subjects_map:
            subjects_map[sid] = {
                "subject_id": sid,
                "subject_name": row["subject_name"],
                "subject_description": row.get("subject_description") or "",
                "topics": [],
                "total_questions": 0
            }

        q_count = int(row["question_count"] or 0)
        subjects_map[sid]["topics"].append({
            "topic_id": row["topic_id"],
            "topic_name": row["topic_name"],
            "difficulty": row.get("topic_difficulty"),
            "question_count": q_count
        })
        subjects_map[sid]["total_questions"] += q_count

    return list(subjects_map.values())


def find_quizzes_by_topic(topic_id: int, include_correct: bool = False) -> List[Dict[str, Any]]:
    """
    Retrieves all practice questions for a topic.
    Omits correct_answer by default for security when sent to client during active test.
    """
    if not topic_id:
        return []
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            if include_correct:
                sql = """
                    SELECT 
                        id, topic_id, question, 
                        option_a, option_b, option_c, option_d, 
                        correct_answer, difficulty, created_at
                    FROM quizzes
                    WHERE topic_id = %s
                    ORDER BY id ASC
                """
            else:
                sql = """
                    SELECT 
                        id, topic_id, question, 
                        option_a, option_b, option_c, option_d, 
                        difficulty, created_at
                    FROM quizzes
                    WHERE topic_id = %s
                    ORDER BY id ASC
                """
            cursor.execute(sql, (topic_id,))
            return cursor.fetchall()
    finally:
        conn.close()


def find_quiz_questions_with_answers(topic_id: int) -> List[Dict[str, Any]]:
    """
    Retrieves practice questions including correct_answer for server-side grading only.
    """
    if not topic_id:
        return []
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            sql = """
                SELECT 
                    id, topic_id, question, 
                    option_a, option_b, option_c, option_d, 
                    correct_answer, difficulty
                FROM quizzes
                WHERE topic_id = %s
                ORDER BY id ASC
            """
            cursor.execute(sql, (topic_id,))
            return cursor.fetchall()
    finally:
        conn.close()


def insert_quiz_attempt_with_answers(
    user_id: int,
    topic_id: int,
    total_questions: int,
    correct_answers: int,
    score_percentage: float,
    answers: List[Dict[str, Any]]
) -> Tuple[bool, str, Optional[int]]:
    """
    Atomically records a student quiz attempt and all per-question answers in one transaction.
    """
    conn = get_db_connection(autocommit=False)
    try:
        with conn.cursor() as cursor:
            # 1. Insert parent attempt
            cursor.execute(
                """
                INSERT INTO quiz_attempts 
                    (user_id, topic_id, total_questions, correct_answers, score_percentage, score)
                VALUES 
                    (%s, %s, %s, %s, %s, %s)
                """,
                (user_id, topic_id, total_questions, correct_answers, score_percentage, score_percentage)
            )
            attempt_id = cursor.lastrowid

            # 2. Bulk insert individual answer choices
            if answers:
                ans_sql = """
                    INSERT INTO quiz_attempt_answers 
                        (attempt_id, quiz_id, selected_answer, correct_answer, is_correct)
                    VALUES 
                        (%s, %s, %s, %s, %s)
                """
                ans_tuples = [
                    (
                        attempt_id,
                        ans['quiz_id'],
                        ans['selected_answer'],
                        ans['correct_answer'],
                        ans['is_correct']
                    )
                    for ans in answers
                ]
                cursor.executemany(ans_sql, ans_tuples)

            conn.commit()
            return True, "Quiz attempt recorded successfully.", attempt_id
    except Exception as exc:
        conn.rollback()
        logger.error("Transaction error saving quiz attempt: %s", sanitize_db_error(exc))
        return False, "Database error recording quiz attempt.", None
    finally:
        conn.close()


def find_quiz_attempt_by_id(attempt_id: int, user_id: int = None) -> Optional[Dict[str, Any]]:
    """
    Retrieves a quiz attempt result with topic and subject details.
    Enforces authorization check if user_id is provided.
    """
    if not attempt_id:
        return None
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            sql = """
                SELECT 
                    qa.id,
                    qa.user_id,
                    qa.topic_id,
                    qa.total_questions,
                    qa.correct_answers,
                    qa.score_percentage,
                    qa.attempted_at,
                    t.topic_name,
                    t.difficulty AS topic_difficulty,
                    s.id AS subject_id,
                    s.name AS subject_name
                FROM quiz_attempts qa
                JOIN topics t ON qa.topic_id = t.id
                JOIN subjects s ON t.subject_id = s.id
                WHERE qa.id = %s
            """
            params = [attempt_id]
            if user_id is not None:
                sql += " AND qa.user_id = %s"
                params.append(user_id)

            cursor.execute(sql, tuple(params))
            return cursor.fetchone()
    finally:
        conn.close()


def find_quiz_attempt_answers(attempt_id: int) -> List[Dict[str, Any]]:
    """
    Retrieves full question-by-question review records for a quiz attempt.
    """
    if not attempt_id:
        return []
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            sql = """
                SELECT 
                    qaa.id,
                    qaa.attempt_id,
                    qaa.quiz_id,
                    qaa.selected_answer,
                    qaa.correct_answer,
                    qaa.is_correct,
                    q.question,
                    q.option_a,
                    q.option_b,
                    q.option_c,
                    q.option_d,
                    q.difficulty
                FROM quiz_attempt_answers qaa
                JOIN quizzes q ON qaa.quiz_id = q.id
                WHERE qaa.attempt_id = %s
                ORDER BY qaa.id ASC
            """
            cursor.execute(sql, (attempt_id,))
            return cursor.fetchall()
    finally:
        conn.close()


def find_quiz_attempts_by_user(user_id: int, limit: int = 50) -> List[Dict[str, Any]]:
    """
    Retrieves historical quiz attempts for the authenticated student.
    """
    if not user_id:
        return []
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            sql = """
                SELECT 
                    qa.id,
                    qa.topic_id,
                    qa.total_questions,
                    qa.correct_answers,
                    qa.score_percentage,
                    qa.attempted_at,
                    t.topic_name,
                    s.name AS subject_name
                FROM quiz_attempts qa
                JOIN topics t ON qa.topic_id = t.id
                JOIN subjects s ON t.subject_id = s.id
                WHERE qa.user_id = %s
                ORDER BY qa.attempted_at DESC
                LIMIT %s
            """
            cursor.execute(sql, (user_id, limit))
            return cursor.fetchall()
    finally:
        conn.close()


def find_topic_quiz_info(topic_id: int) -> Optional[Dict[str, Any]]:
    """
    Retrieves topic details, parent subject, and available question counts.
    """
    if not topic_id:
        return None
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            sql = """
                SELECT 
                    t.id AS topic_id,
                    t.topic_name,
                    t.description AS topic_description,
                    t.difficulty AS topic_difficulty,
                    s.id AS subject_id,
                    s.name AS subject_name,
                    COUNT(q.id) AS question_count
                FROM topics t
                JOIN subjects s ON t.subject_id = s.id
                LEFT JOIN quizzes q ON t.id = q.topic_id
                WHERE t.id = %s
                GROUP BY t.id, s.id
            """
            cursor.execute(sql, (topic_id,))
            row = cursor.fetchone()
            if not row:
                return None
            row["question_count"] = int(row.get("question_count") or 0)
            return row
    finally:
        conn.close()


def find_quiz_questions_by_ids(question_ids: List[int], topic_id: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Fetches genuine question records for grading by question ID list.
    Optionally validates topic_id ownership.
    """
    if not question_ids:
        return []
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            placeholders = ', '.join(['%s'] * len(question_ids))
            sql = f"""
                SELECT id, topic_id, correct_answer
                FROM quizzes
                WHERE id IN ({placeholders})
            """
            params: List[Any] = [int(qid) for qid in question_ids]
            if topic_id is not None:
                sql += " AND topic_id = %s"
                params.append(topic_id)
            cursor.execute(sql, tuple(params))
            return cursor.fetchall()
    finally:
        conn.close()


def has_quiz_for_topic(topic_id: int) -> bool:
    """
    Checks if a given topic has at least one question in the quizzes table.
    """
    if not topic_id:
        return False
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id FROM quizzes WHERE topic_id = %s LIMIT 1", (topic_id,))
            return cursor.fetchone() is not None
    finally:
        conn.close()


def find_user_quiz_stats(user_id: int) -> Dict[str, Any]:
    """
    Calculates aggregated quiz metrics for a user from real quiz_attempts records.
    Provides complete compatibility across both dashboard summary and catalog cards.
    """
    empty_stats = {
        "total_quizzes": 0,
        "total_attempts": 0,
        "average_score": 0.0,
        "avg_score": 0.0,
        "highest_score": 0.0,
        "best_score": 0.0,
        "passed_quizzes": 0,
        "total_questions_answered": 0,
        "total_correct_answers": 0,
        "accuracy_percentage": 0.0,
        "recent_attempts": []
    }
    if not user_id:
        return empty_stats

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            sql = """
                SELECT 
                    COUNT(qa.id) AS total_quizzes,
                    COALESCE(AVG(qa.score_percentage), 0.0) AS average_score,
                    COALESCE(MAX(qa.score_percentage), 0.0) AS highest_score,
                    SUM(CASE WHEN qa.score_percentage >= 70.0 THEN 1 ELSE 0 END) AS passed_quizzes,
                    SUM(qa.total_questions) AS total_questions_answered,
                    SUM(qa.correct_answers) AS total_correct_answers
                FROM quiz_attempts qa
                WHERE qa.user_id = %s
            """
            cursor.execute(sql, (user_id,))
            row = cursor.fetchone() or {}

            total_q = int(row.get("total_questions_answered") or 0)
            total_c = int(row.get("total_correct_answers") or 0)
            accuracy = round((total_c / total_q) * 100.0, 1) if total_q > 0 else 0.0
            avg_score = round(float(row.get("average_score") or 0.0), 1)
            highest_score = round(float(row.get("highest_score") or 0.0), 1)
            total_quizzes = int(row.get("total_quizzes") or 0)
            passed = int(row.get("passed_quizzes") or 0)

            # Fetch recent 3 attempts
            cursor.execute(
                """
                SELECT 
                    a.id,
                    a.topic_id,
                    a.total_questions,
                    a.correct_answers,
                    a.score_percentage,
                    a.attempted_at,
                    t.topic_name,
                    s.name AS subject_name
                FROM quiz_attempts a
                JOIN topics t ON a.topic_id = t.id
                JOIN subjects s ON t.subject_id = s.id
                WHERE a.user_id = %s
                ORDER BY a.attempted_at DESC
                LIMIT 3
                """,
                (user_id,)
            )
            recent = cursor.fetchall()
            for r in recent:
                r["score_percentage"] = float(r.get("score_percentage") or 0.0)

            return {
                "total_quizzes": total_quizzes,
                "total_attempts": total_quizzes,
                "average_score": avg_score,
                "avg_score": avg_score,
                "highest_score": highest_score,
                "best_score": highest_score,
                "passed_quizzes": passed,
                "total_questions_answered": total_q,
                "total_correct_answers": total_c,
                "accuracy_percentage": accuracy,
                "recent_attempts": recent
            }
    finally:
        conn.close()

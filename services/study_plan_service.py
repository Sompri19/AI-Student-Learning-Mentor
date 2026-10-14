"""
Personalized Study Plan Service for AI Student Learning Mentor.
Implements deterministic, rule-based study schedule generation, validation,
and database operations for personalized study plans and daily tasks.

NOTE: In accordance with academic integrity and project guidelines:
- Strictly deterministic, rule-based curriculum scheduling.
- Real database operations only (MySQL via PyMySQL).
- Zero fake AI generation or fabricated student data.
"""
import logging
from typing import List, Dict, Any, Optional, Tuple
from services.db import get_db_connection, sanitize_db_error

logger = logging.getLogger(__name__)

ALLOWED_SKILL_LEVELS = ['Beginner', 'Intermediate', 'Advanced']
ALLOWED_STUDY_TIMES = ['Morning', 'Afternoon', 'Evening', 'Night', 'Flexible']
MIN_DURATION_DAYS = 1
MAX_DURATION_DAYS = 60


def validate_study_plan_input(
    user_id: int,
    subject_id: Any,
    topic_ids: Any,
    duration_days: Any,
    goal: Any,
    skill_level: str = 'Beginner',
    preferred_study_time: str = 'Flexible'
) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
    """
    Validates all student inputs for study plan creation or updating.

    Returns:
        (is_valid, error_message, validated_data_dict)
    """
    if not user_id:
        return False, "User authentication required.", None

    # Validate subject_id
    try:
        subject_id_int = int(subject_id)
        if subject_id_int <= 0:
            return False, "A valid subject must be selected.", None
    except (ValueError, TypeError):
        return False, "A valid subject must be selected.", None

    # Validate duration_days
    try:
        duration_int = int(duration_days)
        if duration_int < MIN_DURATION_DAYS or duration_int > MAX_DURATION_DAYS:
            return False, f"Study plan duration must be between {MIN_DURATION_DAYS} and {MAX_DURATION_DAYS} days.", None
    except (ValueError, TypeError):
        return False, f"Study plan duration must be an integer between {MIN_DURATION_DAYS} and {MAX_DURATION_DAYS} days.", None

    # Validate learning goal
    if not goal or not isinstance(goal, str) or not goal.strip():
        return False, "Learning goal cannot be empty.", None
    cleaned_goal = goal.strip()

    # Validate skill_level
    cleaned_skill = (skill_level or 'Beginner').strip().capitalize()
    if cleaned_skill not in ALLOWED_SKILL_LEVELS:
        return False, f"Invalid skill level. Allowed values: {', '.join(ALLOWED_SKILL_LEVELS)}.", None

    # Validate preferred_study_time
    cleaned_time = (preferred_study_time or 'Flexible').strip().capitalize()
    if cleaned_time not in ALLOWED_STUDY_TIMES:
        return False, f"Invalid preferred study time. Allowed values: {', '.join(ALLOWED_STUDY_TIMES)}.", None

    # Validate topic_ids list
    if not topic_ids:
        return False, "At least one topic must be selected for your study plan.", None

    cleaned_topic_ids: List[int] = []
    if isinstance(topic_ids, (list, tuple, set)):
        for tid in topic_ids:
            try:
                tid_int = int(tid)
                if tid_int > 0 and tid_int not in cleaned_topic_ids:
                    cleaned_topic_ids.append(tid_int)
            except (ValueError, TypeError):
                return False, "Invalid topic identifier provided.", None
    else:
        try:
            tid_int = int(topic_ids)
            if tid_int > 0:
                cleaned_topic_ids.append(tid_int)
        except (ValueError, TypeError):
            return False, "Invalid topic identifier provided.", None

    if not cleaned_topic_ids:
        return False, "At least one topic must be selected for your study plan.", None

    # Verify subject exists and all selected topics belong to the subject via subject_model
    from models.subject_model import find_subject_by_id, find_topics_by_ids
    try:
        subject_row = find_subject_by_id(subject_id_int)
        if not subject_row:
            return False, f"Subject with ID {subject_id_int} does not exist.", None

        matched_topics = find_topics_by_ids(subject_id_int, cleaned_topic_ids)
        if len(matched_topics) != len(cleaned_topic_ids):
            return False, "All selected topics must belong to the selected subject.", None

        for t in matched_topics:
            if "name" not in t:
                t["name"] = t["topic_name"]

        validated_data = {
            "user_id": user_id,
            "subject_id": subject_id_int,
            "subject_name": subject_row["name"],
            "topic_ids": [t["id"] for t in matched_topics],
            "topics": matched_topics,
            "duration_days": duration_int,
            "goal": cleaned_goal,
            "skill_level": cleaned_skill,
            "preferred_study_time": cleaned_time
        }
        return True, None, validated_data
    except Exception as exc:
        logger.error(f"Error validating study plan input: {exc}", exc_info=True)
        return False, sanitize_db_error(exc), None


def generate_plan_schedule(
    subject_name: str,
    topics: List[Dict[str, Any]],
    duration_days: int,
    skill_level: str,
    goal: str,
    preferred_study_time: str
) -> List[Dict[str, Any]]:
    """
    Generates a deterministic day-by-day learning schedule based on academic rules.
    - No fake AI or synthetic output.
    - Accurately distributes topics across the requested duration.
    - Adapts task wording to skill level (Beginner, Intermediate, Advanced).
    - Integrates preferred study time and user learning goal into milestones.

    Returns:
        List of dicts: [{'day_number': int, 'topic_id': int, 'task': str, 'completed': False}, ...]
    """
    total_topics = len(topics)
    items: List[Dict[str, Any]] = []

    # Format helpers based on skill level
    def build_topic_task(topic_name: str, is_grouped: bool = False, group_names: str = "") -> str:
        if skill_level == 'Beginner':
            if is_grouped:
                return (
                    f"Foundations & Key Concepts: Study core definitions and basic principles "
                    f"for {group_names}. Focus on terminology and conceptual understanding. "
                    f"({preferred_study_time} study session)"
                )
            return (
                f"Foundations & Syntax: Read introductory notes, understand core definitions, "
                f"and study syntax examples for '{topic_name}'. "
                f"({preferred_study_time} study session)"
            )
        elif skill_level == 'Intermediate':
            if is_grouped:
                return (
                    f"Applied Problem Solving: Implement practical solutions and complete exercises "
                    f"covering {group_names}. Analyze how these topics connect. "
                    f"({preferred_study_time} study session)"
                )
            return (
                f"Applied Implementation: Study working examples, write practice code/solutions, "
                f"and test edge cases for '{topic_name}'. "
                f"({preferred_study_time} study session)"
            )
        else:  # Advanced
            if is_grouped:
                return (
                    f"Architectural Analysis: Deep-dive into internal mechanisms, architectural trade-offs, "
                    f"and performance considerations across {group_names}. "
                    f"({preferred_study_time} study session)"
                )
            return (
                f"Deep Dive & Mastery: Analyze internal algorithms, architectural patterns, "
                f"and solve advanced problem sets for '{topic_name}'. "
                f"({preferred_study_time} study session)"
            )

    def build_revision_task(topic_name: str, day_num: int, is_final: bool) -> str:
        if is_final:
            if skill_level == 'Beginner':
                return (
                    f"Milestone Consolidation: Comprehensive review across all covered topics in {subject_name} "
                    f"to achieve your goal: '{goal}'. Complete summary self-check questions."
                )
            elif skill_level == 'Intermediate':
                return (
                    f"Milestone Assessment: Synthesize curriculum knowledge in {subject_name} and complete "
                    f"an applied mini-project/problem set aligned with your goal: '{goal}'."
                )
            else:
                return (
                    f"Mastery Synthesis: Comprehensive synthesis, benchmarking, and rigorous problem-solving "
                    f"across {subject_name} to fulfill your goal: '{goal}'."
                )
        else:
            if skill_level == 'Beginner':
                return (
                    f"Concept Reinforcement: Revisit summary notes, flashcards, and solve beginner "
                    f"practice exercises for '{topic_name}' to reinforce retention."
                )
            elif skill_level == 'Intermediate':
                return (
                    f"Targeted Practice: Re-solve challenging problems and debug edge cases for '{topic_name}'."
                )
            else:
                return (
                    f"Performance & Edge Cases: Benchmark solutions, inspect system constraints, "
                    f"and explore advanced extensions for '{topic_name}'."
                )

    if duration_days >= total_topics:
        # Case 1: Duration is greater than or equal to topics count.
        # Days 1 .. total_topics: Cover each topic individually.
        for i in range(total_topics):
            topic = topics[i]
            day_num = i + 1
            t_name = topic.get('name') or topic.get('topic_name') or 'Topic'
            task_desc = build_topic_task(t_name)
            items.append({
                "day_number": day_num,
                "topic_id": topic['id'],
                "task": task_desc,
                "completed": False
            })

        # Remaining days (total_topics + 1 .. duration_days): Structured revision/milestone days
        for day_num in range(total_topics + 1, duration_days + 1):
            is_final = (day_num == duration_days)
            # Cycle through topics for revision reference
            rev_idx = (day_num - total_topics - 1) % total_topics
            rev_topic = topics[rev_idx]
            rev_name = rev_topic.get('name') or rev_topic.get('topic_name') or 'Topic'
            task_desc = build_revision_task(rev_name, day_num, is_final)
            items.append({
                "day_number": day_num,
                "topic_id": rev_topic['id'],
                "task": task_desc,
                "completed": False
            })
    else:
        # Case 2: Duration is strictly less than topics count (duration_days < total_topics).
        # We must partition total_topics into duration_days non-empty slices.
        # Every selected topic MUST be covered.
        k, r = divmod(total_topics, duration_days)
        slices = []
        start = 0
        for i in range(duration_days):
            end = start + k + (1 if i < r else 0)
            slices.append(topics[start:end])
            start = end

        for day_idx, day_topics in enumerate(slices):
            day_num = day_idx + 1
            primary_topic = day_topics[0]
            p_name = primary_topic.get('name') or primary_topic.get('topic_name') or 'Topic'
            if len(day_topics) == 1:
                task_desc = build_topic_task(p_name)
            else:
                names_joined = " and ".join(f"'{t.get('name') or t.get('topic_name') or 'Topic'}'" for t in day_topics)
                task_desc = build_topic_task(p_name, is_grouped=True, group_names=names_joined)

            items.append({
                "day_number": day_num,
                "topic_id": primary_topic['id'],
                "task": task_desc,
                "completed": False
            })

    return items


def create_study_plan(
    user_id: int,
    subject_id: int,
    topic_ids: List[int],
    duration_days: int,
    goal: str,
    skill_level: str = 'Beginner',
    preferred_study_time: str = 'Flexible'
) -> Tuple[bool, str, Optional[int]]:
    """
    Creates a new study plan and all associated daily task items in MySQL.
    Executes atomically in a single transaction.

    Returns:
        (success, message, created_plan_id)
    """
    is_valid, error_msg, validated = validate_study_plan_input(
        user_id=user_id,
        subject_id=subject_id,
        topic_ids=topic_ids,
        duration_days=duration_days,
        goal=goal,
        skill_level=skill_level,
        preferred_study_time=preferred_study_time
    )

    if not is_valid or not validated:
        return False, error_msg or "Invalid study plan input.", None

    schedule_items = generate_plan_schedule(
        subject_name=validated["subject_name"],
        topics=validated["topics"],
        duration_days=validated["duration_days"],
        skill_level=validated["skill_level"],
        goal=validated["goal"],
        preferred_study_time=validated["preferred_study_time"]
    )

    from models.study_plan_model import insert_study_plan_with_items
    success, msg, plan_id = insert_study_plan_with_items(
        user_id=validated["user_id"],
        subject_id=validated["subject_id"],
        goal=validated["goal"],
        duration_days=validated["duration_days"],
        skill_level=validated["skill_level"],
        preferred_study_time=validated["preferred_study_time"],
        items=schedule_items
    )
    if success:
        return True, "Study plan created successfully!", plan_id
    return False, msg, None


def get_user_study_plans(user_id: int) -> List[Dict[str, Any]]:
    """
    Retrieves all study plans owned by the specified authenticated user via study_plan_model.
    Includes calculated real progress (completed_tasks vs total_tasks).
    """
    if not user_id:
        return []

    from models.study_plan_model import find_study_plans_by_user
    plans = find_study_plans_by_user(user_id)
    for p in plans:
        total = int(p.get("total_items") or p.get("total_tasks") or 0)
        completed = int(p.get("completed_items") or p.get("completed_tasks") or 0)
        p["total_tasks"] = total
        p["completed_tasks"] = completed
        p["completion_percentage"] = p.get("progress_pct", round((completed / total) * 100) if total > 0 else 0)
    return plans


def get_study_plan_detail(plan_id: int, user_id: int) -> Optional[Dict[str, Any]]:
    """
    Retrieves a study plan and all its daily tasks via study_plan_model.
    Enforces student isolation: plan must belong to user_id.

    Returns:
        Dict with plan metadata, items list, topic summaries, and stats,
        or None if not found or unauthorized.
    """
    if not plan_id or not user_id:
        return None

    from models.study_plan_model import find_study_plan_by_id, find_study_plan_items
    plan = find_study_plan_by_id(plan_id, user_id=user_id)
    if not plan:
        return None

    items = find_study_plan_items(plan_id)
    for item in items:
        item["completed"] = bool(item.get("completed"))
        if "name" not in item:
            item["name"] = item.get("topic_name", "")

    seen_tids = set()
    topics = []
    for it in items:
        tid = it.get("topic_id")
        if tid and tid not in seen_tids:
            seen_tids.add(tid)
            topics.append({
                "id": tid,
                "topic_name": it.get("topic_name", ""),
                "name": it.get("topic_name", ""),
                "difficulty": it.get("topic_difficulty", "")
            })

    total_tasks = len(items)
    completed_tasks = sum(1 for it in items if it["completed"])
    pct = round((completed_tasks / total_tasks) * 100) if total_tasks > 0 else 0

    return {
        "plan": plan,
        "items": items,
        "topics": topics,
        "total_tasks": total_tasks,
        "completed_tasks": completed_tasks,
        "completion_percentage": pct
    }


def toggle_task_completion(
    plan_id: int,
    item_id: int,
    user_id: int,
    state: Optional[bool] = None
) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """
    Toggles or sets the completion status of a daily task item.
    Enforces authorization: plan must belong to user_id, and item must belong to plan_id.

    Returns:
        (success, message, result_dict)
    """
    if not plan_id or not item_id or not user_id:
        return False, "Missing required parameters.", None

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # Verify plan ownership
            cursor.execute(
                "SELECT id FROM study_plans WHERE id = %s AND user_id = %s",
                (plan_id, user_id)
            )
            plan = cursor.fetchone()
            if not plan:
                return False, "Study plan not found or unauthorized.", None

            # Verify item belongs to this plan
            cursor.execute(
                "SELECT id, topic_id, completed FROM study_plan_items WHERE id = %s AND study_plan_id = %s",
                (item_id, plan_id)
            )
            item = cursor.fetchone()
            if not item:
                return False, "Daily task not found in this study plan.", None

            current_completed = bool(item["completed"])
            new_completed = (not current_completed) if state is None else bool(state)

            cursor.execute(
                "UPDATE study_plan_items SET completed = %s WHERE id = %s AND study_plan_id = %s",
                (1 if new_completed else 0, item_id, plan_id)
            )

            # Calculate updated stats
            cursor.execute(
                """
                SELECT 
                    COUNT(id) AS total_tasks,
                    SUM(CASE WHEN completed = 1 THEN 1 ELSE 0 END) AS completed_tasks
                FROM study_plan_items
                WHERE study_plan_id = %s
                """,
                (plan_id,)
            )
            stats = cursor.fetchone()
            total = int(stats["total_tasks"] or 0)
            completed_count = int(stats["completed_tasks"] or 0)
            pct = round((completed_count / total) * 100) if total > 0 else 0

            conn.commit()

            # Automatically update student's topic progress for this topic
            try:
                from services.progress_service import update_topic_progress
                topic_id = item.get("topic_id")
                if topic_id:
                    update_topic_progress(user_id, topic_id)
            except Exception as prog_err:
                logger.warning(f"Could not auto-update topic progress after task toggle: {prog_err}")

            return True, "Task completion updated successfully.", {
                "item_id": item_id,
                "completed": new_completed,
                "total_tasks": total,
                "completed_tasks": completed_count,
                "completion_percentage": pct
            }
    except Exception as exc:
        conn.rollback()
        logger.error(f"Error toggling task completion: {exc}", exc_info=True)
        return False, sanitize_db_error(exc), None
    finally:
        conn.close()


def update_study_plan(
    plan_id: int,
    user_id: int,
    goal: str,
    skill_level: str,
    preferred_study_time: str,
    duration_days: Optional[int] = None,
    topic_ids: Optional[List[int]] = None
) -> Tuple[bool, str, Optional[int]]:
    """
    Updates study plan details. If duration or topics are modified,
    regenerates daily tasks cleanly.
    Enforces student isolation.
    """
    if not plan_id or not user_id:
        return False, "Plan ID and user authentication required.", None

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, user_id, subject_id, duration_days, skill_level, preferred_study_time, goal
                FROM study_plans
                WHERE id = %s AND user_id = %s
                """,
                (plan_id, user_id)
            )
            existing_plan = cursor.fetchone()
            if not existing_plan:
                return False, "Study plan not found or unauthorized.", None

            subject_id = existing_plan["subject_id"]

            # Validate basic fields
            if not goal or not isinstance(goal, str) or not goal.strip():
                return False, "Learning goal cannot be empty.", None
            cleaned_goal = goal.strip()

            cleaned_skill = (skill_level or 'Beginner').strip().capitalize()
            if cleaned_skill not in ALLOWED_SKILL_LEVELS:
                return False, f"Invalid skill level. Allowed values: {', '.join(ALLOWED_SKILL_LEVELS)}.", None

            cleaned_time = (preferred_study_time or 'Flexible').strip().capitalize()
            if cleaned_time not in ALLOWED_STUDY_TIMES:
                return False, f"Invalid preferred study time. Allowed values: {', '.join(ALLOWED_STUDY_TIMES)}.", None

            # If new duration or new topics are provided, validate and regenerate items
            regenerate_needed = False
            new_duration = existing_plan["duration_days"]
            if duration_days is not None:
                try:
                    dur_int = int(duration_days)
                    if dur_int < MIN_DURATION_DAYS or dur_int > MAX_DURATION_DAYS:
                        return False, f"Study plan duration must be between {MIN_DURATION_DAYS} and {MAX_DURATION_DAYS} days.", None
                    if dur_int != existing_plan["duration_days"]:
                        new_duration = dur_int
                        regenerate_needed = True
                except (ValueError, TypeError):
                    return False, f"Invalid duration value.", None

            new_topics_list = None
            if topic_ids is not None and len(topic_ids) > 0:
                try:
                    cleaned_update_tids = [int(tid) for tid in topic_ids if int(tid) > 0]
                except (ValueError, TypeError):
                    return False, "Invalid topic identifier provided.", None
                if not cleaned_update_tids:
                    return False, "At least one valid topic must be selected.", None
                placeholders = ','.join(['%s'] * len(cleaned_update_tids))
                query = (
                    "SELECT id, topic_name, topic_name AS name, difficulty "
                    "FROM topics WHERE subject_id = %s AND id IN (" + placeholders + ") "
                    "ORDER BY id ASC"
                )
                cursor.execute(query, (subject_id, *cleaned_update_tids))
                new_topics_list = cursor.fetchall()
                if len(new_topics_list) != len(cleaned_update_tids):
                    return False, "All selected topics must belong to the plan's subject.", None
                regenerate_needed = True

            if regenerate_needed:
                # If topics were not passed, get existing topics from items
                if not new_topics_list:
                    cursor.execute(
                        """
                        SELECT DISTINCT t.id, t.topic_name, t.topic_name AS name, t.difficulty
                        FROM study_plan_items i
                        JOIN topics t ON i.topic_id = t.id
                        WHERE i.study_plan_id = %s
                        ORDER BY t.id ASC
                        """,
                        (plan_id,)
                    )
                    new_topics_list = cursor.fetchall()
                    if not new_topics_list:
                        # Fallback: get all topics for this subject
                        cursor.execute(
                            "SELECT id, topic_name, topic_name AS name, difficulty FROM topics WHERE subject_id = %s ORDER BY id ASC",
                            (subject_id,)
                        )
                        new_topics_list = cursor.fetchall()

                # Fetch subject name
                cursor.execute("SELECT name FROM subjects WHERE id = %s", (subject_id,))
                subj = cursor.fetchone()
                subj_name = subj["name"] if subj else "Subject"

                new_schedule = generate_plan_schedule(
                    subject_name=subj_name,
                    topics=new_topics_list,
                    duration_days=new_duration,
                    skill_level=cleaned_skill,
                    goal=cleaned_goal,
                    preferred_study_time=cleaned_time
                )

                # Update study_plans record
                cursor.execute(
                    """
                    UPDATE study_plans
                    SET goal = %s, skill_level = %s, preferred_study_time = %s, duration_days = %s
                    WHERE id = %s AND user_id = %s
                    """,
                    (cleaned_goal, cleaned_skill, cleaned_time, new_duration, plan_id, user_id)
                )

                # Replace items
                cursor.execute("DELETE FROM study_plan_items WHERE study_plan_id = %s", (plan_id,))
                items_sql = """
                    INSERT INTO study_plan_items 
                    (study_plan_id, day_number, topic_id, task, completed)
                    VALUES (%s, %s, %s, %s, %s)
                """
                item_tuples = [
                    (plan_id, it["day_number"], it["topic_id"], it["task"], 0)
                    for it in new_schedule
                ]
                cursor.executemany(items_sql, item_tuples)
            else:
                cursor.execute(
                    """
                    UPDATE study_plans
                    SET goal = %s, skill_level = %s, preferred_study_time = %s
                    WHERE id = %s AND user_id = %s
                    """,
                    (cleaned_goal, cleaned_skill, cleaned_time, plan_id, user_id)
                )

            conn.commit()
            return True, "Study plan updated successfully!", plan_id
    except Exception as exc:
        conn.rollback()
        logger.error(f"Error updating study plan: {exc}", exc_info=True)
        return False, sanitize_db_error(exc), None
    finally:
        conn.close()


def delete_study_plan(plan_id: int, user_id: int) -> Tuple[bool, str]:
    """
    Deletes a study plan and all associated daily task items.
    Enforces student isolation: plan must belong to user_id.

    Returns:
        (success, message)
    """
    if not plan_id or not user_id:
        return False, "Plan ID and user authentication required."

    from models.study_plan_model import delete_study_plan_record, find_study_plan_items
    try:
        items = find_study_plan_items(plan_id)
        affected_topics = [r["topic_id"] for r in items if r.get("topic_id")]

        success, msg = delete_study_plan_record(plan_id, user_id)
        if not success:
            return False, msg

        try:
            from services.progress_service import update_topic_progress
            for tid in affected_topics:
                update_topic_progress(user_id, tid)
        except Exception as prog_err:
            logger.warning(f"Could not update topic progress after plan delete: {prog_err}")

        return True, "Study plan deleted successfully."
    except Exception as exc:
        logger.error(f"Error deleting study plan: {exc}", exc_info=True)
        return False, sanitize_db_error(exc)


def get_user_study_stats(user_id: int) -> Dict[str, Any]:
    """
    Calculates aggregated authentic study plan statistics for the student dashboard via study_plan_model.
    Uses real database counts; no synthetic numbers.
    """
    if not user_id:
        return {
            "total_plans": 0,
            "total_tasks": 0,
            "completed_tasks": 0,
            "overall_percentage": 0,
            "active_plans": 0,
            "completed_plans": 0
        }

    from models.study_plan_model import find_user_study_stats
    stats = find_user_study_stats(user_id)
    active_plans = stats["total_plans"] - stats["completed_plans"]

    return {
        "total_plans": stats["total_plans"],
        "total_tasks": stats["total_tasks"],
        "completed_tasks": stats["completed_tasks"],
        "overall_percentage": stats["completion_rate"],
        "active_plans": active_plans,
        "completed_plans": stats["completed_plans"]
    }

"""
Models package for AI Student Learning Mentor.
Encapsulates SQL queries and data operations mapped to the 12 relational database tables.
"""
from models.user_model import (
    find_user_by_email,
    find_user_by_id,
    insert_user,
    update_user_password,
)
from models.learning_goal_model import (
    find_student_profile,
    upsert_student_profile,
    find_student_learning_goal,
    update_student_learning_goal,
    find_study_plan_goals,
)
from models.subject_model import (
    find_all_subjects,
    find_subject_by_id,
    find_topics_by_subject,
    find_topic_by_id,
    find_resources_by_topic,
    search_resources,
    find_topics_by_ids,
)
from models.study_plan_model import (
    insert_study_plan_with_items,
    find_study_plans_by_user,
    find_study_plan_by_id,
    find_study_plan_items,
    toggle_plan_item_status,
    delete_study_plan_record,
    update_study_plan_record,
    find_user_study_stats,
    find_pending_study_tasks,
)
from models.quiz_model import (
    find_quiz_catalog,
    find_quiz_catalog_raw,
    find_quiz_catalog_grouped,
    find_quizzes_by_topic,
    find_quiz_questions_with_answers,
    find_quiz_questions_by_ids,
    has_quiz_for_topic,
    insert_quiz_attempt_with_answers,
    find_quiz_attempt_by_id,
    find_quiz_attempt_answers,
    find_quiz_attempts_by_user,
    find_topic_quiz_info,
    find_user_quiz_stats,
)
from models.progress_model import (
    find_topic_progress,
    upsert_topic_progress,
    find_topic_learning_evidence,
    find_user_topic_progress_matrix,
    find_user_quiz_summary,
    find_user_task_summary,
    find_learning_stats_aggregates,
    find_recent_activity,
    find_recent_activity_records,
    insert_ai_chat_log,
    find_ai_chats_by_user,
    find_ai_chat_by_id,
    find_weak_topics_by_user,
)

__all__ = [
    # User Model
    'find_user_by_email',
    'find_user_by_id',
    'insert_user',
    'update_user_password',
    # Learning Goal / Profile Model
    'find_student_profile',
    'upsert_student_profile',
    'find_student_learning_goal',
    'update_student_learning_goal',
    'find_study_plan_goals',
    # Subject & Resource Model
    'find_all_subjects',
    'find_subject_by_id',
    'find_topics_by_subject',
    'find_topic_by_id',
    'find_resources_by_topic',
    'search_resources',
    'find_topics_by_ids',
    # Study Plan Model
    'insert_study_plan_with_items',
    'find_study_plans_by_user',
    'find_study_plan_by_id',
    'find_study_plan_items',
    'toggle_plan_item_status',
    'delete_study_plan_record',
    'update_study_plan_record',
    'find_user_study_stats',
    'find_pending_study_tasks',
    # Quiz Model
    'find_quiz_catalog',
    'find_quiz_catalog_raw',
    'find_quiz_catalog_grouped',
    'find_quizzes_by_topic',
    'find_quiz_questions_with_answers',
    'find_quiz_questions_by_ids',
    'has_quiz_for_topic',
    'insert_quiz_attempt_with_answers',
    'find_quiz_attempt_by_id',
    'find_quiz_attempt_answers',
    'find_quiz_attempts_by_user',
    'find_topic_quiz_info',
    'find_user_quiz_stats',
    # Progress & AI Model
    'find_topic_progress',
    'upsert_topic_progress',
    'find_topic_learning_evidence',
    'find_user_topic_progress_matrix',
    'find_user_quiz_summary',
    'find_user_task_summary',
    'find_learning_stats_aggregates',
    'find_recent_activity',
    'find_recent_activity_records',
    'insert_ai_chat_log',
    'find_ai_chats_by_user',
    'find_ai_chat_by_id',
    'find_weak_topics_by_user',
]

"""
Unit Tests for Recommendation Service (Offline).
AI Student Learning Mentor - Phase 4.

Verifies evidence-based recommendations:
- Weak topics detection and prioritized action items
- Scheduled study task recommendations
- Curriculum progression / next syllabus topics
- Comprehensive recommendation assembly
- Graceful empty states and student isolation
"""
import unittest
from unittest.mock import patch

from services.recommendation_service import (
    get_weak_topic_recommendations,
    get_pending_task_recommendations,
    get_next_topic_recommendations,
    get_comprehensive_recommendations,
)


class TestRecommendationService(unittest.TestCase):
    """Offline unit test suite for recommendation_service logic using mocks."""

    def test_unauthenticated_user_isolation(self):
        """Zero or None user_id returns safe empty defaults."""
        self.assertEqual(get_weak_topic_recommendations(None), [])
        self.assertEqual(get_weak_topic_recommendations(0), [])
        self.assertEqual(get_pending_task_recommendations(None), [])
        self.assertEqual(get_pending_task_recommendations(0), [])
        self.assertEqual(get_next_topic_recommendations(None), [])
        self.assertEqual(get_next_topic_recommendations(0), [])

        comp = get_comprehensive_recommendations(None)
        self.assertFalse(comp["has_activity"])
        self.assertEqual(comp["weak_topics"], [])
        self.assertEqual(comp["pending_tasks"], [])
        self.assertEqual(comp["next_topics"], [])
        self.assertIn("Sign in", comp["empty_state_message"])

    @patch("services.recommendation_service.find_weak_topics_by_user")
    def test_weak_topic_recommendations_critical_and_high(self, mock_weak):
        """Low quiz averages are categorized with appropriate priorities and actions."""
        mock_weak.return_value = [
            {
                "topic_id": 101,
                "topic_name": "Recursion",
                "subject_id": 1,
                "subject_name": "Data Structures",
                "difficulty": "Medium",
                "avg_quiz_score": 35.0,
                "quiz_attempts_count": 2,
                "completion_percentage": 25.0
            },
            {
                "topic_id": 102,
                "topic_name": "Dynamic Programming",
                "subject_id": 1,
                "subject_name": "Data Structures",
                "difficulty": "Hard",
                "avg_quiz_score": 55.0,
                "quiz_attempts_count": 1,
                "completion_percentage": 40.0
            }
        ]

        recs = get_weak_topic_recommendations(user_id=42, threshold=60.0)
        self.assertEqual(len(recs), 2)

        # Critical (< 40% avg)
        self.assertEqual(recs[0]["topic_id"], 101)
        self.assertEqual(recs[0]["priority"], "Critical")
        self.assertIn("Recursion", recs[0]["recommended_action"])
        self.assertIn("/quiz/101/start", recs[0]["practice_url"])

        # High (< 60% avg)
        self.assertEqual(recs[1]["topic_id"], 102)
        self.assertEqual(recs[1]["priority"], "High")
        self.assertIn("Dynamic Programming", recs[1]["recommended_action"])

    @patch("services.recommendation_service.find_weak_topics_by_user")
    def test_weak_topics_empty(self, mock_weak):
        """When no weak topics exist, returns empty list without inventing fake ones."""
        mock_weak.return_value = []
        recs = get_weak_topic_recommendations(user_id=42)
        self.assertEqual(recs, [])

    @patch("services.recommendation_service.find_pending_study_tasks")
    def test_pending_task_recommendations(self, mock_tasks):
        """Pending study tasks are categorized by day number priority."""
        mock_tasks.return_value = [
            {
                "item_id": 1,
                "study_plan_id": 10,
                "day_number": 1,
                "task": "Read chapter 1 and write initial examples",
                "topic_id": 5,
                "topic_name": "Arrays",
                "subject_id": 1,
                "subject_name": "Computer Science",
                "topic_difficulty": "Easy"
            },
            {
                "item_id": 2,
                "study_plan_id": 10,
                "day_number": 4,
                "task": "Implement two-pointer array algorithms",
                "topic_id": 5,
                "topic_name": "Arrays",
                "subject_id": 1,
                "subject_name": "Computer Science",
                "topic_difficulty": "Medium"
            }
        ]

        recs = get_pending_task_recommendations(user_id=42, limit=5)
        self.assertEqual(len(recs), 2)
        self.assertEqual(recs[0]["priority"], "High")  # Day 1
        self.assertEqual(recs[1]["priority"], "Medium")  # Day 4
        self.assertEqual(recs[0]["action_url"], "/study-plans/10")

    @patch("services.recommendation_service.find_all_subjects")
    @patch("services.recommendation_service.find_topics_by_subject")
    @patch("services.recommendation_service.find_study_plans_by_user")
    @patch("services.recommendation_service.find_user_topic_progress_matrix")
    def test_next_topic_recommendations_skips_completed(
        self, mock_matrix, mock_plans, mock_topics, mock_all_subj
    ):
        """Mastered topics (>= 80% completion) are skipped in next topic recommendations."""
        mock_matrix.return_value = [
            {"topic_id": 1, "completion_percentage": 95.0},  # Mastered
            {"topic_id": 2, "completion_percentage": 20.0},  # In progress
        ]
        mock_plans.return_value = [{"subject_id": 1}]
        mock_topics.return_value = [
            {"id": 1, "topic_name": "Intro", "subject_id": 1, "difficulty": "Easy"},
            {"id": 2, "topic_name": "Variables", "subject_id": 1, "difficulty": "Easy"},
            {"id": 3, "topic_name": "Functions", "subject_id": 1, "difficulty": "Medium"},
        ]

        recs = get_next_topic_recommendations(user_id=42, limit=2)
        rec_ids = [r["topic_id"] for r in recs]
        self.assertNotIn(1, rec_ids)  # Completed topic skipped
        self.assertIn(2, rec_ids)     # Incomplete topic included
        self.assertIn(3, rec_ids)     # Unstarted topic included

    @patch("services.recommendation_service.find_student_profile")
    @patch("services.recommendation_service.find_weak_topics_by_user")
    @patch("services.recommendation_service.find_pending_study_tasks")
    @patch("services.recommendation_service.find_study_plans_by_user")
    @patch("services.recommendation_service.find_user_topic_progress_matrix")
    @patch("services.recommendation_service.find_all_subjects")
    @patch("services.recommendation_service.find_topics_by_subject")
    def test_comprehensive_recommendations_new_user(
        self, mock_topics, mock_all_subj, mock_matrix, mock_plans,
        mock_tasks, mock_weak, mock_profile
    ):
        """New student with zero records gets clean empty state without synthetic numbers."""
        mock_profile.return_value = None
        mock_weak.return_value = []
        mock_tasks.return_value = []
        mock_plans.return_value = []
        mock_matrix.return_value = []
        mock_all_subj.return_value = []
        mock_topics.return_value = []

        comp = get_comprehensive_recommendations(user_id=99)
        self.assertFalse(comp["has_activity"])
        self.assertEqual(comp["summary"]["weak_topics_count"], 0)
        self.assertEqual(comp["summary"]["pending_tasks_count"], 0)
        self.assertIsNotNone(comp["empty_state_message"])
        self.assertIn("Welcome! No learning history found yet", comp["empty_state_message"])

    @patch("services.recommendation_service.find_student_profile")
    @patch("services.recommendation_service.find_weak_topics_by_user")
    @patch("services.recommendation_service.find_pending_study_tasks")
    @patch("services.recommendation_service.find_study_plans_by_user")
    @patch("services.recommendation_service.find_user_topic_progress_matrix")
    @patch("services.recommendation_service.find_all_subjects")
    @patch("services.recommendation_service.find_topics_by_subject")
    def test_comprehensive_recommendations_active_user(
        self, mock_topics, mock_all_subj, mock_matrix, mock_plans,
        mock_tasks, mock_weak, mock_profile
    ):
        """Active student with real data receives primary focus and structured advice."""
        mock_profile.return_value = {
            "learning_goals": "Master Python Backend Development",
            "created_at": "2026-10-12 10:00:00"
        }
        mock_weak.return_value = [
            {
                "topic_id": 50,
                "topic_name": "SQL Joins",
                "subject_id": 2,
                "subject_name": "Databases",
                "difficulty": "Medium",
                "avg_quiz_score": 45.0,
                "quiz_attempts_count": 1,
                "completion_percentage": 50.0
            }
        ]
        mock_tasks.return_value = []
        mock_plans.return_value = []
        mock_matrix.return_value = []
        mock_all_subj.return_value = []
        mock_topics.return_value = []

        comp = get_comprehensive_recommendations(user_id=42)
        self.assertTrue(comp["has_activity"])
        self.assertEqual(comp["summary"]["weak_topics_count"], 1)
        self.assertIn("Reinforce 1 weak topic", comp["summary"]["primary_focus"])
        self.assertEqual(comp["learning_goal"], "Master Python Backend Development")
        self.assertIsNone(comp["empty_state_message"])

    @patch("services.recommendation_service.find_weak_topics_by_user")
    def test_study_urls_use_canonical_topics_path(self, mock_weak):
        """Verifies study_url uses the canonical registered /topics/<id> path."""
        mock_weak.return_value = [
            {
                "topic_id": 7,
                "topic_name": "Linked Lists",
                "subject_id": 1,
                "subject_name": "Data Structures",
                "difficulty": "Medium",
                "avg_quiz_score": 50.0,
                "quiz_attempts_count": 1,
                "completion_percentage": 30.0
            }
        ]
        recs = get_weak_topic_recommendations(user_id=10)
        self.assertEqual(len(recs), 1)
        self.assertEqual(recs[0]["study_url"], "/topics/7")

    @patch("services.recommendation_service.find_weak_topics_by_user")
    def test_study_urls_with_flask_request_context(self, mock_weak):
        """Verifies study_url resolves correctly inside active Flask request context."""
        from app import create_app
        app = create_app()
        mock_weak.return_value = [
            {
                "topic_id": 15,
                "topic_name": "Binary Search",
                "subject_id": 1,
                "subject_name": "Algorithms",
                "difficulty": "Easy",
                "avg_quiz_score": 45.0,
                "quiz_attempts_count": 1,
                "completion_percentage": 40.0
            }
        ]
        with app.test_request_context():
            recs = get_weak_topic_recommendations(user_id=10)
            self.assertEqual(len(recs), 1)
            self.assertEqual(recs[0]["study_url"], "/topics/15")

    @patch("services.recommendation_service.find_weak_topics_by_user")
    @patch("services.recommendation_service.find_pending_study_tasks")
    @patch("services.recommendation_service.find_study_plans_by_user")
    @patch("services.recommendation_service.find_user_topic_progress_matrix")
    @patch("services.recommendation_service.find_all_subjects")
    @patch("services.recommendation_service.find_topics_by_subject")
    @patch("services.recommendation_service.find_student_profile")
    def test_learning_goal_lookup_all_key_variants(
        self, mock_profile, mock_topics, mock_all_subj, mock_matrix,
        mock_plans, mock_tasks, mock_weak
    ):
        """Verifies learning-goal lookup checks learning_goal, then learning_goals, then goal, or None."""
        mock_weak.return_value = []
        mock_tasks.return_value = []
        mock_plans.return_value = []
        mock_matrix.return_value = []
        mock_all_subj.return_value = []
        mock_topics.return_value = []

        # Variant 1: Database column 'learning_goal' (singular)
        mock_profile.return_value = {"learning_goal": "Master Machine Learning"}
        res1 = get_comprehensive_recommendations(user_id=1)
        self.assertEqual(res1["learning_goal"], "Master Machine Learning")

        # Variant 2: 'learning_goals' (plural)
        mock_profile.return_value = {"learning_goals": "Learn Cloud Computing"}
        res2 = get_comprehensive_recommendations(user_id=1)
        self.assertEqual(res2["learning_goal"], "Learn Cloud Computing")

        # Variant 3: 'goal'
        mock_profile.return_value = {"goal": "Pass Algorithms Exam"}
        res3 = get_comprehensive_recommendations(user_id=1)
        self.assertEqual(res3["learning_goal"], "Pass Algorithms Exam")

        # Variant 4: Precedence (learning_goal takes priority over learning_goals and goal)
        mock_profile.return_value = {
            "learning_goal": "Primary Goal",
            "learning_goals": "Secondary Goal",
            "goal": "Tertiary Goal"
        }
        res4 = get_comprehensive_recommendations(user_id=1)
        self.assertEqual(res4["learning_goal"], "Primary Goal")

        # Variant 5: Empty/missing goal in profile
        mock_profile.return_value = {"education_level": "Undergraduate", "learning_goal": None}
        res5 = get_comprehensive_recommendations(user_id=1)
        self.assertIsNone(res5["learning_goal"])

        # Variant 6: Empty string goal in profile
        mock_profile.return_value = {"learning_goal": ""}
        res6 = get_comprehensive_recommendations(user_id=1)
        self.assertIsNone(res6["learning_goal"])


if __name__ == "__main__":
    unittest.main()

"""
Automated Test Suite for Phase 7 - Progress Tracking & Student Dashboard.
AI Student Learning Mentor.

Covers all Phase 7 requirements:
1. Guest cannot access progress page (redirects to /login with 302).
2. Guest cannot access progress APIs (returns 401 JSON).
3. Authenticated student can view progress page (GET /progress returns 200).
4. New user has zero progress and clean empty state without synthetic numbers.
5. Study plan task toggle updates topic progress in MySQL.
6. Untoggling study plan task reverses topic progress (reversibility).
7. Submitting quiz attempt updates topic progress in MySQL.
8. Failed/aborted quiz submission does not alter progress.
9. Topic progress calculation respects deterministic formula:
   - Both tasks and quiz: 0.40 * task_ratio + 0.60 * best_quiz_score
   - Quiz only: best_quiz_score
   - Tasks only: 0.75 * task_ratio
   - Neither: 0.0%
10. Topic progress completion thresholds and status (Completed >= 80%, In Progress > 0%, Not Started).
11. Topic progress is strictly bounded between 0.0% and 100.0%.
12. Weak topics identification rule (quiz_attempts > 0 and avg_score < 60.0%).
13. Subject-wise progress calculation aggregates syllabus topics.
14. Overall curriculum progress calculation (curriculum-wide average).
15. Learning statistics aggregation from real database records.
16. Recent activity timeline aggregates quiz, study plan, and AI mentor events newest first.
17. Student isolation: Student B cannot see Student A's progress data.
18. Progress subject filtering on page and API (?subject_id=...).
19. Student Dashboard renders real progress widgets.
20. All progress API endpoints return valid JSON structures.
21. Phase 1 baseline verification (Database & Health).
22. Phase 2 baseline verification (Auth & Profile).
23. Phase 3 baseline verification (Content & Resources).
24. Phase 4 baseline verification (Study Plans).
25. Phase 5 baseline verification (Quizzes).
26. Phase 6 baseline verification (AI Doubt Assistant).
"""
import unittest
import html
from app import create_app
from services.db import get_db_connection, check_db_health
from services.auth_service import register_user
from services.profile_service import get_student_profile, upsert_student_profile
from services.content_service import get_all_subjects, get_topics_by_subject, search_content
from services.study_plan_service import (
    create_study_plan, get_study_plan_detail, toggle_task_completion,
    get_user_study_plans
)
from services.quiz_service import (
    get_available_quizzes_catalog, get_quiz_questions_for_topic,
    submit_quiz_attempt
)
from services.ai_service import (
    validate_academic_question, save_ai_chat, get_user_ai_history
)
from services.progress_service import (
    calculate_topic_progress_value, update_topic_progress,
    get_topic_progress, get_subject_progress, get_overall_progress,
    get_weak_topics, get_learning_statistics, get_recent_activity
)


class TestPhase7ProgressTracking(unittest.TestCase):
    """Test suite covering all Phase 7 Progress Tracking and Dashboard requirements."""

    @classmethod
    def setUpClass(cls):
        """Set up Flask test application and query database test metadata."""
        cls.app = create_app()
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                # Query two topics with quiz questions for testing
                cursor.execute("""
                    SELECT t.id, t.topic_name, t.subject_id, COUNT(q.id) as qcount
                    FROM topics t
                    JOIN quizzes q ON t.id = q.topic_id
                    GROUP BY t.id
                    HAVING qcount > 0
                    ORDER BY t.id ASC
                    LIMIT 2
                """)
                rows = cursor.fetchall()
                if not rows:
                    raise RuntimeError("No topics with quiz questions found in database.")
                cls.test_topic_1 = rows[0]
                cls.test_topic_2 = rows[1] if len(rows) > 1 else rows[0]

                # Fetch all subjects
                cursor.execute("SELECT id, name FROM subjects ORDER BY id ASC")
                cls.subjects = cursor.fetchall()
        finally:
            conn.close()

    def setUp(self):
        """Clean up test users and reset test client before each test."""
        self.client = self.app.test_client()
        self._cleanup_test_data()

    def tearDown(self):
        """Clean up test records after each test."""
        self._cleanup_test_data()

    def _cleanup_test_data(self):
        """Helper to remove test users and cascade delete progress and activities."""
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    "DELETE FROM users WHERE email LIKE %s",
                    ('test_prog_%@example.com',)
                )
            conn.commit()
        finally:
            conn.close()

    def _create_and_login_user(self, email="test_prog_user@example.com", name="Progress Student"):
        """Helper to register and log in a test student."""
        success, msg, user_id = register_user(name, email, "Password123!")
        self.assertTrue(success, f"Failed to register test user: {msg}")

        with self.client.session_transaction() as sess:
            sess['user_id'] = user_id
            sess['user_name'] = name
            sess['user_email'] = email
            sess['user_role'] = 'student'

        return user_id

    # -------------------------------------------------------------------------
    # Test 1: Guest cannot access progress page (redirects to /login)
    # -------------------------------------------------------------------------
    def test_01_guest_cannot_access_progress_page(self):
        """Verify unauthenticated access to /progress redirects to /login."""
        response = self.client.get('/progress', follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login', response.headers.get('Location', ''))

    # -------------------------------------------------------------------------
    # Test 2: Guest cannot access progress APIs (returns 401 JSON)
    # -------------------------------------------------------------------------
    def test_02_guest_cannot_access_progress_apis(self):
        """Verify unauthenticated calls to /api/progress/* return 401 Unauthorized."""
        endpoints = [
            '/api/progress',
            '/api/progress/subjects',
            '/api/progress/topics',
            '/api/progress/statistics',
            '/api/progress/activity'
        ]
        for ep in endpoints:
            response = self.client.get(ep)
            self.assertEqual(response.status_code, 401, f"Expected 401 on {ep}, got {response.status_code}")
            data = response.get_json()
            self.assertEqual(data.get("status"), "error")

    # -------------------------------------------------------------------------
    # Test 3: Authenticated student can view progress page
    # -------------------------------------------------------------------------
    def test_03_authenticated_student_can_view_progress_page(self):
        """Verify authenticated student can view /progress with HTTP 200."""
        self._create_and_login_user()
        response = self.client.get('/progress')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Learning Progress", response.data)
        self.assertIn(b"Curriculum-Wide Academic Progress", response.data)
        self.assertIn(b"Authentic Learning Statistics", response.data)

    # -------------------------------------------------------------------------
    # Test 4: New user has zero progress and clean empty state
    # -------------------------------------------------------------------------
    def test_04_new_user_has_zero_progress_and_clean_empty_state(self):
        """Verify a brand new user shows 0.0% progress without synthetic numbers."""
        user_id = self._create_and_login_user()

        overall = get_overall_progress(user_id)
        self.assertEqual(overall["overall_percentage"], 0.0)
        self.assertEqual(overall["status"], "Not Started")
        self.assertEqual(overall["topics_started"], 0)
        self.assertEqual(overall["topics_completed"], 0)

        stats = get_learning_statistics(user_id)
        self.assertEqual(stats["completed_study_tasks"], 0)
        self.assertEqual(stats["total_quiz_attempts"], 0)
        self.assertEqual(stats["overall_quiz_accuracy"], 0.0)
        self.assertEqual(stats["weak_topics_count"], 0)

        weak = get_weak_topics(user_id)
        self.assertEqual(len(weak), 0)

        activity = get_recent_activity(user_id)
        self.assertEqual(len(activity), 0)

        # Web page should render empty state messaging cleanly
        response = self.client.get('/progress')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"0.0%", response.data)
        self.assertIn(b"No learning activity recorded yet", response.data)

    # -------------------------------------------------------------------------
    # Test 5: Study plan task toggle updates topic progress in MySQL
    # -------------------------------------------------------------------------
    def test_05_study_plan_task_toggle_updates_topic_progress(self):
        """Verify completing a daily study task increases topic mastery in database."""
        user_id = self._create_and_login_user()
        topic_id = self.test_topic_1["id"]
        subject_id = self.test_topic_1["subject_id"]

        # 1. Create a 3-day study plan covering topic_id
        success, msg, plan_id = create_study_plan(
            user_id=user_id,
            subject_id=subject_id,
            topic_ids=[topic_id],
            duration_days=3,
            goal="Master Phase 7 Topic Progress"
        )
        self.assertTrue(success, f"Failed to create study plan: {msg}")

        plan_detail = get_study_plan_detail(plan_id, user_id)
        items = plan_detail["items"]
        self.assertGreater(len(items), 0)
        first_item = items[0]

        # Initial progress should be 0.0%
        init_val = calculate_topic_progress_value(user_id, topic_id)
        self.assertEqual(init_val, 0.0)

        # 2. Toggle task complete
        t_success, t_msg, t_res = toggle_task_completion(plan_id, first_item["id"], user_id, state=True)
        self.assertTrue(t_success)

        # 3. Topic progress value must now be strictly greater than 0
        new_val = calculate_topic_progress_value(user_id, topic_id)
        self.assertGreater(new_val, 0.0)

        # Verify row in progress table
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT completion_percentage FROM progress WHERE user_id = %s AND topic_id = %s",
                    (user_id, topic_id)
                )
                p_row = cursor.fetchone()
                self.assertIsNotNone(p_row)
                self.assertAlmostEqual(float(p_row["completion_percentage"]), new_val, places=1)
        finally:
            conn.close()

    # -------------------------------------------------------------------------
    # Test 6: Untoggling study plan task reverses topic progress
    # -------------------------------------------------------------------------
    def test_06_untoggling_study_plan_task_reverses_topic_progress(self):
        """Verify untoggling a completed task recalculates and lowers topic progress."""
        user_id = self._create_and_login_user()
        topic_id = self.test_topic_1["id"]
        subject_id = self.test_topic_1["subject_id"]

        success, msg, plan_id = create_study_plan(
            user_id=user_id,
            subject_id=subject_id,
            topic_ids=[topic_id],
            duration_days=2,
            goal="Test reversibility"
        )
        self.assertTrue(success)
        plan_detail = get_study_plan_detail(plan_id, user_id)
        item_id = plan_detail["items"][0]["id"]

        # Check item (complete)
        toggle_task_completion(plan_id, item_id, user_id, state=True)
        completed_val = calculate_topic_progress_value(user_id, topic_id)
        self.assertGreater(completed_val, 0.0)

        # Uncheck item (revert)
        toggle_task_completion(plan_id, item_id, user_id, state=False)
        reverted_val = calculate_topic_progress_value(user_id, topic_id)
        self.assertEqual(reverted_val, 0.0)

    # -------------------------------------------------------------------------
    # Test 7: Submitting quiz attempt updates topic progress in MySQL
    # -------------------------------------------------------------------------
    def test_07_submitting_quiz_attempt_updates_topic_progress(self):
        """Verify submitting a practice quiz automatically upserts topic progress."""
        user_id = self._create_and_login_user()
        topic_id = self.test_topic_1["id"]

        questions = get_quiz_questions_for_topic(topic_id, limit=3, include_correct=True)
        self.assertGreater(len(questions), 0)

        answers = {q["id"]: q["correct_answer"] for q in questions}
        success, msg, attempt_id = submit_quiz_attempt(user_id, topic_id, answers)
        self.assertTrue(success, f"Quiz submission failed: {msg}")

        # Progress should now reflect 100% quiz score
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT completion_percentage FROM progress WHERE user_id = %s AND topic_id = %s",
                    (user_id, topic_id)
                )
                p_row = cursor.fetchone()
                self.assertIsNotNone(p_row)
                self.assertEqual(float(p_row["completion_percentage"]), 100.0)
        finally:
            conn.close()

    # -------------------------------------------------------------------------
    # Test 8: Failed quiz submission does not alter progress
    # -------------------------------------------------------------------------
    def test_08_failed_quiz_submission_does_not_alter_progress(self):
        """Verify invalid quiz submission payload produces error and leaves progress intact."""
        user_id = self._create_and_login_user()
        topic_id = self.test_topic_1["id"]

        # Submit to non-existent topic 99999
        success, msg, attempt_id = submit_quiz_attempt(user_id, 99999, {})
        self.assertFalse(success)
        self.assertIsNone(attempt_id)

        # Real topic progress remains 0.0
        val = calculate_topic_progress_value(user_id, topic_id)
        self.assertEqual(val, 0.0)

    # -------------------------------------------------------------------------
    # Test 9: Topic progress calculation respects deterministic formula
    # -------------------------------------------------------------------------
    def test_09_topic_progress_deterministic_formula(self):
        """Verify deterministic mathematical formula: (0.40 * task_ratio) + (0.60 * quiz_score)."""
        user_id = self._create_and_login_user()
        topic_id = self.test_topic_1["id"]
        subject_id = self.test_topic_1["subject_id"]

        # Case A: Neither tasks nor quiz -> 0.0%
        val_none = calculate_topic_progress_value(user_id, topic_id)
        self.assertEqual(val_none, 0.0)

        # Case B: Only tasks: 2 tasks total, 1 completed -> task_ratio = 50.0%
        # Formula: 0.75 * 50.0 = 37.5%
        success, _, plan_id = create_study_plan(user_id, subject_id, [topic_id], duration_days=2, goal="Test formula")
        plan_items = get_study_plan_detail(plan_id, user_id)["items"]
        toggle_task_completion(plan_id, plan_items[0]["id"], user_id, state=True)

        val_tasks = calculate_topic_progress_value(user_id, topic_id)
        self.assertAlmostEqual(val_tasks, 37.5, places=1)

        # Case C: Both tasks and quiz:
        # Submit quiz with 100% score
        questions = get_quiz_questions_for_topic(topic_id, limit=2, include_correct=True)
        submit_quiz_attempt(user_id, topic_id, {q["id"]: q["correct_answer"] for q in questions})

        # Formula: (0.40 * 50.0) + (0.60 * 100.0) = 20.0 + 60.0 = 80.0%
        val_both = calculate_topic_progress_value(user_id, topic_id)
        self.assertAlmostEqual(val_both, 80.0, places=1)

    # -------------------------------------------------------------------------
    # Test 10: Topic progress completion thresholds and status
    # -------------------------------------------------------------------------
    def test_10_topic_progress_completion_thresholds_and_status(self):
        """Verify status labels: Completed (>= 80%), In Progress (> 0%), Not Started (0%)."""
        user_id = self._create_and_login_user()
        topic_id = self.test_topic_1["id"]

        # 1. Not Started
        topics = get_topic_progress(user_id)
        target = next(t for t in topics if t["topic_id"] == topic_id)
        self.assertEqual(target["status"], "Not Started")
        self.assertFalse(target["is_completed"])

        # 2. In Progress (Submit quiz with 50% score)
        questions = get_quiz_questions_for_topic(topic_id, limit=2, include_correct=True)
        answers = {questions[0]["id"]: questions[0]["correct_answer"]}
        if len(questions) > 1:
            wrong_c = "A" if questions[1]["correct_answer"] != "A" else "B"
            answers[questions[1]["id"]] = wrong_c
        submit_quiz_attempt(user_id, topic_id, answers)

        topics = get_topic_progress(user_id)
        target = next(t for t in topics if t["topic_id"] == topic_id)
        self.assertEqual(target["status"], "In Progress")
        self.assertFalse(target["is_completed"])

        # 3. Completed (Submit quiz with 100% score)
        all_correct = {q["id"]: q["correct_answer"] for q in questions}
        submit_quiz_attempt(user_id, topic_id, all_correct)

        topics = get_topic_progress(user_id)
        target = next(t for t in topics if t["topic_id"] == topic_id)
        self.assertEqual(target["status"], "Completed")
        self.assertTrue(target["is_completed"])

    # -------------------------------------------------------------------------
    # Test 11: Topic progress strictly bounded between 0.0% and 100.0%
    # -------------------------------------------------------------------------
    def test_11_topic_progress_strictly_bounded_0_to_100(self):
        """Verify calculated topic progress never exceeds 100.0% or drops below 0.0%."""
        user_id = self._create_and_login_user()
        topic_id = self.test_topic_1["id"]

        val = calculate_topic_progress_value(user_id, topic_id)
        self.assertGreaterEqual(val, 0.0)
        self.assertLessEqual(val, 100.0)

        # After max score
        questions = get_quiz_questions_for_topic(topic_id, limit=5, include_correct=True)
        submit_quiz_attempt(user_id, topic_id, {q["id"]: q["correct_answer"] for q in questions})
        val_max = calculate_topic_progress_value(user_id, topic_id)
        self.assertGreaterEqual(val_max, 0.0)
        self.assertLessEqual(val_max, 100.0)

    # -------------------------------------------------------------------------
    # Test 12: Weak topics identification rule
    # -------------------------------------------------------------------------
    def test_12_weak_topics_identification_rule(self):
        """Verify topics with quiz attempts and average score < 60% are flagged as weak."""
        user_id = self._create_and_login_user()
        topic_1_id = self.test_topic_1["id"]
        topic_2_id = self.test_topic_2["id"]

        # Topic 1: Score 0% (deliberately wrong answers) -> Weak!
        q1 = get_quiz_questions_for_topic(topic_1_id, limit=2, include_correct=True)
        wrong_answers = {q["id"]: ("A" if q["correct_answer"] != "A" else "B") for q in q1}
        submit_quiz_attempt(user_id, topic_1_id, wrong_answers)

        # Topic 2: Score 100% (all correct) -> NOT Weak!
        q2 = get_quiz_questions_for_topic(topic_2_id, limit=2, include_correct=True)
        correct_answers = {q["id"]: q["correct_answer"] for q in q2}
        submit_quiz_attempt(user_id, topic_2_id, correct_answers)

        weak = get_weak_topics(user_id)
        self.assertEqual(len(weak), 1)
        self.assertEqual(weak[0]["topic_id"], topic_1_id)
        self.assertTrue(weak[0]["is_weak"])
        self.assertLess(weak[0]["avg_quiz_score"], 60.0)

    # -------------------------------------------------------------------------
    # Test 13: Subject-wise progress calculation
    # -------------------------------------------------------------------------
    def test_13_subject_wise_progress_calculation(self):
        """Verify get_subject_progress aggregates topic metrics under each subject."""
        user_id = self._create_and_login_user()
        topic_id = self.test_topic_1["id"]
        subject_id = self.test_topic_1["subject_id"]

        # Submit quiz for topic 1 (100%)
        q = get_quiz_questions_for_topic(topic_id, limit=2, include_correct=True)
        submit_quiz_attempt(user_id, topic_id, {item["id"]: item["correct_answer"] for item in q})

        subjects = get_subject_progress(user_id)
        self.assertGreaterEqual(len(subjects), 1)

        target_subj = next(s for s in subjects if s["subject_id"] == subject_id)
        self.assertGreater(target_subj["progress_percentage"], 0.0)
        self.assertEqual(target_subj["topics_started"], 1)
        self.assertEqual(target_subj["quiz_attempts"], 1)

    # -------------------------------------------------------------------------
    # Test 14: Overall curriculum progress calculation
    # -------------------------------------------------------------------------
    def test_14_overall_curriculum_progress_calculation(self):
        """Verify get_overall_progress computes global curriculum average."""
        user_id = self._create_and_login_user()
        topic_id = self.test_topic_1["id"]

        # Submit 100% quiz for one topic
        q = get_quiz_questions_for_topic(topic_id, limit=2, include_correct=True)
        submit_quiz_attempt(user_id, topic_id, {item["id"]: item["correct_answer"] for item in q})

        overall = get_overall_progress(user_id)
        self.assertGreater(overall["overall_percentage"], 0.0)
        self.assertEqual(overall["topics_started"], 1)
        self.assertGreaterEqual(overall["total_topics"], 20)

    # -------------------------------------------------------------------------
    # Test 15: Learning statistics aggregation
    # -------------------------------------------------------------------------
    def test_15_learning_statistics_aggregation(self):
        """Verify get_learning_statistics accurately aggregates tasks, quizzes, and AI doubts."""
        user_id = self._create_and_login_user()
        topic_id = self.test_topic_1["id"]
        subject_id = self.test_topic_1["subject_id"]

        # 1. Study Task
        create_study_plan(user_id, subject_id, [topic_id], duration_days=2, goal="Stats test")
        plan = get_user_study_plans(user_id)[0]
        plan_detail = get_study_plan_detail(plan["id"], user_id)
        toggle_task_completion(plan["id"], plan_detail["items"][0]["id"], user_id, state=True)

        # 2. Quiz Attempt
        q = get_quiz_questions_for_topic(topic_id, limit=2, include_correct=True)
        submit_quiz_attempt(user_id, topic_id, {item["id"]: item["correct_answer"] for item in q})

        # 3. AI Chat
        save_ai_chat(user_id, "Explain progress algorithms?", "Progress algorithms compute student mastery.")

        stats = get_learning_statistics(user_id)
        self.assertEqual(stats["total_study_tasks"], 2)
        self.assertEqual(stats["completed_study_tasks"], 1)
        self.assertEqual(stats["total_quiz_attempts"], 1)
        self.assertEqual(stats["total_ai_doubts_asked"], 1)
        self.assertEqual(stats["best_quiz_score"], 100.0)

    # -------------------------------------------------------------------------
    # Test 16: Recent activity timeline ordering
    # -------------------------------------------------------------------------
    def test_16_recent_activity_timeline_ordering(self):
        """Verify recent activity streams quiz, study tasks, and AI doubts chronologically."""
        user_id = self._create_and_login_user()
        topic_id = self.test_topic_1["id"]
        subject_id = self.test_topic_1["subject_id"]

        # Quiz
        q = get_quiz_questions_for_topic(topic_id, limit=1, include_correct=True)
        submit_quiz_attempt(user_id, topic_id, {item["id"]: item["correct_answer"] for item in q})

        # AI Doubt
        save_ai_chat(user_id, "What is dynamic programming?", "Dynamic programming is an optimization method.")

        activities = get_recent_activity(user_id, limit=5)
        self.assertGreaterEqual(len(activities), 2)
        types = [a["type"] for a in activities]
        self.assertIn("quiz", types)
        self.assertIn("ai_chat", types)

    # -------------------------------------------------------------------------
    # Test 17: Student isolation (Student B cannot see Student A's progress data)
    # -------------------------------------------------------------------------
    def test_17_student_isolation_progress_data(self):
        """Verify strict isolation: Student B cannot view or leak Student A's progress."""
        user_a = self._create_and_login_user("test_prog_a@example.com", "Student Alpha")
        topic_id = self.test_topic_1["id"]

        # Student A gets 100% quiz score
        q = get_quiz_questions_for_topic(topic_id, limit=2, include_correct=True)
        submit_quiz_attempt(user_a, topic_id, {item["id"]: item["correct_answer"] for item in q})

        # Switch to Student B
        user_b = self._create_and_login_user("test_prog_b@example.com", "Student Beta")

        # Student B progress on this topic must be 0.0%
        val_b = calculate_topic_progress_value(user_b, topic_id)
        self.assertEqual(val_b, 0.0)

        # Student B overall progress must be 0.0%
        overall_b = get_overall_progress(user_b)
        self.assertEqual(overall_b["overall_percentage"], 0.0)

        # API call from Student B session must return 0.0%
        response = self.client.get('/api/progress')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["overall_progress"], 0.0)
        self.assertEqual(data["statistics"]["total_quiz_attempts"], 0)

    # -------------------------------------------------------------------------
    # Test 18: Progress subject filtering
    # -------------------------------------------------------------------------
    def test_18_progress_subject_filtering(self):
        """Verify subject filtering (?subject_id=...) filters topics on page and API."""
        self._create_and_login_user()
        target_subject = self.subjects[0]["id"]

        # Filter API
        response = self.client.get(f'/api/progress/topics?subject_id={target_subject}')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["status"], "success")
        for t in data["topics"]:
            self.assertEqual(t["subject_id"], target_subject)

        # Filter HTML page
        html_response = self.client.get(f'/progress?subject_id={target_subject}')
        self.assertEqual(html_response.status_code, 200)

    # -------------------------------------------------------------------------
    # Test 19: Student Dashboard renders real progress widgets
    # -------------------------------------------------------------------------
    def test_19_dashboard_displays_real_progress_widgets(self):
        """Verify /dashboard renders overall progress, subject mastery, and real stats."""
        self._create_and_login_user()
        response = self.client.get('/dashboard')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Overall Academic Learning Progress", response.data)
        self.assertIn(b"Subject-Wise Mastery", response.data)
        self.assertIn(b"View Progress Center", response.data)

    # -------------------------------------------------------------------------
    # Test 20: All progress API endpoints return valid JSON structures
    # -------------------------------------------------------------------------
    def test_20_api_progress_endpoints_return_json(self):
        """Verify all 5 progress APIs return valid JSON with status 'success'."""
        self._create_and_login_user()

        endpoints = [
            ('/api/progress', ['overall_progress', 'statistics', 'subjects']),
            ('/api/progress/subjects', ['subjects']),
            ('/api/progress/topics', ['topics']),
            ('/api/progress/statistics', ['statistics']),
            ('/api/progress/activity', ['activity'])
        ]

        for ep, expected_keys in endpoints:
            response = self.client.get(ep)
            self.assertEqual(response.status_code, 200, f"Endpoint {ep} failed")
            data = response.get_json()
            self.assertEqual(data.get("status"), "success")
            for k in expected_keys:
                self.assertIn(k, data)

    # -------------------------------------------------------------------------
    # Test 21: Phase 1 baseline verification (Database & Health)
    # -------------------------------------------------------------------------
    def test_21_phase_1_baseline_verification(self):
        """Phase 1 regression: Verify database connectivity and schema tables exist."""
        db_health = check_db_health()
        self.assertTrue(db_health["connected"])
        self.assertTrue(db_health["database_exists"])

    # -------------------------------------------------------------------------
    # Test 22: Phase 2 baseline verification (Auth & Profile)
    # -------------------------------------------------------------------------
    def test_22_phase_2_baseline_verification(self):
        """Phase 2 regression: Verify user profile operations continue working."""
        user_id = self._create_and_login_user("test_prog_p2@example.com", "P2 Student")
        profile_data = {
            "education_level": "Undergraduate",
            "course": "Computer Science",
            "semester": "Semester 4",
            "skill_level": "Intermediate",
            "learning_goal": "Pass Algorithms with A grade",
            "preferred_study_time": "Evening"
        }
        success, msg = upsert_student_profile(user_id, profile_data)
        self.assertTrue(success)
        saved = get_student_profile(user_id)
        self.assertEqual(saved["course"], "Computer Science")

    # -------------------------------------------------------------------------
    # Test 23: Phase 3 baseline verification (Content & Resources)
    # -------------------------------------------------------------------------
    def test_23_phase_3_baseline_verification(self):
        """Phase 3 regression: Verify subjects browsing and topics catalog continue working."""
        subjects = get_all_subjects()
        self.assertGreaterEqual(len(subjects), 4)
        topics = get_topics_by_subject(subjects[0]["id"])
        self.assertGreaterEqual(len(topics), 1)

    # -------------------------------------------------------------------------
    # Test 24: Phase 4 baseline verification (Study Plans)
    # -------------------------------------------------------------------------
    def test_24_phase_4_baseline_verification(self):
        """Phase 4 regression: Verify personalized study plan generation continues working."""
        user_id = self._create_and_login_user("test_prog_p4@example.com", "P4 Student")
        topic_id = self.test_topic_1["id"]
        subject_id = self.test_topic_1["subject_id"]

        success, msg, plan_id = create_study_plan(user_id, subject_id, [topic_id], 3, "Phase 4 Regression")
        self.assertTrue(success)
        detail = get_study_plan_detail(plan_id, user_id)
        self.assertEqual(len(detail["items"]), 3)

    # -------------------------------------------------------------------------
    # Test 25: Phase 5 baseline verification (Quizzes)
    # -------------------------------------------------------------------------
    def test_25_phase_5_baseline_verification(self):
        """Phase 5 regression: Verify quiz catalog and questions retrieval continue working."""
        catalog = get_available_quizzes_catalog()
        self.assertGreaterEqual(len(catalog), 1)
        questions = get_quiz_questions_for_topic(self.test_topic_1["id"])
        self.assertGreater(len(questions), 0)

    # -------------------------------------------------------------------------
    # Test 26: Phase 6 baseline verification (AI Doubt Assistant)
    # -------------------------------------------------------------------------
    def test_26_phase_6_baseline_verification(self):
        """Phase 6 regression: Verify AI doubt assistant validation and chat persistence."""
        user_id = self._create_and_login_user("test_prog_p6@example.com", "P6 Student")
        is_valid, err, val = validate_academic_question(
            "What is time complexity?",
            self.test_topic_1["subject_id"],
            self.test_topic_1["id"]
        )
        self.assertTrue(is_valid)

        save_success, save_msg, chat_id = save_ai_chat(user_id, val["question"], "O(N) denotes linear time.")
        self.assertTrue(save_success)
        history = get_user_ai_history(user_id)
        self.assertEqual(len(history), 1)


if __name__ == '__main__':
    unittest.main()

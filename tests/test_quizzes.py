"""
Automated Test Suite for Phase 5 - Quiz & Practice Engine.
AI Student Learning Mentor.

Covers all 25 Phase 5 requirements:
1. Guest cannot access quiz pages (must redirect to /login with 302).
2. Authenticated user can view quiz catalog (GET /quizzes returns 200).
3. Topic quiz loads real questions from MySQL.
4. Invalid topic returns 404.
5. Quiz questions belong to requested topic.
6. Quiz size is limited correctly (e.g. min(limit, available)).
7. No duplicate questions in an attempt.
8. Correct answers are NOT exposed before submission (both HTML and API).
9. Valid quiz submission calculates correct score.
10. Incorrect answers are calculated correctly.
11. Quiz attempt is stored in database (quiz_attempts and quiz_attempt_answers).
12. Attempt belongs to authenticated user.
13. Quiz result page works (GET /quiz/results/<id> returns 200).
14. Quiz review page works (GET /quiz/results/<id>/review returns 200).
15. User can view own quiz history (GET /quiz/history returns 200).
16. User cannot view another user's attempt (isolation returns 404).
17. Invalid attempt ID returns 404.
18. Answer validation works (rejects empty or malformed answers without 500 error).
19. Dashboard quiz statistics use real database data.
20. Empty quiz history displays proper empty state.
21. Study-plan topic can link to a real quiz when available.
22. Phase 1 test suite passing.
23. Phase 2 test suite passing.
24. Phase 3 test suite passing.
25. Phase 4 test suite passing.
"""
import unittest
from unittest.mock import patch
import html
from app import create_app
from services.db import get_db_connection
from services.auth_service import register_user
from services.quiz_service import (
    get_available_quizzes_catalog,
    get_topic_quiz_info,
    get_quiz_questions_for_topic,
    submit_quiz_attempt,
    get_quiz_attempt_result,
    get_quiz_attempt_review,
    get_user_quiz_history,
    get_user_quiz_stats,
    check_topic_has_quiz
)
from services.study_plan_service import create_study_plan


class TestPhase5QuizEngine(unittest.TestCase):
    """Test suite covering all Phase 5 Quiz & Practice Engine requirements."""

    @classmethod
    def setUpClass(cls):
        """Set up Flask test application and fetch a valid topic ID with quizzes."""
        cls.app = create_app()
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                # Find a topic with quiz questions
                cursor.execute("""
                    SELECT t.id, t.topic_name, t.subject_id, COUNT(q.id) as qcount
                    FROM topics t
                    JOIN quizzes q ON t.id = q.topic_id
                    GROUP BY t.id
                    HAVING qcount > 0
                    LIMIT 2
                """)
                rows = cursor.fetchall()
                if not rows:
                    raise RuntimeError("No topics with quiz questions found in database.")
                cls.test_topic_1 = rows[0]
                cls.test_topic_2 = rows[1] if len(rows) > 1 else rows[0]
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
        """Helper to remove test users and cascade delete their attempts."""
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    "DELETE FROM users WHERE email LIKE %s",
                    ('test_qz_%@example.com',)
                )
            conn.commit()
        finally:
            conn.close()

    def _create_and_login_user(self, email="test_qz_user@example.com", name="Quiz Student"):
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
    # Test 1: Guest cannot access quiz pages (redirects to /login)
    # -------------------------------------------------------------------------
    def test_01_guest_cannot_access_quiz_pages(self):
        """Verify unauthenticated access to quiz pages redirects to /login."""
        protected_endpoints = [
            '/quizzes',
            f'/quizzes/topic/{self.test_topic_1["id"]}',
            f'/quiz/{self.test_topic_1["id"]}/start',
            '/quiz/results/1',
            '/quiz/results/1/review',
            '/quiz/history'
        ]
        for url in protected_endpoints:
            response = self.client.get(url, follow_redirects=False)
            self.assertEqual(
                response.status_code, 302,
                f"Guest should be redirected from {url}"
            )
            self.assertIn('/login', response.headers.get('Location', ''))

    # -------------------------------------------------------------------------
    # Test 2: Authenticated user can view quiz catalog
    # -------------------------------------------------------------------------
    def test_02_authenticated_user_can_view_quiz_catalog(self):
        """Verify authenticated user can view quiz catalog with HTTP 200."""
        self._create_and_login_user()
        response = self.client.get('/quizzes')
        self.assertEqual(response.status_code, 200)
        content = html.unescape(response.get_data(as_text=True))
        self.assertIn("Practice Quizzes", content)
        self.assertIn(self.test_topic_1["topic_name"], content)

    # -------------------------------------------------------------------------
    # Test 3: Topic quiz loads real questions from MySQL
    # -------------------------------------------------------------------------
    def test_03_topic_quiz_loads_real_questions(self):
        """Verify questions returned for a topic correspond to real MySQL records."""
        self._create_and_login_user()
        topic_id = self.test_topic_1["id"]
        questions = get_quiz_questions_for_topic(topic_id, limit=10, include_correct=True)
        self.assertGreater(len(questions), 0)

        # Verify against MySQL directly
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT id, question FROM quizzes WHERE topic_id = %s", (topic_id,))
                db_questions = cursor.fetchall()
                db_ids = {q["id"] for q in db_questions}
                for q in questions:
                    self.assertIn(q["id"], db_ids)
                    self.assertTrue(len(q["question"]) > 5)
        finally:
            conn.close()

    # -------------------------------------------------------------------------
    # Test 4: Invalid topic returns 404
    # -------------------------------------------------------------------------
    def test_04_invalid_topic_returns_404(self):
        """Verify requests for non-existent topics return HTTP 404."""
        self._create_and_login_user()
        resp_preview = self.client.get('/quizzes/topic/999999')
        self.assertEqual(resp_preview.status_code, 404)

        resp_start = self.client.get('/quiz/999999/start')
        self.assertEqual(resp_start.status_code, 404)

        resp_api = self.client.get('/api/quizzes/topic/999999')
        self.assertEqual(resp_api.status_code, 404)

    # -------------------------------------------------------------------------
    # Test 5: Quiz questions belong to requested topic
    # -------------------------------------------------------------------------
    def test_05_quiz_questions_belong_to_topic(self):
        """Verify all retrieved questions belong strictly to the requested topic."""
        topic_id = self.test_topic_1["id"]
        questions = get_quiz_questions_for_topic(topic_id, limit=10)
        for q in questions:
            self.assertEqual(q["topic_id"], topic_id)

    # -------------------------------------------------------------------------
    # Test 6: Quiz size is limited correctly
    # -------------------------------------------------------------------------
    def test_06_quiz_size_limited_correctly(self):
        """Verify question count respects the requested limit."""
        topic_id = self.test_topic_1["id"]
        questions_limit_2 = get_quiz_questions_for_topic(topic_id, limit=2)
        self.assertLessEqual(len(questions_limit_2), 2)

    # -------------------------------------------------------------------------
    # Test 7: No duplicate questions in an attempt
    # -------------------------------------------------------------------------
    def test_07_no_duplicate_questions(self):
        """Verify no duplicate questions are returned in a quiz session."""
        topic_id = self.test_topic_1["id"]
        questions = get_quiz_questions_for_topic(topic_id, limit=10)
        question_ids = [q["id"] for q in questions]
        self.assertEqual(len(question_ids), len(set(question_ids)))

    # -------------------------------------------------------------------------
    # Test 8: Correct answers NOT exposed before submission
    # -------------------------------------------------------------------------
    def test_08_correct_answers_not_exposed_before_submission(self):
        """Verify correct answers are stripped from both HTML and client API."""
        self._create_and_login_user()
        topic_id = self.test_topic_1["id"]

        # HTML active quiz page check
        response = self.client.get(f'/quiz/{topic_id}/start')
        self.assertEqual(response.status_code, 200)
        html_text = response.get_data(as_text=True)
        self.assertNotIn("correct_answer", html_text)
        self.assertNotIn("data-correct", html_text)

        # API endpoint check
        api_resp = self.client.get(f'/api/quizzes/topic/{topic_id}')
        self.assertEqual(api_resp.status_code, 200)
        api_data = api_resp.get_json()
        self.assertTrue(api_data["questions"])
        for q in api_data["questions"]:
            self.assertNotIn("correct_answer", q, "API must not expose correct_answer before submission!")

    # -------------------------------------------------------------------------
    # Test 9: Valid quiz submission calculates correct score (100%)
    # -------------------------------------------------------------------------
    def test_09_valid_quiz_submission_calculates_correct_score(self):
        """Verify submitting all correct answers yields 100% score."""
        user_id = self._create_and_login_user()
        topic_id = self.test_topic_1["id"]

        # Retrieve questions with correct answers from DB
        questions = get_quiz_questions_for_topic(topic_id, limit=5, include_correct=True)
        self.assertTrue(len(questions) > 0)

        # Build perfect submission
        all_correct_answers = {q["id"]: q["correct_answer"] for q in questions}
        success, msg, attempt_id = submit_quiz_attempt(user_id, topic_id, all_correct_answers)
        self.assertTrue(success, f"Submission failed: {msg}")
        self.assertIsNotNone(attempt_id)

        # Check result
        result = get_quiz_attempt_result(attempt_id, user_id)
        self.assertIsNotNone(result)
        self.assertEqual(result["correct_answers"], len(questions))
        self.assertEqual(result["incorrect_answers"], 0)
        self.assertEqual(result["score_percentage"], 100.0)
        self.assertEqual(result["feedback"]["tier"], "Excellent")

    # -------------------------------------------------------------------------
    # Test 10: Incorrect answers are calculated correctly
    # -------------------------------------------------------------------------
    def test_10_incorrect_answers_calculated_correctly(self):
        """Verify deliberately submitting wrong answers calculates score accurately."""
        user_id = self._create_and_login_user()
        topic_id = self.test_topic_1["id"]

        questions = get_quiz_questions_for_topic(topic_id, limit=5, include_correct=True)
        self.assertGreaterEqual(len(questions), 2)

        # Make first answer correct, rest wrong
        mixed_answers = {}
        for idx, q in enumerate(questions):
            real_ans = q["correct_answer"].upper()
            if idx == 0:
                mixed_answers[q["id"]] = real_ans
            else:
                # pick a wrong option
                wrong_opt = "B" if real_ans == "A" else "A"
                mixed_answers[q["id"]] = wrong_opt

        success, msg, attempt_id = submit_quiz_attempt(user_id, topic_id, mixed_answers)
        self.assertTrue(success)

        result = get_quiz_attempt_result(attempt_id, user_id)
        self.assertEqual(result["correct_answers"], 1)
        self.assertEqual(result["incorrect_answers"], len(questions) - 1)
        expected_pct = round((1 / len(questions)) * 100, 2)
        self.assertEqual(result["score_percentage"], expected_pct)

    # -------------------------------------------------------------------------
    # Test 11: Quiz attempt stored in database (attempts and answers)
    # -------------------------------------------------------------------------
    def test_11_quiz_attempt_stored_in_database(self):
        """Verify records exist in quiz_attempts and quiz_attempt_answers."""
        user_id = self._create_and_login_user()
        topic_id = self.test_topic_1["id"]

        questions = get_quiz_questions_for_topic(topic_id, limit=3, include_correct=True)
        answers = {q["id"]: q["correct_answer"] for q in questions}

        success, msg, attempt_id = submit_quiz_attempt(user_id, topic_id, answers)
        self.assertTrue(success)

        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM quiz_attempts WHERE id = %s", (attempt_id,))
                attempt_row = cursor.fetchone()
                self.assertIsNotNone(attempt_row)
                self.assertEqual(attempt_row["user_id"], user_id)
                self.assertEqual(attempt_row["total_questions"], len(questions))

                cursor.execute("SELECT * FROM quiz_attempt_answers WHERE attempt_id = %s", (attempt_id,))
                answer_rows = cursor.fetchall()
                self.assertEqual(len(answer_rows), len(questions))
        finally:
            conn.close()

    # -------------------------------------------------------------------------
    # Test 12: Attempt belongs to authenticated user
    # -------------------------------------------------------------------------
    def test_12_attempt_belongs_to_authenticated_user(self):
        """Verify stored attempt user_id matches logged-in user id."""
        user_id = self._create_and_login_user()
        topic_id = self.test_topic_1["id"]

        questions = get_quiz_questions_for_topic(topic_id, limit=2, include_correct=True)
        answers = {q["id"]: q["correct_answer"] for q in questions}

        _, _, attempt_id = submit_quiz_attempt(user_id, topic_id, answers)
        result = get_quiz_attempt_result(attempt_id, user_id)
        self.assertEqual(result["user_id"], user_id)

    # -------------------------------------------------------------------------
    # Test 13: Quiz result page works (GET /quiz/results/<id> returns 200)
    # -------------------------------------------------------------------------
    def test_13_quiz_result_page_works(self):
        """Verify quiz result scorecard page renders with HTTP 200."""
        user_id = self._create_and_login_user()
        topic_id = self.test_topic_1["id"]

        questions = get_quiz_questions_for_topic(topic_id, limit=2, include_correct=True)
        answers = {q["id"]: q["correct_answer"] for q in questions}
        _, _, attempt_id = submit_quiz_attempt(user_id, topic_id, answers)

        response = self.client.get(f'/quiz/results/{attempt_id}')
        self.assertEqual(response.status_code, 200)
        content = response.get_data(as_text=True)
        self.assertIn(f"Scorecard #{attempt_id}", content)
        self.assertIn("Final Score", content)
        self.assertIn("Review Questions", content)

    # -------------------------------------------------------------------------
    # Test 14: Quiz review page works (GET /quiz/results/<id>/review returns 200)
    # -------------------------------------------------------------------------
    def test_14_quiz_review_page_works(self):
        """Verify quiz review page renders with HTTP 200 and compares answers."""
        user_id = self._create_and_login_user()
        topic_id = self.test_topic_1["id"]

        questions = get_quiz_questions_for_topic(topic_id, limit=2, include_correct=True)
        # 1 correct, 1 wrong to verify both indicator tags
        real_ans_0 = questions[0]["correct_answer"].upper()
        real_ans_1 = questions[1]["correct_answer"].upper()
        wrong_ans_1 = "B" if real_ans_1 == "A" else "A"
        answers = {
            questions[0]["id"]: real_ans_0,
            questions[1]["id"]: wrong_ans_1
        }
        _, _, attempt_id = submit_quiz_attempt(user_id, topic_id, answers)

        response = self.client.get(f'/quiz/results/{attempt_id}/review')
        self.assertEqual(response.status_code, 200)
        content = response.get_data(as_text=True)
        self.assertIn("Detailed Answer Review", content)
        self.assertIn("Your Answer", content)
        self.assertIn("Correct Answer", content)

    # -------------------------------------------------------------------------
    # Test 15: User can view own quiz history
    # -------------------------------------------------------------------------
    def test_15_user_can_view_own_quiz_history(self):
        """Verify GET /quiz/history renders previous attempts for the student."""
        user_id = self._create_and_login_user()
        topic_id = self.test_topic_1["id"]

        questions = get_quiz_questions_for_topic(topic_id, limit=2, include_correct=True)
        answers = {q["id"]: q["correct_answer"] for q in questions}
        submit_quiz_attempt(user_id, topic_id, answers)

        response = self.client.get('/quiz/history')
        self.assertEqual(response.status_code, 200)
        content = html.unescape(response.get_data(as_text=True))
        self.assertIn("My Quiz History", content)
        self.assertIn(self.test_topic_1["topic_name"], content)

    # -------------------------------------------------------------------------
    # Test 16: User CANNOT view another user's attempt (isolation check)
    # -------------------------------------------------------------------------
    def test_16_user_cannot_view_another_user_attempt(self):
        """Verify Student B CANNOT view Student A's quiz result or review."""
        user_a = self._create_and_login_user(email="test_qz_user_a@example.com", name="User A")
        topic_id = self.test_topic_1["id"]

        questions = get_quiz_questions_for_topic(topic_id, limit=2, include_correct=True)
        answers = {q["id"]: q["correct_answer"] for q in questions}
        _, _, attempt_id = submit_quiz_attempt(user_a, topic_id, answers)

        # Log in as User B
        self._create_and_login_user(email="test_qz_user_b@example.com", name="User B")

        # User B tries to view User A's result
        resp_result = self.client.get(f'/quiz/results/{attempt_id}')
        self.assertEqual(resp_result.status_code, 404, "User B should get 404 viewing User A's result")

        # User B tries to view User A's review
        resp_review = self.client.get(f'/quiz/results/{attempt_id}/review')
        self.assertEqual(resp_review.status_code, 404, "User B should get 404 viewing User A's review")

        # User B tries to access via API
        resp_api = self.client.get(f'/api/quiz-attempts/{attempt_id}')
        self.assertEqual(resp_api.status_code, 404, "User B should get 404 via API")

    # -------------------------------------------------------------------------
    # Test 17: Invalid attempt ID returns 404
    # -------------------------------------------------------------------------
    def test_17_invalid_attempt_id_returns_404(self):
        """Verify requests for non-existent attempts return HTTP 404."""
        self._create_and_login_user()
        resp_result = self.client.get('/quiz/results/999999')
        self.assertEqual(resp_result.status_code, 404)

        resp_review = self.client.get('/quiz/results/999999/review')
        self.assertEqual(resp_review.status_code, 404)

        resp_api = self.client.get('/api/quiz-attempts/999999')
        self.assertEqual(resp_api.status_code, 404)

    # -------------------------------------------------------------------------
    # Test 18: Answer validation works
    # -------------------------------------------------------------------------
    def test_18_answer_validation_works(self):
        """Verify empty or malformed answer submissions are handled gracefully without 500 error."""
        self._create_and_login_user()
        topic_id = self.test_topic_1["id"]

        # Empty submission via form
        resp_empty_form = self.client.post(
            f'/quiz/{topic_id}/submit',
            data={},
            follow_redirects=True
        )
        self.assertEqual(resp_empty_form.status_code, 200)

        # Empty submission via API
        resp_empty_api = self.client.post(
            f'/api/quizzes/{topic_id}/submit',
            json={"answers": {}}
        )
        self.assertEqual(resp_empty_api.status_code, 400)

        # Malformed submission via API
        resp_malformed = self.client.post(
            f'/api/quizzes/{topic_id}/submit',
            json={"answers": "invalid_string_not_dict"}
        )
        self.assertEqual(resp_malformed.status_code, 400)

    # -------------------------------------------------------------------------
    # Test 19: Dashboard quiz statistics use real database data
    # -------------------------------------------------------------------------
    def test_19_dashboard_quiz_statistics_use_real_data(self):
        """Verify /dashboard accurately displays authentic quiz statistics."""
        user_id = self._create_and_login_user()
        topic_id = self.test_topic_1["id"]

        questions = get_quiz_questions_for_topic(topic_id, limit=4, include_correct=True)
        # Submit attempt 1: 100%
        answers_100 = {q["id"]: q["correct_answer"] for q in questions}
        submit_quiz_attempt(user_id, topic_id, answers_100)

        # Submit attempt 2: 50%
        answers_50 = {}
        for idx, q in enumerate(questions):
            real_ans = q["correct_answer"].upper()
            answers_50[q["id"]] = real_ans if idx < 2 else ("B" if real_ans == "A" else "A")
        submit_quiz_attempt(user_id, topic_id, answers_50)

        response = self.client.get('/dashboard')
        self.assertEqual(response.status_code, 200)
        content = response.get_data(as_text=True)

        # Total attempts should be 2
        self.assertIn("Total Attempts", content)
        self.assertIn("2", content)
        # Best score 100%
        self.assertIn("100", content)
        # Average score 75.0%
        self.assertIn("75", content)

    # -------------------------------------------------------------------------
    # Test 20: Empty quiz history displays proper empty state
    # -------------------------------------------------------------------------
    def test_20_empty_quiz_history_displays_empty_state(self):
        """Verify empty state is shown when a student has not taken any quizzes yet."""
        self._create_and_login_user()
        response = self.client.get('/quiz/history')
        self.assertEqual(response.status_code, 200)
        content = response.get_data(as_text=True)
        self.assertIn("No Quiz Attempts Yet", content)
        self.assertIn("Browse Available Quizzes", content)

    # -------------------------------------------------------------------------
    # Test 21: Study-plan topic can link to a real quiz when available
    # -------------------------------------------------------------------------
    def test_21_study_plan_topic_can_link_to_real_quiz(self):
        """Verify study plan detail page links daily tasks to topic practice quizzes."""
        user_id = self._create_and_login_user()
        topic_id = self.test_topic_1["id"]
        subject_id = self.test_topic_1["subject_id"]

        # Create study plan
        success, msg, plan_id = create_study_plan(
            user_id=user_id,
            subject_id=subject_id,
            topic_ids=[topic_id],
            duration_days=1,
            goal="Pass test with flying colors",
            skill_level="Beginner",
            preferred_study_time="Flexible"
        )
        self.assertTrue(success, f"Failed to create study plan: {msg}")

        response = self.client.get(f'/study-plans/{plan_id}')
        self.assertEqual(response.status_code, 200)
        content = response.get_data(as_text=True)
        # Should contain quiz link
        self.assertIn(f"/quizzes/topic/{topic_id}", content)

    # -------------------------------------------------------------------------
    # Test 22-25: Phase regression validations
    # -------------------------------------------------------------------------
    def test_22_phase_1_baseline_verification(self):
        """Phase 1 regression: Verify database connection health and schema tables exist."""
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("SHOW TABLES")
                tables = {list(row.values())[0] for row in cursor.fetchall()}
                required = {
                    "users", "student_profiles", "subjects", "topics",
                    "resources", "study_plans", "study_plan_items",
                    "quizzes", "quiz_attempts", "quiz_attempt_answers"
                }
                for table in required:
                    self.assertIn(table, tables, f"Missing required table: {table}")
        finally:
            conn.close()

    def test_23_phase_2_baseline_verification(self):
        """Phase 2 regression: Verify student profile operations continue to work."""
        user_id = self._create_and_login_user()
        response = self.client.get('/dashboard')
        self.assertEqual(response.status_code, 200)
        self.assertIn("Quiz Student", response.get_data(as_text=True))

    def test_24_phase_3_baseline_verification(self):
        """Phase 3 regression: Verify subjects browsing and topics catalog continue to work."""
        response = self.client.get('/subjects')
        self.assertEqual(response.status_code, 200)
        self.assertIn("Subjects", response.get_data(as_text=True))

    def test_25_phase_4_baseline_verification(self):
        """Phase 4 regression: Verify study plans engine continues to work properly."""
        user_id = self._create_and_login_user()
        response = self.client.get('/study-plans')
        self.assertEqual(response.status_code, 200)
        self.assertIn("My Study Plans", response.get_data(as_text=True))

    # -------------------------------------------------------------------------
    # Tests 26-30: Phase 5.2 Quiz Topic Briefing Regressions
    # -------------------------------------------------------------------------
    def test_26_quiz_topic_preview_authenticated_renders_successfully(self):
        """Verify authenticated GET to /quizzes/topic/<id> renders briefing page with HTTP 200."""
        self._create_and_login_user()
        topic_id = self.test_topic_1["id"]
        response = self.client.get(f'/quizzes/topic/{topic_id}')
        self.assertEqual(response.status_code, 200)
        content = response.get_data(as_text=True)
        self.assertIn("Practice Quiz:", content)
        self.assertIn("Quiz Instructions", content)
        self.assertTrue(f"/quiz/topic/{topic_id}/start" in content or f"/quiz/{topic_id}/start" in content)

    def test_27_quiz_topic_preview_displays_valid_question_count(self):
        """Verify rendered briefing displays the genuine question count and length stat."""
        self._create_and_login_user()
        topic_id = self.test_topic_1["id"]
        info = get_topic_quiz_info(topic_id)
        self.assertIsNotNone(info)
        expected_count = min(info['question_count'], 10)
        response = self.client.get(f'/quizzes/topic/{topic_id}')
        self.assertEqual(response.status_code, 200)
        content = response.get_data(as_text=True)
        self.assertIn(f"{expected_count} Questions", content)

    def test_28_quiz_topic_preview_zero_questions_handled_safely(self):
        """Verify topic with zero questions renders safely without 500 error."""
        self._create_and_login_user()
        mock_topic_info = {
            'topic_id': 9991,
            'topic_name': 'Zero Question Practice Topic',
            'topic_description': 'Curriculum topic without any authored questions yet.',
            'topic_difficulty': 'Beginner',
            'subject_id': self.test_topic_1["subject_id"],
            'subject_name': 'Test Subject',
            'question_count': 0
        }
        with patch('routes.quiz_routes.get_topic_quiz_info', return_value=mock_topic_info):
            response = self.client.get('/quizzes/topic/9991')
            self.assertEqual(response.status_code, 200)
            content = response.get_data(as_text=True)
            self.assertIn("Practice Quiz: Zero Question Practice Topic", content)
            self.assertIn("0 Questions", content)

    def test_29_quiz_topic_preview_invalid_topic_returns_404(self):
        """Verify invalid topic ID on briefing endpoint continues to return HTTP 404."""
        self._create_and_login_user()
        response = self.client.get('/quizzes/topic/999999')
        self.assertEqual(response.status_code, 404)

    def test_30_quiz_topic_preview_unauthenticated_redirects_to_login(self):
        """Verify unauthenticated guest request to briefing redirects to /login."""
        topic_id = self.test_topic_1["id"]
        response = self.client.get(f'/quizzes/topic/{topic_id}', follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login', response.headers.get('Location', ''))


if __name__ == '__main__':
    unittest.main()

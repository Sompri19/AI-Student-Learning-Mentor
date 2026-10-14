"""
Automated Test Suite for Phase 4 - Personalized Study Plan Engine.
AI Student Learning Mentor.

Covers all 25 Phase 4 requirements:
1. Study plans page requires authentication
2. Authenticated user can view study plans page
3. Create study plan page requires authentication
4. Create study plan form loads subjects and topics
5. Successful study plan creation creates database records
6. Study plan items generated for each day
7. Validation error when subject is missing
8. Validation error when topics are empty
9. Validation error when duration is invalid (e.g. 0, negative, > 60)
10. Validation error when goal is empty
11. Selected topics must belong to selected subject
12. Study plan generator allocates topics across days when days >= topics
13. Study plan generator allocates topics across days when days < topics
14. Skill level influences generated task descriptions
15. Study plan detail page displays all daily tasks
16. User can view their own study plan detail
17. User CANNOT view another user's study plan (isolation check)
18. User can toggle task completion status (false -> true)
19. User can un-toggle task completion status (true -> false)
20. User CANNOT toggle tasks on another user's study plan
21. User can edit their own study plan details
22. User CANNOT edit another user's study plan
23. User can delete their own study plan
24. User CANNOT delete another user's study plan
25. Dashboard displays real study plan progress and counts
"""
import unittest
import html
from app import create_app
from services.db import get_db_connection
from services.auth_service import register_user
from services.study_plan_service import (
    validate_study_plan_input, generate_plan_schedule,
    create_study_plan, get_user_study_plans, get_study_plan_detail,
    toggle_task_completion, delete_study_plan
)


class TestPhase4StudyPlans(unittest.TestCase):
    """Test suite covering all Phase 4 Personalized Study Plan Engine requirements."""

    @classmethod
    def setUpClass(cls):
        """Set up Flask test application."""
        cls.app = create_app()

    def setUp(self):
        """Clean up test users and reset test client before each test."""
        self.client = self.app.test_client()
        self._cleanup_test_data()

    def tearDown(self):
        """Clean up test records after each test."""
        self._cleanup_test_data()

    def _cleanup_test_data(self):
        """Helper to remove test users and cascade delete their study plans and items."""
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    "DELETE FROM users WHERE email LIKE %s",
                    ('test_sp_%@example.com',)
                )
            conn.commit()
        finally:
            conn.close()

    def _create_and_login_user(self, email="test_sp_user@example.com", name="Test Student"):
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
    # 1. Authentication Protection Tests
    # -------------------------------------------------------------------------
    def test_01_study_plans_requires_authentication(self):
        """Verify unauthenticated access to /study-plans redirects to /login."""
        response = self.client.get('/study-plans')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login', response.headers.get('Location', ''))

    def test_02_authenticated_user_can_view_study_plans(self):
        """Verify authenticated user can view /study-plans with HTTP 200."""
        self._create_and_login_user()
        response = self.client.get('/study-plans')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"My Study Plans", response.data)

    def test_03_create_study_plan_requires_authentication(self):
        """Verify unauthenticated access to /study-plans/create redirects to /login."""
        response = self.client.get('/study-plans/create')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login', response.headers.get('Location', ''))

    def test_04_create_study_plan_form_loads_subjects(self):
        """Verify /study-plans/create renders form with subjects and topic choices."""
        self._create_and_login_user()
        response = self.client.get('/study-plans/create')
        self.assertEqual(response.status_code, 200)
        content = response.data.decode('utf-8')
        self.assertIn("Python Programming", content)
        self.assertIn("Create Personalized Study Plan", content)
        self.assertIn("name=\"subject_id\"", content)
        self.assertIn("name=\"duration_days\"", content)

    # -------------------------------------------------------------------------
    # 2. Plan Creation and Database Verification Tests
    # -------------------------------------------------------------------------
    def test_05_successful_study_plan_creation(self):
        """Verify POST /study-plans/create creates database records and redirects to detail."""
        user_id = self._create_and_login_user()

        # Subject 1 has topics 1 and 2 in seeded database
        payload = {
            'subject_id': '1',
            'topic_ids': ['1', '2'],
            'duration_days': '5',
            'goal': 'Master Python basic syntax and control flow',
            'skill_level': 'Beginner',
            'preferred_study_time': 'Morning'
        }
        response = self.client.post('/study-plans/create', data=payload, follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/study-plans/', response.headers.get('Location', ''))

        # Verify DB records
        plans = get_user_study_plans(user_id)
        self.assertEqual(len(plans), 1)
        self.assertEqual(plans[0]['goal'], 'Master Python basic syntax and control flow')
        self.assertEqual(plans[0]['duration_days'], 5)
        self.assertEqual(plans[0]['skill_level'], 'Beginner')
        self.assertEqual(plans[0]['preferred_study_time'], 'Morning')

    def test_06_study_plan_items_generated_for_each_day(self):
        """Verify exactly duration_days items are generated with sequential day numbers."""
        user_id = self._create_and_login_user()
        payload = {
            'subject_id': '1',
            'topic_ids': ['1', '2'],
            'duration_days': '7',
            'goal': 'Prepare for coding assessment',
            'skill_level': 'Intermediate',
            'preferred_study_time': 'Evening'
        }
        self.client.post('/study-plans/create', data=payload)
        plans = get_user_study_plans(user_id)
        self.assertEqual(len(plans), 1)
        plan_id = plans[0]['id']

        detail = get_study_plan_detail(plan_id, user_id)
        self.assertIsNotNone(detail)
        items = detail['items']
        self.assertEqual(len(items), 7)

        # Check sequential day numbering
        day_numbers = [item['day_number'] for item in items]
        self.assertEqual(day_numbers, [1, 2, 3, 4, 5, 6, 7])

        # All items should initially be uncompleted
        for item in items:
            self.assertFalse(item['completed'])

    # -------------------------------------------------------------------------
    # 3. Input Validation Tests
    # -------------------------------------------------------------------------
    def test_07_validation_missing_subject(self):
        """Verify validation error when subject_id is missing."""
        user_id = self._create_and_login_user()
        payload = {
            'subject_id': '',
            'topic_ids': ['1'],
            'duration_days': '5',
            'goal': 'Learn Python',
            'skill_level': 'Beginner'
        }
        response = self.client.post('/study-plans/create', data=payload)
        self.assertEqual(response.status_code, 400)
        self.assertIn(b"valid subject must be selected", response.data)

    def test_08_validation_missing_topics(self):
        """Verify validation error when topic_ids is empty."""
        user_id = self._create_and_login_user()
        payload = {
            'subject_id': '1',
            'topic_ids': [],
            'duration_days': '5',
            'goal': 'Learn Python',
            'skill_level': 'Beginner'
        }
        response = self.client.post('/study-plans/create', data=payload)
        self.assertEqual(response.status_code, 400)
        self.assertIn(b"At least one topic must be selected", response.data)

    def test_09_validation_invalid_duration(self):
        """Verify validation error when duration is invalid (0, negative, > 60)."""
        user_id = self._create_and_login_user()

        # Zero duration
        payload_zero = {
            'subject_id': '1',
            'topic_ids': ['1'],
            'duration_days': '0',
            'goal': 'Learn Python'
        }
        res_zero = self.client.post('/study-plans/create', data=payload_zero)
        self.assertEqual(res_zero.status_code, 400)
        self.assertIn(b"between 1 and 60 days", res_zero.data)

        # Negative duration
        payload_neg = {
            'subject_id': '1',
            'topic_ids': ['1'],
            'duration_days': '-5',
            'goal': 'Learn Python'
        }
        res_neg = self.client.post('/study-plans/create', data=payload_neg)
        self.assertEqual(res_neg.status_code, 400)

        # > 60 duration
        payload_large = {
            'subject_id': '1',
            'topic_ids': ['1'],
            'duration_days': '90',
            'goal': 'Learn Python'
        }
        res_large = self.client.post('/study-plans/create', data=payload_large)
        self.assertEqual(res_large.status_code, 400)

    def test_10_validation_empty_goal(self):
        """Verify validation error when goal is empty or whitespace."""
        user_id = self._create_and_login_user()
        payload = {
            'subject_id': '1',
            'topic_ids': ['1'],
            'duration_days': '7',
            'goal': '   '
        }
        response = self.client.post('/study-plans/create', data=payload)
        self.assertEqual(response.status_code, 400)
        self.assertIn(b"Learning goal cannot be empty", response.data)

    def test_11_topics_must_belong_to_subject(self):
        """Verify rejection when selected topics do not belong to the selected subject."""
        user_id = self._create_and_login_user()
        # Topic 6 belongs to Subject 2 (Data Structures), not Subject 1 (Python)
        payload = {
            'subject_id': '1',
            'topic_ids': ['1', '6'],
            'duration_days': '5',
            'goal': 'Cross-subject invalid attempt'
        }
        response = self.client.post('/study-plans/create', data=payload)
        self.assertEqual(response.status_code, 400)
        self.assertIn(b"All selected topics must belong to the selected subject", response.data)

    # -------------------------------------------------------------------------
    # 4. Deterministic Scheduling Logic Tests
    # -------------------------------------------------------------------------
    def test_12_allocation_when_days_greater_or_equal_to_topics(self):
        """Verify topic allocation when duration_days >= len(topics)."""
        topics = [
            {'id': 1, 'topic_name': 'Variables', 'difficulty': 'Beginner'},
            {'id': 2, 'topic_name': 'Loops', 'difficulty': 'Beginner'}
        ]
        schedule = generate_plan_schedule(
            subject_name='Python',
            topics=topics,
            duration_days=4,
            skill_level='Beginner',
            goal='Learn Python basics',
            preferred_study_time='Morning'
        )

        self.assertEqual(len(schedule), 4)
        # Day 1: Topic 1
        self.assertEqual(schedule[0]['day_number'], 1)
        self.assertEqual(schedule[0]['topic_id'], 1)
        self.assertIn('Variables', schedule[0]['task'])

        # Day 2: Topic 2
        self.assertEqual(schedule[1]['day_number'], 2)
        self.assertEqual(schedule[1]['topic_id'], 2)
        self.assertIn('Loops', schedule[1]['task'])

        # Day 3: Structured revision
        self.assertEqual(schedule[2]['day_number'], 3)
        self.assertIn('Reinforcement', schedule[2]['task'])

        # Day 4: Final milestone consolidation towards user goal
        self.assertEqual(schedule[3]['day_number'], 4)
        self.assertIn('Milestone Consolidation', schedule[3]['task'])
        self.assertIn('Learn Python basics', schedule[3]['task'])

    def test_13_allocation_when_days_less_than_topics(self):
        """Verify topic allocation when duration_days < len(topics)."""
        topics = [
            {'id': 1, 'topic_name': 'Topic A', 'difficulty': 'Beginner'},
            {'id': 2, 'topic_name': 'Topic B', 'difficulty': 'Beginner'},
            {'id': 3, 'topic_name': 'Topic C', 'difficulty': 'Intermediate'},
            {'id': 4, 'topic_name': 'Topic D', 'difficulty': 'Intermediate'}
        ]
        # 4 topics across 2 days -> 2 topics per day
        schedule = generate_plan_schedule(
            subject_name='Algorithms',
            topics=topics,
            duration_days=2,
            skill_level='Intermediate',
            goal='Sprint learning',
            preferred_study_time='Evening'
        )

        self.assertEqual(len(schedule), 2)
        # Day 1 should cover Topic A and Topic B
        self.assertIn('Topic A', schedule[0]['task'])
        self.assertIn('Topic B', schedule[0]['task'])

        # Day 2 should cover Topic C and Topic D
        self.assertIn('Topic C', schedule[1]['task'])
        self.assertIn('Topic D', schedule[1]['task'])

    def test_14_skill_level_influences_tasks(self):
        """Verify skill level influences the wording and pedagogy of generated tasks."""
        topic = [{'id': 1, 'topic_name': 'Object-Oriented Programming', 'difficulty': 'Intermediate'}]

        beg_schedule = generate_plan_schedule('Python', topic, 1, 'Beginner', 'Goal', 'Flexible')
        mid_schedule = generate_plan_schedule('Python', topic, 1, 'Intermediate', 'Goal', 'Flexible')
        adv_schedule = generate_plan_schedule('Python', topic, 1, 'Advanced', 'Goal', 'Flexible')

        # Beginner focuses on foundations & syntax
        self.assertIn("Foundations & Syntax", beg_schedule[0]['task'])

        # Intermediate focuses on applied implementation
        self.assertIn("Applied Implementation", mid_schedule[0]['task'])

        # Advanced focuses on deep dive & internals
        self.assertIn("Deep Dive & Mastery", adv_schedule[0]['task'])

    # -------------------------------------------------------------------------
    # 5. Detail View and Task Schedule Display Tests
    # -------------------------------------------------------------------------
    def test_15_study_plan_detail_displays_tasks(self):
        """Verify study plan detail page displays all daily tasks and metadata."""
        user_id = self._create_and_login_user()
        payload = {
            'subject_id': '1',
            'topic_ids': ['1', '2'],
            'duration_days': '3',
            'goal': 'Exam preparation sprint',
            'skill_level': 'Beginner',
            'preferred_study_time': 'Morning'
        }
        self.client.post('/study-plans/create', data=payload)
        plans = get_user_study_plans(user_id)
        plan_id = plans[0]['id']

        response = self.client.get(f'/study-plans/{plan_id}')
        self.assertEqual(response.status_code, 200)
        content = response.data.decode('utf-8')
        self.assertIn("Exam preparation sprint", content)
        self.assertIn("Python Programming", content)
        self.assertIn("3 Days Duration", content)
        self.assertIn("DAY", content)

    def test_16_user_can_view_own_study_plan(self):
        """Verify user can view their own study plan detail (HTTP 200)."""
        user_id = self._create_and_login_user()
        _, _, plan_id = create_study_plan(
            user_id=user_id,
            subject_id=1,
            topic_ids=[1],
            duration_days=3,
            goal="Personal mastery"
        )
        response = self.client.get(f'/study-plans/{plan_id}')
        self.assertEqual(response.status_code, 200)

    # -------------------------------------------------------------------------
    # 6. User Isolation and Security Tests
    # -------------------------------------------------------------------------
    def test_17_user_cannot_view_another_user_plan(self):
        """Verify Student B CANNOT view Student A's study plan (isolation enforced)."""
        # Create Student A with plan
        user_a_id = self._create_and_login_user(email="test_sp_a@example.com", name="Student A")
        _, _, plan_a_id = create_study_plan(
            user_id=user_a_id,
            subject_id=1,
            topic_ids=[1],
            duration_days=3,
            goal="Private Plan A"
        )

        # Log in as Student B
        self._create_and_login_user(email="test_sp_b@example.com", name="Student B")

        # Student B attempts to access Student A's plan
        response = self.client.get(f'/study-plans/{plan_a_id}')
        self.assertEqual(response.status_code, 404)

        # Also verify API endpoint rejects unauthorized access
        api_res = self.client.get(f'/api/study-plans/{plan_a_id}')
        self.assertEqual(api_res.status_code, 404)

    # -------------------------------------------------------------------------
    # 7. Task Completion Toggle Tests
    # -------------------------------------------------------------------------
    def test_18_user_can_toggle_task_completion(self):
        """Verify student can mark a task complete (0 -> 1)."""
        user_id = self._create_and_login_user()
        _, _, plan_id = create_study_plan(
            user_id=user_id,
            subject_id=1,
            topic_ids=[1],
            duration_days=2,
            goal="Toggle test"
        )
        detail = get_study_plan_detail(plan_id, user_id)
        item_id = detail['items'][0]['id']
        self.assertFalse(detail['items'][0]['completed'])

        # Toggle item
        res = self.client.post(f'/api/study-plans/{plan_id}/items/{item_id}/toggle')
        self.assertEqual(res.status_code, 200)
        json_data = res.get_json()
        self.assertTrue(json_data['data']['completed'])
        self.assertEqual(json_data['data']['completed_tasks'], 1)

        # Verify DB directly
        detail_after = get_study_plan_detail(plan_id, user_id)
        self.assertTrue(detail_after['items'][0]['completed'])

    def test_19_user_can_untoggle_task_completion(self):
        """Verify student can mark a completed task as incomplete (1 -> 0)."""
        user_id = self._create_and_login_user()
        _, _, plan_id = create_study_plan(
            user_id=user_id,
            subject_id=1,
            topic_ids=[1],
            duration_days=2,
            goal="Untoggle test"
        )
        detail = get_study_plan_detail(plan_id, user_id)
        item_id = detail['items'][0]['id']

        # Toggle to True
        toggle_task_completion(plan_id, item_id, user_id, state=True)

        # Now untoggle via endpoint
        res = self.client.post(f'/api/study-plans/{plan_id}/items/{item_id}/toggle')
        self.assertEqual(res.status_code, 200)
        json_data = res.get_json()
        self.assertFalse(json_data['data']['completed'])

        # Verify DB directly
        detail_after = get_study_plan_detail(plan_id, user_id)
        self.assertFalse(detail_after['items'][0]['completed'])

    def test_20_user_cannot_toggle_another_user_task(self):
        """Verify Student B CANNOT toggle tasks on Student A's study plan."""
        # Student A creates plan
        user_a_id = self._create_and_login_user(email="test_sp_a2@example.com", name="Student A2")
        _, _, plan_a_id = create_study_plan(user_a_id, 1, [1], 2, "Goal A")
        item_id = get_study_plan_detail(plan_a_id, user_a_id)['items'][0]['id']

        # Student B logs in
        self._create_and_login_user(email="test_sp_b2@example.com", name="Student B2")

        # Student B attempts to toggle Student A's task
        res = self.client.post(f'/api/study-plans/{plan_a_id}/items/{item_id}/toggle')
        self.assertEqual(res.status_code, 404)

        # Verify task completion remains unchanged in DB
        detail = get_study_plan_detail(plan_a_id, user_a_id)
        self.assertFalse(detail['items'][0]['completed'])

    # -------------------------------------------------------------------------
    # 8. Plan Edit and User Isolation Tests
    # -------------------------------------------------------------------------
    def test_21_user_can_edit_own_study_plan(self):
        """Verify student can edit their study plan details."""
        user_id = self._create_and_login_user()
        _, _, plan_id = create_study_plan(user_id, 1, [1], 3, "Original Goal", "Beginner", "Flexible")

        payload = {
            'goal': 'Updated Academic Target',
            'skill_level': 'Intermediate',
            'preferred_study_time': 'Night',
            'duration_days': '5',
            'topic_ids': ['1', '2']
        }
        response = self.client.post(f'/study-plans/{plan_id}/edit', data=payload, follow_redirects=False)
        self.assertEqual(response.status_code, 302)

        # Verify updates in DB
        detail = get_study_plan_detail(plan_id, user_id)
        self.assertEqual(detail['plan']['goal'], 'Updated Academic Target')
        self.assertEqual(detail['plan']['skill_level'], 'Intermediate')
        self.assertEqual(detail['plan']['preferred_study_time'], 'Night')
        self.assertEqual(detail['plan']['duration_days'], 5)
        self.assertEqual(len(detail['items']), 5)

    def test_22_user_cannot_edit_another_user_plan(self):
        """Verify Student B CANNOT edit Student A's study plan."""
        user_a_id = self._create_and_login_user(email="test_sp_a3@example.com", name="Student A3")
        _, _, plan_a_id = create_study_plan(user_a_id, 1, [1], 3, "Goal A")

        # Student B logs in
        self._create_and_login_user(email="test_sp_b3@example.com", name="Student B3")

        # Student B attempts GET edit form
        res_get = self.client.get(f'/study-plans/{plan_a_id}/edit')
        self.assertEqual(res_get.status_code, 404)

        # Student B attempts POST update
        res_post = self.client.post(f'/study-plans/{plan_a_id}/edit', data={
            'goal': 'Malicious Edit',
            'skill_level': 'Advanced',
            'preferred_study_time': 'Night'
        })
        self.assertEqual(res_post.status_code, 404)

        # Verify Student A's plan remains unchanged
        detail = get_study_plan_detail(plan_a_id, user_a_id)
        self.assertEqual(detail['plan']['goal'], "Goal A")

    # -------------------------------------------------------------------------
    # 9. Plan Deletion Tests
    # -------------------------------------------------------------------------
    def test_23_user_can_delete_own_study_plan(self):
        """Verify student can delete their own study plan, cascading all items."""
        user_id = self._create_and_login_user()
        _, _, plan_id = create_study_plan(user_id, 1, [1], 3, "Plan to delete")
        self.assertEqual(len(get_user_study_plans(user_id)), 1)

        response = self.client.post(f'/study-plans/{plan_id}/delete', follow_redirects=False)
        self.assertEqual(response.status_code, 302)

        # Verify plan is gone from DB
        self.assertEqual(len(get_user_study_plans(user_id)), 0)
        self.assertIsNone(get_study_plan_detail(plan_id, user_id))

        # Verify items were cascaded
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) AS count FROM study_plan_items WHERE study_plan_id = %s", (plan_id,))
                count = cursor.fetchone()['count']
                self.assertEqual(count, 0)
        finally:
            conn.close()

    def test_24_user_cannot_delete_another_user_plan(self):
        """Verify Student B CANNOT delete Student A's study plan."""
        user_a_id = self._create_and_login_user(email="test_sp_a4@example.com", name="Student A4")
        _, _, plan_a_id = create_study_plan(user_a_id, 1, [1], 3, "Protected Plan A")

        # Student B logs in
        self._create_and_login_user(email="test_sp_b4@example.com", name="Student B4")

        # Student B attempts deletion
        response = self.client.post(f'/study-plans/{plan_a_id}/delete')
        self.assertEqual(response.status_code, 404)

        # Verify Student A's plan still exists intact
        self.assertEqual(len(get_user_study_plans(user_a_id)), 1)

    # -------------------------------------------------------------------------
    # 10. Dashboard Integration Test
    # -------------------------------------------------------------------------
    def test_25_dashboard_displays_real_study_plan_data(self):
        """Verify /dashboard accurately displays authentic study plans and real completion stats."""
        user_id = self._create_and_login_user()

        # Step 1: Empty state
        res_empty = self.client.get('/dashboard')
        self.assertEqual(res_empty.status_code, 200)
        self.assertIn(b"You haven't generated any study plans yet", res_empty.data)

        # Step 2: Create a plan with 3 tasks
        _, _, plan_id = create_study_plan(user_id, 1, [1], 3, "Comprehensive Math Study")
        detail = get_study_plan_detail(plan_id, user_id)
        item_id = detail['items'][0]['id']

        # Complete 1 task
        toggle_task_completion(plan_id, item_id, user_id, state=True)

        # Step 3: Refresh dashboard
        res_populated = self.client.get('/dashboard')
        self.assertEqual(res_populated.status_code, 200)
        content = res_populated.data.decode('utf-8')

        self.assertIn("Comprehensive Math Study", content)
        self.assertIn("1 / 3", content)  # 1 of 3 tasks completed
        self.assertIn("33%", content)
        self.assertIn("Total Plans", content)


if __name__ == '__main__':
    unittest.main()

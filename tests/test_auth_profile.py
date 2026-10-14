"""
Automated Test Suite for Phase 2 - Authentication & Student Profile.
AI Student Learning Mentor.

Verifies:
1. Successful registration
2. Duplicate email rejection
3. Password hashing (never stored in plain text)
4. Successful login
5. Wrong password rejection
6. Unknown email rejection
7. Logout clears session
8. Dashboard requires authentication
9. Profile requires authentication
10. User can create profile
11. User can update profile
12. User can retrieve own profile
13. User cannot access another user's profile
14. Session information is handled correctly
15. No password/secret leakage
"""
import unittest
from werkzeug.security import check_password_hash
from app import create_app
from config import Config
from services.db import get_db_connection
from services.auth_service import register_user, authenticate_user
from services.profile_service import get_student_profile, upsert_student_profile


class TestPhase2AuthProfile(unittest.TestCase):
    """Test suite covering all Phase 2 Authentication and Student Profile requirements."""

    @classmethod
    def setUpClass(cls):
        """Set up Flask test application and client."""
        cls.app = create_app()
        cls.client = cls.app.test_client()

    def setUp(self):
        """Clean up test records and reset test client before each test."""
        self.client = self.app.test_client()
        self._cleanup_test_data()

    def tearDown(self):
        """Clean up test records after each test."""
        self._cleanup_test_data()

    def _cleanup_test_data(self):
        """Helper to remove test users created during test executions."""
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    "DELETE FROM users WHERE email LIKE %s",
                    ('test_%@example.com',)
                )
        finally:
            conn.close()

    # 1. Successful registration
    def test_01_successful_registration(self):
        """Verify user registration creates record and redirects to login."""
        response = self.client.post('/register', data={
            'name': 'Test Student',
            'email': 'test_student1@example.com',
            'password': 'SecurePassword123!',
            'confirm_password': 'SecurePassword123!'
        }, follow_redirects=False)

        self.assertEqual(response.status_code, 302)
        self.assertIn('/login', response.headers.get('Location', ''))

        # Verify record exists in MySQL
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT id, name, email FROM users WHERE email = %s",
                    ('test_student1@example.com',)
                )
                user = cursor.fetchone()
                self.assertIsNotNone(user)
                self.assertEqual(user['name'], 'Test Student')
        finally:
            conn.close()

    # 2. Duplicate email rejection
    def test_02_duplicate_email_rejection(self):
        """Verify duplicate email registration is rejected with HTTP 400 and error message."""
        # First registration
        register_user("Initial User", "test_duplicate@example.com", "Password123!")

        # Duplicate registration attempt
        response = self.client.post('/register', data={
            'name': 'Duplicate User',
            'email': 'test_duplicate@example.com',
            'password': 'Password123!',
            'confirm_password': 'Password123!'
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 400)
        html = response.get_data(as_text=True)
        self.assertIn("already exists", html.lower())

    # 3. Password hashing
    def test_03_password_hashing(self):
        """Verify password is encrypted using Werkzeug hashing and never stored in plain text."""
        raw_password = "MyPlainSecretPassword123"
        success, msg, user_id = register_user("Hash Student", "test_hash@example.com", raw_password)
        self.assertTrue(success)

        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT password_hash FROM users WHERE id = %s",
                    (user_id,)
                )
                user = cursor.fetchone()
                stored_hash = user['password_hash']

                # Stored password must NOT be plain text
                self.assertNotEqual(stored_hash, raw_password)
                self.assertNotIn(raw_password, stored_hash)

                # Must be a recognized secure hash format
                self.assertTrue(
                    stored_hash.startswith(('scrypt:', 'pbkdf2:')),
                    f"Unexpected hash format: {stored_hash[:20]}"
                )

                # Werkzeug verification must succeed
                self.assertTrue(check_password_hash(stored_hash, raw_password))
        finally:
            conn.close()

    # 4. Successful login
    def test_04_successful_login(self):
        """Verify valid credentials authenticate successfully and set user session."""
        register_user("Login Student", "test_login@example.com", "ValidPass123!")

        with self.client as client:
            response = client.post('/login', data={
                'email': 'test_login@example.com',
                'password': 'ValidPass123!'
            }, follow_redirects=False)

            self.assertEqual(response.status_code, 302)
            self.assertIn('/dashboard', response.headers.get('Location', ''))

            # Verify session data
            from flask import session
            self.assertIn('user_id', session)
            self.assertEqual(session.get('user_name'), "Login Student")
            self.assertEqual(session.get('user_email'), "test_login@example.com")

    # 5. Wrong password rejection
    def test_05_wrong_password_rejection(self):
        """Verify invalid password attempt returns 401 and does not create session."""
        register_user("Wrong Pass Student", "test_wrongpass@example.com", "CorrectPassword123!")

        with self.client as client:
            response = client.post('/login', data={
                'email': 'test_wrongpass@example.com',
                'password': 'WrongPassword999!'
            }, follow_redirects=True)

            self.assertEqual(response.status_code, 401)
            html = response.get_data(as_text=True)
            self.assertIn("Invalid email or password", html)

            from flask import session
            self.assertNotIn('user_id', session)

    # 6. Unknown email rejection
    def test_06_unknown_email_rejection(self):
        """Verify login attempt with unregistered email returns 401."""
        with self.client as client:
            response = client.post('/login', data={
                'email': 'test_nonexistent@example.com',
                'password': 'SomePassword123!'
            }, follow_redirects=True)

            self.assertEqual(response.status_code, 401)
            html = response.get_data(as_text=True)
            self.assertIn("Invalid email or password", html)

            from flask import session
            self.assertNotIn('user_id', session)

    # 7. Logout clears session
    def test_07_logout_clears_session(self):
        """Verify logout endpoint clears user session and redirects to login."""
        register_user("Logout Student", "test_logout@example.com", "LogoutPass123!")

        with self.client as client:
            # First log in
            client.post('/login', data={
                'email': 'test_logout@example.com',
                'password': 'LogoutPass123!'
            })

            from flask import session
            self.assertIn('user_id', session)

            # Now log out
            logout_resp = client.get('/logout', follow_redirects=False)
            self.assertEqual(logout_resp.status_code, 302)

            # Verify session was cleared
            self.assertNotIn('user_id', session)

    # 8. Dashboard requires authentication
    def test_08_dashboard_requires_authentication(self):
        """Verify unauthenticated access to /dashboard is blocked and redirected to login."""
        response = self.client.get('/dashboard', follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login', response.headers.get('Location', ''))

    # 9. Profile requires authentication
    def test_09_profile_requires_authentication(self):
        """Verify unauthenticated access to /profile is blocked and redirected to login."""
        response = self.client.get('/profile', follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login', response.headers.get('Location', ''))

    # 10. User can create profile
    def test_10_user_can_create_profile(self):
        """Verify logged-in student can create their profile fields."""
        _, _, user_id = register_user("Profile Creator", "test_profile_create@example.com", "Pass123!")

        with self.client as client:
            # Authenticate session
            with client.session_transaction() as sess:
                sess['user_id'] = user_id
                sess['user_name'] = "Profile Creator"
                sess['user_email'] = "test_profile_create@example.com"
                sess['user_role'] = "student"

            response = client.post('/profile', data={
                'education_level': 'Undergraduate',
                'course': 'Computer Science & Engineering',
                'semester': 'Semester 4',
                'skill_level': 'Intermediate',
                'preferred_study_time': 'Evening (5 PM - 9 PM)',
                'learning_goal': 'Master Graph Algorithms and Dynamic Programming.'
            }, follow_redirects=False)

            self.assertEqual(response.status_code, 302)

            # Verify profile in database
            profile = get_student_profile(user_id)
            self.assertIsNotNone(profile)
            self.assertEqual(profile['education_level'], 'Undergraduate')
            self.assertEqual(profile['course'], 'Computer Science & Engineering')
            self.assertEqual(profile['semester'], 'Semester 4')
            self.assertEqual(profile['skill_level'], 'Intermediate')
            self.assertEqual(profile['preferred_study_time'], 'Evening (5 PM - 9 PM)')
            self.assertEqual(profile['learning_goal'], 'Master Graph Algorithms and Dynamic Programming.')

    # 11. User can update profile
    def test_11_user_can_update_profile(self):
        """Verify logged-in student can update existing profile data."""
        _, _, user_id = register_user("Profile Updater", "test_profile_update@example.com", "Pass123!")

        # Initial profile
        upsert_student_profile(user_id, {
            'education_level': 'High School',
            'course': 'General Science',
            'semester': 'Grade 11',
            'skill_level': 'Beginner',
            'learning_goal': 'Learn basic programming.',
            'preferred_study_time': 'Morning (6 AM - 12 PM)'
        })

        with self.client as client:
            with client.session_transaction() as sess:
                sess['user_id'] = user_id
                sess['user_name'] = "Profile Updater"
                sess['user_email'] = "test_profile_update@example.com"

            # Update profile
            response = client.post('/profile', data={
                'education_level': 'Undergraduate',
                'course': 'Software Engineering',
                'semester': 'Year 1',
                'skill_level': 'Intermediate',
                'learning_goal': 'Build production-ready web apps.',
                'preferred_study_time': 'Night (9 PM - 2 AM)'
            }, follow_redirects=False)

            self.assertEqual(response.status_code, 302)

            # Check updated record
            updated_profile = get_student_profile(user_id)
            self.assertEqual(updated_profile['education_level'], 'Undergraduate')
            self.assertEqual(updated_profile['course'], 'Software Engineering')
            self.assertEqual(updated_profile['skill_level'], 'Intermediate')
            self.assertEqual(updated_profile['learning_goal'], 'Build production-ready web apps.')

    # 12. User can retrieve own profile
    def test_12_user_can_retrieve_own_profile(self):
        """Verify student's saved profile renders correctly on dashboard and profile pages."""
        _, _, user_id = register_user("Retrieve Student", "test_retrieve@example.com", "Pass123!")
        upsert_student_profile(user_id, {
            'education_level': 'Undergraduate',
            'course': 'Artificial Intelligence Specialization',
            'semester': 'Semester 6',
            'skill_level': 'Advanced',
            'learning_goal': 'Prepare for machine learning engineer certifications.',
            'preferred_study_time': 'Morning (6 AM - 12 PM)'
        })

        with self.client as client:
            with client.session_transaction() as sess:
                sess['user_id'] = user_id
                sess['user_name'] = "Retrieve Student"
                sess['user_email'] = "test_retrieve@example.com"

            # Check /profile
            prof_resp = client.get('/profile')
            self.assertEqual(prof_resp.status_code, 200)
            prof_html = prof_resp.get_data(as_text=True)
            self.assertIn("Artificial Intelligence Specialization", prof_html)
            self.assertIn("Prepare for machine learning engineer certifications.", prof_html)

            # Check /dashboard
            dash_resp = client.get('/dashboard')
            self.assertEqual(dash_resp.status_code, 200)
            dash_html = dash_resp.get_data(as_text=True)
            self.assertIn("Artificial Intelligence Specialization", dash_html)
            self.assertIn("Retrieve Student", dash_html)
            self.assertIn("Advanced", dash_html)

    # 13. User cannot access another user's profile
    def test_13_user_cannot_access_another_profile(self):
        """Verify student A only receives their own profile and cannot view/edit student B's profile."""
        _, _, user_a_id = register_user("Student Alpha", "test_alpha@example.com", "PassA123!")
        _, _, user_b_id = register_user("Student Beta", "test_beta@example.com", "PassB123!")

        upsert_student_profile(user_a_id, {
            'course': 'Alpha Confidential Course',
            'learning_goal': 'Alpha Secret Goal'
        })
        upsert_student_profile(user_b_id, {
            'course': 'Beta Confidential Course',
            'learning_goal': 'Beta Secret Goal'
        })

        with self.client as client:
            # Log in as Student Alpha
            with client.session_transaction() as sess:
                sess['user_id'] = user_a_id
                sess['user_name'] = "Student Alpha"
                sess['user_email'] = "test_alpha@example.com"

            # Access dashboard and profile
            resp_dash = client.get('/dashboard')
            html_dash = resp_dash.get_data(as_text=True)
            self.assertIn("Alpha Confidential Course", html_dash)
            self.assertNotIn("Beta Confidential Course", html_dash)

            resp_prof = client.get('/profile')
            html_prof = resp_prof.get_data(as_text=True)
            self.assertIn("Alpha Confidential Course", html_prof)
            self.assertNotIn("Beta Confidential Course", html_prof)

    # 14. Session information is handled correctly
    def test_14_session_handling(self):
        """Verify session data persists across authenticated requests and terminates on logout."""
        _, _, user_id = register_user("Session Student", "test_session@example.com", "SessionPass123!")

        with self.client as client:
            login_resp = client.post('/login', data={
                'email': 'test_session@example.com',
                'password': 'SessionPass123!'
            })
            self.assertEqual(login_resp.status_code, 302)

            # Check that authenticated route succeeds with session
            dash_resp = client.get('/dashboard')
            self.assertEqual(dash_resp.status_code, 200)

            # Log out
            client.get('/logout')

            # Check that subsequent access to dashboard is blocked
            after_logout_resp = client.get('/dashboard')
            self.assertEqual(after_logout_resp.status_code, 302)
            self.assertIn('/login', after_logout_resp.headers.get('Location', ''))

    # 15. No password/secret leakage
    def test_15_no_password_or_secret_leakage(self):
        """Verify plain passwords, password hashes, and SECRET_KEY are never exposed in responses."""
        secret_pass = "SuperSecretPlainTextPassword!#123"
        _, _, user_id = register_user("Leak Check", "test_leak@example.com", secret_pass)

        # 1. Check register page
        reg_resp = self.client.get('/register')
        self.assertNotIn(secret_pass, reg_resp.get_data(as_text=True))
        self.assertNotIn(Config.SECRET_KEY, reg_resp.get_data(as_text=True))

        # 2. Check login page
        login_resp = self.client.get('/login')
        self.assertNotIn(secret_pass, login_resp.get_data(as_text=True))
        self.assertNotIn(Config.SECRET_KEY, login_resp.get_data(as_text=True))

        # 3. Check authenticated dashboard and profile
        with self.client as client:
            with client.session_transaction() as sess:
                sess['user_id'] = user_id
                sess['user_name'] = "Leak Check"
                sess['user_email'] = "test_leak@example.com"

            dash_text = client.get('/dashboard').get_data(as_text=True)
            self.assertNotIn(secret_pass, dash_text)
            self.assertNotIn(Config.SECRET_KEY, dash_text)
            self.assertNotIn("pbkdf2:", dash_text)
            self.assertNotIn("scrypt:", dash_text)

            prof_text = client.get('/profile').get_data(as_text=True)
            self.assertNotIn(secret_pass, prof_text)
            self.assertNotIn(Config.SECRET_KEY, prof_text)
            self.assertNotIn("pbkdf2:", prof_text)
            self.assertNotIn("scrypt:", prof_text)


if __name__ == '__main__':
    unittest.main()

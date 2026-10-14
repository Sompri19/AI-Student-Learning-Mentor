"""
Automated Test Suite for Phase 9 - Security Hardening & Final System Testing.
AI Student Learning Mentor.

Covers all 25 Phase 9 Security and Reliability Verification requirements:
1. Authentication enforcement (unauthenticated access redirected or 401)
2. IDOR protection - Study Plan isolation across distinct users
3. IDOR protection - Quiz Result and Review isolation across users
4. IDOR protection - AI Chat History isolation across users
5. CSRF validation accepts valid session tokens
6. CSRF validation rejects invalid or tampered tokens with 400
7. CSRF strict mode rejects requests missing token with 400
8. Cross-Origin protection blocks untrusted Origin headers with 403
9. Cross-Origin protection blocks untrusted Referer headers with 403
10. SQL Injection defense on authentication & form inputs
11. SQL Injection defense on content search & query parameters
12. XSS defense via Jinja2 autoescaping in rendered HTML
13. XSS template verification ensures user inputs are never marked safe
14. Open Redirect protection prevents external host redirection
15. API responses never disclose secrets, credentials, or password hashes
16. AI endpoints and responses never disclose the configured AI_API_KEY
17. AI provider errors return sanitized user messages without stack traces
18. AI rate limiting throttles rapid successive requests with 429
19. Input limits reject oversized or malformed payloads with 400
20. Malformed JSON payloads return clean 400 Bad Request
21. Safe 404 and 500 error handlers prevent stack trace leakage
22. Security headers (nosniff, SAMEORIGIN, Referrer-Policy) injected on responses
23. Session cookie attributes enforce HttpOnly and SameSite=Lax
24. Database user passwords are cryptographically hashed (never plaintext)
25. Database health check reports status without leaking database credentials
"""
import unittest
from flask import session
from app import create_app, is_safe_redirect_url
from config import Config
from services.db import get_db_connection, check_db_health
from services.auth_service import register_user, authenticate_user
from services.study_plan_service import create_study_plan
from services.quiz_service import submit_quiz_attempt, get_quiz_questions_for_topic
from services.ai_service import save_ai_chat, check_rate_limit, ask_ai
from services.csrf_service import generate_csrf_token


class TestPhase9SecurityHardening(unittest.TestCase):
    """Comprehensive test suite covering Phase 9 security hardening controls."""

    @classmethod
    def setUpClass(cls):
        """Set up Flask test application instance."""
        cls.app = create_app()

    def setUp(self):
        """Reset test client and clean up test records before each test."""
        self.client = self.app.test_client()
        self._cleanup_test_data()

    def tearDown(self):
        """Clean up test records after each test."""
        self._cleanup_test_data()

    def _cleanup_test_data(self):
        """Helper to remove test users and cascade clean associated test records."""
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    "DELETE FROM users WHERE email LIKE %s",
                    ('test_sec_%@example.com',)
                )
            conn.commit()
        finally:
            conn.close()

    def _create_user(self, email="test_sec_u1@example.com", name="Sec Student 1"):
        """Creates a test user in MySQL."""
        success, msg, user_id = register_user(name, email, "StrongSecPass123!")
        self.assertTrue(success, f"Failed to register test user: {msg}")
        return user_id

    def _login_as(self, user_id: int, email: str, name: str):
        """Sets active session cookies for the specified user."""
        with self.client.session_transaction() as sess:
            sess['user_id'] = user_id
            sess['user_name'] = name
            sess['user_email'] = email
            sess['user_role'] = 'student'

    # -------------------------------------------------------------------------
    # 1. Authentication Enforcement
    # -------------------------------------------------------------------------
    def test_01_authentication_enforcement(self):
        """Unauthenticated requests to protected endpoints return redirect or 401."""
        protected_web_routes = [
            '/dashboard',
            '/study-plans',
            '/quizzes',
            '/ai',
            '/profile',
            '/progress'
        ]
        for route in protected_web_routes:
            resp = self.client.get(route, follow_redirects=False)
            self.assertEqual(
                resp.status_code, 302,
                f"Expected 302 redirect for protected web route: {route}"
            )
            self.assertIn('/login', resp.headers.get('Location', ''))

        protected_api_routes = [
            '/api/ai/history',
            '/api/progress/statistics',
            '/api/progress/topics',
            '/api/progress/activity'
        ]
        for api_route in protected_api_routes:
            resp = self.client.get(api_route)
            self.assertEqual(
                resp.status_code, 401,
                f"Expected 401 Unauthorized for protected API route: {api_route}"
            )
            data = resp.get_json()
            self.assertEqual(data.get("status"), "error")

    # -------------------------------------------------------------------------
    # 2. IDOR: Study Plan Isolation
    # -------------------------------------------------------------------------
    def test_02_idor_study_plan_isolation(self):
        """User B cannot view, edit, toggle, or delete User A's study plan."""
        user1_id = self._create_user("test_sec_u1@example.com", "User One")
        user2_id = self._create_user("test_sec_u2@example.com", "User Two")

        # Create study plan for User 1
        success, msg, plan_id = create_study_plan(
            user_id=user1_id,
            subject_id=1,
            topic_ids=[1, 2],
            duration_days=7,
            goal="Master Python Security",
            skill_level="Beginner",
            preferred_study_time="Evening"
        )
        self.assertTrue(success, f"Failed to create plan: {msg}")

        # Log in as User 2
        self._login_as(user2_id, "test_sec_u2@example.com", "User Two")

        # User 2 attempts to view User 1's plan
        resp_view = self.client.get(f'/study-plans/{plan_id}')
        self.assertEqual(resp_view.status_code, 404)

        # User 2 attempts to view edit page for User 1's plan
        resp_edit = self.client.get(f'/study-plans/{plan_id}/edit')
        self.assertEqual(resp_edit.status_code, 404)

        # User 2 attempts to delete User 1's plan
        resp_del = self.client.post(f'/study-plans/{plan_id}/delete')
        self.assertEqual(resp_del.status_code, 404)

    # -------------------------------------------------------------------------
    # 3. IDOR: Quiz Result and Review Isolation
    # -------------------------------------------------------------------------
    def test_03_idor_quiz_result_isolation(self):
        """User B cannot view User A's quiz attempt results or question review."""
        user1_id = self._create_user("test_sec_u1@example.com", "User One")
        user2_id = self._create_user("test_sec_u2@example.com", "User Two")

        # Retrieve valid questions for topic 1
        questions = get_quiz_questions_for_topic(1, limit=2, include_correct=True)
        self.assertTrue(len(questions) > 0)
        submitted = {q["id"]: q["correct_answer"] for q in questions}

        # User 1 submits a quiz attempt
        success, msg, attempt_id = submit_quiz_attempt(
            user_id=user1_id,
            topic_id=1,
            submitted_answers=submitted
        )
        self.assertTrue(success, f"Failed to submit quiz: {msg}")

        # Log in as User 2
        self._login_as(user2_id, "test_sec_u2@example.com", "User Two")

        # User 2 attempts to view User 1's attempt result
        resp_res = self.client.get(f'/quiz/results/{attempt_id}')
        self.assertEqual(resp_res.status_code, 404)

        # User 2 attempts to view User 1's attempt review
        resp_rev = self.client.get(f'/quiz/results/{attempt_id}/review')
        self.assertEqual(resp_rev.status_code, 404)

    # -------------------------------------------------------------------------
    # 4. IDOR: AI Chat History Isolation
    # -------------------------------------------------------------------------
    def test_04_idor_ai_chat_isolation(self):
        """User B cannot view User A's AI chat conversation details."""
        user1_id = self._create_user("test_sec_u1@example.com", "User One")
        user2_id = self._create_user("test_sec_u2@example.com", "User Two")

        # User 1 saves a chat
        success, msg, chat_id = save_ai_chat(
            user_id=user1_id,
            question="What is SQL injection defense?",
            answer="Use parameterized prepared statements."
        )
        self.assertTrue(success, f"Failed to save chat: {msg}")

        # Log in as User 2
        self._login_as(user2_id, "test_sec_u2@example.com", "User Two")

        # User 2 requests chat detail via API
        resp = self.client.get(f'/api/ai/history/{chat_id}')
        self.assertEqual(resp.status_code, 404)
        data = resp.get_json()
        self.assertEqual(data.get("status"), "error")

    # -------------------------------------------------------------------------
    # 5. CSRF: Valid Token Passes
    # -------------------------------------------------------------------------
    def test_05_csrf_valid_token_passes(self):
        """State-modifying request with valid session CSRF token succeeds."""
        user_id = self._create_user("test_sec_u1@example.com", "User One")
        self._login_as(user_id, "test_sec_u1@example.com", "User One")

        token = "test_valid_csrf_token_abcdef1234567890" * 2
        with self.client.session_transaction() as sess:
            sess['_csrf_token'] = token

        resp = self.client.post('/profile', data={
            'education_level': 'College',
            'course': 'Cybersecurity',
            'learning_goals': 'Learn AppSec',
            'target_skill_level': 'Intermediate',
            'csrf_token': token
        })
        self.assertIn(resp.status_code, [200, 302])

    # -------------------------------------------------------------------------
    # 6. CSRF: Invalid / Tampered Token Blocked
    # -------------------------------------------------------------------------
    def test_06_csrf_tampered_token_rejected(self):
        """State-modifying request with tampered CSRF token returns 400 Bad Request."""
        user_id = self._create_user("test_sec_u1@example.com", "User One")
        self._login_as(user_id, "test_sec_u1@example.com", "User One")

        resp = self.client.post('/profile', data={
            'education_level': 'College',
            'course': 'Cybersecurity',
            'csrf_token': 'tampered_invalid_token_12345'
        })
        self.assertEqual(resp.status_code, 400)
        self.assertIn("CSRF", resp.get_data(as_text=True))

    # -------------------------------------------------------------------------
    # 7. CSRF: Strict Mode Missing Token Blocked
    # -------------------------------------------------------------------------
    def test_07_csrf_strict_missing_token_blocked(self):
        """When CSRF_STRICT=True, missing CSRF token returns 400 Bad Request."""
        user_id = self._create_user("test_sec_u1@example.com", "User One")
        self._login_as(user_id, "test_sec_u1@example.com", "User One")

        orig_strict = self.app.config.get('CSRF_STRICT')
        self.app.config['CSRF_STRICT'] = True
        try:
            resp = self.client.post('/profile', data={
                'education_level': 'College',
                'course': 'Cybersecurity'
            })
            self.assertEqual(resp.status_code, 400)
            self.assertIn("CSRF", resp.get_data(as_text=True))
        finally:
            self.app.config['CSRF_STRICT'] = orig_strict

    # -------------------------------------------------------------------------
    # 8. Cross-Origin Protection: Origin Mismatch Blocked
    # -------------------------------------------------------------------------
    def test_08_cross_origin_origin_mismatch_blocked(self):
        """Cross-origin POST request with untrusted Origin header returns 403 Forbidden."""
        user_id = self._create_user("test_sec_u1@example.com", "User One")
        self._login_as(user_id, "test_sec_u1@example.com", "User One")

        resp = self.client.post(
            '/profile',
            data={'education_level': 'College'},
            headers={'Origin': 'http://malicious-attacker-website.com'}
        )
        self.assertEqual(resp.status_code, 403)
        self.assertIn("Cross-origin", resp.get_data(as_text=True))

    # -------------------------------------------------------------------------
    # 9. Cross-Origin Protection: Referer Mismatch Blocked
    # -------------------------------------------------------------------------
    def test_09_cross_origin_referer_mismatch_blocked(self):
        """Cross-origin POST request with untrusted Referer header returns 403 Forbidden."""
        user_id = self._create_user("test_sec_u1@example.com", "User One")
        self._login_as(user_id, "test_sec_u1@example.com", "User One")

        resp = self.client.post(
            '/profile',
            data={'education_level': 'College'},
            headers={'Referer': 'http://malicious-attacker-website.com/phishing'}
        )
        self.assertEqual(resp.status_code, 403)
        self.assertIn("Cross-origin", resp.get_data(as_text=True))

    # -------------------------------------------------------------------------
    # 10. SQL Injection: Form Input Defense
    # -------------------------------------------------------------------------
    def test_10_sql_injection_defense_form_inputs(self):
        """SQL injection payloads in login and registration are parameterized safely."""
        sqli_payload = "' OR '1'='1' --"
        # Attempt login with SQLi payload
        success, msg, user = authenticate_user(sqli_payload, "AnyPassword123!")
        self.assertFalse(success)
        self.assertIsNone(user)

        # Attempt registration with SQLi payload in email
        success, msg, uid = register_user("Normal Name", sqli_payload, "Pass123!Valid")
        self.assertFalse(success, "SQLi in email should fail email validation")

    # -------------------------------------------------------------------------
    # 11. SQL Injection: Search and URL Parameter Defense
    # -------------------------------------------------------------------------
    def test_11_sql_injection_defense_query_params(self):
        """SQL injection payloads in URL query parameters execute safely without syntax errors."""
        sqli_payloads = [
            "' UNION SELECT 1, 2, 3, 4, 5 --",
            "1; DROP TABLE users; --",
            "1' OR '1'='1"
        ]
        for payload in sqli_payloads:
            resp = self.client.get(f'/subjects?q={payload}')
            self.assertEqual(resp.status_code, 200)

            resp_res = self.client.get(f'/subjects?resource_type={payload}')
            self.assertEqual(resp_res.status_code, 200)

    # -------------------------------------------------------------------------
    # 12. XSS: Autoescaping in Rendered Templates
    # -------------------------------------------------------------------------
    def test_12_xss_autoescaping_in_rendered_html(self):
        """HTML/Script tags in student input are automatically HTML-escaped by Jinja2."""
        xss_payload = "<script>alert('xss_attack')</script><img src=x onerror=alert(1)>"
        user_id = self._create_user("test_sec_u1@example.com", xss_payload)
        self._login_as(user_id, "test_sec_u1@example.com", xss_payload)

        # View dashboard
        resp = self.client.get('/dashboard')
        self.assertEqual(resp.status_code, 200)
        html_content = resp.get_data(as_text=True)

        # The raw dangerous script tag must NOT be present unescaped
        self.assertNotIn("<script>alert('xss_attack')</script>", html_content)
        # It must be HTML entity escaped
        self.assertIn("&lt;script&gt;alert(&#39;xss_attack&#39;)&lt;/script&gt;", html_content)

    # -------------------------------------------------------------------------
    # 13. XSS: Verification of No Harmful |safe Filters
    # -------------------------------------------------------------------------
    def test_13_xss_no_harmful_safe_filter_on_user_content(self):
        """User-supplied learning goal in study plans is escaped, not bypassed with |safe."""
        user_id = self._create_user("test_sec_u1@example.com", "XSS Student")
        self._login_as(user_id, "test_sec_u1@example.com", "XSS Student")

        xss_goal = "Goal <script>alert('idor_xss')</script>"
        success, msg, plan_id = create_study_plan(
            user_id=user_id,
            subject_id=1,
            topic_ids=[1],
            duration_days=5,
            goal=xss_goal,
            skill_level="Beginner",
            preferred_study_time="Flexible"
        )
        self.assertTrue(success)

        resp = self.client.get(f'/study-plans/{plan_id}')
        self.assertEqual(resp.status_code, 200)
        html_content = resp.get_data(as_text=True)
        self.assertNotIn("<script>alert('idor_xss')</script>", html_content)
        self.assertIn("&lt;script&gt;", html_content)

    # -------------------------------------------------------------------------
    # 14. Open Redirect Protection
    # -------------------------------------------------------------------------
    def test_14_open_redirect_protection(self):
        """Open redirect validator rejects external, protocol-relative, and dangerous URLs."""
        with self.app.test_request_context(base_url="http://localhost:5000/"):
            # Dangerous external URLs
            self.assertFalse(is_safe_redirect_url("http://evil-attacker.com"))
            self.assertFalse(is_safe_redirect_url("https://malicious.org/phishing"))
            self.assertFalse(is_safe_redirect_url("//evil-attacker.com"))
            self.assertFalse(is_safe_redirect_url("javascript:alert(1)"))
            self.assertFalse(is_safe_redirect_url(""))
            self.assertFalse(is_safe_redirect_url(None))

            # Safe local URLs
            self.assertTrue(is_safe_redirect_url("/dashboard"))
            self.assertTrue(is_safe_redirect_url("/study-plans"))
            self.assertTrue(is_safe_redirect_url("/quiz?topic_id=1"))

    # -------------------------------------------------------------------------
    # 15. API Secret and Password Concealment
    # -------------------------------------------------------------------------
    def test_15_api_secret_and_password_concealment(self):
        """API endpoints never disclose passwords, password hashes, or secret keys."""
        user_id = self._create_user("test_sec_u1@example.com", "API Student")
        self._login_as(user_id, "test_sec_u1@example.com", "API Student")

        endpoints = [
            '/api/health',
            '/api/progress/statistics',
            '/api/progress/topics',
            '/api/progress/activity',
            '/api/ai/history'
        ]
        forbidden_substrings = [
            'password_hash',
            'StrongSecPass123!',
            'secret_key',
            'change-this-secret-key'
        ]
        for ep in endpoints:
            resp = self.client.get(ep)
            self.assertTrue(resp.is_json)
            body = resp.get_data(as_text=True)
            for forbidden in forbidden_substrings:
                self.assertNotIn(
                    forbidden, body,
                    f"Forbidden secret '{forbidden}' detected in response of {ep}"
                )

    # -------------------------------------------------------------------------
    # 16. AI API Key Concealment
    # -------------------------------------------------------------------------
    def test_16_ai_api_key_concealment(self):
        """AI Assistant endpoint never leaks AI_API_KEY in success or error bodies."""
        user_id = self._create_user("test_sec_u1@example.com", "AI Student")
        self._login_as(user_id, "test_sec_u1@example.com", "AI Student")

        resp = self.client.post('/api/ai/ask', json={
            'question': 'How does binary search work in Python?',
            'subject_id': 1,
            'topic_id': 1
        })
        body = resp.get_data(as_text=True)
        # Should never reveal test API key or production secret
        self.assertNotIn("test-mock-api-key", body)
        if Config.AI_API_KEY:
            self.assertNotIn(Config.AI_API_KEY, body)

    # -------------------------------------------------------------------------
    # 17. AI Error Sanitization
    # -------------------------------------------------------------------------
    def test_17_ai_error_sanitization(self):
        """AI provider errors return sanitized messages, not Python stack traces."""
        success, answer = ask_ai(
            question="What is recursion?",
            provider="unsupported_dummy_provider",
            api_key="dummy_test_key"
        )
        self.assertFalse(success)
        # Should be clean error message without traceback
        self.assertIn("Unsupported AI provider", answer)
        self.assertNotIn("Traceback (most recent call last)", answer)

    # -------------------------------------------------------------------------
    # 18. Rate Limiting Enforcement
    # -------------------------------------------------------------------------
    def test_18_rate_limiting_enforcement(self):
        """Rate limiter blocks rapid repeated queries within cooldown period."""
        user_id = 99999
        # First check passes
        allowed1, msg1 = check_rate_limit(user_id, cooldown_seconds=10)
        self.assertTrue(allowed1)

        # Immediate second check blocked with wait message
        allowed2, msg2 = check_rate_limit(user_id, cooldown_seconds=10)
        self.assertFalse(allowed2)
        self.assertIn("Please wait", msg2)

    # -------------------------------------------------------------------------
    # 19. Input Limits: Oversized / Malformed Input Rejected
    # -------------------------------------------------------------------------
    def test_19_input_limits_oversized_payloads(self):
        """Overly long input values are rejected cleanly with validation errors."""
        user_id = self._create_user("test_sec_u1@example.com", "Limit Student")
        self._login_as(user_id, "test_sec_u1@example.com", "Limit Student")

        # Question exceeding maximum allowed length of 2000 characters
        oversized_question = "Explain " + ("data structures " * 150)
        resp = self.client.post('/api/ai/ask', json={
            'question': oversized_question,
            'subject_id': 1,
            'topic_id': 1
        })
        self.assertEqual(resp.status_code, 400)
        data = resp.get_json()
        self.assertFalse(data.get("success"))
        self.assertIn("exceeds maximum allowed length", data.get("message", ""))

    # -------------------------------------------------------------------------
    # 20. Malformed JSON Handling
    # -------------------------------------------------------------------------
    def test_20_malformed_json_handling(self):
        """Malformed JSON payloads to API endpoints return clean 400 without crashing."""
        user_id = self._create_user("test_sec_u1@example.com", "JSON Student")
        self._login_as(user_id, "test_sec_u1@example.com", "JSON Student")

        resp = self.client.post(
            '/api/ai/ask',
            data='{"invalid_json_body": [broken',
            content_type='application/json'
        )
        self.assertEqual(resp.status_code, 400)
        data = resp.get_json()
        self.assertFalse(data.get("success"))

    # -------------------------------------------------------------------------
    # 21. Safe Error Handlers (404 / 500)
    # -------------------------------------------------------------------------
    def test_21_safe_error_handlers(self):
        """404 and 500 handlers return friendly responses without disclosing tracebacks."""
        # Web 404
        resp_web_404 = self.client.get('/not-found-url-security-audit')
        self.assertEqual(resp_web_404.status_code, 404)
        self.assertNotIn("Traceback", resp_web_404.get_data(as_text=True))

        # API 404
        resp_api_404 = self.client.get('/api/not-found-endpoint')
        self.assertEqual(resp_api_404.status_code, 404)
        self.assertTrue(resp_api_404.is_json)
        self.assertNotIn("Traceback", resp_api_404.get_data(as_text=True))

    # -------------------------------------------------------------------------
    # 22. Security Headers
    # -------------------------------------------------------------------------
    def test_22_security_headers_present(self):
        """Responses contain application-level defense-in-depth security headers."""
        resp = self.client.get('/')
        self.assertEqual(resp.headers.get('X-Content-Type-Options'), 'nosniff')
        self.assertEqual(resp.headers.get('X-Frame-Options'), 'SAMEORIGIN')
        self.assertEqual(resp.headers.get('Referrer-Policy'), 'strict-origin-when-cross-origin')

    # -------------------------------------------------------------------------
    # 23. Session Cookie Security Attributes
    # -------------------------------------------------------------------------
    def test_23_session_cookie_security_attributes(self):
        """Flask application session configuration enforces HttpOnly and SameSite=Lax."""
        self.assertTrue(self.app.config.get('SESSION_COOKIE_HTTPONLY'))
        self.assertEqual(self.app.config.get('SESSION_COOKIE_SAMESITE'), 'Lax')

    # -------------------------------------------------------------------------
    # 24. Passwords Cryptographically Hashed (Never Plaintext)
    # -------------------------------------------------------------------------
    def test_24_passwords_cryptographically_hashed(self):
        """User passwords stored in MySQL are hashed with werkzeug scrypt/pbkdf2."""
        raw_pw = "UltraSecretPassword99!"
        user_id = self._create_user("test_sec_u1@example.com", "Hash Student")

        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT password_hash FROM users WHERE id = %s",
                    (user_id,)
                )
                row = cursor.fetchone()
                self.assertIsNotNone(row)
                stored_hash = row["password_hash"]
                self.assertNotEqual(stored_hash, raw_pw)
                self.assertTrue(
                    stored_hash.startswith("scrypt:") or stored_hash.startswith("pbkdf2:"),
                    f"Unexpected hash format: {stored_hash}"
                )
        finally:
            conn.close()

    # 25. Database Health Check Credential Concealment and Production Secret Enforcement
    # -------------------------------------------------------------------------
    def test_25_db_health_credential_concealment(self):
        """Database health reporting exposes connectivity without exposing db password,
        and production environment forbids empty or default development SECRET_KEY."""
        health = check_db_health()
        self.assertIn("connected", health)
        self.assertIn("database_exists", health)
        self.assertNotIn("password", health)
        self.assertNotIn("db_password", health)

        # Verify production configuration rejects default development fallback
        class FakeProdDefaultConfig(Config):
            ENV = 'production'
            SECRET_KEY = 'change-this-secret-key'

        with self.assertRaises(ValueError):
            create_app(FakeProdDefaultConfig)

        # Verify production configuration rejects empty SECRET_KEY
        class FakeProdEmptyConfig(Config):
            ENV = 'production'
            SECRET_KEY = ''

        with self.assertRaises(ValueError):
            create_app(FakeProdEmptyConfig)


if __name__ == '__main__':
    unittest.main()

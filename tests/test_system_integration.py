"""
Automated Test Suite for Phase 8 - System Polish, Integration & Final Deployment Readiness.
AI Student Learning Mentor.

Verifies:
1. Landing page renders Phase 8 integrated branding and features.
2. Web 404 handler returns clean HTML error page with safe navigation.
3. API 404 handler returns structured JSON payload.
4. API 405 Method Not Allowed returns structured JSON payload.
5. Web 405 Method Not Allowed returns clean HTML error page.
6. Unauthenticated API access returns 401 Unauthorized JSON payload.
7. Unauthenticated browser access redirects to /login with next-URL query param.
8. CSRF token generation creates 64-character hex tokens bound to session.
9. CSRF token rotation changes the token on security lifecycle events.
10. CSRF token validation verifies matching tokens and rejects tampered tokens.
11. CSRF Origin validation blocks malicious cross-origin POST requests with 403.
12. Strict CSRF enforcement rejects POST requests missing CSRF tokens with 400.
13. Strict CSRF enforcement accepts POST requests with valid tokens.
14. Open redirect protection prevents malicious external redirects.
15. Base template injects CSRF meta tag and active phase badges.
16. API health endpoint reports Phase 8 project metadata.
"""
import unittest
from flask import session
from app import create_app, is_safe_redirect_url
from config import Config
from services.csrf_service import (
    generate_csrf_token, validate_csrf_token, rotate_csrf_token
)


class TestPhase8SystemIntegration(unittest.TestCase):
    """Test suite covering Phase 8 system-wide integration and quality requirements."""

    @classmethod
    def setUpClass(cls):
        """Configure test application."""
        cls.app = create_app()

    def setUp(self):
        """Create fresh test client."""
        self.client = self.app.test_client()

    # 1. Landing page renders Phase 8 branding and features
    def test_01_landing_page_renders_phase_8(self):
        """Verify landing page renders Phase 8 milestone and companion tagline."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("AI Student Learning Mentor", html)
        self.assertIn("Phase 8", html)
        self.assertIn("Your Personal AI-Powered Learning Companion", html)

    # 2. Web 404 handler returns clean HTML error page
    def test_02_web_404_error_page(self):
        """Verify non-existent web route returns HTTP 404 HTML error page."""
        response = self.client.get('/definitely-non-existent-page-xyz')
        self.assertEqual(response.status_code, 404)
        html = response.get_data(as_text=True)
        self.assertIn("404", html)
        self.assertIn("Content Not Found", html)
        self.assertIn("href=\"/\"", html)

    # 3. API 404 handler returns structured JSON payload
    def test_03_api_404_error_json(self):
        """Verify non-existent /api/* route returns HTTP 404 JSON response."""
        response = self.client.get('/api/non-existent-resource-endpoint')
        self.assertEqual(response.status_code, 404)
        self.assertTrue(response.is_json)
        data = response.get_json()
        self.assertEqual(data.get("status"), "error")
        self.assertIn("message", data)

    # 4. API 405 Method Not Allowed returns structured JSON
    def test_04_api_405_method_not_allowed_json(self):
        """Verify disallow HTTP method on /api/health returns HTTP 405 JSON response."""
        response = self.client.post('/api/health')
        self.assertEqual(response.status_code, 405)
        self.assertTrue(response.is_json)
        data = response.get_json()
        self.assertEqual(data.get("status"), "error")
        self.assertIn("message", data)

    # 5. Web 405 Method Not Allowed returns clean HTML error page
    def test_05_web_405_method_not_allowed_html(self):
        """Verify disallowed method on a web route returns HTTP 405 error page."""
        response = self.client.post('/logout')
        self.assertEqual(response.status_code, 405)
        html = response.get_data(as_text=True)
        self.assertIn("405", html)
        self.assertIn("Method Not Allowed", html)

    # 6. Unauthenticated API access returns 401 Unauthorized JSON
    def test_06_unauthenticated_api_returns_401_json(self):
        """Verify calling protected API unauthenticated returns HTTP 401 JSON."""
        response = self.client.get('/api/progress/statistics')
        self.assertEqual(response.status_code, 401)
        self.assertTrue(response.is_json)
        data = response.get_json()
        self.assertEqual(data.get("status"), "error")
        self.assertIn("Authentication required", data.get("message", ""))

    # 7. Unauthenticated browser access redirects to /login with next-URL query param
    def test_07_unauthenticated_browser_redirects_to_login(self):
        """Verify unauthenticated page visits redirect to /login?next=<path>."""
        for path in ['/dashboard', '/profile', '/study-plans', '/progress']:
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 302)
                self.assertIn('/login', response.headers.get('Location', ''))
                self.assertIn(f'next={path}', response.headers.get('Location', ''))

    # 8. CSRF token generation creates 64-character hex tokens
    def test_08_csrf_token_generation(self):
        """Verify generate_csrf_token creates a cryptographically strong 64-char token."""
        with self.app.test_request_context():
            token1 = generate_csrf_token()
            self.assertEqual(len(token1), 64)
            self.assertIsInstance(token1, str)
            # Second call in same session returns identical token
            token2 = generate_csrf_token()
            self.assertEqual(token1, token2)

    # 9. CSRF token rotation changes the token on security events
    def test_09_csrf_token_rotation(self):
        """Verify rotate_csrf_token regenerates a fresh distinct token."""
        with self.app.test_request_context():
            token_original = generate_csrf_token()
            token_rotated = rotate_csrf_token()
            self.assertEqual(len(token_rotated), 64)
            self.assertNotEqual(token_original, token_rotated)
            self.assertEqual(session.get('_csrf_token'), token_rotated)

    # 10. CSRF token validation logic
    def test_10_csrf_token_validation_logic(self):
        """Verify validate_csrf_token accurately compares valid, tampered, and empty tokens."""
        with self.app.test_request_context():
            valid_token = generate_csrf_token()
            self.assertTrue(validate_csrf_token(valid_token))
            self.assertFalse(validate_csrf_token(""))
            self.assertFalse(validate_csrf_token(None))
            tampered_suffix = "ff" if not valid_token.endswith("ff") else "00"
            self.assertFalse(validate_csrf_token(valid_token[:-2] + tampered_suffix))

    # 11. CSRF Origin validation blocks malicious cross-origin POST
    def test_11_cross_origin_post_blocked(self):
        """Verify cross-origin POST requests are rejected with HTTP 403 Forbidden."""
        custom_app = create_app()
        custom_app.config['CSRF_ENABLED'] = True
        client = custom_app.test_client()

        response = client.post(
            '/login',
            data={'email': 'test@example.com', 'password': 'password123'},
            headers={'Origin': 'https://malicious-attacker-domain.com'}
        )
        self.assertEqual(response.status_code, 403)
        html = response.get_data(as_text=True)
        self.assertIn("403", html)
        self.assertIn("Forbidden", html)

    # 12. Strict CSRF enforcement rejects missing token
    def test_12_strict_csrf_rejects_missing_token(self):
        """Verify strict mode rejects state-changing requests lacking CSRF token."""
        custom_app = create_app()
        custom_app.config['CSRF_ENABLED'] = True
        custom_app.config['CSRF_STRICT'] = True
        client = custom_app.test_client()

        # Attempt POST without csrf_token field
        response = client.post(
            '/login',
            data={'email': 'test@example.com', 'password': 'password123'}
        )
        self.assertEqual(response.status_code, 400)
        html = response.get_data(as_text=True)
        self.assertIn("400", html)
        self.assertIn("CSRF", html)

    # 13. Strict CSRF enforcement accepts valid token
    def test_13_strict_csrf_accepts_valid_token(self):
        """Verify strict mode accepts state-changing requests with matching CSRF token."""
        custom_app = create_app()
        custom_app.config['CSRF_ENABLED'] = True
        custom_app.config['CSRF_STRICT'] = True
        client = custom_app.test_client()

        # Seed session token by requesting GET /login
        with client.session_transaction() as sess:
            sess['_csrf_token'] = 'a' * 64

        from unittest.mock import patch
        with patch('app.authenticate_user', return_value=(False, 'Invalid credentials.', None)):
            response = client.post(
                '/login',
                data={
                    'email': 'unknown@example.com',
                    'password': 'badpassword',
                    'csrf_token': 'a' * 64
                }
            )
            # Should not be blocked by CSRF (400/403); instead reaches auth logic (401 invalid creds)
            self.assertEqual(response.status_code, 401)

    # 14. Open redirect protection
    def test_14_open_redirect_protection(self):
        """Verify is_safe_redirect_url rejects external domains and accepts local paths."""
        with self.app.test_request_context('/login'):
            self.assertTrue(is_safe_redirect_url('/dashboard'))
            self.assertTrue(is_safe_redirect_url('/study-plans'))
            self.assertTrue(is_safe_redirect_url('/topics/1'))
            self.assertFalse(is_safe_redirect_url('http://malicious.com'))
            self.assertFalse(is_safe_redirect_url('https://evil.org/phish'))
            self.assertFalse(is_safe_redirect_url('//attacker.com/bypass'))
            self.assertFalse(is_safe_redirect_url('javascript:alert(1)'))
            self.assertFalse(is_safe_redirect_url(''))
            self.assertFalse(is_safe_redirect_url(None))

    # 15. Base template CSRF meta tag
    def test_15_base_template_csrf_meta_tag(self):
        """Verify base layout includes CSRF meta tag for asynchronous fetch requests."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn('name="csrf-token"', html)

    # 16. API health endpoint reports Phase 9 project metadata
    def test_16_api_health_phase_metadata(self):
        """Verify /api/health reports Phase 9 milestone metadata."""
        response = self.client.get('/api/health')
        self.assertIn(response.status_code, [200, 503])
        self.assertTrue(response.is_json)
        data = response.get_json()
        self.assertEqual(data.get("phase"), 9)
        self.assertEqual(data.get("project"), "AI Student Learning Mentor")


if __name__ == '__main__':
    unittest.main()

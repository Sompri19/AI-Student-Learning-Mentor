"""
Automated Test Suite for Phase 1 - Project Foundation & Database Architecture.
AI Student Learning Mentor.

Verifies:
1. Flask application imports successfully.
2. Home page returns HTTP 200.
3. Home page contains project name.
4. Home page contains expected feature sections.
5. /api/health exists.
6. /api/health returns JSON.
7. Database configuration loads correctly.
8. Database connection can be established.
9. Database student_learning_mentor exists.
10. Required tables exist.
11. Foreign-key relationships are valid.
12. No passwords/secrets are exposed in application responses.
"""
import unittest
import pymysql
from app import create_app, app
from config import Config
from services.db import get_db_connection, check_db_health, REQUIRED_TABLES


class TestPhase1Foundation(unittest.TestCase):
    """Test suite covering all Phase 1 foundation and architecture requirements."""

    @classmethod
    def setUpClass(cls):
        """Set up test client for Flask application."""
        cls.app = create_app()
        cls.client = cls.app.test_client()

    # 1. Flask application imports successfully
    def test_01_flask_application_imports(self):
        """Verify Flask application imports and initializes properly."""
        self.assertIsNotNone(app)
        self.assertIsNotNone(self.app)
        self.assertEqual(self.app.name, 'app')

    # 2. Home page returns HTTP 200
    def test_02_home_page_status_200(self):
        """Verify GET / returns HTTP status 200."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

    # 3. Home page contains project name
    def test_03_home_page_contains_project_name(self):
        """Verify home page contains the project name and companion tagline."""
        response = self.client.get('/')
        html = response.get_data(as_text=True)
        self.assertIn("AI Student Learning Mentor", html)
        self.assertIn("Your Personal AI-Powered Learning Companion", html)

    # 4. Home page contains expected feature sections
    def test_04_home_page_contains_feature_sections(self):
        """Verify home page contains all five required feature previews."""
        response = self.client.get('/')
        raw_html = response.get_data(as_text=True)
        expected_features = [
            "Personalized Study Plan",
            "AI Doubt Assistant",
            "Quiz & Practice",
            "Progress Tracking",
            "Learning Goals"
        ]
        for feature in expected_features:
            with self.subTest(feature=feature):
                found = (feature in raw_html) or (feature.replace('&', '&amp;') in raw_html)
                self.assertTrue(found, f"Feature section '{feature}' missing from home page.")

    # 5. /api/health exists
    def test_05_health_endpoint_exists(self):
        """Verify GET /api/health route exists (does not return 404)."""
        response = self.client.get('/api/health')
        self.assertNotEqual(response.status_code, 404)

    # 6. /api/health returns JSON
    def test_06_health_endpoint_returns_json(self):
        """Verify GET /api/health returns valid JSON with expected structure."""
        response = self.client.get('/api/health')
        self.assertTrue(response.is_json, "Response from /api/health is not JSON.")
        data = response.get_json()
        self.assertIn("status", data)
        self.assertIn("project", data)
        self.assertIn("phase", data)
        self.assertIn("database", data)
        self.assertEqual(data["project"], "AI Student Learning Mentor")
        self.assertEqual(data["phase"], Config.CURRENT_PHASE)
        self.assertIn("connected", data["database"])
        self.assertIn("database_exists", data["database"])
        self.assertIn("database_name", data["database"])

    # 7. Database configuration loads correctly
    def test_07_database_configuration_loads(self):
        """Verify database and app configuration values are loaded and well-typed."""
        self.assertIsInstance(Config.DB_HOST, str)
        self.assertIsInstance(Config.DB_PORT, int)
        self.assertIsInstance(Config.DB_USER, str)
        self.assertIsInstance(Config.DB_NAME, str)
        self.assertIn(Config.DB_NAME, ("student_learning_mentor", "edumentor_ai"))
        self.assertIsInstance(Config.SECRET_KEY, str)
        self.assertGreater(len(Config.SECRET_KEY), 0)

    # 8. Database connection can be established
    def test_08_database_connection_established(self):
        """Verify database connection to MySQL can be established using PyMySQL."""
        try:
            conn = get_db_connection()
            self.assertTrue(conn.open)
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1 AS alive")
                row = cursor.fetchone()
                self.assertEqual(row["alive"], 1)
            conn.close()
        except pymysql.MySQLError as e:
            self.fail(f"Could not connect to MySQL server. Ensure MySQL is started in XAMPP: {e}")

    # 9. Database student_learning_mentor exists
    def test_09_database_exists(self):
        """Verify student_learning_mentor database exists in MySQL."""
        conn = get_db_connection(database='')
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME = %s",
                    (Config.DB_NAME,)
                )
                db_record = cursor.fetchone()
                self.assertIsNotNone(
                    db_record,
                    f"Database '{Config.DB_NAME}' does not exist in MySQL."
                )
        finally:
            conn.close()

    # 10. Required tables exist
    def test_10_required_tables_exist(self):
        """Verify all 11 required tables exist in student_learning_mentor database."""
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT TABLE_NAME 
                    FROM INFORMATION_SCHEMA.TABLES 
                    WHERE TABLE_SCHEMA = %s AND TABLE_TYPE = 'BASE TABLE'
                    """,
                    (Config.DB_NAME,)
                )
                rows = cursor.fetchall()
                found_tables = {r["TABLE_NAME"] for r in rows}
                
                for table in REQUIRED_TABLES:
                    with self.subTest(table=table):
                        self.assertIn(
                            table,
                            found_tables,
                            f"Required table '{table}' is missing from '{Config.DB_NAME}'."
                        )
        finally:
            conn.close()

    # 11. Foreign-key relationships are valid
    def test_11_foreign_key_relationships_valid(self):
        """Verify required foreign key constraints are established in database schema."""
        expected_fks = [
            ("student_profiles", "users"),
            ("topics", "subjects"),
            ("resources", "topics"),
            ("study_plans", "users"),
            ("study_plans", "subjects"),
            ("study_plan_items", "study_plans"),
            ("study_plan_items", "topics"),
            ("quizzes", "topics"),
            ("quiz_attempts", "users"),
            ("quiz_attempts", "quizzes"),
            ("progress", "users"),
            ("progress", "topics"),
            ("ai_chats", "users"),
        ]
        
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT TABLE_NAME, REFERENCED_TABLE_NAME
                    FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
                    WHERE TABLE_SCHEMA = %s AND REFERENCED_TABLE_NAME IS NOT NULL
                    """,
                    (Config.DB_NAME,)
                )
                fks = {(r["TABLE_NAME"], r["REFERENCED_TABLE_NAME"]) for r in cursor.fetchall()}
                
                for table, ref_table in expected_fks:
                    with self.subTest(table=table, ref_table=ref_table):
                        self.assertIn(
                            (table, ref_table),
                            fks,
                            f"Missing foreign key relationship: {table} -> {ref_table}"
                        )
        finally:
            conn.close()

    # 12. No passwords/secrets are exposed in application responses
    def test_12_no_secrets_exposed(self):
        """Verify passwords and secret keys are never exposed in responses or health API."""
        # 1. Test home page response
        home_res = self.client.get('/')
        home_text = home_res.get_data(as_text=True)
        self.assertNotIn(Config.SECRET_KEY, home_text)
        if Config.DB_PASSWORD:
            self.assertNotIn(Config.DB_PASSWORD, home_text)

        # 2. Test health endpoint response
        health_res = self.client.get('/api/health')
        health_text = health_res.get_data(as_text=True)
        self.assertNotIn(Config.SECRET_KEY, health_text)
        self.assertNotIn("password", health_text.lower())
        if Config.DB_PASSWORD:
            self.assertNotIn(Config.DB_PASSWORD, health_text)


if __name__ == '__main__':
    unittest.main()

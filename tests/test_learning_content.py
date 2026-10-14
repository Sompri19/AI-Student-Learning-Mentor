"""
Automated Test Suite for Phase 3 - Learning Content & Resource Engine.
AI Student Learning Mentor.

Verifies:
1. Subjects page returns 200.
2. Subjects are loaded from database.
3. Subject detail returns 200 for valid subject.
4. Invalid subject returns 404.
5. Topics are correctly associated with subjects.
6. Topic detail returns 200.
7. Invalid topic returns 404.
8. Resources are correctly associated with topics.
9. Resource type is displayed correctly.
10. Search works.
11. Difficulty filtering works.
12. Resource-type filtering works.
13. API subjects endpoint works.
14. API topic endpoint works.
15. API resources endpoint works.
16. Unsafe resource URLs are rejected/handled safely.
"""
import unittest
import html as html_parser
from app import create_app
from services.db import get_db_connection
from services.content_service import (
    get_all_subjects, get_subject_by_id, get_topics_by_subject,
    get_topic_by_id, get_resources_by_topic, search_content,
    is_safe_resource_url
)


class TestPhase3LearningContent(unittest.TestCase):
    """Test suite covering all Phase 3 Learning Content & Resource Engine requirements."""

    @classmethod
    def setUpClass(cls):
        """Set up Flask test application."""
        cls.app = create_app()

    def setUp(self):
        """Initialize fresh test client for each test."""
        self.client = self.app.test_client()

    # 1. Subjects page returns 200
    def test_01_subjects_page_returns_200(self):
        """Verify GET /subjects returns HTTP 200."""
        response = self.client.get('/subjects')
        self.assertEqual(response.status_code, 200)

    # 2. Subjects are loaded from database
    def test_02_subjects_loaded_from_database(self):
        """Verify subjects displayed on /subjects originate from the database."""
        db_subjects = get_all_subjects()
        self.assertGreater(len(db_subjects), 0, "No subjects found in database.")

        response = self.client.get('/subjects')
        html = html_parser.unescape(response.get_data(as_text=True))

        for s in db_subjects:
            self.assertIn(s['name'], html)

    # 3. Subject detail returns 200 for valid subject
    def test_03_subject_detail_returns_200(self):
        """Verify GET /subjects/<id> returns HTTP 200 for an existing subject."""
        subjects = get_all_subjects()
        self.assertGreater(len(subjects), 0)
        valid_id = subjects[0]['id']

        response = self.client.get(f'/subjects/{valid_id}')
        self.assertEqual(response.status_code, 200)
        html = html_parser.unescape(response.get_data(as_text=True))
        self.assertIn(subjects[0]['name'], html)

    # 4. Invalid subject returns 404
    def test_04_invalid_subject_returns_404(self):
        """Verify GET /subjects/<id> returns HTTP 404 for a non-existent subject."""
        response = self.client.get('/subjects/999999')
        self.assertEqual(response.status_code, 404)

    # 5. Topics are correctly associated with subjects
    def test_05_topics_associated_with_subjects(self):
        """Verify only topics belonging to the selected subject are displayed."""
        subjects = get_all_subjects()
        self.assertGreater(len(subjects), 0)
        subject = subjects[0]
        topics = get_topics_by_subject(subject['id'])

        response = self.client.get(f'/subjects/{subject["id"]}')
        html = html_parser.unescape(response.get_data(as_text=True))

        for t in topics:
            self.assertIn(t['topic_name'], html)

    # 6. Topic detail returns 200
    def test_06_topic_detail_returns_200(self):
        """Verify GET /topics/<id> returns HTTP 200 for an existing topic."""
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT id, topic_name FROM topics LIMIT 1")
                topic = cursor.fetchone()
        finally:
            conn.close()

        self.assertIsNotNone(topic)
        response = self.client.get(f'/topics/{topic["id"]}')
        self.assertEqual(response.status_code, 200)
        html = html_parser.unescape(response.get_data(as_text=True))
        self.assertIn(topic['topic_name'], html)

    # 7. Invalid topic returns 404
    def test_07_invalid_topic_returns_404(self):
        """Verify GET /topics/<id> returns HTTP 404 for a non-existent topic."""
        response = self.client.get('/topics/999999')
        self.assertEqual(response.status_code, 404)

    # 8. Resources are correctly associated with topics
    def test_08_resources_associated_with_topics(self):
        """Verify learning resources belonging to a topic appear on the topic detail page."""
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT t.id, t.topic_name, COUNT(r.id) AS res_count
                    FROM topics t
                    JOIN resources r ON t.id = r.topic_id
                    GROUP BY t.id
                    HAVING res_count > 0
                    LIMIT 1
                    """
                )
                topic_with_res = cursor.fetchone()
        finally:
            conn.close()

        self.assertIsNotNone(topic_with_res, "Expected at least one topic with resources.")
        topic_id = topic_with_res['id']
        resources = get_resources_by_topic(topic_id)

        response = self.client.get(f'/topics/{topic_id}')
        html = response.get_data(as_text=True)

        for r in resources:
            self.assertIn(r['title'], html)

    # 9. Resource type is displayed correctly
    def test_09_resource_type_displayed_correctly(self):
        """Verify resource types (Documentation, Article, Notes, Practice, Video) render properly."""
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT topic_id, resource_type FROM resources LIMIT 1")
                sample_res = cursor.fetchone()
        finally:
            conn.close()

        self.assertIsNotNone(sample_res)
        response = self.client.get(f'/topics/{sample_res["topic_id"]}')
        html = response.get_data(as_text=True)
        self.assertIn(sample_res['resource_type'], html)

    # 10. Search works
    def test_10_search_works(self):
        """Verify database-driven search returns relevant subjects, topics, and resources."""
        # Search by subject name
        res_subj = self.client.get('/subjects?q=Python')
        self.assertEqual(res_subj.status_code, 200)
        html_subj = html_parser.unescape(res_subj.get_data(as_text=True))
        self.assertIn("Python Programming", html_subj)

        # Search by specific topic keyword
        res_topic = self.client.get('/subjects?q=Variables')
        self.assertEqual(res_topic.status_code, 200)
        html_topic = html_parser.unescape(res_topic.get_data(as_text=True))
        self.assertIn("Variables & Data Types", html_topic)

        # Service-level search verification
        results = search_content(query="Variables")
        self.assertGreater(results["total_matches"], 0)

    # 11. Difficulty filtering works
    def test_11_difficulty_filtering_works(self):
        """Verify filtering content by difficulty (Beginner, Intermediate, Advanced) works."""
        subjects = get_all_subjects()
        sub_id = subjects[0]['id']

        # Filter topics on subject detail
        res = self.client.get(f'/subjects/{sub_id}?difficulty=Beginner')
        self.assertEqual(res.status_code, 200)
        topics = get_topics_by_subject(sub_id, difficulty='Beginner')
        for t in topics:
            self.assertEqual(t['difficulty'], 'Beginner')

        # Filter via search
        search_res = search_content(difficulty="Advanced")
        for r in search_res["resources"]:
            self.assertEqual(r['difficulty'], "Advanced")

    # 12. Resource-type filtering works
    def test_12_resource_type_filtering_works(self):
        """Verify filtering resources by resource_type returns matching records."""
        # Find a topic with resources
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT DISTINCT topic_id FROM resources LIMIT 1")
                row = cursor.fetchone()
        finally:
            conn.close()

        self.assertIsNotNone(row)
        topic_id = row['topic_id']

        response = self.client.get(f'/topics/{topic_id}?resource_type=Documentation')
        self.assertEqual(response.status_code, 200)

        # Direct service check
        docs = get_resources_by_topic(topic_id, resource_type='Documentation')
        for d in docs:
            self.assertEqual(d['resource_type'], 'Documentation')

    # 13. API subjects endpoint works
    def test_13_api_subjects_endpoint(self):
        """Verify GET /api/subjects returns valid JSON with subjects list."""
        response = self.client.get('/api/subjects')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.is_json)
        data = response.get_json()
        self.assertEqual(data["status"], "success")
        self.assertIn("subjects", data)
        self.assertGreater(data["count"], 0)

        # Single subject API
        sub_id = data["subjects"][0]["id"]
        single_resp = self.client.get(f'/api/subjects/{sub_id}')
        self.assertEqual(single_resp.status_code, 200)
        single_data = single_resp.get_json()
        self.assertEqual(single_data["status"], "success")
        self.assertIn("topics", single_data)

    # 14. API topic endpoint works
    def test_14_api_topic_endpoint(self):
        """Verify GET /api/topics/<id> returns valid JSON with topic details and resources."""
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT id FROM topics LIMIT 1")
                topic_id = cursor.fetchone()["id"]
        finally:
            conn.close()

        response = self.client.get(f'/api/topics/{topic_id}')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.is_json)
        data = response.get_json()
        self.assertEqual(data["status"], "success")
        self.assertIn("topic", data)
        self.assertIn("resources", data)

        # Invalid topic API returns 404
        bad_resp = self.client.get('/api/topics/999999')
        self.assertEqual(bad_resp.status_code, 404)

    # 15. API resources endpoint works
    def test_15_api_resources_endpoint(self):
        """Verify GET /api/resources supports search and filtering via query parameters."""
        response = self.client.get('/api/resources?q=Python')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.is_json)
        data = response.get_json()
        self.assertEqual(data["status"], "success")
        self.assertIn("resources", data)

    # 16. Unsafe resource URLs are rejected/handled safely
    def test_16_unsafe_resource_urls_handled_safely(self):
        """Verify URL validation rejects dangerous schemes and approves safe HTTP/HTTPS URLs."""
        # Unsafe URLs
        self.assertFalse(is_safe_resource_url("javascript:alert(1)"))
        self.assertFalse(is_safe_resource_url("data:text/html,<script>alert('xss')</script>"))
        self.assertFalse(is_safe_resource_url("vbscript:msgbox(1)"))
        self.assertFalse(is_safe_resource_url("file:///C:/Windows/System32/cmd.exe"))
        self.assertFalse(is_safe_resource_url("about:blank"))
        self.assertFalse(is_safe_resource_url(""))
        self.assertFalse(is_safe_resource_url(None))

        # Safe URLs
        self.assertTrue(is_safe_resource_url("https://docs.python.org/3/tutorial/"))
        self.assertTrue(is_safe_resource_url("http://example.com/guide.pdf"))

    # 17. All seven curriculum subjects present with topics
    def test_17_all_seven_subjects_present_with_topics(self):
        """Verify all 7 required academic subjects exist in the database with syllabus topics."""
        expected_subjects = [
            "Python Programming",
            "Data Structures & Algorithms",
            "Web Development Basics",
            "Java Programming",
            "Database Management Systems",
            "Computer Networks",
            "Operating Systems"
        ]
        subjects = get_all_subjects()
        subject_names = {s['name'] for s in subjects}

        for expected in expected_subjects:
            self.assertIn(expected, subject_names, f"Missing required subject: {expected}")

        for s in subjects:
            topics = get_topics_by_subject(s['id'])
            self.assertGreater(len(topics), 0, f"Subject '{s['name']}' has no topics.")

    # 18. All required topics have learning resources
    def test_18_all_required_topics_have_learning_resources(self):
        """Verify each required curriculum topic has accessible verified learning resources."""
        required_topics = [
            "IP Addressing & Subnetting",
            "TCP/IP & Transport Protocols",
            "Binary Trees & BST",
            "Database Fundamentals & ER Model",
            "Normalization & Normal Forms",
            "Java Syntax & Primitive Types",
            "Java Collections Framework",
            "Processes & Process Management",
            "Memory Management & Virtual Memory",
            "Lists, Tuples & Sets",
            "Dictionaries & Hash Maps",
            "JavaScript Fundamentals"
        ]

        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                for top_name in required_topics:
                    cursor.execute("SELECT id, subject_id, topic_name FROM topics WHERE topic_name = %s", (top_name,))
                    topic = cursor.fetchone()
                    self.assertIsNotNone(topic, f"Required topic '{top_name}' not found in database.")

                    resources = get_resources_by_topic(topic['id'])
                    self.assertGreater(
                        len(resources), 0,
                        f"Topic '{top_name}' (ID: {topic['id']}) has 0 resources."
                    )
        finally:
            conn.close()

    # 19. All curriculum resource URLs are verified safe
    def test_19_all_curriculum_resource_urls_are_safe(self):
        """Verify 100% of educational resources stored in the database satisfy URL safety rules."""
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT id, title, url FROM resources")
                all_resources = cursor.fetchall()
                self.assertGreater(len(all_resources), 0)

                for r in all_resources:
                    self.assertTrue(
                        is_safe_resource_url(r['url']),
                        f"Resource ID {r['id']} '{r['title']}' has unsafe URL: {r['url']}"
                    )
        finally:
            conn.close()


if __name__ == '__main__':
    unittest.main()

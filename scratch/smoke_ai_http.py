"""End-to-end smoke test through the real Flask HTTP interface.

Exercises: landing page -> health -> register -> login -> AI mentor (live Groq)
-> AI history -> persisted ai_chats row.

Run:  python3 scratch/smoke_ai_http.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from services.ai_service import reset_rate_limits
from services.content_service import get_all_subjects, get_topics_by_subject
from services.db import get_db_connection

EMAIL = "test_smoke_ai@example.com"
PASSWORD = "Password123!"

app = create_app()
client = app.test_client()

failures = []


def check(label, condition, detail=""):
    print(("  PASS  " if condition else "  FAIL  ") + label + (f"  [{detail}]" if detail and not condition else ""))
    if not condition:
        failures.append(label)


# Clean any previous run
conn = get_db_connection()
with conn.cursor() as cur:
    cur.execute("DELETE FROM users WHERE email = %s", (EMAIL,))
conn.commit()
conn.close()

print("1) Public pages and DB health")
check("/ returns 200", client.get("/").status_code == 200)
health = client.get("/api/health")
check("/api/health returns 200", health.status_code == 200, str(health.status_code))
check("health status is 'healthy'", health.get_json().get("status") == "healthy", str(health.get_json()))
check("/login returns 200", client.get("/login").status_code == 200)
check("/subjects returns 200", client.get("/subjects").status_code == 200)

print("2) Registration and login")
resp = client.post(
    "/register",
    data={"name": "Smoke Student", "email": EMAIL, "password": PASSWORD, "confirm_password": PASSWORD},
)
check("POST /register succeeds", resp.status_code in (200, 302), str(resp.status_code))
resp = client.post("/login", data={"email": EMAIL, "password": PASSWORD})
check("POST /login succeeds", resp.status_code == 302, str(resp.status_code))
check("/dashboard reachable after login", client.get("/dashboard").status_code == 200)

print("3) AI mentor over Groq (live API call)")
subjects = get_all_subjects()
topics = get_topics_by_subject(subjects[0]["id"]) if subjects else []
payload = {"question": "Why is a Python tuple immutable while a list is mutable?"}
if topics:
    payload["subject_id"] = subjects[0]["id"]
    payload["topic_id"] = topics[0]["id"]

ai = client.post("/api/ai/ask", json=payload)
body = ai.get_json() or {}
check("POST /api/ai/ask returns 201", ai.status_code == 201, f"{ai.status_code} {body.get('message', '')}")
check("response reports success", body.get("success") is True, str(body.get("message")))
answer = body.get("answer") or ""
check("answer is a real explanation", len(answer) > 40, repr(answer[:80]))
check("chat was persisted (chat_id present)", body.get("chat_id") is not None)
check("no API key leaked in response", "gsk_" not in ai.get_data(as_text=True))

# The web route must render the answer as HTML, not dump raw Markdown syntax.
reset_rate_limits()  # the per-student cooldown would otherwise 429 this second call
rendered = client.post(
    "/ai/ask",
    data={"question": "Explain Python list slicing with one short example."},
    follow_redirects=True,
)
rendered_html = rendered.get_data(as_text=True)
check("POST /ai/ask returns 200", rendered.status_code == 200, str(rendered.status_code))
check(
    "answer rendered as HTML elements",
    any(tag in rendered_html for tag in ("<p>", "<ul>", "<ol>", "<h2>", "<h3>", "<strong>")),
)
check("no raw markdown heading syntax in output", "### " not in rendered_html)
check("no raw markdown table syntax in output", "|---|" not in rendered_html)

if answer:
    print("        answer preview:", answer[:220].replace("\n", " "))

print("4) AI history and persistence")
history = client.get("/ai/history")
check("GET /ai/history returns 200", history.status_code == 200, str(history.status_code))
check("history shows the asked question", "tuple immutable" in history.get_data(as_text=True))

conn = get_db_connection()
with conn.cursor() as cur:
    cur.execute(
        "SELECT COUNT(*) AS n FROM ai_chats c JOIN users u ON u.id = c.user_id WHERE u.email = %s",
        (EMAIL,),
    )
    rows = cur.fetchone()["n"]
    cur.execute("DELETE FROM users WHERE email = %s", (EMAIL,))
conn.commit()
conn.close()
check("ai_chats row written for this user", rows >= 1, f"rows={rows}")

print("-" * 60)
if failures:
    print("FAILED CHECKS:", failures)
    sys.exit(1)
print("ALL HTTP SMOKE CHECKS PASSED")

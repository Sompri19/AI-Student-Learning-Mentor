"""Verify the Groq provider through the application's real AI service entry point.

Run:  python3 scratch/verify_groq_integration.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config
from services.ai_service import ask_ai, UNAVAILABLE_MESSAGE
from services.markdown_service import render_markdown

print("Resolved AI configuration (no secrets printed):")
print("  AI_PROVIDER :", Config.AI_PROVIDER)
print("  AI_MODEL    :", Config.AI_MODEL)
print("  AI_API_KEY  :", "set" if Config.AI_API_KEY else "MISSING")
print("-" * 70)

failures = []

# 1. Live Groq call through ask_ai with syllabus context.
ok, answer = ask_ai(
    "Explain the difference between a list and a tuple in Python.",
    subject_name="Python Programming",
    topic_name="Lists and Tuples",
)
print("[1] live groq call -> success:", ok)
if ok:
    print("    answer preview:", answer[:400].replace("\n", " "))
else:
    print("    message:", answer)
    failures.append("live groq call failed")

# 2. Unavailable-model handling should return a clear, non-crashing message.
ok_bad, msg_bad = ask_ai(
    "What is a tuple?", provider="groq", model="definitely-not-a-real-model"
)
print("[2] invalid model -> success:", ok_bad, "| message:", msg_bad)
if ok_bad or "model is not available" not in msg_bad:
    failures.append("invalid model handling unexpected")

# 3. Missing key must return the safe unavailable message, never a fabricated answer.
ok_nokey, msg_nokey = ask_ai("What is a set?", provider="groq", api_key="")
print("[3] missing key -> success:", ok_nokey, "| is UNAVAILABLE_MESSAGE:", msg_nokey == UNAVAILABLE_MESSAGE)
if ok_nokey or msg_nokey != UNAVAILABLE_MESSAGE:
    failures.append("missing-key handling unexpected")

# 4. The API key must never appear in any returned message.
if Config.AI_API_KEY and Config.AI_API_KEY in (answer + msg_bad + msg_nokey):
    failures.append("API key leaked into a response")

# 5. The live model answer must render as HTML without leaking raw Markdown syntax.
if ok:
    rendered = str(render_markdown(answer))
    print("[5] live answer rendered -> html chars:", len(rendered))
    print("    preview:", rendered[:300].replace("\n", " "))
    if not any(tag in rendered for tag in ("<p>", "<ul>", "<ol>", "<h2>", "<h3>", "<pre>", "<table>")):
        failures.append("live answer produced no HTML blocks")
    if "|---|" in rendered:
        failures.append("raw table divider leaked from live answer")
    if "\n### " in rendered:
        failures.append("raw heading syntax leaked from live answer")
    if "<script" in rendered.lower():
        failures.append("unescaped script tag in rendered answer")

print("-" * 70)
if failures:
    print("FAILURES:", failures)
    sys.exit(1)
print("ALL GROQ INTEGRATION CHECKS PASSED")

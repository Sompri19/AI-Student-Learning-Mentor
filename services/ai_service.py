"""
AI Doubt Assistant Service.
AI Student Learning Mentor - Phase 6.

Provides a clean provider abstraction for academic doubt resolution.
Supports external LLM providers (Google Gemini, OpenAI, Groq) and controlled test mocks.
Handles timeouts, rate limiting, provider errors, and safe rendering without
exposing API keys or private user credentials.
"""
import os
import time
import math
import logging
import threading
from typing import Dict, Any, Optional, Tuple, List
import requests

from config import Config
from services.db import get_db_connection, sanitize_db_error
from models.subject_model import find_subject_by_id, find_topic_by_id
from models.progress_model import (
    insert_ai_chat_log,
    find_ai_chats_by_user,
    find_ai_chat_by_id,
)

logger = logging.getLogger(__name__)

# Constants
MAX_QUESTION_LENGTH = 2000
MIN_QUESTION_LENGTH = 3
DEFAULT_TIMEOUT_SECONDS = 20
DEFAULT_RATE_LIMIT_SECONDS = 5

# OpenAI-compatible provider endpoints.
OPENAI_API_BASE = "https://api.openai.com/v1"
GROQ_API_BASE = "https://api.groq.com/openai/v1"

# Per-provider default models used when no model is explicitly configured.
DEFAULT_GEMINI_MODEL = "gemini-1.5-flash"
DEFAULT_OPENAI_MODEL = "gpt-3.5-turbo"
DEFAULT_GROQ_MODEL = "openai/gpt-oss-120b"

PROVIDER_DEFAULT_MODELS = {
    "gemini": DEFAULT_GEMINI_MODEL,
    "openai": DEFAULT_OPENAI_MODEL,
    "chatgpt": DEFAULT_OPENAI_MODEL,
    "groq": DEFAULT_GROQ_MODEL,
}

DEFAULT_SYSTEM_PROMPT = (
    "You are an AI Student Learning Mentor. Help students understand academic concepts "
    "clearly and accurately. Explain difficult concepts in simple language, provide examples "
    "when useful, and encourage understanding rather than rote memorization. If a question "
    "is ambiguous, ask for clarification. Do not claim certainty when information is uncertain.\n\n"
    "Formatting rules:\n"
    "- Answer in concise GitHub-flavoured Markdown, but never wrap the whole reply in a code block.\n"
    "- Open with a one or two sentence direct answer, then add short sections with bullet points.\n"
    "- Keep the entire answer under roughly 400 words unless the student explicitly asks for depth.\n"
    "- Prefer short bulleted lists over large tables; use a table only for genuinely tabular data, "
    "and never repeat the same content in both a list and a table.\n"
    "- Use fenced code blocks only for actual code, limited to a short, illustrative snippet.\n"
    "- Use plain ASCII punctuation: write a hyphen (-) for asides and ranges, never an em dash or en dash.\n"
    "- Do not use horizontal rules to pad the answer or append a summary that repeats what you already said."
)

UNAVAILABLE_MESSAGE = "AI assistant is currently unavailable. Please configure the AI service."

# In-memory rate limiting tracker: user_id -> timestamp of last successful request
_rate_limit_lock = threading.Lock()
_user_last_request_time: Dict[int, float] = {}

# Test hook allowing mocks to be registered dynamically in unit tests
_mock_handler = None


def set_test_mock_handler(handler):
    """Sets a custom test mock handler for testing."""
    global _mock_handler
    _mock_handler = handler


def reset_rate_limits():
    """Resets rate limit timestamps (used in unit testing)."""
    with _rate_limit_lock:
        _user_last_request_time.clear()


# -----------------------------------------------------------------------------
# Input Validation
# -----------------------------------------------------------------------------
def validate_academic_question(
    question: str,
    subject_id: Optional[int] = None,
    topic_id: Optional[int] = None
) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Validates student question and optional academic context server-side.
    
    Checks:
    - Question is present, string, non-empty
    - Question length is between 3 and 2000 characters
    - Subject exists (if provided)
    - Topic exists and belongs to selected subject (if provided)

    Returns:
        (is_valid: bool, error_message: str, validated_data: dict)
    """
    if not question or not isinstance(question, str):
        return False, "Please enter an academic question.", {}

    cleaned_q = question.strip()
    if not cleaned_q:
        return False, "Question cannot be empty or whitespace.", {}

    if len(cleaned_q) < MIN_QUESTION_LENGTH:
        return False, f"Question must be at least {MIN_QUESTION_LENGTH} characters long.", {}

    if len(cleaned_q) > MAX_QUESTION_LENGTH:
        return False, f"Question exceeds maximum allowed length of {MAX_QUESTION_LENGTH} characters.", {}

    validated: Dict[str, Any] = {
        "question": cleaned_q,
        "subject_id": None,
        "subject_name": None,
        "topic_id": None,
        "topic_name": None
    }

    # Verify subject and topic in MySQL via models if provided
    if subject_id is not None or topic_id is not None:
        # Validate subject
        if subject_id is not None and subject_id > 0:
            subj_row = find_subject_by_id(subject_id)
            if not subj_row:
                return False, f"Selected subject #{subject_id} does not exist.", {}
            validated["subject_id"] = subj_row["id"]
            validated["subject_name"] = subj_row["name"]

        # Validate topic
        if topic_id is not None and topic_id > 0:
            topic_row = find_topic_by_id(topic_id)
            if not topic_row:
                return False, f"Selected topic #{topic_id} does not exist.", {}

            # Ensure topic belongs to the selected subject (if subject specified)
            if validated["subject_id"] and topic_row["subject_id"] != validated["subject_id"]:
                return False, "Selected topic does not belong to the selected subject.", {}

            validated["topic_id"] = topic_row["id"]
            validated["topic_name"] = topic_row["topic_name"]
            if not validated["subject_id"]:
                s_row = find_subject_by_id(topic_row["subject_id"])
                if s_row:
                    validated["subject_id"] = s_row["id"]
                    validated["subject_name"] = s_row["name"]

    return True, "", validated


# -----------------------------------------------------------------------------
# Rate Limiting / Abuse Protection
# -----------------------------------------------------------------------------
def check_rate_limit(user_id: int, cooldown_seconds: int = DEFAULT_RATE_LIMIT_SECONDS) -> Tuple[bool, Optional[str]]:
    """
    Application-level cooldown to prevent spamming the AI service.
    Ensures a student waits at least `cooldown_seconds` between AI questions.

    Returns:
        (allowed: bool, wait_message: Optional[str])
    """
    if not user_id or cooldown_seconds <= 0:
        return True, None

    now = time.time()
    with _rate_limit_lock:
        last_time = _user_last_request_time.get(user_id, 0.0)
        elapsed = now - last_time
        if elapsed < cooldown_seconds:
            wait_time = math.ceil(cooldown_seconds - elapsed)
            return False, f"Please wait {wait_time} second{'s' if wait_time != 1 else ''} before asking another academic question."

        _user_last_request_time[user_id] = now
        return True, None


# -----------------------------------------------------------------------------
# Provider Implementations
# -----------------------------------------------------------------------------
def _call_gemini_api(
    api_key: str,
    model: str,
    prompt: str,
    system_prompt: str,
    timeout: int = DEFAULT_TIMEOUT_SECONDS
) -> Tuple[bool, str]:
    """
    Dispatches request to Google Gemini REST API.
    Does NOT leak the API key in headers or error strings.
    """
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    payload = {
        "systemInstruction": {
            "parts": [{"text": system_prompt}]
        },
        "contents": [
            {
                "role": "user",
                "parts": [{"text": prompt}]
            }
        ],
        "generationConfig": {
            "temperature": 0.4,
            "maxOutputTokens": 2048
        }
    }

    try:
        response = requests.post(
            url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=timeout
        )

        if response.status_code == 200:
            data = response.json()
            candidates = data.get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                if parts and "text" in parts[0]:
                    return True, parts[0]["text"].strip()
            return False, "AI provider returned an empty response. Please try rephrasing your question."

        elif response.status_code in (401, 403):
            logger.error("Gemini API authentication failed (HTTP %s).", response.status_code)
            return False, "AI assistant authentication failed. Please verify the configured API credentials."

        elif response.status_code == 429:
            logger.warning("Gemini API rate limit exceeded.")
            return False, "AI assistant is currently experiencing high demand. Please try again in a few moments."

        elif response.status_code >= 500:
            logger.error("Gemini API server error (HTTP %s).", response.status_code)
            return False, "AI provider service is temporarily unavailable. Please try again shortly."

        else:
            logger.error("Gemini API unexpected error (HTTP %s): %s", response.status_code, response.text[:200])
            return False, "Unable to generate an explanation at this time. Please try again later."

    except requests.exceptions.Timeout:
        logger.warning("Gemini API request timed out after %s seconds.", timeout)
        return False, "The AI mentor took too long to respond. Please try asking again."

    except requests.exceptions.RequestException as exc:
        logger.error("Gemini API connection error: %s", exc)
        return False, "Could not reach the AI service. Please check your network connection."


def _call_openai_compatible_api(
    api_key: str,
    model: str,
    prompt: str,
    system_prompt: str,
    base_url: str,
    provider_label: str,
    default_model: str,
    timeout: int = DEFAULT_TIMEOUT_SECONDS
) -> Tuple[bool, str]:
    """
    Dispatches a request to any OpenAI Chat Completions compatible REST API.

    Shared by the OpenAI provider and the Groq provider, since GroqCloud
    exposes an OpenAI-compatible `/chat/completions` endpoint at
    https://api.groq.com/openai/v1. The API key is never logged.
    """
    url = f"{base_url.rstrip('/')}/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model or default_model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.4,
        "max_tokens": 2048
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=timeout)
        if response.status_code == 200:
            data = response.json()
            choices = data.get("choices", [])
            if choices:
                answer = (choices[0].get("message", {}).get("content") or "").strip()
                if answer:
                    return True, answer
            return False, "AI provider returned an empty response. Please try rephrasing your question."

        elif response.status_code in (401, 403):
            logger.error("%s API authentication failed (HTTP %s).", provider_label, response.status_code)
            return False, "AI assistant authentication failed. Please verify the configured API credentials."

        elif response.status_code == 404:
            logger.error(
                "%s API model unavailable (HTTP 404) for model '%s'.",
                provider_label, model or default_model
            )
            return False, "The configured AI model is not available. Please verify the AI_MODEL setting."

        elif response.status_code == 429:
            logger.warning("%s API rate limit exceeded.", provider_label)
            return False, "AI assistant rate limit reached. Please wait a moment before trying again."

        elif response.status_code >= 500:
            logger.error("%s API server error (HTTP %s).", provider_label, response.status_code)
            return False, "AI provider service is temporarily unavailable. Please try again shortly."

        else:
            logger.error(
                "%s API unexpected error (HTTP %s): %s",
                provider_label, response.status_code, response.text[:200]
            )
            return False, "Unable to generate an explanation at this time. Please try again later."

    except requests.exceptions.Timeout:
        logger.warning("%s API request timed out after %s seconds.", provider_label, timeout)
        return False, "The AI mentor took too long to respond. Please try asking again."

    except requests.exceptions.RequestException as exc:
        logger.error("%s connection error: %s", provider_label, exc)
        return False, "Could not reach the AI service. Please check your network connection."


def _call_openai_api(
    api_key: str,
    model: str,
    prompt: str,
    system_prompt: str,
    timeout: int = DEFAULT_TIMEOUT_SECONDS
) -> Tuple[bool, str]:
    """Dispatches request to the OpenAI Chat Completions REST API."""
    return _call_openai_compatible_api(
        api_key=api_key,
        model=model,
        prompt=prompt,
        system_prompt=system_prompt,
        base_url=OPENAI_API_BASE,
        provider_label="OpenAI",
        default_model=DEFAULT_OPENAI_MODEL,
        timeout=timeout,
    )


def _call_groq_api(
    api_key: str,
    model: str,
    prompt: str,
    system_prompt: str,
    timeout: int = DEFAULT_TIMEOUT_SECONDS
) -> Tuple[bool, str]:
    """Dispatches request to the GroqCloud OpenAI-compatible Chat Completions API."""
    return _call_openai_compatible_api(
        api_key=api_key,
        model=model,
        prompt=prompt,
        system_prompt=system_prompt,
        base_url=GROQ_API_BASE,
        provider_label="Groq",
        default_model=DEFAULT_GROQ_MODEL,
        timeout=timeout,
    )


# -----------------------------------------------------------------------------
# Main AI Query Interface
# -----------------------------------------------------------------------------
def ask_ai(
    question: str,
    subject_name: Optional[str] = None,
    topic_name: Optional[str] = None,
    provider: Optional[str] = None,
    api_key: Optional[str] = None,
    model: Optional[str] = None
) -> Tuple[bool, str]:
    """
    Core AI Mentor query abstraction.
    
    Academic Integrity & Privacy:
    - Never fabricates fake AI answers when no API key is configured.
    - If provider is missing credentials, gracefully returns UNAVAILABLE_MESSAGE.
    - Sends only academic subject/topic context; never user credentials or secrets.

    Returns:
        (success: bool, answer_or_message: str)
    """
    # Check for active unit test mock handler
    global _mock_handler
    if _mock_handler is not None:
        return _mock_handler(question, subject_name=subject_name, topic_name=topic_name)

    # Determine provider configuration
    active_provider = (provider or Config.AI_PROVIDER or "gemini").lower().strip()
    active_api_key = (api_key if api_key is not None else Config.AI_API_KEY).strip()
    provider_default_model = PROVIDER_DEFAULT_MODELS.get(active_provider, DEFAULT_GEMINI_MODEL)
    active_model = (model or Config.AI_MODEL or provider_default_model).strip()

    # Special mock provider for controlled automated testing
    if active_provider == "mock":
        subject_info = f" in {subject_name}" if subject_name else ""
        topic_info = f" ({topic_name})" if topic_name else ""
        explanation = (
            f"Here is an educational explanation for your question{subject_info}{topic_info}:\n\n"
            f"Key Concept: {question.strip()}\n\n"
            f"Explanation: A list is mutable, meaning its items can be modified after creation, "
            f"while a tuple is immutable, meaning its elements cannot be changed."
        )
        return True, explanation

    # If no API key is configured, return safe unavailable message without crashing or faking
    if not active_api_key:
        return False, UNAVAILABLE_MESSAGE

    # Assemble educational prompt with optional academic context
    prompt_parts = []
    if subject_name:
        prompt_parts.append(f"Academic Subject: {subject_name}")
    if topic_name:
        prompt_parts.append(f"Syllabus Topic: {topic_name}")
    prompt_parts.append(f"\nStudent Academic Question:\n{question.strip()}")
    prompt_parts.append("\nPlease provide a step-by-step educational explanation with an example.")
    assembled_prompt = "\n".join(prompt_parts)

    # Dispatch to configured provider
    if active_provider == "gemini":
        return _call_gemini_api(
            api_key=active_api_key,
            model=active_model,
            prompt=assembled_prompt,
            system_prompt=DEFAULT_SYSTEM_PROMPT
        )
    elif active_provider in ("openai", "chatgpt"):
        return _call_openai_api(
            api_key=active_api_key,
            model=active_model,
            prompt=assembled_prompt,
            system_prompt=DEFAULT_SYSTEM_PROMPT
        )
    elif active_provider == "groq":
        return _call_groq_api(
            api_key=active_api_key,
            model=active_model,
            prompt=assembled_prompt,
            system_prompt=DEFAULT_SYSTEM_PROMPT
        )
    else:
        logger.error("Unsupported AI provider configured: %s", active_provider)
        return False, f"Unsupported AI provider '{active_provider}'. Supported: gemini, openai, groq."


# -----------------------------------------------------------------------------
# Database Chat History Management
# -----------------------------------------------------------------------------
def save_ai_chat(user_id: int, question: str, answer: str) -> Tuple[bool, str, Optional[int]]:
    """
    Stores an authentic AI chat interaction in the MySQL `ai_chats` table.
    Does NOT store failed queries or synthetic conversations.
    Delegates to models.progress_model.insert_ai_chat_log.

    Returns:
        (success: bool, message: str, chat_id: Optional[int])
    """
    if not user_id:
        return False, "Authentication required to save chat.", None

    if not question or not answer:
        return False, "Both question and answer are required to store chat history.", None

    chat_id = insert_ai_chat_log(user_id, question.strip(), answer.strip())
    if chat_id:
        return True, "Chat saved successfully.", chat_id
    else:
        return False, "Failed to save AI chat.", None


def get_user_ai_history(user_id: int, limit: int = 50) -> List[Dict[str, Any]]:
    """
    Retrieves real AI conversation history belonging to the authenticated student.
    Enforces user isolation: WHERE user_id = %s.
    Delegates to models.progress_model.find_ai_chats_by_user.
    """
    if not user_id:
        return []

    return find_ai_chats_by_user(user_id, limit=max(1, min(limit, 100)))


def get_ai_chat_detail(chat_id: int, user_id: int) -> Optional[Dict[str, Any]]:
    """
    Retrieves a single AI conversation by ID, strictly enforcing student ownership.
    Returns None if chat does not exist or belongs to another user.
    Delegates to models.progress_model.find_ai_chat_by_id.
    """
    if not chat_id or not user_id:
        return None

    return find_ai_chat_by_id(chat_id, user_id)

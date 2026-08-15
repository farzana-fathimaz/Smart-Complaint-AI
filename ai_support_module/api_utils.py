"""
api_utils.py
────────────
Utility functions for:
1. Django REST API calls (complaint data)
2. Google Gemini AI response generation
"""

import requests
import google.generativeai as genai
from decouple import config

# ── Load environment variables ────────────────────────────
GEMINI_API_KEY  = config("GEMINI_API_KEY")
DJANGO_API_URL  = config("DJANGO_API_URL", default="http://127.0.0.1:8000/api")

# ── Configure Gemini ──────────────────────────────────────
genai.configure(api_key=GEMINI_API_KEY)

# Use Gemini 1.5 Flash (fast + free tier)
_model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    system_instruction="""
You are a helpful AI support assistant for a Smart Complaint Management System (CSM).
Your job is to:
- Help users understand their complaint status and progress
- Guide users on how to escalate complaints if unresolved
- Provide general support and troubleshooting advice
- Answer real-time questions about emergency contacts, utility helplines etc.
- Be polite, professional, and concise
- If a user asks for a specific complaint ID status, tell them you'll fetch it

Always respond in a friendly, professional tone.
Keep responses concise — max 3-4 sentences unless more detail is needed.
If you don't know something, say so honestly.
""",
)


# ─────────────────────────────────────────────────────────
#  DJANGO API HELPERS
# ─────────────────────────────────────────────────────────

def fetch_complaint(complaint_id: int) -> dict | None:
    """Fetches a single complaint from the Django API."""
    try:
        res = requests.get(f"{DJANGO_API_URL}/complaints/{complaint_id}/", timeout=8)
        res.raise_for_status()
        return res.json()
    except requests.exceptions.RequestException as e:
        print(f"[API] Could not fetch complaint {complaint_id}: {e}")
        return None


def fetch_complaint_track(complaint_id: int) -> dict | None:
    """Fetches the complaint timeline/tracking info."""
    try:
        res = requests.get(f"{DJANGO_API_URL}/complaints/{complaint_id}/track/", timeout=8)
        res.raise_for_status()
        return res.json()
    except requests.exceptions.RequestException as e:
        print(f"[API] Could not track complaint {complaint_id}: {e}")
        return None


def fetch_open_complaints(limit: int = 5) -> list:
    """Fetches open complaints from the Django API."""
    try:
        res = requests.get(
            f"{DJANGO_API_URL}/complaints/",
            params={"status": "Open"},
            timeout=8
        )
        res.raise_for_status()
        data = res.json()
        results = data.get("results", data) if isinstance(data, dict) else data
        return results[:limit]
    except requests.exceptions.RequestException as e:
        print(f"[API] Could not fetch open complaints: {e}")
        return []


def fetch_stats() -> dict | None:
    """Fetches dashboard stats from the Django API."""
    try:
        res = requests.get(f"{DJANGO_API_URL}/stats/", timeout=8)
        res.raise_for_status()
        return res.json()
    except requests.exceptions.RequestException as e:
        print(f"[API] Could not fetch stats: {e}")
        return None


# ─────────────────────────────────────────────────────────
#  GEMINI AI RESPONSE
# ─────────────────────────────────────────────────────────

def get_ai_response(user_message: str, conversation_history: list[dict]) -> str:
    """
    Sends user message to Gemini API with full conversation history.

    Args:
        user_message         : The current user input
        conversation_history : Previous messages in Gemini format

    Returns:
        AI response string
    """
    try:
        # Start a chat session with history
        chat = _model.start_chat(history=conversation_history)

        # Send the current message
        response = chat.send_message(user_message)

        return response.text.strip()

    except Exception as e:
        print(f"[Gemini Error]: {e}")
        return "I'm sorry, I encountered an error. Please try again in a moment."


def get_ai_response_with_context(user_message: str, extra_context: str, history: list[dict]) -> str:
    """
    Sends message with additional context (e.g. complaint data injected).

    Args:
        user_message  : User's question
        extra_context : Extra data to inject (complaint details, stats etc.)
        history       : Previous messages in Gemini format
    """
    enriched_message = f"{user_message}\n\n[System Context]: {extra_context}"

    try:
        chat     = _model.start_chat(history=history)
        response = chat.send_message(enriched_message)
        return response.text.strip()
    except Exception as e:
        print(f"[Gemini Error]: {e}")
        return "I'm sorry, I encountered an error processing your request."
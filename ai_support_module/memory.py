"""
memory.py
─────────
Manages conversation history for the AI assistant.
Stores messages in memory AND saves to a JSON file for persistence.
"""

import json
import os
from datetime import datetime

HISTORY_FILE = "chat_history.json"

# In-memory conversation history (list of dicts)
# Each dict: {"role": "user"/"assistant", "content": "...", "timestamp": "..."}
_conversation: list[dict] = []


def add_message(role: str, content: str) -> None:
    """
    Adds a message to the conversation history.

    Args:
        role   : "user" or "assistant"
        content: The message text
    """
    entry = {
        "role"     : role,
        "content"  : content,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    _conversation.append(entry)
    _save_to_file()


def get_history() -> list[dict]:
    """Returns the full conversation history."""
    return _conversation.copy()


def get_gemini_history() -> list[dict]:
    """
    Returns history in the format Gemini API expects:
    [{"role": "user", "parts": [{"text": "..."}]}, ...]

    Note: Gemini uses 'model' instead of 'assistant'.
    """
    gemini_history = []
    for msg in _conversation:
        gemini_role = "model" if msg["role"] == "assistant" else "user"
        gemini_history.append({
            "role" : gemini_role,
            "parts": [{"text": msg["content"]}]
        })
    return gemini_history


def clear_history() -> None:
    """Clears all conversation history from memory and file."""
    global _conversation
    _conversation = []
    if os.path.exists(HISTORY_FILE):
        os.remove(HISTORY_FILE)
    print("[Memory] Conversation history cleared.")


def get_context_summary() -> str:
    """
    Returns a brief summary of recent conversation for context injection.
    Includes only the last 6 messages to keep context window small.
    """
    recent = _conversation[-6:] if len(_conversation) > 6 else _conversation
    if not recent:
        return "No previous conversation."

    lines = []
    for msg in recent:
        prefix = "User" if msg["role"] == "user" else "Assistant"
        lines.append(f"{prefix}: {msg['content'][:120]}")

    return "\n".join(lines)


def _save_to_file() -> None:
    """Saves current conversation to JSON file."""
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(_conversation, f, indent=2, ensure_ascii=False)
    except IOError as e:
        print(f"[Memory Warning] Could not save history: {e}")


def load_from_file() -> None:
    """Loads conversation history from JSON file if it exists."""
    global _conversation
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                _conversation = json.load(f)
            print(f"[Memory] Loaded {len(_conversation)} messages from history.")
        except (json.JSONDecodeError, IOError):
            _conversation = []
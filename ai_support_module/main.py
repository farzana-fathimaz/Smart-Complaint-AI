"""
main.py
───────
AI Support Assistant Entry Point.
Runs a terminal-based chatbot using Google Gemini API.

Features:
- Remembers conversation history
- Fetches real complaint data from Django API
- Guides on escalation and support
- Answers real-time questions

Run:
    python main.py
"""

import re
from memory    import add_message, get_history, get_gemini_history, clear_history, load_from_file
from api_utils import (
    get_ai_response,
    get_ai_response_with_context,
    fetch_complaint,
    fetch_complaint_track,
    fetch_open_complaints,
    fetch_stats,
)

# ── Quick command shortcuts ───────────────────────────────
SPECIAL_COMMANDS = {
    "/clear"  : "clear",     # Clear conversation history
    "/stats"  : "stats",     # Show system statistics
    "/open"   : "open",      # Show open complaints
    "/help"   : "help",      # Show commands
    "/exit"   : "exit",      # Exit the chat
    "/quit"   : "exit",
}

HELP_TEXT = """
╔══════════════════════════════════════════╗
║         AI SUPPORT ASSISTANT COMMANDS    ║
╠══════════════════════════════════════════╣
║  /help      Show this help menu          ║
║  /stats     Show complaint statistics    ║
║  /open      List open complaints         ║
║  /clear     Clear conversation history   ║
║  /exit      Exit the assistant           ║
╠══════════════════════════════════════════╣
║  Or just chat naturally! Examples:       ║
║  "Check complaint 5"                     ║
║  "How do I escalate a complaint?"        ║
║  "What is the electricity helpline?"     ║
╚══════════════════════════════════════════╝
"""


def extract_complaint_id(text: str) -> int | None:
    """
    Extracts complaint ID number from user text.
    Handles: "complaint 5", "ID 12", "check #3", etc.
    """
    # Look for patterns like "complaint 5", "id 12", "#3", just a number
    patterns = [
        r"complaint\s*(?:id|#)?\s*(\d+)",
        r"(?:check|track|status|id|#)\s*(\d+)",
        r"\b(\d+)\b",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return int(match.group(1))
    return None


def handle_special_command(cmd: str) -> bool:
    """
    Handles /commands. Returns True if handled, False if unknown.
    """
    action = SPECIAL_COMMANDS.get(cmd.strip().lower())

    if not action:
        return False

    if action == "help":
        print(HELP_TEXT)

    elif action == "clear":
        clear_history()
        print("[System] Conversation cleared.\n")

    elif action == "stats":
        stats = fetch_stats()
        if stats:
            ov = stats.get("overview", {})
            print(f"\n📊 System Statistics:")
            print(f"  Total Complaints : {ov.get('total_complaints', 0)}")
            print(f"  Open             : {stats.get('by_status', {}).get('Open', 0)}")
            print(f"  In Progress      : {stats.get('by_status', {}).get('In Progress', 0)}")
            print(f"  Resolved         : {ov.get('resolved', 0)}")
            print(f"  Active Staff     : {ov.get('total_staff', 0)}\n")
        else:
            print("[!] Could not fetch stats. Is the Django server running?\n")

    elif action == "open":
        complaints = fetch_open_complaints()
        if complaints:
            print(f"\n📋 Open Complaints ({len(complaints)} shown):")
            for c in complaints:
                print(f"  #{c['id']} | {c['priority']:6} | {c['title'][:50]}")
            print()
        else:
            print("[!] No open complaints found or server unavailable.\n")

    elif action == "exit":
        print("\n👋 Goodbye! AI Assistant closed.\n")
        return "exit"

    return True


def process_user_input(user_input: str) -> bool:
    """
    Processes user input:
    1. Check for /commands
    2. Check for complaint ID mentions — inject real data
    3. Send to Gemini with conversation history

    Returns:
        False if user wants to exit, True otherwise.
    """
    stripped = user_input.strip()

    # ── Handle /commands ──────────────────────────────────
    if stripped.startswith("/"):
        result = handle_special_command(stripped)
        if result == "exit":
            return False
        return True

    # ── Save user message to memory ───────────────────────
    add_message("user", stripped)

    # ── Check if user is asking about a specific complaint ─
    complaint_id = extract_complaint_id(stripped.lower())
    extra_context = ""

    if complaint_id:
        # Try to fetch complaint tracking data
        track_data = fetch_complaint_track(complaint_id)
        if track_data:
            extra_context = (
                f"Complaint #{complaint_id} details: "
                f"Title: {track_data['title']}. "
                f"Status: {track_data['current_status']}. "
                f"Priority: {track_data['priority']}. "
                f"Timeline events: {len(track_data.get('timeline', []))}."
            )
        else:
            extra_context = f"Complaint #{complaint_id} was not found in the system."

    # ── Get Gemini history format ─────────────────────────
    history = get_gemini_history()

    # Remove last message from history (it's the current user message)
    # Gemini adds it via send_message, so we exclude it from history
    if history and history[-1]["role"] == "user":
        history = history[:-1]

    # ── Get AI response ───────────────────────────────────
    if extra_context:
        response = get_ai_response_with_context(stripped, extra_context, history)
    else:
        response = get_ai_response(stripped, history)

    # ── Save and display response ─────────────────────────
    add_message("assistant", response)
    print(f"\n🤖 Assistant: {response}\n")

    return True


def main():
    """Main chat loop."""

    print("=" * 56)
    print("  🤖  Smart CSM — AI Support Assistant")
    print("  Powered by Google Gemini 1.5 Flash")
    print("=" * 56)
    print("  Type /help for commands | /exit to quit")
    print("  Make sure Django server is running on port 8000")
    print("=" * 56 + "\n")

    # Load previous conversation from file
    load_from_file()

    history_count = len(get_history())
    if history_count:
        print(f"[Memory] Resumed with {history_count} previous messages. Type /clear to reset.\n")

    print("🤖 Assistant: Hello! I'm your complaint management AI assistant. "
          "How can I help you today? You can ask me about complaint status, "
          "escalation procedures, or any support questions.\n")

    # ── Main loop ─────────────────────────────────────────
    while True:
        try:
            user_input = input("You: ").strip()

            if not user_input:
                continue

            should_continue = process_user_input(user_input)
            if not should_continue:
                break

        except KeyboardInterrupt:
            print("\n\n[System] Interrupted. Goodbye!")
            break
        except EOFError:
            break


if __name__ == "__main__":
    main()
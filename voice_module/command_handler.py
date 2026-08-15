"""
command_handler.py
──────────────────
Parses voice commands and routes them to the correct API action.
Each handler function manages one specific complaint action.
"""

from voice_input  import speak, listen, listen_for_number
from api_client   import (
    create_complaint,
    get_complaint,
    get_open_complaints,
    get_complaint_track,
    get_departments,
    get_stats,
)


# ─────────────────────────────────────────────────────────
#  COMMAND KEYWORDS
# ─────────────────────────────────────────────────────────

REGISTER_KEYWORDS  = ["register", "new complaint", "add complaint", "create", "submit", "raise"]
STATUS_KEYWORDS    = ["check status", "status", "track", "complaint status", "check complaint"]
LIST_KEYWORDS      = ["list", "open complaints", "show complaints", "all complaints", "active"]
STATS_KEYWORDS     = ["stats", "statistics", "summary", "dashboard", "overview"]
HELP_KEYWORDS      = ["help", "what can you do", "commands", "options"]
EXIT_KEYWORDS      = ["exit", "quit", "goodbye", "bye", "stop", "close"]


def parse_command(text: str) -> str:
    """
    Matches spoken text to a command category.

    Args:
        text: Lowercase transcribed speech.

    Returns:
        Command string: 'register' | 'status' | 'list' |
                        'stats' | 'help' | 'exit' | 'unknown'
    """
    if any(k in text for k in EXIT_KEYWORDS):
        return "exit"
    if any(k in text for k in REGISTER_KEYWORDS):
        return "register"
    if any(k in text for k in STATUS_KEYWORDS):
        return "status"
    if any(k in text for k in LIST_KEYWORDS):
        return "list"
    if any(k in text for k in STATS_KEYWORDS):
        return "stats"
    if any(k in text for k in HELP_KEYWORDS):
        return "help"
    return "unknown"


# ─────────────────────────────────────────────────────────
#  HANDLER: REGISTER COMPLAINT
# ─────────────────────────────────────────────────────────

def handle_register_complaint() -> None:
    """
    Guides the user through registering a new complaint via voice.
    Collects: title, description, department, name — then POSTs to API.
    """
    speak("Let's register your complaint. I'll ask you a few questions.")

    # ── Step 1: Get complaint title ──────────────────────
    speak("Please say the title of your complaint.")
    title = listen("Say the complaint title")
    if not title:
        speak("I didn't catch the title. Cancelling registration.")
        return

    # ── Step 2: Get complaint description ────────────────
    speak("Now describe the issue in detail.")
    description = listen("Describe the issue", timeout=15)
    if not description:
        speak("I didn't catch the description. Please try again.")
        return

    # ── Step 3: Choose department ────────────────────────
    departments = get_departments()
    if not departments:
        speak("Could not fetch departments. Please check if the server is running.")
        return

    # Read departments aloud
    speak("Which department should handle this? Here are the options:")
    dept_map = {}
    for i, dept in enumerate(departments, 1):
        speak(f"{i}. {dept['name']}")
        dept_map[i] = dept

    dept_num = listen_for_number("Say the department number")
    if not dept_num or dept_num not in dept_map:
        speak("Invalid department selection. Using department 1 by default.")
        dept_num = 1

    selected_dept = dept_map[dept_num]
    speak(f"You selected {selected_dept['name']}.")

    # ── Step 4: Get user's name ──────────────────────────
    speak("Please say your name.")
    name = listen("Say your name")
    if not name:
        name = "Anonymous"
    speak(f"Thank you, {name}.")

    # ── Step 5: Confirm and submit ───────────────────────
    speak(f"Submitting your complaint: {title}. Please wait.")
    result = create_complaint(title, description, selected_dept["id"], name)

    if result and "complaint" in result:
        c = result["complaint"]
        speak(
            f"Complaint registered successfully! "
            f"Your complaint ID is {c['id']}. "
            f"Priority has been set to {c['priority']}. "
            f"Please note this ID to track your complaint later."
        )
    else:
        speak("Sorry, I couldn't register the complaint. Please try again.")


# ─────────────────────────────────────────────────────────
#  HANDLER: CHECK COMPLAINT STATUS
# ─────────────────────────────────────────────────────────

def handle_check_status() -> None:
    """
    Asks for a complaint ID and reads out its current status and timeline.
    """
    speak("Sure! I'll check the complaint status for you.")
    complaint_id = listen_for_number("Please say the complaint ID number.")

    if not complaint_id:
        speak("I couldn't get the complaint ID. Please try again.")
        return

    speak(f"Fetching details for complaint number {complaint_id}. Please wait.")
    data = get_complaint_track(complaint_id)

    if not data:
        speak(f"I couldn't find any complaint with ID {complaint_id}. Please check the number.")
        return

    # Read out the complaint details
    speak(
        f"Complaint ID {data['complaint_id']}: {data['title']}. "
        f"Current status is {data['current_status']}. "
        f"Priority is {data['priority']}."
    )

    # Read timeline
    if data.get("timeline"):
        speak("Here is the complaint timeline:")
        for event in data["timeline"]:
            speak(f"{event['event']}: {event['detail']}.")
    else:
        speak("No timeline events recorded yet.")


# ─────────────────────────────────────────────────────────
#  HANDLER: LIST OPEN COMPLAINTS
# ─────────────────────────────────────────────────────────

def handle_list_open_complaints() -> None:
    """
    Fetches and reads aloud all complaints with status 'Open'.
    """
    speak("Fetching all open complaints. Please wait.")
    complaints = get_open_complaints()

    if not complaints:
        speak("Great news! There are no open complaints at the moment.")
        return

    speak(f"There are {len(complaints)} open complaints.")

    # Read first 5 to avoid very long responses
    limit      = min(len(complaints), 5)
    speak(f"I will read the first {limit} complaints.")

    for i, c in enumerate(complaints[:limit], 1):
        speak(
            f"Complaint {i}: ID {c['id']}. "
            f"Title: {c['title']}. "
            f"Priority: {c['priority']}. "
            f"Department: {c.get('department_name', 'Unknown')}."
        )

    if len(complaints) > 5:
        speak(f"And {len(complaints) - 5} more. Visit the dashboard to see all.")


# ─────────────────────────────────────────────────────────
#  HANDLER: DASHBOARD STATS
# ─────────────────────────────────────────────────────────

def handle_stats() -> None:
    """
    Fetches and reads aloud key dashboard statistics.
    """
    speak("Fetching system statistics.")
    stats = get_stats()

    if not stats:
        speak("Could not fetch statistics. Please check the server.")
        return

    ov = stats.get("overview", {})
    speak(
        f"Here is the system summary. "
        f"Total complaints: {ov.get('total_complaints', 0)}. "
        f"Open complaints: {stats.get('by_status', {}).get('Open', 0)}. "
        f"Resolved: {ov.get('resolved', 0)}. "
        f"Active staff: {ov.get('total_staff', 0)}. "
        f"Total departments: {ov.get('total_departments', 0)}."
    )


# ─────────────────────────────────────────────────────────
#  HANDLER: HELP
# ─────────────────────────────────────────────────────────

def handle_help() -> None:
    """Reads available voice commands aloud."""
    speak(
        "Here are the commands you can use. "
        "Say 'Register complaint' to create a new complaint. "
        "Say 'Check status' followed by a complaint ID to track progress. "
        "Say 'List open complaints' to hear all active issues. "
        "Say 'Statistics' for a system summary. "
        "Say 'Exit' or 'Quit' to close the assistant."
    )


# ─────────────────────────────────────────────────────────
#  MAIN DISPATCHER
# ─────────────────────────────────────────────────────────

def dispatch(command: str) -> bool:
    """
    Routes a parsed command to the correct handler.

    Returns:
        False if the user wants to exit, True otherwise.
    """
    if command == "register":
        handle_register_complaint()
    elif command == "status":
        handle_check_status()
    elif command == "list":
        handle_list_open_complaints()
    elif command == "stats":
        handle_stats()
    elif command == "help":
        handle_help()
    elif command == "exit":
        speak("Goodbye! Have a great day.")
        return False
    else:
        speak("I didn't understand that command. Say 'help' to hear available commands.")

    return True
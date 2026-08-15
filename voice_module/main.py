"""
main.py
───────
Entry point for the Voice Complaint Assistant.
Starts the voice loop and keeps listening until user says exit.

Run:
    python main.py
"""

from voice_input     import speak, listen
from command_handler import parse_command, dispatch


WELCOME_MESSAGE = (
    "Welcome to the Smart Complaint Management Voice Assistant. "
    "I can help you register complaints, check status, and list open issues. "
    "Say 'help' to hear all available commands, or say 'exit' to quit."
)

IDLE_PROMPT = (
    "What would you like to do? "
    "Say a command or say 'help'."
)


def main():
    """Main voice assistant loop."""

    print("=" * 55)
    print("  🎙️  Smart Complaint Voice Assistant")
    print("  Make sure Django server is running on port 8000")
    print("=" * 55)

    # Greet the user
    speak(WELCOME_MESSAGE)

    running = True
    while running:
        # Prompt user
        speak(IDLE_PROMPT)

        # Listen for command
        text = listen("Waiting for your command...")

        if text is None:
            # No speech detected — loop again
            continue

        # Parse what the user said
        command = parse_command(text)
        print(f"[COMMAND PARSED]: {command}")

        # Dispatch to correct handler
        running = dispatch(command)

    print("\n[System] Voice assistant stopped.")


if __name__ == "__main__":
    main()
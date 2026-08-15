"""
main.py
───────
Speech-to-Image Issue Visualization System.

Flow:
1. User selects language
2. User speaks a complaint description
3. Text is sent to MonsterAPI to generate an image
4. Image is saved locally

Run:
    python main.py
"""

import os
from speech_input    import listen_for_complaint, select_language, get_complaint_text_from_file
from image_generator import generate_image

BANNER = """
╔══════════════════════════════════════════╗
║   🎙️  Speech-to-Image Complaint System   ║
║   Speak → Visualize → Save               ║
╚══════════════════════════════════════════╝
"""

MENU = """
Choose input mode:
  1. 🎙️  Speak a complaint (microphone)
  2. 📁  Load from audio file
  3. ⌨️  Type a complaint (text input)
  4. 🚪  Exit
"""


def run_microphone_mode(language_code: str) -> None:
    """Captures complaint from microphone and generates image."""
    complaint_text = listen_for_complaint(language_code=language_code)

    if not complaint_text:
        print("⚠️  No complaint captured. Try again.\n")
        return

    print(f"\n📝 Your complaint: \"{complaint_text}\"")
    confirm = input("Generate image for this complaint? (y/n): ").strip().lower()

    if confirm != "y":
        print("Cancelled.\n")
        return

    image_path = generate_image(complaint_text)

    if image_path:
        print(f"\n🎉 Success! Image saved at: {image_path}")
        print(f"   Open the '{os.path.dirname(image_path)}' folder to view it.")
    else:
        print("\n⚠️  Image generation failed. Check your API key and internet.")


def run_file_mode() -> None:
    """Transcribes speech from an audio file and generates image."""
    filepath = input("Enter path to audio file (WAV/FLAC/AIFF): ").strip()

    complaint_text = get_complaint_text_from_file(filepath)
    if not complaint_text:
        return

    image_path = generate_image(complaint_text)
    if image_path:
        print(f"\n🎉 Image saved: {image_path}")


def run_text_mode() -> None:
    """Takes typed complaint text and generates image."""
    complaint_text = input("\nType your complaint description: ").strip()

    if len(complaint_text) < 10:
        print("⚠️  Description too short. Please be more descriptive.")
        return

    image_path = generate_image(complaint_text)
    if image_path:
        print(f"\n🎉 Image saved: {image_path}")


def main():
    """Main application loop."""
    print(BANNER)

    # Select language once at startup
    language_code = select_language()

    while True:
        print(MENU)
        choice = input("Enter choice (1-4): ").strip()

        if choice == "1":
            run_microphone_mode(language_code)
        elif choice == "2":
            run_file_mode()
        elif choice == "3":
            run_text_mode()
        elif choice == "4":
            print("\n👋 Goodbye!\n")
            break
        else:
            print("⚠️  Invalid choice. Enter 1, 2, 3, or 4.\n")


if __name__ == "__main__":
    main()
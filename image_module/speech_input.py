"""
speech_input.py
───────────────
Captures microphone audio and converts speech to text.
Supports multiple languages via Google Web Speech API.
"""

import speech_recognition as sr

# All supported languages with their BCP-47 codes
SUPPORTED_LANGUAGES = {
    "1" : ("English (India)",  "en-IN"),
    "2" : ("English (US)",     "en-US"),
    "3" : ("Hindi",            "hi-IN"),
    "4" : ("Tamil",            "ta-IN"),
    "5" : ("Telugu",           "te-IN"),
    "6" : ("Kannada",          "kn-IN"),
    "7" : ("Malayalam",        "ml-IN"),
    "8" : ("Bengali",          "bn-IN"),
    "9" : ("Marathi",          "mr-IN"),
    "10": ("Spanish",          "es-ES"),
}

# Initialize recognizer
_recognizer = sr.Recognizer()
_recognizer.energy_threshold         = 300
_recognizer.dynamic_energy_threshold = True
_recognizer.pause_threshold          = 1.0


def list_languages() -> None:
    """Prints available languages to the console."""
    print("\n── Available Languages ──────────────────")
    for key, (name, code) in SUPPORTED_LANGUAGES.items():
        print(f"  {key:>2}. {name} ({code})")
    print("─────────────────────────────────────────")


def select_language() -> str:
    """
    Prompts user to select a language and returns the BCP-47 code.
    Defaults to English (India) if invalid input.
    """
    list_languages()
    choice = input("\nSelect language number (press Enter for English India): ").strip()

    if choice in SUPPORTED_LANGUAGES:
        name, code = SUPPORTED_LANGUAGES[choice]
        print(f"✅ Language set to: {name}")
        return code

    print("⚡ Defaulting to English (India)")
    return "en-IN"


def listen_for_complaint(language_code: str = "en-IN", timeout: int = 10) -> str | None:
    """
    Listens to the microphone and returns transcribed complaint text.

    Args:
        language_code: BCP-47 language code (e.g., "hi-IN" for Hindi)
        timeout      : Max seconds to wait for speech

    Returns:
        Transcribed string, or None if failed.
    """
    with sr.Microphone() as source:
        print("\n🎙️  Adjusting for ambient noise... Please wait.")
        _recognizer.adjust_for_ambient_noise(source, duration=1)

        print("🎙️  Listening... Speak your complaint now.")

        try:
            audio = _recognizer.listen(source, timeout=timeout, phrase_time_limit=20)
            print("⏳ Processing speech...")

            text = _recognizer.recognize_google(audio, language=language_code)
            print(f"\n✅ Transcribed: {text}")
            return text

        except sr.WaitTimeoutError:
            print("⚠️  No speech detected. Please try again.")
            return None
        except sr.UnknownValueError:
            print("⚠️  Could not understand speech. Please speak clearly.")
            return None
        except sr.RequestError as e:
            print(f"❌ Speech service error: {e}")
            print("   Make sure you have an active internet connection.")
            return None


def get_complaint_text_from_file(filepath: str) -> str | None:
    """
    Alternative: transcribes speech from an audio file instead of microphone.
    Supports WAV, AIFF, FLAC formats.

    Args:
        filepath: Path to the audio file.

    Returns:
        Transcribed text, or None if failed.
    """
    try:
        with sr.AudioFile(filepath) as source:
            audio = _recognizer.record(source)
            text  = _recognizer.recognize_google(audio, language="en-IN")
            print(f"✅ Transcribed from file: {text}")
            return text
    except FileNotFoundError:
        print(f"❌ Audio file not found: {filepath}")
        return None
    except Exception as e:
        print(f"❌ Error transcribing file: {e}")
        return None
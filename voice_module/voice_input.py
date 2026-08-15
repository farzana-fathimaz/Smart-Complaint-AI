"""
voice_input.py
──────────────
Handles microphone input (speech-to-text)
and speaker output (text-to-speech).
"""

import speech_recognition as sr
import pyttsx3


# ─────────────────────────────────────────────────────────
#  TEXT-TO-SPEECH SETUP
# ─────────────────────────────────────────────────────────

# Initialize the TTS engine once at module level
_engine = pyttsx3.init()

# Set voice properties
_engine.setProperty("rate", 165)    # Speed (words per minute)
_engine.setProperty("volume", 1.0)  # Volume (0.0 to 1.0)

# Try to use a female voice if available
voices = _engine.getProperty("voices")
for voice in voices:
    if "female" in voice.name.lower() or "zira" in voice.name.lower():
        _engine.setProperty("voice", voice.id)
        break


def speak(text: str) -> None:
    """
    Converts text to speech and plays it aloud.

    Args:
        text: The string to speak out loud.
    """
    print(f"\n[🤖 Assistant]: {text}")
    _engine.say(text)
    _engine.runAndWait()


# ─────────────────────────────────────────────────────────
#  SPEECH-TO-TEXT SETUP
# ─────────────────────────────────────────────────────────

# Initialize recognizer
_recognizer = sr.Recognizer()

# Tune sensitivity
_recognizer.energy_threshold       = 300   # Minimum audio energy to consider for recording
_recognizer.dynamic_energy_threshold = True  # Auto-adjust for ambient noise
_recognizer.pause_threshold        = 0.8   # Seconds of silence before phrase is considered complete


def listen(prompt: str = "Listening...", timeout: int = 8) -> str | None:
    """
    Captures microphone input and converts it to text.

    Args:
        prompt : Message to display while listening.
        timeout: How long to wait for speech (seconds).

    Returns:
        Transcribed text string, or None if recognition failed.
    """
    with sr.Microphone() as source:
        print(f"\n[🎙️  {prompt}]")

        # Adjust for ambient noise (0.5 sec calibration)
        _recognizer.adjust_for_ambient_noise(source, duration=0.5)

        try:
            # Listen for speech
            audio = _recognizer.listen(source, timeout=timeout, phrase_time_limit=15)

            # Use Google Web Speech API (free, no API key needed)
            text = _recognizer.recognize_google(audio, language="en-IN")
            print(f"[👂 You said]: {text}")
            return text.lower().strip()

        except sr.WaitTimeoutError:
            speak("I didn't hear anything. Please try again.")
            return None
        except sr.UnknownValueError:
            speak("Sorry, I couldn't understand that.")
            return None
        except sr.RequestError as e:
            speak("Speech service is unavailable. Please check your internet.")
            print(f"[ERROR] Speech recognition service error: {e}")
            return None


def listen_for_number(prompt: str = "Please say a number") -> int | None:
    """
    Listens specifically for a number and returns it as int.

    Returns:
        Integer if recognized, None otherwise.
    """
    speak(prompt)
    text = listen(prompt="Say a number")
    if text:
        # Extract digits from the spoken text
        digits = "".join(filter(str.isdigit, text))
        if digits:
            return int(digits)
        # Handle word numbers
        word_map = {
            "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
            "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10
        }
        for word, num in word_map.items():
            if word in text:
                return num
    return None
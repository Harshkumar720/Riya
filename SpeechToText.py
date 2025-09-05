# SpeechToText.py
import speech_recognition as sr
import mtranslate as mt
import re

# -------------------- Helper Functions --------------------
def QueryModifier(query: str) -> str:
    """
    Add proper punctuation to the query and capitalize first letter.
    """
    query = query.strip()
    question_words = [
        "how", "what", "who", "where", "when", "why", "which", "whose", "whom",
        "can you", "what's", "where's", "how's"
    ]
    if any(query.lower().startswith(q) for q in question_words):
        if not query.endswith("?"):
            query += "?"
    else:
        if not query.endswith("."):
            query += "."
    return query[0].upper() + query[1:]

def UniversalTranslator(text: str) -> str:
    """
    Translate any text to English.
    """
    try:
        return mt(text, "en", "auto").capitalize()
    except Exception:
        return text

# -------------------- Speech-to-Text Function --------------------
def SpeechToText(recognizer, source) -> str:
    """
    Capture speech from microphone and return translated + punctuated text.
    """
    try:
        audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
        recognized_text = recognizer.recognize_google(audio)
        translated_text = UniversalTranslator(recognized_text)
        final_text = QueryModifier(translated_text)
        return final_text
    except sr.WaitTimeoutError:
        return ""  # No speech detected
    except sr.UnknownValueError:
        return ""  # Could not understand audio
    except sr.RequestError as e:
        print(f"⚠️ Could not request results; {e}")
        return ""

# -------------------- Main --------------------
if __name__ == "__main__":
    recognizer = sr.Recognizer()
    microphone = sr.Microphone()

    print("🎤 Listening continuously (say 'exit', 'quit', or 'bye' to stop)...")
    last_text = ""  # to avoid duplicates

    exit_keywords = ["exit", "quit", "bye"]

    with microphone as source:
        recognizer.adjust_for_ambient_noise(source, duration=1)

        while True:
            text = SpeechToText(recognizer, source)
            if not text:
                continue

            # Check if any exit keyword is in the recognized text (case-insensitive)
            if any(word in text.lower() for word in exit_keywords):
                break  # exit silently

            # Avoid printing duplicates
            if text != last_text:
                print("You said:", text)
                last_text = text


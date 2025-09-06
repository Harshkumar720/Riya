import speech_recognition as sr
import mtranslate as mt
import re
import pygame
import asyncio
import edge_tts
import os
import tempfile
import random
import threading
from dotenv import dotenv_values
import time

# -------------------- Load Environment --------------------
env_vars = dotenv_values(".env")
AssistantVoice = env_vars.get("AssistantVoice", "en-US-JennyNeural")
AssistantMode = env_vars.get("AssistantMode", "friendly").lower()  # friendly | echo
AssistantRate  = env_vars.get("AssistantRate", "-15%")
AssistantPitch = env_vars.get("AssistantPitch", "-2Hz")

# -------------------- Initialize Pygame --------------------
pygame.mixer.init()

# -------------------- Global Stop Flag --------------------
TTS_STOP_FLAG = False  # ✅ Interrupt TTS if needed

# Manage playback + resume
_PLAY_LOCK = threading.Lock()
_PLAY_THREAD = None
LAST_REPLY = ""               # ✅ will store last spoken reply
LAST_WAS_INTERRUPTED = False  # ✅ true if we stopped mid-utterance

# -------------------- Helper Functions --------------------
def QueryModifier(query: str) -> str:
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
    return query[0].upper() + query[1:] if query else query

def UniversalTranslator(text: str) -> str:
    try:
        return mt(text, "en", "auto").capitalize()
    except Exception:
        return text

def clean_text_for_speech(text):
    emoji_pattern = re.compile(
        "[" 
        "\U0001F600-\U0001F64F"
        "\U0001F300-\U0001F5FF"
        "\U0001F680-\U0001F6FF"
        "\U0001F1E0-\U0001F1FF"
        "\U00002700-\U000027BF"
        "\U0001F900-\U0001F9FF"
        "\U0001FA70-\U0001FAFF"
        "]+", flags=re.UNICODE
    )
    return emoji_pattern.sub(r'', text)

# -------------------- Speech Recognition --------------------
def SpeechToText(recognizer, source) -> str:
    try:
        audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
        recognized_text = recognizer.recognize_google(audio)
        translated_text = UniversalTranslator(recognized_text)
        final_text = QueryModifier(translated_text)
        return final_text
    except sr.WaitTimeoutError:
        return ""
    except sr.UnknownValueError:
        return ""
    except sr.RequestError as e:
        print(f"⚠️ Could not request results; {e}")
        return ""

# -------------------- Text-to-Speech (Edge + pygame, interruptible) --------------------
async def text_to_audio_file(text, file_path):
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
        except Exception:
            pass
    communicate = edge_tts.Communicate(text, AssistantVoice, pitch=AssistantPitch, rate=AssistantRate)
    await communicate.save(file_path)

def _play_audio(file_path):
    global TTS_STOP_FLAG, LAST_WAS_INTERRUPTED
    try:
        pygame.mixer.music.load(file_path)
        pygame.mixer.music.play()
    except Exception as e:
        print(f"⚠️ Audio play error: {e}")
        return

    interrupted = False
    while pygame.mixer.music.get_busy():
        if TTS_STOP_FLAG:
            try:
                pygame.mixer.music.stop()
            except Exception:
                pass
            interrupted = True
            break
        pygame.time.Clock().tick(20)

    # mark state for resume logic
    LAST_WAS_INTERRUPTED = interrupted

def stop_tts():
    """
    Immediately stop current speech playback.
    """
    global TTS_STOP_FLAG, LAST_WAS_INTERRUPTED
    TTS_STOP_FLAG = True
    LAST_WAS_INTERRUPTED = True
    try:
        pygame.mixer.music.stop()
    except Exception:
        pass
    time.sleep(0.02)  # let mixer settle

def TTS(text):
    """Interruptible TTS using edge-tts + pygame, non-blocking."""
    global TTS_STOP_FLAG, _PLAY_THREAD, LAST_REPLY, LAST_WAS_INTERRUPTED

    if not text or not text.strip():
        return

    # Remember last reply for resume
    LAST_REPLY = text
    LAST_WAS_INTERRUPTED = False

    # Clean text for audio (remove emojis etc.)
    text_for_speech = clean_text_for_speech(text)

    # Stop any ongoing playback before starting new
    with _PLAY_LOCK:
        stop_tts()
        TTS_STOP_FLAG = False

    # Temp mp3 path
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_file:
        file_path = temp_file.name

    # Generate audio file (robust to nested event loop)
    try:
        asyncio.run(text_to_audio_file(text_for_speech, file_path))
    except RuntimeError:
        # If we're already inside an event loop (e.g., GUI), use a fresh loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(text_to_audio_file(text_for_speech, file_path))
        loop.close()

    # Play audio in separate thread
    with _PLAY_LOCK:
        _PLAY_THREAD = threading.Thread(target=_play_audio, args=(file_path,), daemon=True)
        _PLAY_THREAD.start()

# -------------------- Main Loop --------------------
if __name__ == "__main__":
    recognizer = sr.Recognizer()
    microphone = sr.Microphone()

    exit_keywords = ["exit", "quit", "bye"]
    stop_keywords = ["stop", "pause", "be quiet", "chup", "mute"]
    resume_keywords = ["resume", "continue", "bol", "speak"]
    last_text = ""

    friendly_responses = {
        "hi": [
            "Hello sir! How are you today?",
            "Hi there! Ready to assist you.",
            "Greetings! Always happy to help."
        ],
        "how are you": [
            "I'm doing great, thank you for asking!",
            "Always ready to help you, sir.",
            "Feeling awesome, how about you?"
        ],
        "default": [
            "Okay, working on it.",
            "I'm on it, just a moment please.",
            "Let me take care of that."
        ]
    }

    print("🎤 Listening continuously (say 'exit' to quit, 'stop' to pause TTS, 'resume' to replay last reply)...")
    with microphone as source:
        recognizer.adjust_for_ambient_noise(source, duration=1)

        while True:
            text = SpeechToText(recognizer, source)
            if not text:
                continue

            low = text.lower()

            # Exit
            if any(word in low for word in exit_keywords):
                TTS_STOP_FLAG = True
                stop_tts()
                break

            # Pause current TTS immediately
            if any(word in low for word in stop_keywords):
                print("⏸ TTS paused. Say 'resume' to replay last reply.")
                stop_tts()
                continue  # keep listening

            # Resume (replay last reply if it was interrupted)
            if any(word in low for word in resume_keywords):
                print("▶️ Resuming.")
                # clear stop and replay last reply only if it was interrupted
                TTS_STOP_FLAG = False
                if LAST_WAS_INTERRUPTED and LAST_REPLY:
                    TTS(LAST_REPLY)
                else:
                    TTS("Resumed.")
                continue

            if text == last_text:
                continue
            last_text = text

            print("You said:", text)

            if AssistantMode == "echo":
                reply = text
            else:
                if "hi" in low:
                    reply = random.choice(friendly_responses["hi"])
                elif "how are you" in low:
                    reply = random.choice(friendly_responses["how are you"])
                else:
                    reply = random.choice(friendly_responses["default"])

            print(f"Riya: {reply}")
            TTS(reply)

    pygame.mixer.quit()

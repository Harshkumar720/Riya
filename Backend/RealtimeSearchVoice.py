# Backend/RealtimeSearchVoice.py
import speech_recognition as sr
import sys
import os
import datetime  # ✅ for time-based greeting

# ✅ Ensure Backend folder is in sys.path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Backend.SpeechToSpeech import SpeechToText, TTS, TTS_STOP_FLAG, stop_tts
from Backend.RealtimeSearchEngine import RealtimeSearchEngine

# ✅ Greeting config
USERNAME = "Harsh"
ASSISTANT_NAME = "Riya"

def greet_user():
    now = datetime.datetime.now()
    hour = now.hour
    if 5 <= hour < 12:
        greeting = "Good Morning"
    elif 12 <= hour < 17:
        greeting = "Good Afternoon"
    else:
        greeting = "Good Evening"
    msg = f"{greeting} {USERNAME}, I am {ASSISTANT_NAME}. How can I help you today?"
    print(f"{ASSISTANT_NAME}: {msg}")
    TTS(msg)

# -------------------- Voice Search Loop --------------------
def voice_search_loop():
    global TTS_STOP_FLAG

    recognizer = sr.Recognizer()
    microphone = sr.Microphone()
    exit_keywords = ["exit", "quit", "bye"]
    stop_keywords = ["stop", "pause", "be quiet", "chup", "mute"]
    resume_keywords = ["resume", "continue", "bol", "speak"]
    last_text = ""
    last_answer = ""   # ✅ always holds the latest answer

    # ✅ Speak greeting first
    greet_user()

    print("🎤 Speak your query (say 'exit', 'quit', 'bye' to stop, 'stop' to pause TTS, 'resume' to continue)...")

    with microphone as source:
        recognizer.adjust_for_ambient_noise(source, duration=1)

        while True:
            query = SpeechToText(recognizer, source)
            if not query:
                continue

            lower_query = query.lower()

            # Exit loop completely
            if any(word in lower_query for word in exit_keywords):
                print("Exiting voice search...")
                TTS_STOP_FLAG = True
                stop_tts()
                break

            # Pause TTS
            if any(word in lower_query for word in stop_keywords):
                print("⏸ TTS paused. Say 'resume' to continue speaking the latest answer.")
                TTS_STOP_FLAG = True
                stop_tts()
                continue

            # Resume TTS → continue speaking the latest answer
            if any(word in lower_query for word in resume_keywords):
                print("▶️ Resuming TTS with the latest answer.")
                TTS_STOP_FLAG = False
                if last_answer:
                    stop_tts()
                    TTS(last_answer)  # ✅ continue speaking the newest answer
                else:
                    TTS("There is no new answer to continue.")
                continue

            # Avoid duplicate recognition
            if query == last_text:
                continue
            last_text = query

            print(f"🔍 Searching for: {query}")
            try:
                answer = RealtimeSearchEngine(query)
            except Exception as e:
                answer = f"⚠️ Error fetching result: {str(e)}"

            print(f"💡 Answer:\n{answer}")
            last_answer = answer  # ✅ always update with latest result

            # Speak only if TTS is not paused
            if not TTS_STOP_FLAG:
                stop_tts()
                TTS(answer)

# -------------------- Run --------------------
if __name__ == "__main__":
    voice_search_loop()

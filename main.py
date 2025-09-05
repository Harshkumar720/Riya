# main.py
import sys
import json
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# -------------------- Paths --------------------
ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "Data"
HISTORY_PATH = DATA_DIR / "GUIChatLog.json"

# Load .env from project root explicitly
load_dotenv(dotenv_path=str(ROOT / ".env"))

# -------------------- Alias for Chatbot's 'from Model import ...' --------------------
import importlib
try:
    Models_mod = importlib.import_module("Backend.Models")
    sys.modules.setdefault("Model", Models_mod)
except Exception:
    pass

# -------------------- Qt / Threads -------------------------------------------------
from PyQt5.QtCore import QObject, QThread, pyqtSignal
from PyQt5.QtWidgets import QApplication

# -------------------- External libs (mic) ------------------------------------------
import speech_recognition as sr

# -------------------- Project modules (package imports) -----------------------------
from Frontend import GUI
from Backend.SpeechToText import SpeechToText
from Backend.SpeechToSpeech import TTS, stop_tts
from Backend.RealtimeSearchEngine import RealtimeSearchEngine
from Backend.Automation import automation_commands
from Backend.Chatbot import chat_with_ai

# -------------------- STT Worker ---------------------------------------------------
class STTWorker(QObject):
    text_ready = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._stop = False

    def stop(self):
        self._stop = True

    def run(self):
        """Continuously listens and emits recognized text."""
        recognizer = sr.Recognizer()
        try:
            with sr.Microphone() as source:
                recognizer.adjust_for_ambient_noise(source, duration=1)
                while not self._stop:
                    text = SpeechToText(recognizer, source)
                    if self._stop:
                        break
                    if text:
                        self.text_ready.emit(text)
        except Exception as e:
            self.error.emit(f"⚠️ Microphone error: {e}")

# -------------------- App Controller ----------------------------------------------
class RiyaController(QObject):
    append_chat = pyqtSignal(str)     # Thread-safe text appending to chat_display
    set_busy = pyqtSignal(bool)       # Optional: show busy state if you add a spinner/label

    def __init__(self):
        super().__init__()
        # Ensure data dir & history file exist
        DATA_DIR.mkdir(exist_ok=True)
        if not HISTORY_PATH.exists():
            HISTORY_PATH.write_text("[]", encoding="utf-8")

        # GUI
        self.gui = GUI.RiyaGUI()

        # Disconnect GUI’s built-in mic click handler and replace with ours
        try:
            self.gui.mic_button.clicked.disconnect()
        except Exception:
            pass
        self.gui.mic_button.clicked.connect(self.on_mic_clicked)

        # Wire send button (Enter already triggers send_button via GUI.eventFilter)
        self.gui.send_button.clicked.connect(self.on_send_clicked)

        # Wire Clear button if present in your GUI (safe even if not)
        try:
            self.gui.clear_button.clicked.connect(self.gui.clear_chat)
        except Exception:
            pass

        # Signals to update UI
        self.append_chat.connect(self._append_chat_safely)
        try:
            self.set_busy.connect(self.gui.set_thinking)  # if GUI has thinking label
        except Exception:
            pass

        # STT worker/thread placeholders
        self._stt_thread = None
        self._stt_worker = None

        # 🔔 Show greeting immediately (in UI + TTS), then load history below it, then persist greeting
        try:
            self._show_greeting_then_load_and_save()
        except Exception:
            # Non-fatal, continue even if TTS or file IO fails
            pass

    # ---------------- Greeting + load order ----------------
    def _make_greeting_message(self) -> str:
        hour = datetime.now().hour
        if 5 <= hour < 12:
            greeting = "Good Morning"
        elif 12 <= hour < 17:
            greeting = "Good Afternoon"
        else:
            greeting = "Good Evening"
        return f"{greeting} Sir, what's your plan today?"

    def _show_greeting_then_load_and_save(self):
        """
        1) Show + speak greeting immediately,
        2) Load & render previous history below greeting,
        3) Persist the greeting so it appears in future runs.
        """
        # 1) Show + speak greeting (do not persist yet)
        message = self._make_greeting_message()
        self.append_chat.emit(f"🤖 Riya: {message}")
        try:
            stop_tts()
            TTS(message)
        except Exception:
            # non-fatal TTS failure
            pass

        # 2) Load previous history and render it BELOW the greeting
        self._load_history_into_ui()

        # 3) Persist greeting to history for future runs
        try:
            self._save_message("assistant", message)
        except Exception:
            pass

    # ---------------- Persistence ----------------
    def _load_history_into_ui(self):
        """Load past chats from HISTORY_PATH and display in the chat box."""
        try:
            data = json.loads(HISTORY_PATH.read_text(encoding="utf-8") or "[]")
            # Expecting list of {"role":"user"/"assistant","content":str,"ts": "..."}
            for item in data:
                role = (item.get("role") or "").lower()
                content = item.get("content") or ""
                if not content:
                    continue
                if role == "user":
                    self._append_chat_safely(f"🧑 You: {content}")
                elif role == "assistant":
                    self._append_chat_safely(f"🤖 Riya: {content}")
                else:
                    # Unknown role—show raw
                    self._append_chat_safely(content)
        except Exception as e:
            self._append_chat_safely(f"⚠️ Failed to load chat history: {e}")

    def _save_message(self, role: str, content: str):
        """Append a message to HISTORY_PATH with timestamp."""
        try:
            data = json.loads(HISTORY_PATH.read_text(encoding="utf-8") or "[]")
        except Exception:
            data = []
        data.append({
            "role": role,
            "content": content,
            "ts": datetime.now().isoformat(timespec="seconds")
        })
        # Keep file from growing unbounded (optional: last 1000 messages)
        if len(data) > 1000:
            data = data[-1000:]
        HISTORY_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    # ---------------- Routing & UI ----------------
    def on_send_clicked(self):
        text = self.gui.input_box.toPlainText().strip()
        if not text:
            return
        self.gui.input_box.clear()
        self.handle_user_text(text)

    def on_mic_clicked(self):
        """Mirror GUI icon toggle, then start/stop STT worker."""
        try:
            self.gui.toggle_mic_icon()
        except Exception as e:
            self.append_chat.emit(f"⚠️ Mic toggle error: {e}")
            return

        if getattr(self.gui, "mic_on", False):
            self.start_stt()
        else:
            self.stop_stt()

    def start_stt(self):
        if self._stt_thread and self._stt_thread.isRunning():
            return  # already running

        self._stt_worker = STTWorker()
        self._stt_thread = QThread()
        self._stt_worker.moveToThread(self._stt_thread)

        self._stt_thread.started.connect(self._stt_worker.run)
        self._stt_worker.text_ready.connect(self.handle_user_text)
        self._stt_worker.error.connect(self.append_chat.emit)

        # Ensure cleanup when thread finishes
        self._stt_thread.finished.connect(self._stt_thread.deleteLater)
        self._stt_thread.finished.connect(self._clear_worker_refs)

        self._stt_thread.start()

    def stop_stt(self):
        if self._stt_worker:
            self._stt_worker.stop()
        if self._stt_thread:
            self._stt_thread.quit()
            self._stt_thread.wait(1500)  # wait up to ~1.5s for clean stop

    def _clear_worker_refs(self):
        self._stt_worker = None
        self._stt_thread = None

    def handle_user_text(self, text: str):
        """Append user text, route it, append answer, speak it, and persist both."""
        try:
            # show + save user message
            self.append_chat.emit(f"🧑 You: {text}")
            self._save_message("user", text)
            try:
                self.set_busy.emit(True)
            except Exception:
                pass

            # --------- Priority routing ----------
            low = text.lower().strip()

            # 1) Automation intents (open/close/create/ppt/whatsapp/etc.)
            automation_triggers = (
                "open", "launch", "close", "create a folder",
                "create pdf from recent downloads", "whatsapp", "ppt", "presentation"
            )
            if any(trig in low for trig in automation_triggers):
                answer = automation_commands(text)  # pass original text

            # 2) Real-time: weather/news/stock/crypto keywords
            elif any(k in low for k in (
                "weather", "news", "stock", "stock price", "crypto",
                "bitcoin", "ethereum", "solana", "dogecoin"
            )):
                answer = RealtimeSearchEngine(text)

            # 3) Otherwise: general chat
            else:
                answer = chat_with_ai(text)

            # show + save assistant message
            self.append_chat.emit(f"🤖 Riya: {answer}")
            self._save_message("assistant", answer)

            # speak
            try:
                stop_tts()  # interrupt previous speech if any
                TTS(answer)
            except Exception as e:
                self.append_chat.emit(f"⚠️ TTS error: {e}")

        except Exception as e:
            self.append_chat.emit(f"⚠️ Routing error: {e}")
        finally:
            try:
                self.set_busy.emit(False)
            except Exception:
                pass

    # -------------- UI helpers --------------
    def _append_chat_safely(self, text: str):
        if not text.endswith("\n"):
            text += "\n"
        self.gui.chat_display.append(text)

    def show(self):
        self.gui.show()

    def cleanup(self):
        try:
            self.stop_stt()
            stop_tts()
        except Exception:
            pass

# -------------------- Entry point ---------------------------------------------------
def main():
    DATA_DIR.mkdir(exist_ok=True)

    app = QApplication(sys.argv)
    app.setApplicationName("Riya Assistant")

    controller = RiyaController()
    controller.show()

    app.aboutToQuit.connect(controller.cleanup)
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()

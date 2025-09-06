import pygame
import random
import asyncio
import edge_tts
import os
import tempfile
import re
from dotenv import dotenv_values

# Load environment variables
env_vars = dotenv_values(".env")
AssistantVoice = env_vars.get("AssistantVoice", "en-US-AriaNeural")
AssistantMode = env_vars.get("AssistantMode", "friendly").lower()  # friendly | echo

# Initialize pygame once
pygame.mixer.init()

# Function to remove emojis for speech but keep them for display
def clean_text_for_speech(text):
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map symbols
        "\U0001F1E0-\U0001F1FF"  # flags
        "\U00002700-\U000027BF"  # Dingbats
        "\U0001F900-\U0001F9FF"  # Supplemental Symbols and Pictographs
        "\U0001FA70-\U0001FAFF"  # Symbols and Pictographs Extended-A
        "]+", flags=re.UNICODE
    )
    return emoji_pattern.sub(r'', text)

# Async TTS to audio file
async def text_to_audio_file(text, file_path):
    if os.path.exists(file_path):
        os.remove(file_path)  # Remove old file
    communicate = edge_tts.Communicate(text, AssistantVoice, pitch='+5Hz', rate='+13%')
    await communicate.save(file_path)

# Core TTS function
def TTS(text, func=lambda r=None: True):
    try:
        text_for_speech = clean_text_for_speech(text)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_file:
            file_path = temp_file.name

        asyncio.run(text_to_audio_file(text_for_speech, file_path))

        pygame.mixer.music.load(file_path)
        pygame.mixer.music.play()

        while pygame.mixer.music.get_busy():
            if func() is False:
                break
            pygame.time.Clock().tick(10)

        return True
    except Exception as e:
        print(f"Error in TTS: {e}")
        return False
    finally:
        try:
            func(False)
            pygame.mixer.music.stop()
        except Exception:
            pass

# Smarter TextToSpeech manager
def TextToSpeech(text, func=lambda r=None: True):
    sentences = str(text).split(".")
    responses = [
        "The rest of the result has been printed to the chat screen, kindly check it out sir.",
        "Please check the chat screen for the remaining text, sir.",
        "You'll find the rest of the answer on the chat screen, sir.",
        "The continuation of the text is available on the chat screen, sir."
    ]

    if len(sentences) > 4 and len(text) >= 250:
        partial_text = ". ".join(sentences[:2]) + ". " + random.choice(responses)
        TTS(partial_text, func)
    else:
        TTS(text, func)


# Alias so GUI.py can still import `speak`
speak = TextToSpeech

# Main loop
if __name__ == "__main__":
    print("🚀 Riya is ready to speak! 🎙️\n")

    # Predefined assistant-style responses
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

    while True:
        try:
            user_input = input("You: ")

            if user_input.lower() in ["exit", "quit", "bye"]:
                farewell = "Goodbye 👋, shutting down."
                print(f"Riya: {farewell}")
                TextToSpeech(farewell)
                break

            # 🔀 Mode switching
            if AssistantMode == "echo":
                reply = user_input   # just repeat what user said
            else:  # friendly
                lower_input = user_input.lower()
                if "hi" in lower_input:
                    reply = random.choice(friendly_responses["hi"])
                elif "how are you" in lower_input:
                    reply = random.choice(friendly_responses["how are you"])
                else:
                    reply = random.choice(friendly_responses["default"])

            print(f"Riya: {reply}")
            TextToSpeech(reply)

        except KeyboardInterrupt:
            break

    pygame.mixer.quit()
    print("Goodbye 👋")

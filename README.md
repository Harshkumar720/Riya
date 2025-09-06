# Riya - AI Voice Assistant  

Riya is a Python-based AI-powered voice assistant inspired by JARVIS. It supports **speech recognition, text-to-speech, chatbot responses, automation, real-time search, and image generation** with a modern GUI.  

---

## 🚀 Features  
- 🎙️ **Speech-to-Text (STT)** – Converts voice into text  
- 🔊 **Text-to-Speech (TTS)** – Responds in English & Hindi  
- 🗣️ **Speech-to-Speech** – Real-time voice interaction  
- 💬 **Chatbot** – AI-powered conversations  
- 🌐 **Realtime Search** – Fetches information from the web  
- 🖼️ **Image Generation** – Create AI-generated images  
- ⚡ **Automation** – Open/close apps, system-level tasks  
- 🖥️ **GUI** – Interactive interface with buttons & animations (GIF of Jarvis)  

---

## 📂 Project Structure  
```
RIYA (JARVIS)/
│-- Backend/               # Core logic files
│   │-- Chatbot.py
│   │-- TextToSpeech.py
│   │-- SpeechToText.py
│   │-- SpeechToSpeech.py
│   │-- RealtimeSearchEngine.py
│   │-- RealtimeSearchVoice.py
│   │-- ImageGeneration.py
│   │-- Automation.py
│   │-- Model.py
│
│-- Frontend/              # GUI and media files
│   │-- GUI.py
│   │-- Jarvis.gif
│   │-- Mic_on.png
│   │-- Mic_off.png
│   │-- Home.png
│   │-- Close.png
│   │-- Minimize.png
│   │-- Maximize.png
│   │-- Settings.png
│   │-- Chats.png
│
│-- Data/                  # Logs and configs
│   │-- GUIChatLog.json
│
│-- GeneratedImages/       # AI generated images saved here
│
│-- main.py                # Entry point
│-- run_riya.bat           # Windows startup script
│-- requirements.txt       # Dependencies list
│-- .env                   # API keys & environment variables
│-- README.md              # Documentation
```

---

## ⚙️ Installation  

### 1. Clone the Repository  
```bash
git clone https://github.com/your-username/riya.git
cd riya
```

### 2. Create Virtual Environment  
```bash
python -m venv venv
source venv/bin/activate   # On Linux/Mac
venv\Scripts\activate      # On Windows
```

### 3. Install Dependencies  
```bash
pip install -r requirements.txt
```

### 4. Setup Environment Variables  
Create a `.env` file in the root directory:  
```
OPENAI_API_KEY=your_api_key
SERPAPI_KEY=your_serpapi_key
```

---

## ▶️ Run the Project  
```bash
python main.py
```

Or just double-click `run_riya.bat` on Windows.  

---

## 📸 Screenshots  
(Add screenshots of your GUI here)

---

## 🤝 Contribution  
1. Fork the repo  
2. Create a new branch (`feature-xyz`)  
3. Commit your changes  
4. Open a Pull Request  

---

## 📜 License  
This project is licensed under the MIT License.  

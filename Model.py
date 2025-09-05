# Model.py
import os
import requests
from dotenv import load_dotenv
import cohere
from openai import OpenAI

# Load API keys from .env
load_dotenv()
groq_api_key = os.getenv("GroqAPIKey")
openai_api_key = os.getenv("OpenAIAPIKey")
deepseek_api_key = os.getenv("DeepSeekAPIKey")
cohere_api_key = os.getenv("CohereAPIKey")

# ===== GROQ =====
# You need Groq SDK installed and valid key
try:
    from groq import Groq
    groq_client = Groq(api_key=groq_api_key)
except Exception:
    groq_client = None

def get_groq_response(prompt: str) -> str:
    if not groq_client:
        return "⚠️ Groq client not initialized."
    try:
        response = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",  # Change to your Groq model
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"⚠️ Groq error: {str(e)}"

# ===== OPENAI =====
openai_client = OpenAI(api_key=openai_api_key)

def get_openai_response(prompt: str) -> str:
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"⚠️ OpenAI error: {str(e)}"

# ===== DEEPSEEK =====
def deepseek_request(prompt: str) -> str:
    if not deepseek_api_key:
        return "⚠️ DeepSeek API key not found."
    try:
        url = "https://api.deepseek.com/chat/completions"
        headers = {"Authorization": f"Bearer {deepseek_api_key}", "Content-Type": "application/json"}
        payload = {
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": prompt}]
        }
        response = requests.post(url, headers=headers, json=payload)
        data = response.json()
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        return f"⚠️ DeepSeek error: {str(e)}"

# ===== COHERE =====
cohere_client = cohere.Client(api_key=cohere_api_key)

def first_layer_dmm(prompt: str) -> dict:
    """
    Cohere Decision-Making Model
    Returns structured output for query type (general, realtime, automation)
    """
    try:
        response = cohere_client.chat(
            model="command-r-plus",
            message=prompt,
            temperature=0.3
        )
        return {"response": response.text}
    except Exception as e:
        return {"response": f"⚠️ Cohere error: {str(e)}"}


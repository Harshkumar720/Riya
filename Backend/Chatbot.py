# Chatbot.py
"""
RIYA Chatbot with automatic query routing
----------------------------------------
Uses Cohere DMM to classify queries and routes to Groq/OpenAI/DeepSeek for answers.
"""

import os
from dotenv import load_dotenv
from datetime import datetime
from .Model import (
    get_groq_response,
    get_openai_response,
    deepseek_request,
    first_layer_dmm,
)


# Load API keys
load_dotenv()

# Names
USERNAME = "Harsh"
ASSISTANT_NAME = "RIYA"

# Default answer provider if general chat
DEFAULT_PROVIDER = "groq"  # can be "groq" / "openai" / "deepseek"


def chat_with_ai(prompt: str) -> str:
    """
    Main function: uses Cohere DMM to classify the query,
    then routes to the appropriate model for response.
    """
    # 1️⃣ Use Cohere DMM to classify the query
    dmm_result = first_layer_dmm(prompt)
    classification = dmm_result.get("response", "general")  # default fallback
    classification_lower = classification.lower()

    # 2️⃣ Handle date/day/time queries automatically
    now = datetime.now()
    today_date = now.strftime("%d %B %Y")   # e.g., 28 August 2025
    today_day = now.strftime("%A")          # e.g., Thursday
    current_time = now.strftime("%I:%M:%S %p") # e.g., 12:05:30 PM

    # Convert user prompt to lowercase for matching
    query_lower = prompt.lower()

    # Check for combined queries first
    if any(word in query_lower for word in ["date and time", "day and time", "full date"]):
        return f"Today is {today_day}, {today_date}, and the current time is {current_time}."
    # Check date first
    elif any(word in query_lower for word in ["date", "today’s date", "today date"]):
        return f"Today’s date is {today_date}."
    # Then time
    elif any(word in query_lower for word in ["time", "current time", "what time"]):
        return f"The current time is {current_time}."
    # Then day
    elif any(word in query_lower for word in ["day", "which day", "today is"]):
        return f"Today is {today_day}."

    # 3️⃣ Detect task keywords
    task_keywords = ["open", "close", "play", "generate image", "reminder",
                     "system", "content", "google search", "youtube search", "exit"]
    for keyword in task_keywords:
        if classification_lower.startswith(keyword):
            return f"Task detected: {classification}"

    # 4️⃣ If it's general or realtime, send to LLM provider
    response = ""
    if DEFAULT_PROVIDER == "openai":
        response = get_openai_response(prompt)
    elif DEFAULT_PROVIDER == "groq":
        response = get_groq_response(prompt)
    elif DEFAULT_PROVIDER == "deepseek":
        response = deepseek_request(prompt)
    else:
        response = "⚠️ No valid answer provider set."

    return response


# =============================
# Command-line Interface
# =============================
if __name__ == "__main__":
    print(f"=== {ASSISTANT_NAME} Chatbot ===")
    print(f"Hello {USERNAME}, I am {ASSISTANT_NAME}. How can I help you today?\n")

    while True:
        try:
            user_input = input(f"{USERNAME}: ").strip()
            if user_input.lower() in ["exit", "quit", "bye"]:
                print(f"{ASSISTANT_NAME}: Goodbye {USERNAME}! 👋")
                break

            # Chat and auto-route
            response = chat_with_ai(user_input)
            print(f"{ASSISTANT_NAME}: {response}\n")

        except KeyboardInterrupt:
            print(f"\n{ASSISTANT_NAME}: Session ended. Bye {USERNAME}! 👋")
            break


from googlesearch import search
from groq import Groq
from json import load, dump
import datetime
from dotenv import dotenv_values
import yfinance as yf
import requests
import re   # ✅ For city extraction

# 🔹 Load environment variables
env_vars = dotenv_values(".env")
Username = env_vars.get("Username")
Assistantname = env_vars.get("Assistantname")
GroqAPIKey = env_vars.get("GroqAPIKey")
WeatherAPI = env_vars.get("WeatherAPI")   # OpenWeatherMap API key
NewsAPI = env_vars.get("NewsAPI")         # NewsAPI key

client = Groq(api_key=GroqAPIKey)

# 🔹 System prompt
System = f"""Hello, I am {Username}, You are a very accurate and advanced AI chatbot named {Assistantname}.
*** Provide answers in a professional way, with proper grammar. ***
*** Use real-time data when available. ***"""

try:
    with open(r"Data\ChatLog.json", "r") as f:
        messages = load(f)
except:
    with open(r"Data\ChatLog.json", "w") as f:
        dump([], f)

# -------------------- Real-Time APIs --------------------

def get_stock_price(ticker: str) -> str:
    try:
        stock = yf.Ticker(ticker)
        data = stock.history(period="1d", interval="1m")
        if data.empty:
            return f"⚠️ No stock data found for {ticker}."
        latest = data.iloc[-1]
        return (
            f"📈 Real-time stock data for {ticker}:\n"
            f"- Price: ${latest['Close']:.2f}\n"
            f"- Open: ${latest['Open']:.2f}\n"
            f"- High: ${latest['High']:.2f}\n"
            f"- Low: ${latest['Low']:.2f}\n"
            f"- Volume: {int(latest['Volume'])}\n"
        )
    except Exception as e:
        return f"⚠️ Error fetching stock price: {str(e)}"

# -------------------- Stock Lookup --------------------
STOCK_TICKERS = {
    "apple": "AAPL",
    "microsoft": "MSFT",
    "tesla": "TSLA",
    "tata motors": "TATAMOTORS.NS",   # NSE India
    "reliance": "RELIANCE.NS",
    "infosys": "INFY.NS",
    "hdfc bank": "HDFCBANK.NS",
    "icici bank": "ICICIBANK.NS",
    "sbi": "SBIN.NS",
    "wipro": "WIPRO.NS",
    "tcs": "TCS.NS",
    "google": "GOOGL",
    "amazon": "AMZN",
    "meta": "META",
}

def find_ticker(company: str) -> str:
    """
    Try to find a stock ticker dynamically via yfinance.
    If not found, fall back to STOCK_TICKERS dict.
    """
    company_lower = company.lower()

    # Check dictionary first
    for name, ticker in STOCK_TICKERS.items():
        if name in company_lower:
            return ticker

    try:
        search_ticker = yf.Ticker(company)
        info = search_ticker.info
        if "symbol" in info:
            return info["symbol"]
    except:
        pass

    return None

# -------------------- Crypto --------------------

def get_crypto_price(coin: str = "bitcoin") -> str:
    try:
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin}&vs_currencies=usd"
        res = requests.get(url).json()
        if coin not in res:
            return f"⚠️ No crypto data found for {coin}."
        price = res[coin]["usd"]
        return f"🪙 Real-time price of {coin.capitalize()}: ${price}"
    except Exception as e:
        return f"⚠️ Error fetching crypto price: {str(e)}"

def find_crypto(query: str) -> str:
    """Extract crypto coin name from query"""
    common_coins = ["bitcoin", "ethereum", "dogecoin", "solana", "cardano", "litecoin", "ripple"]
    for coin in common_coins:
        if coin in query.lower():
            return coin
    return "bitcoin"

# -------------------- Weather --------------------

def get_weather(city: str) -> str:
    try:
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={WeatherAPI}&units=metric"
        res = requests.get(url).json()
        if res.get("cod") != 200:
            return f"⚠️ City not found: {city}"
        desc = res["weather"][0]["description"].capitalize()
        temp = res["main"]["temp"]
        humidity = res["main"]["humidity"]
        return (
            f"🌦 Weather in {city}:\n"
            f"- Condition: {desc}\n"
            f"- Temperature: {temp}°C\n"
            f"- Humidity: {humidity}%\n"
        )
    except Exception as e:
        return f"⚠️ Error fetching weather: {str(e)}"

# -------------------- News --------------------

def get_news(topic: str = "technology") -> str:
    try:
        url = f"https://newsapi.org/v2/everything?q={topic}&apiKey={NewsAPI}&pageSize=5"
        res = requests.get(url).json()
        if res.get("status") != "ok":
            return f"⚠️ No news found for {topic}"
        news_list = res["articles"]
        result = f"📰 Latest news about {topic}:\n"
        for n in news_list[:5]:
            result += f"- {n['title']} ({n['source']['name']})\n"
        return result
    except Exception as e:
        return f"⚠️ Error fetching news: {str(e)}"

# -------------------- Location Detection --------------------

def get_user_location() -> str:
    """Detect user's city using IP address"""
    try:
        res = requests.get("http://ip-api.com/json/").json()
        if res.get("status") == "success":
            return res.get("city", "Delhi")
        return "Delhi"
    except:
        return "Delhi"

# -------------------- Helpers --------------------

def GoogleSearch(query):
    try:
        results = search(query, num=5, stop=5, pause=2)
        Answer = f"The search results for '{query}' are:\n[start]\n"
        for url in results:
            Answer += f"- {url}\n"
        Answer += "[end]"
        return Answer
    except Exception as e:
        return f"⚠️ Google Search error: {str(e)}"

def AnswerModifier(Answer):
    lines = Answer.split('\n')
    non_empty_lines = [line for line in lines if line.strip()]
    return '\n'.join(non_empty_lines)

def Information():
    now = datetime.datetime.now()
    return (
        "Use This Real-time Information if needed:\n"
        f"Day: {now.strftime('%A')}\n"
        f"Date: {now.strftime('%d')}\n"
        f"Month: {now.strftime('%B')}\n"
        f"Year: {now.strftime('%Y')}\n"
        f"Time: {now.strftime('%H')}:{now.strftime('%M')}:{now.strftime('%S')}\n"
    )

SystemChatBot = [
    {"role": "system", "content": System},
    {"role": "user", "content": "Hi"},
    {"role": "assistant", "content": "Hello, how can I help you?"}
]

# -------------------- Main Search Engine --------------------

def RealtimeSearchEngine(prompt):
    global SystemChatBot, messages
    
    # 🔎 Stock price queries
    if "stock" in prompt.lower() or "price" in prompt.lower():
        match = re.search(r"stock price of ([a-zA-Z\s]+)", prompt.lower())
        company = match.group(1).strip() if match else prompt
        ticker = find_ticker(company)
        if ticker:
            return get_stock_price(ticker)
        else:
            return f"⚠️ Could not find stock ticker for {company}."
    
    # 🔎 Crypto queries
    if "crypto" in prompt.lower() or "bitcoin" in prompt.lower() or "ethereum" in prompt.lower():
        coin = find_crypto(prompt)
        return get_crypto_price(coin)
    
    # 🔎 Weather queries
    if "weather" in prompt.lower():
        match = re.search(r"weather (?:in|of) ([a-zA-Z\s]+)", prompt.lower())
        if match:
            city = match.group(1).strip().title()
        else:
            city = get_user_location()
        return get_weather(city)
    
    # 🔎 News queries
    if "news" in prompt.lower():
        topic = prompt.split("news about")[-1].strip() if "news about" in prompt.lower() else "technology"
        return get_news(topic)
    
    # 🔹 Otherwise fall back to Google + Groq
    with open(r"Data\ChatLog.json", "r") as f:
        messages = load(f)
    
    messages.append({"role": "user", "content": f"{prompt}"})

    MAX_HISTORY = 5
    messages_to_send = messages[-MAX_HISTORY:]
    SystemChatBot.append({"role": "system", "content": GoogleSearch(prompt)})

    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=SystemChatBot + [{"role": "system", "content": Information()}] + messages_to_send,
        temperature=0.7,
        max_tokens=1024,
        top_p=1,
        stream=True
    )

    Answer = ""
    for chunk in completion:
        if chunk.choices[0].delta.content:
            Answer += chunk.choices[0].delta.content
    
    Answer = Answer.strip().replace("</s>", "")
    messages.append({"role": "assistant", "content": Answer})
    
    if len(messages) > 20:
        messages = messages[-20:]
    
    with open(r"Data\ChatLog.json", "w") as f:
        dump(messages, f, indent=4)
    
    SystemChatBot.pop()
    return AnswerModifier(Answer)

# -------------------- Run --------------------
if __name__ == "__main__":
    while True:
        prompt = input("Enter your query: ")
        print(f"\n📝 Query: {prompt}\n")
        print(f"💡 Answer:\n{RealtimeSearchEngine(prompt)}\n")

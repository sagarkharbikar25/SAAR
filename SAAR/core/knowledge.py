# core/knowledge.py
import requests
import json
import random

try:
    import yfinance as yf
    import feedparser
    YF_AVAILABLE = True
except Exception:
    YF_AVAILABLE = False

class KnowledgeHub:
    def __init__(self):
        pass

    # ================= FINANCIAL DATA =================
    def get_stock_price(self, ticker: str):
        if not YF_AVAILABLE:
            return "Finance module unavailable boss."
        try:
            ticker = ticker.upper()
            stock = yf.Ticker(ticker)
            data = stock.history(period="1d")
            if data.empty:
                return f"Could not find stock data for {ticker} boss."
            price = round(data['Close'].iloc[-1], 2)
            currency = stock.info.get('currency', 'USD')
            return f"The current price of {ticker} is {price} {currency} boss."
        except Exception as e:
            return f"Failed to fetch stock price: {e}"

    def get_crypto_price(self, coin: str):
        if not YF_AVAILABLE:
            return "Finance module unavailable boss."
        try:
            # yfinance uses symbols like BTC-USD
            ticker = f"{coin.upper()}-USD"
            crypto = yf.Ticker(ticker)
            data = crypto.history(period="1d")
            if data.empty:
                return f"Could not find crypto data for {coin} boss."
            price = round(data['Close'].iloc[-1], 2)
            return f"The current price of {coin.upper()} is ${price} USD boss."
        except Exception as e:
            return f"Failed to fetch crypto price: {e}"

    # ================= LIVE DATA =================
    def get_weather(self, location: str):
        try:
            # wttr.in format=3 returns "Location: weather condition +temp"
            url = f"https://wttr.in/{location}?format=3"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                return response.text.strip()
            return f"Couldn't fetch weather for {location} boss."
        except Exception as e:
            return f"Weather API error: {e}"

    def get_daily_news(self):
        if not YF_AVAILABLE:
            return "Feed parser unavailable boss."
        try:
            # Using BBC World News RSS feed (public & free)
            url = "http://feeds.bbci.co.uk/news/world/rss.xml"
            feed = feedparser.parse(url)
            if not feed.entries:
                return "Couldn't fetch news headlines boss."
            
            headlines = [entry.title for entry in feed.entries[:3]]
            news_text = "Here are the top headlines:\n- " + "\n- ".join(headlines)
            return news_text
        except Exception as e:
            return f"News error: {e}"

    def get_quote_and_joke(self):
        try:
            # Public free API for quotes
            quote_res = requests.get("https://api.quotable.io/random", timeout=5).json()
            quote = f"\"{quote_res['content']}\" - {quote_res['author']}"
        except:
            quote = "\"The best way to predict the future is to invent it.\" - Alan Kay"

        try:
            # Public free API for programming jokes
            joke_res = requests.get("https://v2.jokeapi.dev/joke/Programming?type=single", timeout=5).json()
            joke = joke_res.get('joke', "Why do programmers prefer dark mode? Because light attracts bugs.")
        except:
            joke = "Why do programmers prefer dark mode? Because light attracts bugs."

        return f"💡 Quote: {quote}\n\n😂 Joke: {joke}"

    # ================= ENTERTAINMENT SEARCH =================
    def search_media(self, title: str, media_type: str):
        import webbrowser
        try:
            query = f"{title} {media_type}".replace(" ", "+")
            if media_type == "movie":
                url = f"https://www.imdb.com/find?q={query}"
            elif media_type == "book":
                url = f"https://www.goodreads.com/search?q={query}"
            elif media_type == "game":
                url = f"https://www.ign.com/search?q={query}"
            else:
                url = f"https://www.google.com/search?q={query}"
            
            webbrowser.open(url)
            return f"Searching for the {media_type} '{title}' boss."
        except Exception as e:
            return f"Search Error: {e}"

# Global instance
knowledge_hub = KnowledgeHub()

import os
import time
import requests
import pandas as pd
import yfinance as yf
import pytz
import streamlit as st

from datetime import datetime

# ==========================================
# PAGE CONFIG
# ==========================================
st.set_page_config(page_title="AI Index Dashboard", layout="wide")

st.title("🤖 AI Trading Dashboard (NIFTY / SENSEX)")

# ==========================================
# INDEX SELECTION
# ==========================================
index_choice = st.selectbox(
    "📊 Select Index",
    ["NIFTY 50", "SENSEX"]
)

# Map symbol
SYMBOL_MAP = {
    "NIFTY 50": "^NSEI",
    "SENSEX": "^BSESN"
}

SYMBOL = SYMBOL_MAP[index_choice]

st.write(f"Selected Symbol: {SYMBOL}")

# ==========================================
# TELEGRAM CONFIG
# ==========================================
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

def send_alert(message):
    if not BOT_TOKEN or not CHAT_ID:
        return

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    params = {"chat_id": CHAT_ID, "text": message}

    try:
        requests.get(url, params=params, timeout=5)
    except:
        pass

# ==========================================
# MARKET CHECK
# ==========================================
def market_open():
    india = pytz.timezone("Asia/Kolkata")
    now = datetime.now(india)

    if now.weekday() >= 5:
        return False

    start = now.replace(hour=9, minute=15, second=0)
    end = now.replace(hour=15, minute=30, second=0)

    return start <= now <= end

# ==========================================
# FETCH DATA (DYNAMIC SYMBOL)
# ==========================================
@st.cache_data(ttl=60)
def fetch_data(symbol, interval="5m"):
    try:
        data = yf.download(
            symbol,
            period="5d",
            interval=interval,
            auto_adjust=True,
            progress=False
        )

        if data.empty:
            return None

        return data.ffill()

    except:
        return None

# ==========================================
# INDICATORS
# ==========================================
def calculate_indicators(data):
    data = data.copy()

    data["EMA9"] = data["Close"].ewm(span=9).mean()
    data["EMA21"] = data["Close"].ewm(span=21).mean()

    delta = data["Close"].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)

    avg_gain = gain.rolling(14).mean()
    avg_loss = loss.rolling(14).mean()

    rs = avg_gain / avg_loss
    data["RSI"] = 100 - (100 / (1 + rs))

    tp = (data["High"] + data["Low"] + data["Close"]) / 3
    data["VWAP"] = (tp * data["Volume"]).cumsum() / data["Volume"].cumsum()

    data["AVG_VOLUME"] = data["Volume"].rolling(20).mean()

    return data.dropna()

# ==========================================
# SIGNAL ENGINE
# ==========================================
def generate_signal(data, symbol):

    latest = data.iloc[-1]

    close = float(latest["Close"])
    ema9 = float(latest["EMA9"])
    ema21 = float(latest["EMA21"])
    rsi = float(latest["RSI"])
    vwap = float(latest["VWAP"])

    score = 0

    score += 25 if ema9 > ema21 else -25
    score += 20 if rsi > 60 else -20 if rsi < 40 else 0
    score += 20 if close > vwap else -20

    signal = "BUY CE 🚀" if score >= 50 else "BUY PE 🔻" if score <= -50 else "NO TRADE"

    return {
        "signal": signal,
        "score": score,
        "price": close,
        "symbol": symbol
    }

# ==========================================
# MAIN UI
# ==========================================
if market_open():
    st.success("Market is OPEN 🟢")

    data = fetch_data(SYMBOL)

    if data is not None:
        data = calculate_indicators(data)
        result = generate_signal(data, SYMBOL)

        col1, col2, col3 = st.columns(3)

        col1.metric("Signal", result["signal"])
        col2.metric("Score", result["score"])
        col3.metric("Price", result["price"])

        st.info(f"Tracking: {index_choice} ({SYMBOL})")

    else:
        st.error("No market data available")

else:
    st.warning("Market is CLOSED 🔴")

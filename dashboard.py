import os
import time
import requests
import pandas as pd
import yfinance as yf
import pytz
import streamlit as st

from datetime import datetime
from streamlit.runtime.scriptrunner import add_script_run_ctx
from streamlit_autorefresh import st_autorefresh

# ==========================================
# PAGE CONFIG
# ==========================================
st.set_page_config(page_title="AI NIFTY Dashboard", layout="wide")

st.title("🤖 AI NIFTY Trading Dashboard")

# Auto refresh every 60 seconds
st_autorefresh(interval=60000, key="data_refresh")

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
    except Exception as e:
        st.error(f"Telegram Error: {e}")

# ==========================================
# MARKET HOURS
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
# FETCH DATA
# ==========================================
@st.cache_data(ttl=60)
def fetch_data(interval="5m"):
    try:
        data = yf.download(
            "^NSEI",
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

    data['EMA9'] = data['Close'].ewm(span=9).mean()
    data['EMA21'] = data['Close'].ewm(span=21).mean()

    delta = data['Close'].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)

    avg_gain = gain.rolling(14).mean()
    avg_loss = loss.rolling(14).mean()

    rs = avg_gain / avg_loss
    data['RSI'] = 100 - (100 / (1 + rs))

    tp = (data['High'] + data['Low'] + data['Close']) / 3
    data['VWAP'] = (tp * data['Volume']).cumsum() / data['Volume'].cumsum()

    data['AVG_VOLUME'] = data['Volume'].rolling(20).mean()

    return data.dropna()

# ==========================================
# CANDLESTICK PATTERN
# ==========================================
def candlestick_pattern(data):
    if len(data) < 2:
        return "NONE"

    latest = data.iloc[-1]
    prev = data.iloc[-2]

    if (
        prev['Close'] < prev['Open'] and
        latest['Close'] > latest['Open'] and
        latest['Close'] > prev['Open'] and
        latest['Open'] < prev['Close']
    ):
        return "BULLISH_ENGULFING"

    if (
        prev['Close'] > prev['Open'] and
        latest['Close'] < latest['Open'] and
        latest['Open'] > prev['Close'] and
        latest['Close'] < prev['Open']
    ):
        return "BEARISH_ENGULFING"

    return "NONE"

# ==========================================
# OPTION CHAIN
# ==========================================
@st.cache_data(ttl=120)
def get_option_chain():
    try:
        url = "https://www.nseindia.com/api/option-chain-indices?symbol=NIFTY"
        headers = {"User-Agent": "Mozilla/5.0"}

        session = requests.Session()
        session.get("https://www.nseindia.com", headers=headers, timeout=5)

        response = session.get(url, headers=headers, timeout=5)
        data = response.json()

        records = data['records']['data']

        ce_oi, pe_oi = {}, {}
        total_ce_oi = total_pe_oi = 0
        total_ce_change = total_pe_change = 0
        iv_values = []

        ce_premium = pe_premium = 0

        for item in records:
            strike = item.get("strikePrice", 0)

            if "CE" in item:
                ce = item["CE"]
                oi = ce.get("openInterest", 0)
                ce_oi[strike] = oi
                total_ce_oi += oi
                total_ce_change += ce.get("changeinOpenInterest", 0)
                iv_values.append(ce.get("impliedVolatility", 0))
                ce_premium = ce.get("lastPrice", 0)

            if "PE" in item:
                pe = item["PE"]
                oi = pe.get("openInterest", 0)
                pe_oi[strike] = oi
                total_pe_oi += oi
                total_pe_change += pe.get("changeinOpenInterest", 0)
                iv_values.append(pe.get("impliedVolatility", 0))
                pe_premium = pe.get("lastPrice", 0)

        resistance = max(ce_oi, key=ce_oi.get) if ce_oi else 0
        support = max(pe_oi, key=pe_oi.get) if pe_oi else 0

        pcr = round(total_pe_oi / total_ce_oi, 2) if total_ce_oi else 1
        avg_iv = round(sum(iv_values) / len(iv_values), 2) if iv_values else 0

        return {
            "support": support,
            "resistance": resistance,
            "pcr": pcr,
            "ce_change": total_ce_change,
            "pe_change": total_pe_change,
            "iv": avg_iv,
            "ce_premium": ce_premium,
            "pe_premium": pe_premium
        }

    except Exception as e:
        st.warning(f"Option Chain Error: {e}")
        return {
            "support": 0,
            "resistance": 0,
            "pcr": 1,
            "ce_change": 0,
            "pe_change": 0,
            "iv": 0,
            "ce_premium": 0,
            "pe_premium": 0
        }

# ==========================================
# VIX
# ==========================================
@st.cache_data(ttl=120)
def get_vix():
    try:
        vix = yf.download("^INDIAVIX", period="1d", interval="5m", progress=False)
        return round(float(vix['Close'].iloc[-1]), 2)
    except:
        return 0

# ==========================================
# SIGNAL ENGINE (SIMPLIFIED SAFE VERSION)
# ==========================================
def generate_signal(data):
    latest = data.iloc[-1]

    close = float(latest['Close'])
    ema9 = float(latest['EMA9'])
    ema21 = float(latest['EMA21'])
    rsi = float(latest['RSI'])
    vwap = float(latest['VWAP'])

    option = get_option_chain()
    vix = get_vix()

    score = 0

    score += 25 if ema9 > ema21 else -25
    score += 20 if rsi > 60 else -20 if rsi < 40 else 0
    score += 20 if close > vwap else -20
    score -= 10 if vix > 20 else 0

    signal = "BUY CE 🚀" if score >= 50 else "BUY PE 🔻" if score <= -50 else "NO TRADE"

    return {
        "signal": signal,
        "score": score,
        "price": close,
        "support": option["support"],
        "resistance": option["resistance"],
        "pcr": option["pcr"],
        "vix": vix,
        "iv": option["iv"]
    }

# ==========================================
# MAIN UI
# ==========================================
if market_open():
    st.success("Market is OPEN 🟢")

    data = fetch_data()

    if data is not None:
        data = calculate_indicators(data)
        result = generate_signal(data)

        col1, col2, col3 = st.columns(3)

        col1.metric("Signal", result["signal"])
        col2.metric("Score", result["score"])
        col3.metric("Price", result["price"])

        st.divider()

        col4, col5, col6 = st.columns(3)

        col4.metric("Support", result["support"])
        col5.metric("Resistance", result["resistance"])
        col6.metric("PCR", result["pcr"])

        st.metric("VIX", result["vix"])
        st.metric("IV", result["iv"])

    else:
        st.error("No market data available")

else:
    st.warning("Market is CLOSED 🔴")

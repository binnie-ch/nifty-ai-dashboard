import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go

#from strategy import generate_signal
def generate_signal(data):

    latest = data.iloc[-1]

    ema9 = latest['EMA9']
    ema21 = latest['EMA21']
    rsi = latest['RSI']
    close = latest['Close']
    vwap = latest['VWAP']
    volume = latest['Volume']

    # Handle Series issue
    if hasattr(ema9, "iloc"):
        ema9 = ema9.iloc[0]

    if hasattr(ema21, "iloc"):
        ema21 = ema21.iloc[0]

    if hasattr(rsi, "iloc"):
        rsi = rsi.iloc[0]

    if hasattr(close, "iloc"):
        close = close.iloc[0]

    if hasattr(vwap, "iloc"):
        vwap = vwap.iloc[0]

    if hasattr(volume, "iloc"):
        volume = volume.iloc[0]

    # Convert to float
    ema9 = float(ema9)
    ema21 = float(ema21)
    rsi = float(rsi)
    close = float(close)
    vwap = float(vwap)
    volume = float(volume)

    score = 0

    # EMA Trend
    if ema9 > ema21:
        score += 30
    else:
        score -= 30

    # RSI
    if rsi > 60:
        score += 25

    elif rsi < 40:
        score -= 25

    # VWAP
    if close > vwap:
        score += 20

    else:
        score -= 20

    # Volume
    avg_volume = float(data['Volume'].tail(10).mean())

    if volume > avg_volume:
        score += 15

    # Final Signal
    if score >= 50:
        return "BUY CE 🚀", score

    elif score <= -50:
        return "BUY PE 🔻", score

    else:
        return "NO TRADE", score
#from bot import send_telegram_alert
import requests

def send_telegram_alert(bot_token, chat_id, message):

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

    requests.get(url, params={
        "chat_id": chat_id,
        "text": message
    })

st.set_page_config(layout="wide")

st.title("🤖 AI Nifty/Sensex Trading Dashboard")

symbol = st.selectbox(
    "Select Index",
    ["^NSEI", "^BSESN"]
)

# Download Data
data = yf.download(
    symbol,
    period="7d",
    interval="15m",
    progress=False
)

if data.empty:
    st.error("No data found")
    st.stop()
    
data.columns = [col[0] if isinstance(col, tuple) else col for col in data.columns]

# Indicators
data['EMA9'] = data['Close'].ewm(span=9).mean()
data['EMA21'] = data['Close'].ewm(span=21).mean()

# RSI
delta = data['Close'].diff()

gain = (delta.where(delta > 0, 0)).rolling(14).mean()
loss = (-delta.where(delta < 0, 0)).rolling(14).mean()

rs = gain / loss

data['RSI'] = 100 - (100 / (1 + rs))

# VWAP
tp = (data['High'] + data['Low'] + data['Close']) / 3

data['VWAP'] = (
    (tp * data['Volume']).cumsum()
    / data['Volume'].cumsum()
)

from datetime import datetime
import pytz

# Indian market time
india = pytz.timezone('Asia/Kolkata')
now = datetime.now(india)

# Market timings
market_open = now.replace(hour=9, minute=15, second=0)
market_close = now.replace(hour=15, minute=30, second=0)

# Weekends
if now.weekday() >= 5:
    st.warning("📴 Market Closed (Weekend)")
    st.stop()

# Market hours check
if now < market_open or now > market_close:
    st.warning("📴 Market Closed")
    st.stop()
    
# Generate Signal
signal, score = generate_signal(data)

latest = data.iloc[-1]

# Telegram Alert
if "last_signal" not in st.session_state:
    st.session_state.last_signal = ""

if signal != st.session_state.last_signal:

    if signal != "NO TRADE":

        send_telegram_alert(
            st.secrets["BOT_TOKEN"],
            st.secrets["CHAT_ID"],
            f"""
🤖 AI SIGNAL

{signal}

Price: {round(float(latest['Close']),2)}

AI Score: {score}
"""
        )

    st.session_state.last_signal = signal

# Chart
fig = go.Figure(data=[go.Candlestick(
    x=data.index,
    open=data['Open'],
    high=data['High'],
    low=data['Low'],
    close=data['Close']
)])

fig.add_trace(go.Scatter(
    x=data.index,
    y=data['EMA9'],
    name="EMA9"
))

fig.add_trace(go.Scatter(
    x=data.index,
    y=data['EMA21'],
    name="EMA21"
))

st.plotly_chart(fig, use_container_width=True)

# Metrics
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Signal", signal)

with col2:
    st.metric("AI Score", score)

with col3:
    st.metric(
        "Price",
        round(float(latest['Close']),2)
    )

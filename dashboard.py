import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go

#from strategy import generate_signal
def generate_signal(data):

    latest = data.iloc[-1].squeeze()

    ema9 = latest.get('EMA9', 0)
    ema21 = latest.get('EMA21', 0)
    rsi = latest.get('RSI', 0)
    close = latest.get('Close', 0)
    vwap = latest.get('VWAP', 0)
    volume = latest.get('Volume', 0)

    # Convert safely
    ema9 = float(ema9)
    ema21 = float(ema21)
    rsi = float(rsi)
    close = float(close)
    vwap = float(vwap)
    volume = float(volume)

    score = 0

    # EMA
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

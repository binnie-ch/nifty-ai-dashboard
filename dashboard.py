import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go

#from strategy import generate_signal
def generate_signal(data):

    latest = data.iloc[-1]

    score = 0

    # EMA Trend
    if latest['EMA9'] > latest['EMA21']:
        score += 30
    else:
        score -= 30

    # RSI Strength
    if latest['RSI'] > 60:
        score += 25
    elif latest['RSI'] < 40:
        score -= 25

    # VWAP
    if latest['Close'] > latest['VWAP']:
        score += 20
    else:
        score -= 20

    # Volume Check
    avg_volume = data['Volume'].tail(10).mean()

    if latest['Volume'] > avg_volume:
        score += 15

    # Final Signal
    if score >= 50:
        return "BUY CE 🚀", score

    elif score <= -50:
        return "BUY PE 🔻", score

    else:
        return "NO TRADE", score
from bot import send_telegram_alert

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

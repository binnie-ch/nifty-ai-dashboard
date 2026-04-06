import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
import requests

st.set_page_config(layout="wide")

st.title("📊 Nifty AI Live Dashboard")

# Fetch data
data = yf.download("^NSEI", period="2d", interval="5m")

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
data['VWAP'] = (data['Volume'] * (data['High']+data['Low']+data['Close'])/3).cumsum() / data['Volume'].cumsum()

latest = data.iloc[-1]

# Signal logic
signal = "NO TRADE"

if latest['Close'] > latest['VWAP'] and latest['EMA9'] > latest['EMA21'] and latest['RSI'] > 55:
    signal = "BUY CE 🚀"
elif latest['Close'] < latest['VWAP'] and latest['EMA9'] < latest['EMA21'] and latest['RSI'] < 45:
    signal = "BUY PE 🔻"

# Telegram Alert Function
def send_alert(message):
    bot_token = st.secrets["BOT_TOKEN"]
    chat_id = st.secrets["CHAT_ID"]
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    requests.get(url, params={"chat_id": chat_id, "text": message})

# Send alert only when signal changes
if "last_signal" not in st.session_state:
    st.session_state.last_signal = ""

if signal != st.session_state.last_signal:
    if signal != "NO TRADE":
        send_alert(f"📊 NIFTY SIGNAL\n\n{signal}\nPrice: {round(latest['Close'],2)}")
    st.session_state.last_signal = signal

# Layout
col1, col2 = st.columns([3,1])

with col1:
    fig = go.Figure(data=[go.Candlestick(
        x=data.index,
        open=data['Open'],
        high=data['High'],
        low=data['Low'],
        close=data['Close']
    )])

    fig.add_trace(go.Scatter(x=data.index, y=data['EMA9'], name='EMA9'))
    fig.add_trace(go.Scatter(x=data.index, y=data['EMA21'], name='EMA21'))

    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.metric("Nifty Price", round(latest['Close'],2))
    st.metric("Signal", signal)

    entry = latest['Close']
    sl = entry * 0.98
    target = entry * 1.04

    st.write(f"🎯 Entry: {entry:.2f}")
    st.write(f"🛑 Stop Loss: {sl:.2f}")
    st.write(f"💰 Target: {target:.2f}")

# RSI Chart
st.subheader("RSI Indicator")

fig2 = go.Figure()
fig2.add_trace(go.Scatter(x=data.index, y=data['RSI'], name='RSI'))
fig2.add_hline(y=70)
fig2.add_hline(y=30)

st.plotly_chart(fig2, use_container_width=True)

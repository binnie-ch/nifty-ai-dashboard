import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
import time

st.set_page_config(layout="wide")

st.title("📊 Nifty AI Dashboard (Stable Version)")

# -------------------------------
# SAFE DATA FETCH FUNCTION
# -------------------------------
def get_data():
    for i in range(3):
        try:
            data = yf.download("NIFTYBEES.NS", period="7d", interval="15m", progress=False)
            if not data.empty:
                return data
        except:
            time.sleep(2)
    return pd.DataFrame()

data = get_data()

if data.empty:
    st.error("❌ Data not loading. Please refresh after some time.")
    st.stop()

# -------------------------------
# CLEAN DATA
# -------------------------------
# Ensure data is valid
if not isinstance(data, pd.DataFrame):
    st.error("❌ Data format error")
    st.stop()

if data is None or data.empty:
    st.error("❌ No data received from server")
    st.stop()

# Clean safely
data = data.copy()

if 'Close' not in data.columns:
    st.error("❌ Invalid data structure")
    st.stop()

data = data.ffill()
data = data.dropna()

# -------------------------------
# INDICATORS
# -------------------------------
data['EMA9'] = data['Close'].ewm(span=9).mean()
data['EMA21'] = data['Close'].ewm(span=21).mean()

delta = data['Close'].diff()
gain = (delta.where(delta > 0, 0)).rolling(14).mean()
loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
rs = gain / loss
data['RSI'] = 100 - (100 / (1 + rs))

latest = data.iloc[-1]

# -------------------------------
# SIGNAL LOGIC
# -------------------------------
signal = "NO TRADE"

if latest['EMA9'] > latest['EMA21'] and latest['RSI'] > 55:
    signal = "BUY CE 🚀"
elif latest['EMA9'] < latest['EMA21'] and latest['RSI'] < 45:
    signal = "BUY PE 🔻"

# -------------------------------
# DISPLAY
# -------------------------------
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
    st.metric("Price", round(latest['Close'],2))
    st.metric("Signal", signal)

st.write("Rows loaded:", len(data))

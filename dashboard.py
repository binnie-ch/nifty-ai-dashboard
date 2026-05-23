import streamlit as st
from streamlit_autorefresh import st_autorefresh

import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import requests
import os
import pytz

from datetime import datetime

# ======================================================
# PAGE CONFIG
# ======================================================

st.set_page_config(
    page_title="AI NIFTY LIVE DASHBOARD",
    layout="wide"
)

# ======================================================
# AUTO REFRESH EVERY 60 SECONDS
# ======================================================

st_autorefresh(interval=60000, key="refresh")

# ======================================================
# TITLE
# ======================================================

st.title("🤖 AI NIFTY LIVE DASHBOARD")

# ======================================================
# TELEGRAM CONFIG
# ======================================================

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# ======================================================
# TELEGRAM ALERT
# ======================================================

def send_alert(message):

    try:

        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

        params = {
            "chat_id": CHAT_ID,
            "text": message
        }

        requests.get(url, params=params)

    except Exception as e:

        print("Telegram Error:", e)

# ======================================================
# MARKET HOURS
# ======================================================

def market_open():

    india = pytz.timezone("Asia/Kolkata")

    now = datetime.now(india)

    if now.weekday() >= 5:
        return False

    market_start = now.replace(
        hour=9,
        minute=15,
        second=0
    )

    market_end = now.replace(
        hour=15,
        minute=30,
        second=0
    )

    return market_start <= now <= market_end

# ======================================================
# FETCH NIFTY DATA
# ======================================================

@st.cache_data(ttl=60)

def fetch_data(interval="5m"):

    data = yf.download(
        "^NSEI",
        period="5d",
        interval=interval,
        auto_adjust=True,
        progress=False
    )

    if data.empty:
        return None

    data = data.ffill()

    return data

# ======================================================
# TECHNICAL INDICATORS
# ======================================================

def calculate_indicators(data):

    # EMA

    data['EMA9'] = data['Close'].ewm(span=9).mean()

    data['EMA21'] = data['Close'].ewm(span=21).mean()

    # RSI

    delta = data['Close'].diff()

    gain = delta.where(delta > 0, 0)

    loss = -delta.where(delta < 0, 0)

    avg_gain = gain.rolling(14).mean()

    avg_loss = loss.rolling(14).mean()

    rs = avg_gain / avg_loss

    data['RSI'] = 100 - (100 / (1 + rs))

    # VWAP

    tp = (
        data['High'] +
        data['Low'] +
        data['Close']
    ) / 3

    data['VWAP'] = (
        (tp * data['Volume']).cumsum()
        / data['Volume'].cumsum()
    )

    # Average Volume

    data['AVG_VOLUME'] = (
        data['Volume'].rolling(20).mean()
    )

    return data.dropna()

# ======================================================
# CANDLESTICK PATTERN
# ======================================================

def candlestick_pattern(data):

    try:

        latest = data.iloc[-1]
        prev = data.iloc[-2]

        latest_open = float(latest['Open'])
        latest_close = float(latest['Close'])

        prev_open = float(prev['Open'])
        prev_close = float(prev['Close'])

        # Bullish Engulfing

        if (
            prev_close < prev_open and
            latest_close > latest_open and
            latest_close > prev_open and
            latest_open < prev_close
        ):

            return "BULLISH ENGULFING"

        # Bearish Engulfing

        if (
            prev_close > prev_open and
            latest_close < latest_open and
            latest_open > prev_close and
            latest_close < prev_open
        ):

            return "BEARISH ENGULFING"

        return "NONE"

    except:

        return "NONE"

# ======================================================
# OPTION CHAIN ANALYSIS
# ======================================================

@st.cache_data(ttl=60)

def get_option_chain():

    try:

        url = "https://www.nseindia.com/api/option-chain-indices?symbol=NIFTY"

        headers = {
            "User-Agent": "Mozilla/5.0"
        }

        session = requests.Session()

        session.get(
            "https://www.nseindia.com",
            headers=headers
        )

        response = session.get(
            url,
            headers=headers
        )

        data = response.json()

        records = data['records']['data']

        ce_oi = {}
        pe_oi = {}

        total_ce_oi = 0
        total_pe_oi = 0

        total_ce_change = 0
        total_pe_change = 0

        iv_values = []

        ce_premium = 0
        pe_premium = 0

        for item in records:

            strike = item['strikePrice']

            if 'CE' in item:

                ce = item['CE']

                oi = ce.get('openInterest', 0)

                change = ce.get(
                    'changeinOpenInterest',
                    0
                )

                ce_oi[strike] = oi

                total_ce_oi += oi
                total_ce_change += change

                iv_values.append(
                    ce.get(
                        'impliedVolatility',
                        0
                    )
                )

                ce_premium = ce.get(
                    'lastPrice',
                    0
                )

            if 'PE' in item:

                pe = item['PE']

                oi = pe.get('openInterest', 0)

                change = pe.get(
                    'changeinOpenInterest',
                    0
                )

                pe_oi[strike] = oi

                total_pe_oi += oi
                total_pe_change += change

                iv_values.append(
                    pe.get(
                        'impliedVolatility',
                        0
                    )
                )

                pe_premium = pe.get(
                    'lastPrice',
                    0
                )

        resistance = max(
            ce_oi,
            key=ce_oi.get
        )

        support = max(
            pe_oi,
            key=pe_oi.get
        )

        pcr = round(
            total_pe_oi / total_ce_oi,
            2
        )

        avg_iv = round(
            sum(iv_values) / len(iv_values),
            2
        )

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

        print("Option Chain Error:", e)

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

# ======================================================
# INDIA VIX
# ======================================================

@st.cache_data(ttl=60)

def get_vix():

    try:

        vix = yf.download(
            "^INDIAVIX",
            period="1d",
            interval="5m",
            auto_adjust=True,
            progress=False
        )

        latest_vix = float(
            vix['Close'].iloc[-1]
        )

        return round(latest_vix, 2)

    except:

        return 0

# ======================================================
# ORB STRATEGY
# ======================================================

def orb_strategy(data):

    try:

        opening = data.between_time(
            "09:15",
            "09:30"
        )

        orb_high = opening['High'].max()

        orb_low = opening['Low'].min()

        latest_close = float(
            data['Close'].iloc[-1]
        )

        if latest_close > orb_high:
            return "BULLISH"

        elif latest_close < orb_low:
            return "BEARISH"

        return "NONE"

    except:

        return "NONE"

# ======================================================
# MULTI TIMEFRAME
# ======================================================

@st.cache_data(ttl=60)

def multi_timeframe():

    try:

        data15 = fetch_data("15m")

        data1h = fetch_data("1h")

        data15['EMA9'] = (
            data15['Close'].ewm(span=9).mean()
        )

        data15['EMA21'] = (
            data15['Close'].ewm(span=21).mean()
        )

        data1h['EMA9'] = (
            data1h['Close'].ewm(span=9).mean()
        )

        data1h['EMA21'] = (
            data1h['Close'].ewm(span=21).mean()
        )

        trend15 = (
            data15['EMA9'].iloc[-1]
            >
            data15['EMA21'].iloc[-1]
        )

        trend1h = (
            data1h['EMA9'].iloc[-1]
            >
            data1h['EMA21'].iloc[-1]
        )

        return trend15, trend1h

    except:

        return False, False

# ======================================================
# SECTOR STRENGTH
# ======================================================

@st.cache_data(ttl=60)

def sector_strength():

    score = 0

    sector_message = ""

    sectors = {
        "BANK": "BANKBEES.NS",
        "IT": "ITBEES.NS",
        "AUTO": "AUTOBEES.NS",
        "PHARMA": "PHARMABEES.NS"
    }

    try:

        for sector, symbol in sectors.items():

            data = yf.download(
                symbol,
                period="1d",
                interval="5m",
                auto_adjust=True,
                progress=False
            )

            change = (
                data['Close'].iloc[-1]
                -
                data['Close'].iloc[0]
            )

            if change > 0:

                score += 5

                sector_message += (
                    f"✅ {sector} Strong\n"
                )

            else:

                score -= 5

                sector_message += (
                    f"🔻 {sector} Weak\n"
                )

        return score, sector_message

    except:

        return 0, "Sector Data Error"

# ======================================================
# FETCH MAIN DATA
# ======================================================

data = fetch_data()

if data is None:

    st.error("No market data available")

    st.stop()

data = calculate_indicators(data)

latest = data.iloc[-1]

# ======================================================
# BASIC VALUES
# ======================================================

close = float(latest['Close'])

ema9 = float(latest['EMA9'])

ema21 = float(latest['EMA21'])

rsi = float(latest['RSI'])

vwap = float(latest['VWAP'])

volume = float(latest['Volume'])

avg_volume = float(latest['AVG_VOLUME'])

# ======================================================
# AI SCORE ENGINE
# ======================================================

score = 0

# EMA

if ema9 > ema21:
    score += 25
else:
    score -= 25

# RSI

if rsi > 60:
    score += 20

elif rsi < 40:
    score -= 20

# VWAP

if close > vwap:
    score += 20
else:
    score -= 20

# VOLUME BREAKOUT

volume_breakout = False

if volume > avg_volume * 1.5:

    volume_breakout = True

    if close > vwap:
        score += 15
    else:
        score -= 15

# ======================================================
# CANDLE PATTERN
# ======================================================

pattern = candlestick_pattern(data)

if pattern == "BULLISH ENGULFING":
    score += 20

elif pattern == "BEARISH ENGULFING":
    score -= 20

# ======================================================
# OPTION CHAIN
# ======================================================

option = get_option_chain()

support = option['support']

resistance = option['resistance']

pcr = option['pcr']

ce_change = option['ce_change']

pe_change = option['pe_change']

iv = option['iv']

ce_premium = option['ce_premium']

pe_premium = option['pe_premium']

# PCR

if pcr > 1:
    score += 15
else:
    score -= 15

# OI CHANGE

if pe_change > ce_change:
    score += 10
else:
    score -= 10

# IV

if iv < 15:
    score += 10

elif iv > 25:
    score -= 10

# PREMIUM ANALYSIS

if ce_premium > pe_premium:
    score += 10
else:
    score -= 10

# ======================================================
# INDIA VIX
# ======================================================

vix = get_vix()

if vix > 20:
    score -= 10

# ======================================================
# ORB STRATEGY
# ======================================================

orb = orb_strategy(data)

if orb == "BULLISH":
    score += 20

elif orb == "BEARISH":
    score -= 20

# ======================================================
# MULTI TIMEFRAME
# ======================================================

trend15, trend1h = multi_timeframe()

if trend15 and trend1h:
    score += 15

elif (not trend15) and (not trend1h):
    score -= 15

# ======================================================
# SECTOR STRENGTH
# ======================================================

sector_score, sector_message = sector_strength()

score += sector_score

# ======================================================
# FINAL SIGNAL
# ======================================================

signal = "NO TRADE"

if score >= 50:
    signal = "BUY CE 🚀"

elif score <= -50:
    signal = "BUY PE 🔻"

# ======================================================
# WIN PROBABILITY
# ======================================================

probability = min(
    95,
    max(
        50,
        abs(score)
    )
)

# ======================================================
# SL / TARGET
# ======================================================

entry = round(close, 2)

if signal == "BUY CE 🚀":

    sl = round(close - 80, 2)

    target1 = round(close + 120, 2)

    target2 = round(close + 220, 2)

elif signal == "BUY PE 🔻":

    sl = round(close + 80, 2)

    target1 = round(close - 120, 2)

    target2 = round(close - 220, 2)

else:

    sl = 0

    target1 = 0

    target2 = 0

# ======================================================
# TELEGRAM ALERT
# ======================================================

if "last_signal" not in st.session_state:
    st.session_state.last_signal = ""

if signal != st.session_state.last_signal:

    if signal != "NO TRADE":

        message = f"""
🤖 AI NIFTY SIGNAL

{signal}

📊 Price: {entry}

🧠 AI Score: {score}
🎯 Win Probability: {probability}%

📈 Support: {support}
📉 Resistance: {resistance}

📊 PCR: {pcr}
📊 INDIA VIX: {vix}
📊 IV: {iv}

🕯 Pattern: {pattern}
🚀 ORB: {orb}

📈 Volume Breakout: {volume_breakout}

🏦 Sector Analysis:
{sector_message}

🛑 Stop Loss: {sl}

💰 Target 1: {target1}
💰 Target 2: {target2}
"""

        send_alert(message)

    st.session_state.last_signal = signal

# ======================================================
# DASHBOARD LAYOUT
# ======================================================

col1, col2 = st.columns([3,1])

# ======================================================
# CANDLE CHART
# ======================================================

with col1:

    fig = go.Figure()

    fig.add_trace(go.Candlestick(
        x=data.index,
        open=data['Open'],
        high=data['High'],
        low=data['Low'],
        close=data['Close'],
        name="NIFTY"
    ))

    fig.add_trace(go.Scatter(
        x=data.index,
        y=data['EMA9'],
        name='EMA9'
    ))

    fig.add_trace(go.Scatter(
        x=data.index,
        y=data['EMA21'],
        name='EMA21'
    ))

    st.plotly_chart(
        fig,
        use_container_width=True
    )

# ======================================================
# SIDE PANEL
# ======================================================

with col2:

    st.metric(
        "NIFTY PRICE",
        round(close, 2)
    )

    st.metric(
        "AI SCORE",
        score
    )

    st.metric(
        "SIGNAL",
        signal
    )

    st.metric(
        "RSI",
        round(rsi, 2)
    )

    st.metric(
        "PCR",
        pcr
    )

    st.metric(
        "VIX",
        vix
    )

    st.metric(
        "WIN %",
        probability
    )

# ======================================================
# EXTRA ANALYSIS
# ======================================================

st.subheader("📊 MARKET ANALYSIS")

col3, col4, col5 = st.columns(3)

with col3:

    st.info(f"""
🕯 Pattern:
{pattern}

🚀 ORB:
{orb}
""")

with col4:

    st.info(f"""
📈 Support:
{support}

📉 Resistance:
{resistance}
""")

with col5:

    st.info(f"""
🛑 Stop Loss:
{sl}

💰 Target:
{target1}
""")

# ======================================================
# RSI CHART
# ======================================================

st.subheader("📊 RSI INDICATOR")

fig2 = go.Figure()

fig2.add_trace(go.Scatter(
    x=data.index,
    y=data['RSI'],
    name='RSI'
))

fig2.add_hline(y=70)

fig2.add_hline(y=30)

st.plotly_chart(
    fig2,
    use_container_width=True
)

# ======================================================
# SECTOR ANALYSIS
# ======================================================

st.subheader("🏦 SECTOR STRENGTH")

st.success(sector_message)

# ======================================================
# FOOTER
# ======================================================

st.caption(
    "🔄 Auto Refresh Every 60 Seconds"
        )

import streamlit as st
import numpy as np
import random
import time
import requests
import holidays
from datetime import datetime
import pytz

# =========================
# TELEGRAM CONFIG
# =========================
BOT_TOKEN = "8568497873:AAHEXglTw7nowIhX27AmPnKCs24ku6lF6gc"
CHAT_ID = "8540013665"

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, data={"chat_id": CHAT_ID, "text": msg}, timeout=10)
    except:
        pass


# =========================
# DYNAMIC HOLIDAY CHECK
# =========================
def is_holiday():
    india_holidays = holidays.India()
    today = datetime.now().date()
    return today in india_holidays


def holiday_name():
    india_holidays = holidays.India()
    today = datetime.now().date()
    return india_holidays.get(today, None)


# =========================
# MARKET HOURS CHECK
# =========================
def is_market_open():
    india = pytz.timezone("Asia/Kolkata")
    now = datetime.now(india)

    if now.weekday() >= 5:
        return False

    start = now.replace(hour=9, minute=15, second=0)
    end = now.replace(hour=15, minute=30, second=0)

    return start <= now <= end


def market_status():
    if is_holiday():
        return False, f"⛔ NSE Holiday: {holiday_name()}"
    if not is_market_open():
        return False, "⛔ Market Closed (Time Filter)"
    return True, "✅ Market Active"

#=========================
#Stop Loss Function
#==========================
def calculate_sl(price, signal, market):
    volatility = random.uniform(0.002, 0.008)  # proxy volatility

    if signal == "BUY":
        sl = price * (1 - volatility)
    elif signal == "SELL":
        sl = price * (1 + volatility)
    else:
        sl = price

    return round(sl, 2)
    
    def calculate_targets(price, signal):
    if signal == "BUY":
        return round(price * 1.01, 2), round(price * 1.02, 2)
    elif signal == "SELL":
        return round(price * 0.99, 2), round(price * 0.98, 2)
    return price, price
# =========================
# MARKET DATA
# =========================
def get_market(index):
    price = random.uniform(22000, 26000) if index == "NIFTY50" else random.uniform(70000, 80000)

    return {
        "price": price,
        "rsi": random.randint(20, 80),
        "orb": random.choice(["Breakout Up", "Breakout Down", "No Breakout"]),
        "volume": random.randint(100000, 1000000),
    }


# =========================
# OPTION CHAIN DATA
# =========================
def get_option_chain(price):
    chain = []

    for i in range(-10, 11):
        strike = price + i * 100

        chain.append({
            "strike": strike,
            "call_oi": random.randint(5000, 60000),
            "put_oi": random.randint(5000, 60000),
            "call_change": random.randint(-8000, 8000),
            "put_change": random.randint(-8000, 8000),
        })

    return chain


# =========================
# PCR CALCULATION
# =========================
def calculate_pcr(chain):
    call = sum(x["call_oi"] for x in chain)
    put = sum(x["put_oi"] for x in chain)
    return round(put / call, 2)


# =========================
# MAX PAIN
# =========================
def max_pain(chain):
    return min(chain, key=lambda x: x["call_oi"] + x["put_oi"])["strike"]


# =========================
# SMART MONEY FLOW
# =========================
def smart_money(chain, market):
    call_flow = sum(x["call_change"] for x in chain)
    put_flow = sum(x["put_change"] for x in chain)

    oi_pressure = call_flow - put_flow

    whale = any(abs(x["call_change"]) > 5000 or abs(x["put_change"]) > 5000 for x in chain)

    if oi_pressure > 15000 and market["volume"] > 500000:
        return "🚀 INSTITUTIONAL BUYING", 25, oi_pressure
    elif oi_pressure < -15000 and market["volume"] > 500000:
        return "📉 INSTITUTIONAL SELLING", -25, oi_pressure
    elif whale:
        return "🐳 WHALE ACTIVITY DETECTED", 10, oi_pressure
    else:
        return "⚖️ NEUTRAL FLOW", 0, oi_pressure


# =========================
# CE / PE MAPPING
# =========================
def option_direction(signal):
    if signal == "BUY":
        return "CE (CALL BUY)"
    elif signal == "SELL":
        return "PE (PUT BUY)"
    return "NO TRADE"


# =========================
# AI ENGINE
# =========================
def ai_engine(market, chain):
    pcr = calculate_pcr(chain)
    maxp = max_pain(chain)

    flow, bias, oi = smart_money(chain, market)

    score = 0

    # RSI
    if market["rsi"] < 30:
        score += 20
    elif market["rsi"] > 70:
        score -= 20

    # ORB
    if market["orb"] == "Breakout Up":
        score += 15
    elif market["orb"] == "Breakout Down":
        score -= 15

    # PCR
    if pcr < 0.8:
        score += 15
    elif pcr > 1.2:
        score -= 15

    # Smart money
    score += bias

    signal = "BUY" if score > 20 else "SELL" if score < -20 else "HOLD"
    prob = min(95, max(50, 50 + abs(score)))

    return signal, score, prob, pcr, maxp, flow, oi


# =========================
# TELEGRAM MESSAGE
# =========================
def format_msg(index, signal, market, score, prob, pcr, maxp, flow, oi):
    direction = option_direction(signal)

    return f"""
🚨 AI {index} SMART MONEY SIGNAL

📊 Signal: {signal}
📌 Options: {direction}

📊 Price: {round(market['price'],2)}

🧠 AI Score: {score}
🎯 Win Probability: {prob}%

📊 PCR: {pcr}
🎯 Max Pain: {maxp}

🛑 Stop Loss: {sl}
🎯 Target 1: {t1}
🎯 Target 2: {t2}

💰 Flow: {flow}
📈 OI Pressure: {oi}

📉 RSI: {market['rsi']}
🚀 ORB: {market['orb']}

⚡ Dynamic Holiday + Smart Money System
"""


# =========================
# STREAMLIT UI
# =========================
st.title("📊 SMART MONEY AI TRADING DASHBOARD (PRO)")

tab1, tab2 = st.tabs(["📈 NIFTY50", "📊 SENSEX"])

if "last_signal" not in st.session_state:
    st.session_state.last_signal = {"NIFTY50": None, "SENSEX": None}


def run(index):
    allowed, status = market_status()
    st.info(status)

    if not allowed:
        st.warning("🚫 No alerts - Market Closed / Holiday")
        return

    market = get_market(index)
    chain = get_option_chain(market["price"])

    signal, score, prob, pcr, maxp, flow, oi = ai_engine(market, chain)

    st.subheader(f"{index} → {signal}")

    st.metric("Price", round(market["price"], 2))
    st.metric("AI Score", score)
    st.metric("Win Probability", f"{prob}%")

    st.write("📊 PCR:", pcr)
    st.write("🎯 Max Pain:", maxp)
    
    st.write("🛑 Stop Loss:", sl)
    st.write("🎯 Target 1:", t1)
    st.write("🎯 Target 2:", t2)
    st.success(flow)

    st.info(f"Options Strategy: {option_direction(signal)}")

    # ALERT SYSTEM
    if signal != "HOLD" and signal != st.session_state.last_signal[index]:
        msg = format_msg(index, signal, market, score, prob, pcr, maxp, flow, oi, sl, t1, t2)
        send_telegram(msg)
        st.success("🚨 Telegram Alert Sent")
        st.session_state.last_signal[index] = signal


with tab1:
    run("NIFTY50")

with tab2:
    run("SENSEX")


time.sleep(60)
st.rerun()

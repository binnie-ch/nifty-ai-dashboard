import streamlit as st
import numpy as np
import random
import time
import requests

# -----------------------------
# TELEGRAM CONFIG
# -----------------------------
BOT_TOKEN = "8568497873:AAHEXglTw7nowIhX27AmPnKCs24ku6lF6gc"
CHAT_ID = "8540013665"

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})


# -----------------------------
# MARKET DATA
# -----------------------------
def get_market(index):
    price = random.uniform(22000, 26000) if index == "NIFTY50" else random.uniform(70000, 80000)

    return {
        "price": price,
        "rsi": random.randint(20, 80),
        "orb": random.choice(["Breakout Up", "Breakout Down", "No Breakout"]),
        "volume": random.randint(100000, 1000000),
    }


# -----------------------------
# OPTION CHAIN
# -----------------------------
def get_option_chain(price):
    chain = []

    for i in range(-10, 11):
        strike = price + i * 100

        call_oi = random.randint(5000, 60000)
        put_oi = random.randint(5000, 60000)

        call_change = random.randint(-8000, 8000)
        put_change = random.randint(-8000, 8000)

        chain.append({
            "strike": strike,
            "call_oi": call_oi,
            "put_oi": put_oi,
            "call_change": call_change,
            "put_change": put_change
        })

    return chain


# -----------------------------
# MAX PAIN
# -----------------------------
def max_pain(chain):
    pain = []

    for c in chain:
        cp = c["call_oi"] * max(0, c["strike"] - c["strike"])
        pp = c["put_oi"] * max(0, c["strike"] - c["strike"])
        pain.append((c["strike"], cp + pp))

    return min(pain, key=lambda x: x[1])[0]


# -----------------------------
# PCR
# -----------------------------
def pcr(chain):
    call = sum(x["call_oi"] for x in chain)
    put = sum(x["put_oi"] for x in chain)
    return round(put / call, 2)


# -----------------------------
# SMART MONEY FLOW DETECTION
# -----------------------------
def smart_money_flow(chain, market):
    total_call_change = sum(x["call_change"] for x in chain)
    total_put_change = sum(x["put_change"] for x in chain)

    oi_pressure = total_call_change - total_put_change

    # Whale activity detection
    whale_spike = any(abs(x["call_change"]) > 5000 or abs(x["put_change"]) > 5000 for x in chain)

    # Volume confirmation
    volume_strength = market["volume"] > 500000

    # Flow classification
    if oi_pressure > 15000 and volume_strength:
        flow = "🚀 STRONG INSTITUTIONAL BUYING"
        bias = 25
    elif oi_pressure < -15000 and volume_strength:
        flow = "📉 STRONG DISTRIBUTION (SELLING)"
        bias = -25
    elif whale_spike:
        flow = "🐳 WHALE ACTIVITY DETECTED"
        bias = 10
    else:
        flow = "⚖️ NEUTRAL / MIXED FLOW"
        bias = 0

    return flow, bias, oi_pressure, whale_spike


# -----------------------------
# AI ENGINE
# -----------------------------
def ai_engine(market, chain):
    pcr_val = pcr(chain)
    max_pain_val = max_pain(chain)

    flow, flow_bias, oi_pressure, whale = smart_money_flow(chain, market)

    score = 0

    # RSI logic
    if market["rsi"] < 30:
        score += 20
    elif market["rsi"] > 70:
        score -= 20

    # ORB logic
    if market["orb"] == "Breakout Up":
        score += 15
    elif market["orb"] == "Breakout Down":
        score -= 15

    # PCR logic
    if pcr_val < 0.8:
        score += 15
    elif pcr_val > 1.2:
        score -= 15

    # Smart money flow
    score += flow_bias

    signal = "BUY" if score > 20 else "SELL" if score < -20 else "HOLD"
    direction = option_direction(signal)
    win_prob = min(95, max(50, 50 + abs(score)))

    return signal, score, win_prob, pcr_val, max_pain_val, flow, oi_pressure

def option_direction(signal):
    if signal == "BUY":
        return "CE (CALL BUY)"
    elif signal == "SELL":
        return "PE (PUT BUY)"
    else:
        return "NO TRADE"
        
# -----------------------------
# TELEGRAM MESSAGE
# -----------------------------
def format_msg(index, signal, market, score, prob, pcr_val, max_pain_val, flow, oi_pressure):
    direction = option_direction(signal)

    return f"""
🚨 AI {index} SMART MONEY SIGNAL

📊 Signal: {signal}
📌 Options Action: {direction}

📊 Price: {round(market['price'],2)}

🧠 AI Score: {score}
🎯 Win Probability: {prob}%

📊 PCR: {pcr_val}
🎯 Max Pain: {max_pain_val}

💰 Smart Money Flow:
{flow}

📈 OI Pressure: {oi_pressure}

📉 RSI: {market['rsi']}
🚀 ORB: {market['orb']}
"""


# -----------------------------
# STREAMLIT UI
# -----------------------------
st.title("📊 SMART MONEY AI TRADING DASHBOARD")

tab1, tab2 = st.tabs(["📈 NIFTY50", "📊 SENSEX"])

if "last_signal" not in st.session_state:
    st.session_state.last_signal = {"NIFTY50": None, "SENSEX": None}


def run(index):
    market = get_market(index)
    chain = get_option_chain(market["price"])

    signal, score, prob, pcr_val, max_pain_val, flow, oi_pressure = ai_engine(market, chain)

    st.subheader(f"{index} → {signal}")

    st.metric("Price", round(market["price"], 2))
    st.metric("AI Score", score)
    st.metric("Win Probability", f"{prob}%")

    st.write("📊 PCR:", pcr_val)
    st.write("🎯 Max Pain:", max_pain_val)

    st.success(flow)
    st.success(f"Options Signal: {option_direction(signal)}")

    # ALERT SYSTEM
    if signal != "HOLD" and signal != st.session_state.last_signal[index]:
        msg = format_msg(index, signal, market, score, prob, pcr_val, max_pain_val, flow, oi_pressure)
        send_telegram(msg)
        st.warning("🚨 Telegram Alert Sent!")
        st.session_state.last_signal[index] = signal


with tab1:
    run("NIFTY50")

with tab2:
    run("SENSEX")
time.sleep(60)
st.rerun()

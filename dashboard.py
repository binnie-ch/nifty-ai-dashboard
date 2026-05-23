import streamlit as st
import random
import time

# -----------------------------
# SAMPLE DATA (Replace with real API later)
# -----------------------------
def get_analysis(index_name):
    base_price = random.uniform(22000, 26000) if index_name == "NIFTY" else random.uniform(70000, 80000)

    return {
        "index": index_name,
        "signal": random.choice(["BUY", "SELL", "HOLD"]),
        "price": round(base_price, 2),
        "score": random.randint(50, 95),
        "probability": random.randint(55, 92),
        "support": round(base_price - random.uniform(200, 800), 2),
        "resistance": round(base_price + random.uniform(200, 800), 2),
        "pcr": round(random.uniform(0.6, 1.4), 2),
        "vix": round(random.uniform(10, 25), 2),
        "iv": round(random.uniform(12, 35), 2),
        "pattern": random.choice(["Doji", "Engulfing", "Breakout", "Reversal"]),
        "orb": random.choice(["Bullish ORB", "Bearish ORB", "No Breakout"]),
        "volume_breakout": random.choice(["YES", "NO"]),
        "sector_message": "Banking & IT showing mixed momentum",
        "sl": round(base_price - random.uniform(300, 1200), 2),
        "target1": round(base_price + random.uniform(400, 1200), 2),
        "target2": round(base_price + random.uniform(1200, 2000), 2),
    }


# -----------------------------
# FORMAT MESSAGE (Telegram Style)
# -----------------------------
def format_signal(result):
    return f"""
🧠 AI {result['index']} SIGNAL: {result['signal']}

📊 Price: {result['price']}

🧠 AI Score: {result['score']}
🎯 Win Probability: {result['probability']}%

📈 Support: {result['support']}
📉 Resistance: {result['resistance']}

📊 PCR: {result['pcr']}
📊 INDIA VIX: {result['vix']}
📊 IV: {result['iv']}

🕯 Pattern: {result['pattern']}
🚀 ORB: {result['orb']}

📈 Volume Breakout: {result['volume_breakout']}

🏦 Sector Analysis:
{result['sector_message']}

🛑 Stop Loss: {result['sl']}

💰 Target 1: {result['target1']}
💰 Target 2: {result['target2']}
"""


# -----------------------------
# STREAMLIT UI
# -----------------------------
st.set_page_config(page_title="AI MARKET DASHBOARD", layout="wide")

st.title("📊 AI MARKET SIGNAL DASHBOARD")
st.markdown("Live AI-based signals for **NIFTY & SENSEX**")

tab1, tab2 = st.tabs(["📈 NIFTY 50", "📊 SENSEX"])

placeholder_nifty = st.empty()
placeholder_sensex = st.empty()

# -----------------------------
# AUTO REFRESH LOOP
# -----------------------------
while True:

    nifty_data = get_analysis("NIFTY")
    sensex_data = get_analysis("SENSEX")

    nifty_msg = format_signal(nifty_data)
    sensex_msg = format_signal(sensex_data)

    with tab1:
        with placeholder_nifty.container():
            st.markdown("### 🚨 NIFTY SIGNAL")
            st.code(nifty_msg)

            c1, c2, c3 = st.columns(3)
            c1.metric("Price", nifty_data["price"])
            c2.metric("AI Score", nifty_data["score"])
            c3.metric("Win %", nifty_data["probability"])

            st.progress(nifty_data["score"] / 100)

    with tab2:
        with placeholder_sensex.container():
            st.markdown("### 🚨 SENSEX SIGNAL")
            st.code(sensex_msg)

            c1, c2, c3 = st.columns(3)
            c1.metric("Price", sensex_data["price"])
            c2.metric("AI Score", sensex_data["score"])
            c3.metric("Win %", sensex_data["probability"])

            st.progress(sensex_data["score"] / 100)

    time.sleep(60)

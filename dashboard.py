import streamlit as st
import requests
from streamlit_autorefresh import st_autorefresh

# =========================
# AUTO REFRESH
# =========================
st_autorefresh(interval=10000, key="refresh")

# =========================
# CONFIG
# =========================
st.set_page_config(page_title="PE/CE AI Multi Index", layout="wide")
st.title("📊 LIVE PE / CE AI SYSTEM (NIFTY • BANKNIFTY • SENSEX)")

# =========================
# TELEGRAM CONFIG
# =========================
TELEGRAM_TOKEN = "8568497873:AAHEXglTw7nowIhX27AmPnKCs24ku6lF6gc"
CHAT_ID = "8540013665"

def send_telegram(msg):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": msg})
    except:
        pass

# =========================
# INDEX MAP
# =========================
INDEX_MAP = {
    "NIFTY50": "NIFTY",
    "BANKNIFTY": "BANKNIFTY",
    "SENSEX": "SENSEX"
}

# =========================
# NSE OPTION CHAIN FETCH
# =========================
def fetch_option_chain(symbol):
    NSE_URL = f"https://www.nseindia.com/api/option-chain-indices?symbol={symbol}"

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept-Language": "en-US,en;q=0.9"
    }

    try:
        session = requests.Session()
        session.get("https://www.nseindia.com", headers=headers, timeout=5)

        response = session.get(NSE_URL, headers=headers, timeout=5)
        data = response.json()

        records = data["records"]["data"]

        ce_oi = 0
        pe_oi = 0

        for r in records:
            if "CE" in r:
                ce_oi += r["CE"].get("openInterest", 0)
            if "PE" in r:
                pe_oi += r["PE"].get("openInterest", 0)

        return ce_oi, pe_oi

    except:
        return 0, 0

# =========================
# PCR
# =========================
def calculate_pcr(ce_oi, pe_oi):
    if ce_oi == 0:
        return 0
    return pe_oi / ce_oi

# =========================
# AI ENGINE
# =========================
def ai_signal(pcr, ce_oi, pe_oi):

    score = 0

    # PCR logic
    if pcr > 1.2:
        score += 30
    elif pcr < 0.8:
        score -= 30

    # OI logic
    if pe_oi > ce_oi:
        score += 20
    else:
        score -= 20

    # Signal
    if score > 40:
        return "🟢 BUY CE (Bullish)", score
    elif score < -40:
        return "🔴 BUY PE (Bearish)", score
    else:
        return "⚪ NO TRADE", score

# =========================
# UI
# =========================
index_name = st.selectbox("Select Index", list(INDEX_MAP.keys()))
symbol = INDEX_MAP[index_name]

# =========================
# LIVE DATA
# =========================
ce_oi, pe_oi = fetch_option_chain(symbol)
pcr = calculate_pcr(ce_oi, pe_oi)

signal, score = ai_signal(pcr, ce_oi, pe_oi)

# =========================
# DASHBOARD
# =========================
col1, col2, col3 = st.columns(3)

col1.metric("📈 Call OI", f"{ce_oi:,}")
col2.metric("📉 Put OI", f"{pe_oi:,}")
col3.metric("⚖️ PCR", round(pcr, 2))

st.divider()

st.subheader(f"🤖 AI SIGNAL - {index_name}")
st.markdown(f"## {signal}")
st.write("AI Score:", score)

# =========================
# MARKET BIAS
# =========================
if score > 40:
    st.success("Market Bias: BULLISH (CE dominance)")
    send_telegram(f"🟢 {index_name} BUY CE SIGNAL | Score: {score}")

elif score < -40:
    st.error("Market Bias: BEARISH (PE dominance)")
    send_telegram(f"🔴 {index_name} BUY PE SIGNAL | Score: {score}")

else:
    st.warning("Market Bias: SIDEWAYS / NO TRADE")

st.info("Auto-refresh every 10 seconds | Telegram alerts enabled")

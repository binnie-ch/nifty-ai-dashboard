import streamlit as st
import requests
from streamlit_autorefresh import st_autorefresh

# =========================
# AUTO REFRESH (10 sec)
# =========================
st_autorefresh(interval=10000, key="refresh")

# =========================
# CONFIG
# =========================
st.set_page_config(page_title="PE/CE AI Live System", layout="wide")

st.title("📊 LIVE PE / CE AI TRADING SYSTEM (INDIA)")

# =========================
# NSE OPTION CHAIN FETCH
# =========================
NSE_URL = "https://www.nseindia.com/api/option-chain-indices?symbol=NIFTY"

headers = {
    "User-Agent": "Mozilla/5.0",
    "Accept-Language": "en-US,en;q=0.9"
}

@st.cache_data(ttl=8)
def fetch_option_chain():
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

    except Exception:
        return 0, 0


# =========================
# INDICATORS
# =========================
def calculate_pcr(ce_oi, pe_oi):
    if ce_oi == 0:
        return 0
    return pe_oi / ce_oi


def detect_trend_mock():
    # Replace later with EMA / yfinance / broker data
    return "UP"


# =========================
# AI ENGINE
# =========================
def ai_signal(pcr, ce_oi, pe_oi, trend):

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

    # Trend logic
    if trend == "UP":
        score += 25
    else:
        score -= 25

    if score > 40:
        return "🟢 BUY CE (Bullish Market)", score
    elif score < -40:
        return "🔴 BUY PE (Bearish Market)", score
    else:
        return "⚪ NO TRADE (Sideways Market)", score


# =========================
# LIVE DATA
# =========================
ce_oi, pe_oi = fetch_option_chain()
pcr = calculate_pcr(ce_oi, pe_oi)
trend = detect_trend_mock()

signal, score = ai_signal(pcr, ce_oi, pe_oi, trend)


# =========================
# DASHBOARD UI
# =========================
col1, col2, col3 = st.columns(3)

col1.metric("📈 Call Open Interest", f"{ce_oi:,}")
col2.metric("📉 Put Open Interest", f"{pe_oi:,}")
col3.metric("⚖️ PCR Ratio", round(pcr, 2))

st.divider()

st.subheader("🤖 AI Trading Signal Engine")
st.markdown(f"## {signal}")
st.write("📊 AI Score:", score)

st.divider()

# =========================
# MARKET INSIGHT PANEL
# =========================
if score > 40:
    st.success("Market Bias: BULLISH → CE dominance detected")
elif score < -40:
    st.error("Market Bias: BEARISH → PE dominance detected")
else:
    st.warning("Market Bias: SIDEWAYS / RANGE BOUND")

st.info("Auto-refresh every 10 seconds | NSE Option Chain Live Data")

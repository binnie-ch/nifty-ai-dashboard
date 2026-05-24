import streamlit as st
import numpy as np
import random
import time
import requests
import holidays
from datetime import datetime
import pytz

# =====================================
# TELEGRAM CONFIG
# =====================================
BOT_TOKEN = "YOUR_BOT_TOKEN"
CHAT_ID = "YOUR_CHAT_ID"


def send_telegram(msg):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    try:
        requests.post(
            url,
            data={
                "chat_id": CHAT_ID,
                "text": msg
            },
            timeout=10
        )

    except Exception as e:
        print("Telegram Error:", e)


# =====================================
# HOLIDAY CHECK
# =====================================
def is_holiday():
    india_holidays = holidays.India()
    today = datetime.now().date()
    return today in india_holidays


def holiday_name():
    india_holidays = holidays.India()
    today = datetime.now().date()
    return india_holidays.get(today, None)


# =====================================
# MARKET HOURS
# =====================================
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
        return False, "⛔ Market Closed"

    return True, "✅ Market Active"


# =====================================
# MARKET DATA
# =====================================
def get_market(index):

    if index == "NIFTY50":
        price = random.uniform(22000, 26000)

    elif index == "BANKNIFTY":
        price = random.uniform(48000, 58000)

    else:
        price = random.uniform(70000, 80000)

    return {
        "price": round(price, 2),
        "rsi": random.randint(20, 80),
        "volume": random.randint(100000, 1000000),
        "orb": random.choice([
            "Breakout Up",
            "Breakout Down",
            "No Breakout"
        ]),
        "candle": random.choice([
            "Bullish Engulfing",
            "Bearish Engulfing",
            "Hammer",
            "Shooting Star",
            "Strong Bull Candle",
            "Strong Bear Candle"
        ])
    }


# =====================================
# OPTION CHAIN
# =====================================
def get_option_chain(price):

    chain = []

    for i in range(-10, 11):

        strike = round(price / 100) * 100 + i * 100

        chain.append({
            "strike": strike,
            "call_oi": random.randint(5000, 60000),
            "put_oi": random.randint(5000, 60000),
            "call_change": random.randint(-8000, 8000),
            "put_change": random.randint(-8000, 8000)
        })

    return chain


# =====================================
# BUILDUP SCANNER
# =====================================
def buildup_scanner(chain):

    buildup_data = []

    for row in chain:

        ce_move = random.uniform(-5, 5)
        pe_move = random.uniform(-5, 5)

        if ce_move > 0 and row["call_change"] > 0:
            ce_signal = "🟢 CE LONG BUILDUP"

        elif ce_move < 0 and row["call_change"] > 0:
            ce_signal = "🔴 CE SHORT BUILDUP"

        elif ce_move > 0 and row["call_change"] < 0:
            ce_signal = "🚀 CE SHORT COVERING"

        else:
            ce_signal = "⚠️ CE LONG UNWINDING"

        if pe_move > 0 and row["put_change"] > 0:
            pe_signal = "🟢 PE LONG BUILDUP"

        elif pe_move < 0 and row["put_change"] > 0:
            pe_signal = "🔴 PE SHORT BUILDUP"

        elif pe_move > 0 and row["put_change"] < 0:
            pe_signal = "🚀 PE SHORT COVERING"

        else:
            pe_signal = "⚠️ PE LONG UNWINDING"

        buildup_data.append({
            "strike": row["strike"],
            "ce_signal": ce_signal,
            "pe_signal": pe_signal,
            "call_change": row["call_change"],
            "put_change": row["put_change"]
        })

    return buildup_data


# =====================================
# ATM STRIKE
# =====================================
def atm_strike(price):
    return round(price / 100) * 100


# =====================================
# STRONGEST BUILDUP
# =====================================
def strongest_buildup(buildup_data):

    return max(
        buildup_data,
        key=lambda x: abs(x["call_change"]) + abs(x["put_change"])
    )


# =====================================
# PCR
# =====================================
def calculate_pcr(chain):

    call = sum(x["call_oi"] for x in chain)
    put = sum(x["put_oi"] for x in chain)

    return round(put / call, 2)


# =====================================
# MAX PAIN
# =====================================
def max_pain(chain):

    return min(
        chain,
        key=lambda x: x["call_oi"] + x["put_oi"]
    )["strike"]


# =====================================
# VWAP ENGINE
# =====================================
def vwap_position(price):

    vwap = round(price * random.uniform(0.995, 1.005), 2)

    if price > vwap:
        return vwap, "ABOVE VWAP (Bullish)", 10

    return vwap, "BELOW VWAP (Bearish)", -10


# =====================================
# INDIA VIX
# =====================================
def india_vix():

    vix = round(random.uniform(10, 25), 2)

    if vix > 20:
        signal = "HIGH VOLATILITY"

    elif vix < 13:
        signal = "LOW VOLATILITY"

    else:
        signal = "NORMAL VOLATILITY"

    return vix, signal


# =====================================
# BREAKOUT STRENGTH
# =====================================
def breakout_strength():

    strength = random.randint(1, 100)

    if strength > 75:
        return "STRONG BREAKOUT", 15

    elif strength > 50:
        return "MODERATE BREAKOUT", 5

    return "WEAK BREAKOUT", -10


# =====================================
# FAKE BREAKOUT
# =====================================
def fake_breakout(market):

    if market["orb"] != "No Breakout" and market["volume"] < 300000:
        return True

    return False


# =====================================
# MULTI TIMEFRAME
# =====================================
def timeframe_trend():

    trends = ["BULLISH", "BEARISH", "SIDEWAYS"]

    tf_5m = random.choice(trends)
    tf_15m = random.choice(trends)
    tf_1h = random.choice(trends)
    tf_1d = random.choice(trends)

    bullish = [tf_5m, tf_15m, tf_1h, tf_1d].count("BULLISH")
    bearish = [tf_5m, tf_15m, tf_1h, tf_1d].count("BEARISH")

    if bullish >= 3:
        final = "STRONG BULLISH"
        bias = 20

    elif bearish >= 3:
        final = "STRONG BEARISH"
        bias = -20

    else:
        final = "SIDEWAYS"
        bias = 0

    return {
        "5m": tf_5m,
        "15m": tf_15m,
        "1h": tf_1h,
        "1d": tf_1d,
        "final": final,
        "bias": bias
    }


# =====================================
# SMART MONEY FLOW
# =====================================
def smart_money(chain, market):

    call_flow = sum(x["call_change"] for x in chain)
    put_flow = sum(x["put_change"] for x in chain)

    oi_pressure = call_flow - put_flow

    whale = any(
        abs(x["call_change"]) > 5000 or
        abs(x["put_change"]) > 5000
        for x in chain
    )

    if oi_pressure > 15000 and market["volume"] > 500000:
        return "🚀 INSTITUTIONAL BUYING", 25, oi_pressure

    elif oi_pressure < -15000 and market["volume"] > 500000:
        return "📉 INSTITUTIONAL SELLING", -25, oi_pressure

    elif whale:
        return "🐳 WHALE ACTIVITY DETECTED", 10, oi_pressure

    return "⚖️ NEUTRAL FLOW", 0, oi_pressure


# =====================================
# STOP LOSS
# =====================================
def calculate_sl(price, signal, index):

    if index == "BANKNIFTY":
        volatility = random.uniform(0.004, 0.012)

    else:
        volatility = random.uniform(0.002, 0.008)

    if signal == "BUY":
        sl = price * (1 - volatility)

    elif signal == "SELL":
        sl = price * (1 + volatility)

    else:
        sl = price

    return round(sl, 2)


# =====================================
# TARGETS
# =====================================
def calculate_targets(price, signal):

    if signal == "BUY":
        return round(price * 1.01, 2), round(price * 1.02, 2)

    elif signal == "SELL":
        return round(price * 0.99, 2), round(price * 0.98, 2)

    return price, price


# =====================================
# ENTRY ZONE
# =====================================
def entry_zone(price):

    low = round(price - 20, 2)
    high = round(price + 20, 2)

    return low, high


# =====================================
# OPTION DIRECTION
# =====================================
def option_direction(signal):

    if signal == "BUY":
        return "CE (CALL BUY)"

    elif signal == "SELL":
        return "PE (PUT BUY)"

    return "NO TRADE"


# =====================================
# AI GRADE
# =====================================
def ai_grade(score):

    if score >= 70:
        return "A+"

    elif score >= 50:
        return "A"

    elif score >= 30:
        return "B"

    return "NO TRADE"


# =====================================
# AI ENGINE
# =====================================
def ai_engine(market, chain):

    score = 0

    pcr = calculate_pcr(chain)
    maxp = max_pain(chain)

    flow, smart_bias, oi = smart_money(chain, market)

    vwap, vwap_status, vwap_bias = vwap_position(
        market["price"]
    )

    vix, vix_status = india_vix()

    breakout, breakout_bias = breakout_strength()

    tf = timeframe_trend()

    fakeout = fake_breakout(market)

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

    # Candle Momentum
    if "Bullish" in market["candle"]:
        score += 10

    elif "Bearish" in market["candle"]:
        score -= 10

    # Smart Money
    score += smart_bias

    # VWAP
    score += vwap_bias

    # Breakout
    score += breakout_bias

    # Multi timeframe
    score += tf["bias"]

    # Fake breakout penalty
    if fakeout:
        score -= 30

    signal = "BUY" if score > 25 else "SELL" if score < -25 else "HOLD"

    if fakeout or abs(score) < 20:
        signal = "NO TRADE"

    probability = min(95, max(50, 50 + abs(score)))

    grade = ai_grade(abs(score))

    return (
        signal,
        score,
        probability,
        pcr,
        maxp,
        flow,
        oi,
        vwap,
        vwap_status,
        vix,
        vix_status,
        breakout,
        tf,
        fakeout,
        grade
    )


# =====================================
# TELEGRAM MESSAGE
# =====================================
def format_msg(
    index,
    signal,
    market,
    score,
    probability,
    pcr,
    maxp,
    flow,
    oi,
    sl,
    t1,
    t2,
    atm,
    strong,
    vwap,
    vwap_status,
    vix,
    vix_status,
    breakout,
    tf,
    grade,
    entry_low,
    entry_high
):

    direction = option_direction(signal)

    return f"""
🚨 AI {index} SIGNAL

📊 Signal: {signal}
📌 Option Strategy: {direction}

📊 Price: {market['price']}

🧠 AI Score: {score}
🎯 Win Probability: {probability}%
🧠 AI Grade: {grade}

📊 PCR: {pcr}
🎯 Max Pain: {maxp}

📊 VWAP: {vwap}
📈 VWAP Status: {vwap_status}

📊 INDIA VIX: {vix}
⚡ VIX Signal: {vix_status}

🚀 Breakout Strength: {breakout}

📈 Multi Timeframe:
5m: {tf['5m']}
15m: {tf['15m']}
1h: {tf['1h']}
1D: {tf['1d']}

🎯 ENTRY ZONE:
{entry_low} - {entry_high}

🛑 Stop Loss: {sl}
🎯 Target 1: {t1}
🎯 Target 2: {t2}

🎯 ATM Strike: {atm}

📊 BUILDUP ANALYSIS
CE: {strong['ce_signal']}
PE: {strong['pe_signal']}

🔥 Active Strike: {strong['strike']}

💰 Smart Money Flow: {flow}
📈 OI Pressure: {oi}

📉 RSI: {market['rsi']}
🕯 Candle: {market['candle']}
🚀 ORB: {market['orb']}
"""


# =====================================
# STREAMLIT UI
# =====================================
st.set_page_config(
    page_title="BINNY AI DASHBOARD",
    layout="wide"
)

st.title("📊 BINNY AI SMART MONEY DASHBOARD")


tab1, tab2, tab3 = st.tabs([
    "📈 NIFTY50",
    "🏦 BANKNIFTY",
    "📊 SENSEX"
])


if "last_signal" not in st.session_state:

    st.session_state.last_signal = {
        "NIFTY50": None,
        "BANKNIFTY": None,
        "SENSEX": None
    }


# =====================================
# MAIN ENGINE
# =====================================
def run(index):

    allowed, status = market_status()

    st.info(status)

    if not allowed:
        st.warning("🚫 Market Closed / Holiday")
        return

    market = get_market(index)

    chain = get_option_chain(
        market["price"]
    )

    buildup = buildup_scanner(chain)

    strong = strongest_buildup(buildup)

    atm = atm_strike(
        market["price"]
    )

    (
        signal,
        score,
        probability,
        pcr,
        maxp,
        flow,
        oi,
        vwap,
        vwap_status,
        vix,
        vix_status,
        breakout,
        tf,
        fakeout,
        grade
    ) = ai_engine(market, chain)

    sl = calculate_sl(
        market["price"],
        signal,
        index
    )

    t1, t2 = calculate_targets(
        market["price"],
        signal
    )

    entry_low, entry_high = entry_zone(
        market["price"]
    )

    st.subheader(f"{index} → {signal}")

    st.metric("Price", market["price"])
    st.metric("AI Score", score)
    st.metric("Win Probability", f"{probability}%")
    st.metric("AI Grade", grade)

    st.write("📊 PCR:", pcr)
    st.write("🎯 Max Pain:", maxp)

    st.write("📊 VWAP:", vwap)
    st.write("📈 VWAP Status:", vwap_status)

    st.write("📊 INDIA VIX:", vix)
    st.write("⚡ VIX Signal:", vix_status)

    st.write("🚀 Breakout Strength:", breakout)

    st.write("🛑 Stop Loss:", sl)
    st.write("🎯 Target 1:", t1)
    st.write("🎯 Target 2:", t2)

    st.write("🎯 ENTRY ZONE:")
    st.success(f"{entry_low} - {entry_high}")

    st.subheader("📊 CE / PE BUILDUP")

    st.write(f"🎯 ATM Strike: {atm}")

    st.success(
        f"Strongest Activity Strike: {strong['strike']}"
    )

    st.info(f"""
    CE: {strong['ce_signal']}
    PE: {strong['pe_signal']}
    """)

    st.subheader("📈 MULTI TIMEFRAME")

    st.json(tf)

    if fakeout:
        st.error("⚠️ FAKE BREAKOUT DETECTED")

    if signal == "NO TRADE":
        st.warning("🚫 NO TRADE ZONE")

    st.success(flow)

    st.info(
        f"Options Strategy: {option_direction(signal)}"
    )

    # TELEGRAM ALERT
    if (
        signal not in ["HOLD", "NO TRADE"] and
        signal != st.session_state.last_signal[index]
    ):

        msg = format_msg(
            index,
            signal,
            market,
            score,
            probability,
            pcr,
            maxp,
            flow,
            oi,
            sl,
            t1,
            t2,
            atm,
            strong,
            vwap,
            vwap_status,
            vix,
            vix_status,
            breakout,
            tf,
            grade,
            entry_low,
            entry_high
        )

        send_telegram(msg)

        st.success("🚨 Telegram Alert Sent")

        st.session_state.last_signal[index] = signal


with tab1:
    run("NIFTY50")

with tab2:
    run("BANKNIFTY")

with tab3:
    run("SENSEX")


time.sleep(60)
st.rerun()

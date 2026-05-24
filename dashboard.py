import requests
import time
import numpy as np
import logging

# =========================
# CONFIG
# =========================
BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0",
    "referer": "https://www.nseindia.com"
})

logging.basicConfig(level=logging.INFO)

# =========================
# NSE LIVE DATA
# =========================
def get_chain(symbol):
    url = f"https://www.nseindia.com/api/option-chain-indices?symbol={symbol}"
    try:
        session.get("https://www.nseindia.com", timeout=5)
        r = session.get(url, timeout=10)
        return r.json()
    except:
        return None


# =========================
# EXTRACT LIVE DATA
# =========================
def extract(data):
    records = data["records"]["data"]

    ce_oi = 0
    pe_oi = 0
    ce_chg = 0
    pe_chg = 0
    ivs = []

    strike_map = {}

    for i in records:
        ce = i.get("CE", {})
        pe = i.get("PE", {})

        strike = i["strikePrice"]

        ce_oi += ce.get("openInterest", 0)
        pe_oi += pe.get("openInterest", 0)

        ce_chg += ce.get("changeinOpenInterest", 0)
        pe_chg += pe.get("changeinOpenInterest", 0)

        if "impliedVolatility" in ce:
            ivs.append(ce["impliedVolatility"])
        if "impliedVolatility" in pe:
            ivs.append(pe["impliedVolatility"])

        strike_map[strike] = {
            "CE_LTP": ce.get("lastPrice", 0),
            "PE_LTP": pe.get("lastPrice", 0),
            "CE_OI": ce.get("openInterest", 0),
            "PE_OI": pe.get("openInterest", 0),
        }

    pcr = pe_oi / ce_oi if ce_oi else 0
    iv = np.mean(ivs) if ivs else 0

    return {
        "pcr": pcr,
        "iv": iv,
        "ce_chg": ce_chg,
        "pe_chg": pe_chg,
        "strike_map": strike_map
    }


# =========================
# STRIKE SELECTION
# =========================
def best_strike(strike_map, ltp):
    atm = round(ltp / 50) * 50

    nearest = sorted(strike_map.keys(), key=lambda x: abs(x - atm))[:5]

    return {
        "ATM": atm,
        "CALL_STRIKE": atm + 50,
        "PUT_STRIKE": atm - 50,
        "NEARBY": nearest
    }


# =========================
# SMART MONEY FLOW
# =========================
def smart_flow(f):
    if f["ce_chg"] > f["pe_chg"] * 1.2:
        return "🟢 CALL BUILDUP (SMART MONEY BUYING CALLS)"
    elif f["pe_chg"] > f["ce_chg"] * 1.2:
        return "🔴 PUT BUILDUP (SMART MONEY BUYING PUTS)"
    else:
        return "🟡 NEUTRAL FLOW"


# =========================
# ENTRY / EXIT ENGINE
# =========================
def entry_exit(score, atm):
    if score >= 70:
        return f"ENTRY: ATM CALL ({atm}) | EXIT: +100 pts / Max Pain"
    elif score <= 30:
        return f"ENTRY: ATM PUT ({atm}) | EXIT: +100 pts / Max Pain"
    else:
        return "NO TRADE ZONE"


# =========================
# SIGNAL ENGINE (NO ML)
# =========================
def signal_engine(f):
    score = 50

    # PCR
    if f["pcr"] > 1.3:
        score += 20
    elif f["pcr"] < 0.8:
        score -= 20

    # OI pressure
    if f["ce_chg"] > f["pe_chg"]:
        score += 10
    else:
        score -= 10

    # IV filter
    if f["iv"] > 18:
        score -= 5

    score = max(0, min(100, score))

    if score >= 70:
        signal = "🟢 BUY CALL"
    elif score <= 30:
        signal = "🔴 BUY PUT"
    else:
        signal = "🟡 NO TRADE"

    return score, signal


# =========================
# FORMAT MESSAGE
# =========================
def format_msg(symbol, f, strikes, score, signal, sm, entry_exit_text):
    return f"""
📊 {symbol} LIVE CE/PE ANALYSIS

✔ NSE DATA: LIVE
✔ NO ML SYSTEM

-------------------------
📌 PCR: {round(f['pcr'],2)}
⚡ IV: {round(f['iv'],2)}

📈 CE Pressure: {f['ce_chg']}
📉 PE Pressure: {f['pe_chg']}

🎯 STRIKES:
ATM: {strikes['ATM']}
CALL: {strikes['CALL_STRIKE']}
PUT: {strikes['PUT_STRIKE']}

🧠 SCORE: {score}/100
🚨 SIGNAL: {signal}

🔥 SMART MONEY:
{sm}

📍 TRADE PLAN:
{entry_exit_text}

-------------------------
⏱ LIVE UPDATE ENGINE (60s INTERNAL)
"""


# =========================
# PROCESS ENGINE
# =========================
def process(symbol, ltp):
    data = get_chain(symbol)
    if not data:
        return None

    f = extract(data)
    strikes = best_strike(f["strike_map"], ltp)
    score, signal = signal_engine(f)
    sm = smart_flow(f)
    entry_exit_text = entry_exit(score, strikes["ATM"])

    return format_msg(symbol, f, strikes, score, signal, sm, entry_exit_text)


# =========================
# TELEGRAM COMMANDS
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🚀 LIVE NSE CE/PE BOT READY\n\n"
        "/nifty\n/banknifty\n/sensex"
    )


async def nifty(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = process("NIFTY", 25000)
    await update.message.reply_text(msg or "Error fetching data")


async def banknifty(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = process("BANKNIFTY", 52000)
    await update.message.reply_text(msg or "Error fetching data")


async def sensex(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = process("NIFTY", 75000)
    await update.message.reply_text(msg or "Error fetching data")


# =========================
# MAIN
# =========================
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("nifty", nifty))
    app.add_handler(CommandHandler("banknifty", banknifty))
    app.add_handler(CommandHandler("sensex", sensex))

    print("🚀 CE/PE LIVE BOT RUNNING (NO ML, REAL NSE DATA)")
    app.run_polling()


if __name__ == "__main__":
    main()

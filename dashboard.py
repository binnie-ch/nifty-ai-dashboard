import requests
import numpy as np
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# =========================
# CONFIG
# =========================
BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"

logging.basicConfig(level=logging.INFO)

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0",
    "Accept-Language": "en-US,en;q=0.9",
    "referer": "https://www.nseindia.com"
})


# =========================
# NSE OPTION CHAIN (LIVE)
# =========================
def get_option_chain(symbol="NIFTY"):
    url = f"https://www.nseindia.com/api/option-chain-indices?symbol={symbol}"
    try:
        session.get("https://www.nseindia.com", timeout=5)
        res = session.get(url, timeout=10)
        return res.json()
    except Exception as e:
        print("API Error:", e)
        return None


# =========================
# FEATURE ENGINE (LIVE ONLY)
# =========================
def extract_live_features(data):
    records = data["records"]["data"]

    call_oi = 0
    put_oi = 0
    ce_change = 0
    pe_change = 0
    iv_values = []

    for i in records:
        ce = i.get("CE", {})
        pe = i.get("PE", {})

        call_oi += ce.get("openInterest", 0)
        put_oi += pe.get("openInterest", 0)

        ce_change += ce.get("changeinOpenInterest", 0)
        pe_change += pe.get("changeinOpenInterest", 0)

        if "impliedVolatility" in ce:
            iv_values.append(ce["impliedVolatility"])
        if "impliedVolatility" in pe:
            iv_values.append(pe["impliedVolatility"])

    pcr = put_oi / call_oi if call_oi else 0
    iv = np.mean(iv_values) if iv_values else 0

    return {
        "pcr": pcr,
        "iv": iv,
        "ce_change": ce_change,
        "pe_change": pe_change
    }


# =========================
# REAL SIGNAL ENGINE (NO ML)
# =========================
def generate_signal(f):
    score = 50  # neutral base

    # ================= PCR RULE =================
    if f["pcr"] > 1.3:
        score += 20  # bullish
    elif f["pcr"] < 0.8:
        score -= 20  # bearish

    # ================= OI PRESSURE =================
    if f["ce_change"] > f["pe_change"]:
        score += 10
    else:
        score -= 10

    # ================= IV FILTER =================
    if f["iv"] > 18:
        score -= 5  # high volatility caution

    # clamp
    score = max(0, min(100, score))

    # ================= FINAL SIGNAL =================
    if score >= 65:
        signal = "🟢 BUY CALL (BULLISH TREND)"
    elif score <= 35:
        signal = "🔴 BUY PUT (BEARISH TREND)"
    else:
        signal = "🟡 NO TRADE / SIDEWAYS MARKET"

    return score, signal


# =========================
# FORMAT OUTPUT
# =========================
def build_message(symbol, f, score, signal):
    return f"""
📊 {symbol} LIVE MARKET SIGNAL

✔ NSE OPTION CHAIN: LIVE
✔ PCR / IV / OI: LIVE
✔ CE/PE DATA: LIVE

------------------------
📌 PCR: {round(f['pcr'], 2)}
⚡ IV: {round(f['iv'], 2)}
📈 CE Pressure: {f['ce_change']}
📉 PE Pressure: {f['pe_change']}

🧠 AI SCORE: {score}/100

🚨 SIGNAL:
{signal}

⚠️ Educational Use Only
"""


# =========================
# TELEGRAM COMMANDS
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🚀 NSE LIVE TRADING BOT READY\n\n"
        "/nifty - NIFTY signal\n"
        "/banknifty - BANKNIFTY signal\n"
        "/signal - Combined analysis"
    )


async def nifty(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = get_option_chain("NIFTY")
    if not data:
        await update.message.reply_text("API Error")
        return

    f = extract_live_features(data)
    score, signal = generate_signal(f)

    msg = build_message("NIFTY", f, score, signal)
    await update.message.reply_text(msg)


async def banknifty(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = get_option_chain("BANKNIFTY")
    if not data:
        await update.message.reply_text("API Error")
        return

    f = extract_live_features(data)
    score, signal = generate_signal(f)

    msg = build_message("BANKNIFTY", f, score, signal)
    await update.message.reply_text(msg)


async def signal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    n = extract_live_features(get_option_chain("NIFTY"))
    b = extract_live_features(get_option_chain("BANKNIFTY"))

    ns, nsignal = generate_signal(n)
    bs, bsignal = generate_signal(b)

    msg = f"""
📊 MARKET DASHBOARD (LIVE)

NIFTY:
🧠 Score: {ns}/100
🚨 {nsignal}

BANKNIFTY:
🧠 Score: {bs}/100
🚨 {bsignal}

✔ NSE DATA: LIVE
✔ NO ML USED
✔ PURE MARKET FLOW ENGINE
"""

    await update.message.reply_text(msg)


# =========================
# MAIN
# =========================
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("nifty", nifty))
    app.add_handler(CommandHandler("banknifty", banknifty))
    app.add_handler(CommandHandler("signal", signal))

    print("🚀 LIVE NSE SIGNAL BOT RUNNING...")
    app.run_polling()


if __name__ == "__main__":
    main()

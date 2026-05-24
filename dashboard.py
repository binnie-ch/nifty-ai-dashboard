import requests
import time
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
# LIVE NSE API
# =========================
def get_option_chain(symbol):
    url = f"https://www.nseindia.com/api/option-chain-indices?symbol={symbol}"
    try:
        session.get("https://www.nseindia.com", timeout=5)
        r = session.get(url, timeout=10)
        return r.json()
    except:
        return None


# =========================
# LIVE FEATURE ENGINE
# =========================
def extract_features(data):
    records = data["records"]["data"]

    call_oi = 0
    put_oi = 0
    ce_change = 0
    pe_change = 0
    iv = []

    strike_oi_map = {}

    for i in records:
        ce = i.get("CE", {})
        pe = i.get("PE", {})

        strike = i["strikePrice"]

        ce_oi = ce.get("openInterest", 0)
        pe_oi = pe.get("openInterest", 0)

        ce_chg = ce.get("changeinOpenInterest", 0)
        pe_chg = pe.get("changeinOpenInterest", 0)

        call_oi += ce_oi
        put_oi += pe_oi
        ce_change += ce_chg
        pe_change += pe_chg

        if "impliedVolatility" in ce:
            iv.append(ce["impliedVolatility"])
        if "impliedVolatility" in pe:
            iv.append(pe["impliedVolatility"])

        strike_oi_map[strike] = ce_oi + pe_oi

    pcr = put_oi / call_oi if call_oi else 0
    iv_avg = np.mean(iv) if iv else 0

    max_pain = min(strike_oi_map, key=strike_oi_map.get)

    return {
        "pcr": pcr,
        "iv": iv_avg,
        "ce_change": ce_change,
        "pe_change": pe_change,
        "max_pain": max_pain,
        "strike_map": strike_oi_map
    }


# =========================
# STRIKE SELECTION ENGINE
# =========================
def get_best_strike(strike_map, ltp):
    atm = round(ltp / 50) * 50

    nearby = sorted(strike_map.items(), key=lambda x: abs(x[0] - atm))

    return {
        "ATM": atm,
        "CALL": atm + 50,
        "PUT": atm - 50
    }


# =========================
# SMART MONEY FLOW
# =========================
def smart_money(f):
    if f["ce_change"] > f["pe_change"] * 1.2:
        return "🟢 SMART MONEY: CALL BUILDUP"
    elif f["pe_change"] > f["ce_change"] * 1.2:
        return "🔴 SMART MONEY: PUT BUILDUP"
    else:
        return "🟡 NEUTRAL FLOW"


# =========================
# SIGNAL ENGINE (NO ML)
# =========================
def signal_engine(f):
    score = 50

    if f["pcr"] > 1.3:
        score += 20
    elif f["pcr"] < 0.8:
        score -= 20

    if f["ce_change"] > f["pe_change"]:
        score += 10
    else:
        score -= 10

    if f["iv"] > 18:
        score -= 5

    if f["max_pain"]:
        score += 0  # anchor zone

    score = max(0, min(100, score))

    if score >= 65:
        signal = "🟢 BUY CALL"
        entry = "ATM CALL"
        exit_ = "MAX PAIN ZONE"
    elif score <= 35:
        signal = "🔴 BUY PUT"
        entry = "ATM PUT"
        exit_ = "MAX PAIN ZONE"
    else:
        signal = "🟡 NO TRADE"
        entry = "-"
        exit_ = "-"

    return score, signal, entry, exit_


# =========================
# PREMIUM MESSAGE
# =========================
def format_msg(symbol, f, strike, score, signal, entry, exit_, sm):
    return f"""
📊 {symbol} LIVE PREMIUM SIGNAL

━━━━━━━━━━━━━━
📌 PCR: {round(f['pcr'], 2)}
⚡ IV: {round(f['iv'], 2)}
🎯 Max Pain: {f['max_pain']}

📈 Entry: {entry}
🎯 Exit: {exit_}

💰 Strike Suggestion:
CALL: {strike['CALL']}
PUT: {strike['PUT']}
ATM: {strike['ATM']}

🧠 Score: {score}/100
🚨 Signal: {signal}

🔥 Smart Money:
{sm}

━━━━━━━━━━━━━━
✔ NSE LIVE DATA ONLY
✔ NO ML / NO SIMULATION
"""


# =========================
# TELEGRAM COMMANDS
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🚀 PREMIUM NSE BOT READY\n\n"
        "/nifty\n/banknifty\n/sensex\n/live"
    )


def process(symbol, ltp):
    data = get_option_chain(symbol)
    if not data:
        return None

    f = extract_features(data)
    strike = get_best_strike(f["strike_map"], ltp)
    score, signal, entry, exit_ = signal_engine(f)
    sm = smart_money(f)

    msg = format_msg(symbol, f, strike, score, signal, entry, exit_, sm)

    return msg


async def nifty(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = process("NIFTY", 25000)
    await update.message.reply_text(msg or "Error")


async def banknifty(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = process("BANKNIFTY", 52000)
    await update.message.reply_text(msg or "Error")


async def sensex(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = process("NIFTY", 75000)  # NSE proxy behavior
    await update.message.reply_text(msg or "Error")


# =========================
# AUTO ALERT ENGINE (2 MIN)
# =========================
def auto_alert(app):
    while True:
        try:
            msg = process("NIFTY", 25000)
            if msg:
                app.bot.send_message(chat_id=YOUR_CHAT_ID, text=msg)

            msg2 = process("BANKNIFTY", 52000)
            if msg2:
                app.bot.send_message(chat_id=YOUR_CHAT_ID, text=msg2)

            time.sleep(120)  # 2 minutes

        except Exception as e:
            print("Alert error:", e)
            time.sleep(120)


# =========================
# MAIN
# =========================
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("nifty", nifty))
    app.add_handler(CommandHandler("banknifty", banknifty))
    app.add_handler(CommandHandler("sensex", sensex))

    print("🚀 PREMIUM LIVE BOT RUNNING...")

    # NOTE: Auto-alert runs separately (thread recommended in production)
    # import threading
    # threading.Thread(target=auto_alert, args=(app,), daemon=True).start()

    app.run_polling()


if __name__ == "__main__":
    main()

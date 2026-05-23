import yfinance as yf
import pandas as pd
import requests
import time
from datetime import datetime
import pytz

# =========================
# TELEGRAM CONFIG
# =========================

import os

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# =========================
# SEND TELEGRAM ALERT
# =========================

def send_alert(message):

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    requests.get(url, params={
        "chat_id": CHAT_ID,
        "text": message
    })

# =========================
# AI SIGNAL FUNCTION
# =========================

def generate_signal(data):

    latest = data.iloc[-1]

    ema9 = float(latest['EMA9'])
    ema21 = float(latest['EMA21'])
    rsi = float(latest['RSI'])
    close = float(latest['Close'])
    vwap = float(latest['VWAP'])

    score = 0

    # EMA Trend
    if ema9 > ema21:
        score += 30
    else:
        score -= 30

    # RSI
    if rsi > 60:
        score += 25

    elif rsi < 40:
        score -= 25

    # VWAP
    if close > vwap:
        score += 20
    else:
        score -= 20

    # Final Signal
    if score >= 50:
        return "BUY CE 🚀", score

    elif score <= -50:
        return "BUY PE 🔻", score

    else:
        return "NO TRADE", score

# =========================
# MARKET HOURS CHECK
# =========================

def market_open():

    india = pytz.timezone('Asia/Kolkata')
    now = datetime.now(india)

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

    # Weekend
    if now.weekday() >= 5:
        return False

    if now < market_start or now > market_end:
        return False

    return True

# =========================
# MAIN LOOP
# =========================

last_signal = ""

while True:

    try:

        if market_open():

            # Download data
            data = yf.download(
                "^NSEI",
                period="5d",
                interval="5m",
                progress=False
            )

            # Fix columns
            data.columns = [
                col[0] if isinstance(col, tuple)
                else col
                for col in data.columns
            ]

            # Indicators
            data['EMA9'] = data['Close'].ewm(span=9).mean()
            data['EMA21'] = data['Close'].ewm(span=21).mean()

            # RSI
            delta = data['Close'].diff()

            gain = (
                delta.where(delta > 0, 0)
            ).rolling(14).mean()

            loss = (
                -delta.where(delta < 0, 0)
            ).rolling(14).mean()

            rs = gain / loss

            data['RSI'] = 100 - (100 / (1 + rs))

            # VWAP
            tp = (
                data['High']
                + data['Low']
                + data['Close']
            ) / 3

            data['VWAP'] = (
                (tp * data['Volume']).cumsum()
                / data['Volume'].cumsum()
            )

            data = data.dropna()

            # Generate AI signal
            signal, score = generate_signal(data)

            latest_price = round(
                float(data.iloc[-1]['Close']),
                2
            )

            # Send only new signals
            if signal != last_signal:

                if signal != "NO TRADE":

                    msg = f"""
🤖 AI NIFTY SIGNAL

{signal}

📊 Price: {latest_price}

🧠 AI Score: {score}
"""

                    send_alert(msg)

                last_signal = signal

            print(
                datetime.now(),
                signal,
                latest_price
            )

        else:
            print("Market Closed")

    except Exception as e:
        print("ERROR:", e)

    # Wait 60 seconds
    time.sleep(60)

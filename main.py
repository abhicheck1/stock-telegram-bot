import os

print("API KEY PRESENT:", bool(os.getenv("TWELVE_DATA_API_KEY")))
print("TELEGRAM TOKEN PRESENT:", bool(os.getenv("TELEGRAM_TOKEN")))
print("CHAT ID PRESENT:", bool(os.getenv("TELEGRAM_CHAT_ID")))

import time
import requests
import pandas as pd

# ================= CONFIG =================

STOCKS = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA"]

API_KEY = os.getenv("TWELVE_DATA_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# ================= INDICATORS =================

def rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

# ================= DATA FETCH =================

def get_stock_data(symbol):
    url = "https://api.twelvedata.com/time_series"
    params = {
        "symbol": symbol,
        "interval": "1day",
        "outputsize": 100,
        "apikey": API_KEY
    }

    r = requests.get(url, params=params, timeout=10)
    data = r.json()

    if "values" not in data:
        return None

    df = pd.DataFrame(data["values"])
    df["datetime"] = pd.to_datetime(df["datetime"])
    df.set_index("datetime", inplace=True)
    df = df.sort_index()

    df["close"] = df["close"].astype(float)
    return df

# ================= ANALYSIS =================

def analyze():
    report = []

    for stock in STOCKS:
        df = get_stock_data(stock)

        if df is None or len(df) < 30:
            continue

        rsi_val = rsi(df["close"]).iloc[-1]
        price = df["close"].iloc[-1]

        signal = "HOLD 😐"
        if rsi_val < 35:
            signal = "BUY 🟢"
        elif rsi_val > 65:
            signal = "SELL 🔴"

        report.append(
            f"{stock}\nPrice: ${price:.2f}\nRSI: {rsi_val:.2f}\nSignal: {signal}\n"
        )

        time.sleep(8)  # VERY IMPORTANT for free tier

    if not report:
        return "❌ No stock data received."

    return "📊 *Daily Stock Update*\n\n" + "\n".join(report)

# ================= TELEGRAM =================

def send_telegram(msg):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": msg,
        "parse_mode": "Markdown"
    }

    requests.post(url, json=payload, timeout=10)

# ================= MAIN =================

if __name__ == "__main__":
    message = analyze()
    print(message)
    send_telegram(message)

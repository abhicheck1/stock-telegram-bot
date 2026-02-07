import os
import time
import requests
import pandas as pd

# ================= CONFIG =================

PORTFOLIO = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA"]

FMP_API_KEY = os.getenv("FMP_API_KEY")
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

# ================= DATA FETCH (FMP) =================

def get_stock_data(ticker):
    if not FMP_API_KEY:
        return None

    url = f"https://financialmodelingprep.com/api/v3/historical-price-full/{ticker}"
    params = {"apikey": FMP_API_KEY}

    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
    except Exception:
        return None

    if "historical" not in data:
        return None

    df = pd.DataFrame(data["historical"])
    if df.empty:
        return None

    df["date"] = pd.to_datetime(df["date"])
    df.set_index("date", inplace=True)
    df.sort_index(inplace=True)

    return df[["close"]].rename(columns={"close": "Close"})

# ================= ANALYSIS =================

def analyze_market():
    report = []

    for ticker in PORTFOLIO:
        df = get_stock_data(ticker)

        if df is None or len(df) < 30:
            continue

        rsi_val = rsi(df["Close"]).iloc[-1]
        price = df["Close"].iloc[-1]

        signal = "HOLD 😐"
        if rsi_val < 35:
            signal = "BUY 🟢"
        elif rsi_val > 65:
            signal = "SELL 🔴"

        report.append(
            f"{ticker}\nPrice: ${price:.2f}\nRSI: {rsi_val:.2f}\nSignal: {signal}\n"
        )

        time.sleep(1)  # API safety

    if not report:
        return "❌ No stock data received."

    message = "📊 *Daily Stock Update*\n\n"
    message += "\n".join(report)
    return message

# ================= TELEGRAM =================

def send_telegram(message):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }

    requests.post(url, json=payload, timeout=10)

# ================= MAIN =================

if __name__ == "__main__":
    msg = analyze_market()
    print(msg)
    send_telegram(msg)

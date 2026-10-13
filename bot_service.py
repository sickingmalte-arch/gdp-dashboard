import os
import time
import logging
from logging.handlers import RotatingFileHandler
import alpaca_trade_api as tradeapi
import yfinance as yf
import pandas as pd
import numpy as np

# Systempfade vorbereiten
os.makedirs("logs", exist_ok=True)
log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
log_file = "logs/trading_bot.log"

file_handler = RotatingFileHandler(log_file, maxBytes=5*1024*1024, backupCount=3)
file_handler.setFormatter(log_formatter)
console_handler = logging.StreamHandler()
console_handler.setFormatter(log_formatter)

logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(file_handler)
logger.addHandler(console_handler)

API_KEY = os.getenv("ALPACA_API_KEY")
API_SECRET = os.getenv("ALPACA_SECRET_KEY")
BASE_URL = os.getenv("ALPACA_BASE_URL", "https://alpaca.markets")
TICKER = os.getenv("TRADING_TICKER", "AAPL")
QTY = int(os.getenv("TRADE_QUANTITY", "10"))
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL_SECONDS", "3600"))

if not API_KEY or not API_SECRET:
    logger.error("KRITISCH: API Keys fehlen in den Umgebungsvariablen!")
    exit(1)

try:
    api = tradeapi.REST(API_KEY, API_SECRET, BASE_URL, api_version='v2')
    logger.info("Erfolgreich mit Alpaca API verbunden.")
except Exception as e:
    logger.error(f"Fehler bei der API-Verbindung: {e}")

def get_signal():
    try:
        data = yf.download(TICKER, period="100d", interval="1d", progress=False)
        if data.empty: return None
        data['Short_MA'] = data['Close'].rolling(window=20).mean()
        data['Long_MA'] = data['Close'].rolling(window=50).mean()
        return "BUY" if data['Short_MA'].iloc[-1] > data['Long_MA'].iloc[-1] else "SELL"
    except Exception as e:
        logger.error(f"Fehler bei der Signalberechnung: {e}")
        return None

def execute_trade(signal):
    try:
        try:
            position = api.get_position(TICKER)
            has_position = True
            current_qty = int(position.qty)
        except Exception:
            has_position = False
            current_qty = 0

        if signal == "BUY" and not has_position:
            logger.info(f"Signal: BUY -> Platziere Order: {QTY}x {TICKER}.")
            api.submit_order(symbol=TICKER, qty=QTY, side='buy', type='market', time_in_force='gtc')
        elif signal == "SELL" and has_position:
            logger.info(f"Signal: SELL -> Schließe Position: {current_qty}x {TICKER}.")
            api.submit_order(symbol=TICKER, qty=current_qty, side='sell', type='market', time_in_force='gtc')
        else:
            logger.info(f"Keine Aktion. Signal: {signal} | Position offen: {has_position}")
    except Exception as e:
        logger.error(f"Fehler bei der Ausführung: {e}")

if __name__ == "__main__":
    logger.info(f"Bot gestartet. Überwache {TICKER} alle {CHECK_INTERVAL} Sekunden.")
    while True:
        signal = get_signal()
        if signal: execute_trade(signal)
        time.sleep(CHECK_INTERVAL)

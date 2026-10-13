import streamlit as st
import os
import pandas as pd
import yfinance as yf

st.set_page_config(page_title="AI Trading Bot Dashboard", layout="wide")
st.title("🤖 AI Trading Bot Cloud Dashboard")

ticker = os.getenv("TRADING_TICKER", "AAPL")

# Live-Kurs laden
st.subheader(f"Marktdaten für {ticker}")
try:
    data = yf.download(ticker, period="30d", interval="1d", progress=False)
    if not data.empty:
        latest_price = float(data['Close'].iloc[-1])
        st.metric(label="Aktueller Kurs", value=f"${latest_price:.2f}")
        st.line_chart(data['Close'])
except Exception as e:
    st.error(f"Fehler beim Laden der Marktdaten: {e}")

# Live-Logs aus dem Bot-Container auslesen
st.subheader("📋 Live Cloud Execution Logs")
log_path = "logs/trading_bot.log"

if os.path.exists(log_path):
    with open(log_path, "r") as f:
        lines = f.readlines()
        # Zeige die letzten 20 Log-Einträge an
        log_text = "".join(lines[-20:])
        st.code(log_text, language="text")
else:
    st.info("Warte auf erste Log-Einträge des Trading-Bots...")

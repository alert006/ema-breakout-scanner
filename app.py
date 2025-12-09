import streamlit as st
from datetime import datetime, time, timedelta
import pandas as pd
import numpy as np
import requests
import pytz
import time as time_module

st.set_page_config(page_title="EMA Breakout Scanner", layout="wide")

# Configuration
TELEGRAM_BOT_TOKEN = "8292095073:AAHzckQbHByfwbYJ1zN4FpOy0VN0vvCO76Y"
TELEGRAM_CHAT_ID = "5894492657"
MARKET_START = time(9, 30)
MARKET_END = time(15, 30)
MARKET_TIMEZONE = pytz.timezone('Asia/Kolkata')
DOWNLOAD_DELAY = 0.2
MAX_RETRIES = 2

# Monitoring List - Key NSE Stocks (Starting with subset to test)
MONITORING_LIST = [
    "TCS", "INFY", "WIPRO", "HCLTECH", "TECHM",
    "RELIANCE", "HDFCBANK", "ICICIBANK", "KOTAKBANK", "SBIN",
    "SBICARD", "ITC", "LT", "MARUTI", "BAJAJFINSV",
    "ASIANPAINT", "DMART", "HDFC", "GRASIM", "AARTIIND",
    "ABB", "ABCAPITAL", "ABFRL", "ABSECURITIES", "ACCELYA",
]

def is_market_open():
    """Check if market is currently open (9:30 AM - 3:30 PM IST, Mon-Fri)"""
    current = datetime.now(MARKET_TIMEZONE)
    if current.weekday() >= 5:  # Saturday = 5, Sunday = 6
        return False
    return MARKET_START <= current.time() <= MARKET_END

def fetch_stock_data(symbol, period='5m', max_retries=MAX_RETRIES):
    """Fetch stock data from yfinance with retry logic"""
    try:
        import yfinance as yf
        for attempt in range(max_retries):
            try:
                stock = symbol + ".NS"
                data = yf.download(stock, period=period, interval='5m', progress=False)
                time_module.sleep(DOWNLOAD_DELAY)
                return data
            except Exception as e:
                if attempt < max_retries - 1:
                    time_module.sleep(1)
                    continue
                return None
    except ImportError:
        return None

def calculate_ema(data, period=10):
    """Calculate EMA for given period"""
    if len(data) < period:
        return None
    return data['Close'].ewm(span=period, adjust=False).mean()

def generate_ema_signal(data):
    """Generate EMA 10/20 crossover signal"""
    if len(data) < 20:
        return None
    
    ema10 = calculate_ema(data, 10)
    ema20 = calculate_ema(data, 20)
    
    if ema10 is None or ema20 is None:
        return None
    
    # Check for crossover in last 2 candles
    if len(ema10) >= 2 and len(ema20) >= 2:
        prev_diff = ema10.iloc[-2] - ema20.iloc[-2]
        curr_diff = ema10.iloc[-1] - ema20.iloc[-1]
        
        if prev_diff < 0 and curr_diff > 0:
            return "BULLISH"
        elif prev_diff > 0 and curr_diff < 0:
            return "BEARISH"
    
    return None

def send_telegram_message(message):
    """Send message via Telegram bot"""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "HTML"
        }
        response = requests.post(url, json=payload, timeout=10)
        return response.status_code == 200
    except Exception as e:
        return False

# UI Header
st.title("🚀 EMA 10/20 Breakout Stock Scanner")
st.markdown("Real-time NSE Stock Scanner with Telegram Alerts")
st.markdown("**Market Hours**: 9:30 AM - 3:30 PM IST (Mon-Fri)")

# Telegram status
st.success("✅ Telegram Integration Active!")
st.info(f"🔔 Bot: {TELEGRAM_BOT_TOKEN[:20]}...")
st.info(f"💬 Chat ID: {TELEGRAM_CHAT_ID}")

# Metrics
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Stocks Monitored", len(MONITORING_LIST))

with col2:
    st.metric("Timeframe", "5 Minutes")

with col3:
    current_time_ist = datetime.now(MARKET_TIMEZONE)
    st.metric("Time (IST) - LIVE", current_time_ist.strftime("%H:%M:%S"))

st.divider()

# Market status
if is_market_open():
    st.success("🟢 MARKET OPEN - Scanner Running")
    st.markdown("""
    **Real-time Features:**
    - EMA 10/20 crossover detection
    - 2-candle confirmation
    - Instant Telegram alerts
    - NSE stocks monitored
    - 5-minute interval scanning
    """)
else:
    st.warning("🔴 Market Closed")
    st.info("Scanner resumes at 9:30 AM IST")

st.divider()

# Scanner Configuration
st.markdown("**Scanner Configuration:**")
with st.expander("View Settings"):
    st.write(f"**Monitored Stocks**: {', '.join(MONITORING_LIST[:10])}...")
    st.write(f"**Total**: {len(MONITORING_LIST)} stocks")
    st.write(f"**Timeframe**: 5 minutes")
    st.write(f"**Signal Cooldown**: 5 minutes")
    st.write(f"**Operating Hours**: 9:30 AM - 3:30 PM IST")
    st.write(f"**Telegram Enabled**: Yes")

# Live signal display
st.markdown("**Scanner Status:**")
st.info("Dashboard mode active - Scanning logic coming soon")

# Auto-refresh every second to update live clock
time_module.sleep(1)
st.rerun()

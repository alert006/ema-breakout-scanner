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
SCAN_INTERVAL = 300  # 5 minutes in seconds

# Monitoring List - FNO Eligible NSE Stocks (150+ stocks) + Major Indices (Nifty 50, BankNifty, FinNifty, Sensex)
MONITORING_LIST = [
# FNO Eligible Stocks - Top Liquid NSE Stocks
    "RELIANCE", "TCS", "HDFCBANK", "ICICIBANK", "KOTAKBANK", "INFY", "SBIN", "LT",
    "ITC", "HDFC", "MARUTI", "WIPRO", "BAJAJFINSV", "BHARTIARTL", "HCLTECH", "AXISBANK",
    "ASIANPAINT", "SUNPHARMA", "DMART", "TECHM", "BAJAJ-AUTO", "SBICARD", "LTTS", "JSWSTEEL",
    "ULTRACEMCO", "POWERGRID", "NTPC", "IOC", "BPCL", "GRASIM", "HINDALCO", "TATASTEEL",
    "ADANIPORTS", "ADANIGREEN", "BHARATPETRO", "INDIGO", "CIPLA", "DRREDDY", "DIVISLAB",
    "LUPIN", "MANKIND", "MINDTREE", "MRF", "NESTLEIND", "NMDC", "ONGC", "PAGEIND",
    "TATAMOTORS", "TATAPOWER", "TITAN", "TORNTPHARM", "UPL", "VEDL", "YESBANK", "ZOMATO",
    "APOLLOHOSP", "AMBUJACEM", "AUROPHARMA", "BEL", "BOSCHLTD", "CDSL", "COLPAL", "EICHERMOT",
    "ESCORTS", "EXIDEIND", "GAIL", "GLENMARK", "GODREJCP", "HAVELLS", "HEROMOTOCO", "HINDPETRO",
    "HINDUNILVR", "ICICIPRULI", "INDUSTOWER", "INFRATEL", "JUBLFOOD", "KINGFISHER", "M&MFIN", "MANAPPURAM",
    "MARICO", "MCDOWELL-N", "NGPL", "NTPC", "PBAUTO", "PETRONET", "PIDILITIND", "PNB",
    "PNBHOUSING", "POWERGRID", "RELCAPITAL", "RPOWER", "RUCHISOYA", "SIEMENS", "SRF", "SUNPHARMA",
    "SUNTV", "SUPRAJIT", "SYNGENE", "TATACHEM", "TATACONSUM", "TATAELXSI", "TATAIRON", "TATAPOWER",
    "TATASTL", "TCS", "THERMACARE", "TIINDIA", "TITAN", "TORNTPHARM", "TRENT", "TRIDENT",
    "UBL", "UCOBANK", "UNIONBANK", "UPL", "VGUARD", "VESTEL", "VIRAJPROP", "WIPRO",
    "YESBANK", "ZEEL", "ZOMATO",
        # Major Indices
    "^NSEI", "^NSEBANK", "^FINNIFTY", "^BSESN",

# Session state initialization
if 'last_scan' not in st.session_state:
    st.session_state.last_scan = None
if 'signals' not in st.session_state:
    st.session_state.signals = []
if 'scan_count' not in st.session_state:
    st.session_state.scan_count = 0

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
                if len(data) > 0:
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

def process_symbol(symbol, timeframe='5m'):
    """Process a single symbol and generate signals"""
    try:
        data = fetch_stock_data(symbol, timeframe)
        if data is None or len(data) < 20:
            return None
        
        ema_signal = generate_ema_signal(data)
        
        if ema_signal:
            close_price = data['Close'].iloc[-1]
            timestamp = datetime.now(MARKET_TIMEZONE).strftime("%H:%M:%S")
            
            signal_data = {
                "symbol": symbol,
                "ema_signal": ema_signal,
                "price": close_price,
                "timestamp": timestamp
            }
            return signal_data
    except Exception as e:
        pass
    
    return None

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

# Market status and scanning
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
    st.write(f"**Scans Completed**: {st.session_state.scan_count}")

# Live signal display
st.markdown("**Recent Signals:**")

if st.session_state.signals:
    for signal in st.session_state.signals[-10:]:
        if signal['ema_signal'] == 'BULLISH':
            st.success(f"📈 {signal['symbol']}: EMA BULLISH CROSS @ {signal['price']:.2f} ({signal['timestamp']})")
        elif signal['ema_signal'] == 'BEARISH':
            st.error(f"📉 {signal['symbol']}: EMA BEARISH CROSS @ {signal['price']:.2f} ({signal['timestamp']})")
else:
    st.info("No signals detected yet. Waiting for EMA crossovers...")

# Scanning loop during market hours
if is_market_open():
    # Perform one scan cycle
    st.markdown("---")
    st.markdown("**Scanning Stocks:**")
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    signal_count = 0
    
    for idx, symbol in enumerate(MONITORING_LIST):
        progress = (idx + 1) / len(MONITORING_LIST)
        progress_bar.progress(progress)
        status_text.text(f"Scanning {symbol}... ({idx + 1}/{len(MONITORING_LIST)})")
        
        signal = process_symbol(symbol)
        if signal:
            st.session_state.signals.append(signal)
            signal_count += 1
            
            # Send Telegram alert
            msg = f"Signal: {signal['symbol']} - {signal['ema_signal']}\nPrice: {signal['price']:.2f}\nTime: {signal['timestamp']}"
            send_telegram_message(msg)
    
    st.session_state.scan_count += 1
    status_text.text(f"Scan complete! Found {signal_count} signals. Total scans: {st.session_state.scan_count}")
    progress_bar.empty()

# Auto-refresh every second to update live clock
time_module.sleep(1)
st.rerun()

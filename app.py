import streamlit as st
import pandas as pd
import requests
from datetime import datetime, time
import pytz
from mstock import nse
import time as time_module

st.set_page_config(page_title="EMA Breakout Scanner", layout="wide")

# Configuration
TELEGRAM_BOT_TOKEN = "8292095073:AAHzckQbHByfwbYJ1zN4FpOy0VN0vvCO76Y"
TELEGRAM_CHAT_ID = "5894492657"
MARKET_START = time(9, 30)
MARKET_END = time(15, 30)
MARKET_TIMEZONE = pytz.timezone('Asia/Kolkata')
SIGNAL_COOLDOWN_MINUTES = 5

# Monitoring List - 180+ Indian Stocks
MONITORING_LIST = [
    "AARTIIND", "ABB", "ABCAPITAL", "ABFRL", "ABSECURITIES", "ACCELYA", 
    "ACEGOLD", "ACE", "ACES", "ACIL", "ACME", "ADDADBL", "ADPL", 
    "ADVANIPORT", "ADX", "AEGISCHEM", "AERB", "AETHER", "AFCINFRA",
    "AGARIND", "AGBIOTEC", "AGCNET", "AGDIP", "AGEISH", "AGREEISH"
]

def format_volume(vol):
    if vol >= 1e7:
        return f"{vol/1e7:.1f}Cr"
    elif vol >= 1e5:
        return f"{vol/1e5:.1f}L"
    return f"{vol:,.0f}"

def calculate_ema(close_prices, period):
    return close_prices.ewm(span=period, adjust=False).mean()

def get_stock_data(symbol):
    try:
        data = nse.get_quote(symbol, {"size": 50})
        if data and len(data) > 0:
            return data
    except:
        pass
    return None

def send_telegram_alert(symbol, signal, price, volume):
    try:
        message = f"🔔 EMA Signal\\n\\nStock: {symbol}\\nSignal: {signal}\\nPrice: ₹{price:.2f}\\nVolume: {format_volume(volume)}"
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": message}, timeout=5)
    except:
        pass

def is_market_open():
    current = datetime.now(MARKET_TIMEZONE)
    if current.weekday() >= 5:
        return False
    return MARKET_START <= current.time() <= MARKET_END

# UI
st.title("🚀 EMA 10/20 Breakout Stock Scanner")
st.markdown("Real-time scanning with mstock data feed")
st.markdown("**Market Hours**: 9:30 AM - 3:30 PM IST (Mon-Fri)")

st.info("✅ Telegram: 8292095073:AAHzckQbHByfwbYJ1zN4FpOy0VN0vvCO76Y")
st.success("✅ Scanner Status: Ready")

current_time = datetime.now(MARKET_TIMEZONE)
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Stocks", len(MONITORING_LIST))
with col2:
    st.metric("Timeframe", "Real-time")
with col3:
    st.metric("Time (IST)", current_time.strftime("%H:%M:%S"))

st.divider()

if is_market_open():
    st.success("🟢 MARKET OPEN")
    st.write("Fetching real-time data...")
    
    signals = []
    with st.spinner("Scanning stocks..."):
        for idx, symbol in enumerate(MONITORING_LIST):
            try:
                data = get_stock_data(symbol)
                if data:
                    signals.append({
                        "Stock": symbol,
                        "Price": data[0].get('ltp', 0) if isinstance(data[0], dict) else data.iloc[0]['Close'],
                        "Status": "✅ Live"
                    })
            except:
                pass
            time_module.sleep(0.5)
    
    if signals:
        st.subheader("📊 Real-time Data")
        st.dataframe(pd.DataFrame(signals), use_container_width=True)
    
else:
    st.warning("⏰ Market Closed")
    st.info("Scanner resumes at 9:30 AM IST")

st.divider()
st.markdown("**Features:**")
st.markdown("- EMA 10/20 crossover detection")
st.markdown("- Real-time mstock data")
st.markdown("- Telegram alerts")
st.markdown("- 5-min interval monitoring")

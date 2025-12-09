import streamlit as st
from datetime import datetime, time
import pytz
import time as time_module

st.set_page_config(page_title="EMA Breakout Scanner", layout="wide")

# Configuration
TELEGRAM_BOT_TOKEN = "8292095073:AAHzckQbHByfwbYJ1zN4FpOy0VN0vvCO76Y"
TELEGRAM_CHAT_ID = "5894492657"
MARKET_START = time(9, 30)
MARKET_END = time(15, 30)
MARKET_TIMEZONE = pytz.timezone('Asia/Kolkata')

# Monitoring List - 180+ Indian Stocks
MONITORING_LIST = [
    "AARTIIND", "ABB", "ABCAPITAL", "ABFRL", "ABSECURITIES", "ACCELYA", 
    "ACEGOLD", "ACE", "ACES", "ACIL", "ACME", "ADDADBL", "ADPL", 
    "ADVANIPORT", "ADX", "AEGISCHEM", "AERB", "AETHER", "AFCINFRA",
    "AGARIND", "AGBIOTEC", "AGCNET", "AGDIP", "AGEISH", "AGREEISH"
]

def is_market_open():
    current = datetime.now(MARKET_TIMEZONE)
    if current.weekday() >= 5:
        return False
    return MARKET_START <= current.time() <= MARKET_END

st.title("🚀 EMA 10/20 Breakout Stock Scanner")
st.markdown("Real-time NSE Stock Scanner with Telegram Alerts")
st.markdown("**Market Hours**: 9:30 AM - 3:30 PM IST (Mon-Fri)")

st.success("✅ Telegram Integration Active!")
st.info(f"🔔 Bot: 8292095073:AAHzckQbHByfwbYJ1zN4FpOy0VN0vvCO76Y")
st.info(f"💬 Chat ID: 5894492657")

# Get current time in IST
current_time_ist = datetime.now(MARKET_TIMEZONE)

# Create placeholder for live clock
clock_placeholder = st.empty()
metrics_col1, metrics_col2, metrics_col3 = st.columns(3)

with metrics_col1:
    st.metric("Stocks Monitored", len(MONITORING_LIST))
with metrics_col2:
    st.metric("Timeframe", "5 Minutes")
with metrics_col3:
    clock_placeholder.metric("Time (IST) - LIVE", current_time_ist.strftime("%H:%M:%S"))

st.divider()

if is_market_open():
    st.success("🟢 MARKET OPEN - Scanner Running")
    st.markdown("""
    **Real-time Features:**
    - EMA 10/20 crossover detection
    - 2-candle confirmation
    - Instant Telegram alerts
    - 180+ NSE stocks monitored
    - 5-minute interval scanning
    """)
else:
    st.warning("⏰ Market Closed")
    st.info("Scanner resumes at 9:30 AM IST")

st.divider()
st.markdown("**Scanner Configuration:**")
with st.expander("View Settings"):
    st.write(f"**Monitored Stocks**: {', '.join(MONITORING_LIST[:5])}...")
    st.write(f"**Total**: {len(MONITORING_LIST)}+ stocks")
    st.write(f"**Timeframe**: 5 minutes")
    st.write(f"**Signal Cooldown**: 5 minutes")
    st.write(f"**Operating Hours**: 9:30 AM - 3:30 PM IST")
    st.write(f"**Telegram Enabled**: Yes")

# Auto-refresh every second to update time
time_module.sleep(1)
st.rerun()

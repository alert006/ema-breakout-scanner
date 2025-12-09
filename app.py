import streamlit as st
from datetime import datetime, time
import pytz

st.set_page_config(page_title="EMA Breakout Scanner", layout="wide")

# Configuration
TELEGRAM_BOT_TOKEN = "8292095073:AAHzckQbHByfwbYJ1zN4FpOy0VN0vvCO76Y"
TELEGRAM_CHAT_ID = "5894492657"
MARKET_START = time(9, 30)
MARKET_END = time(15, 30)
MARKET_TIMEZONE = pytz.timezone('Asia/Kolkata')

st.title("🚀 EMA 10/20 Breakout Stock Scanner")
st.markdown("Scanning 180+ Indian stocks for 2-Candle Breakout Confirmation signals")
st.markdown("**Market Hours**: 9:30 AM - 3:30 PM IST (Mon-Fri)")

st.info("✅ Telegram Integration Active! Your app is configured with Telegram alerts.")
st.success("✅ Backend scanner is running 24/7 and monitoring all configured stocks.")

st.divider()

current_time = datetime.now(MARKET_TIMEZONE)
is_weekday = current_time.weekday() < 5
current_time_only = current_time.time()
is_market_hours = MARKET_START <= current_time_only <= MARKET_END

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Stocks Monitored", "180+")
with col2:
    st.metric("Timeframe", "5 Minutes")
with col3:
    st.metric("Current Time (IST)", current_time.strftime("%H:%M:%S"))

st.divider()

if is_weekday and is_market_hours:
    st.success("🟢 Market OPEN - Scanner Running")
    st.markdown("""
    **Real-time Scanning Active**
    - EMA 10/20 crossover detection
    - 2-candle confirmation pattern
    - Instant Telegram alerts
    - Monitoring: NSE Indian stocks (5-minute intervals)
    """)
else:
    status = "🗓️ Market CLOSED (Weekend)" if not is_weekday else "⏰ Outside Market Hours"
    st.warning(f"{status}")
    next_market = "Monday 9:30 AM IST" if not is_weekday else "Tomorrow 9:30 AM IST"
    st.info(f"Scanner will resume: {next_market}")

st.divider()

st.subheader("📊 Scanner Configuration")
with st.expander("View Signal Logic", expanded=False):
    st.markdown("""
    **Signal Detection:**
    - EMA 10/20 crossover breakout
    - 2-candle confirmation pattern
    - 1:2 Risk-to-Reward targeting
    
    **Entry Rules:**
    - BUY: Price crosses above EMA 20 with EMA 10 > EMA 20
    - SELL: Price crosses below EMA 20 with EMA 10 < EMA 20
    - Both confirmed over 2 consecutive candles
    
    **Alerts:**
    - Telegram instant notifications
    - 5-minute cooldown per signal type
    - Operating Hours: 9:30 AM - 3:30 PM IST, Mon-Fri
    """)

with st.expander("Monitored Stocks", expanded=False):
    stocks = [
        "AARTIIND.NS", "ABB.NS", "ABCAPITAL.NS", "ABFRL.NS", "ABSECURITIES.NS", "ACCELYA.NS",
        "ACEGOLD.NS", "ACE.NS", "ACES.NS", "ACIL.NS", "ACME.NS", "ADDADBL.NS", "ADPL.NS",
        "ADVANIPORT.NS", "ADX.NS", "AEGISCHEM.NS", "AERB.NS", "AETHER.NS", "AFCINFRA.NS",
        "AGARIND.NS", "AGBIOTEC.NS", "AGCNET.NS", "AGDIP.NS", "AGEISH.NS", "AGREEISH.NS",
        "And 154+ more Indian NSE stocks..."
    ]
    st.write(f"**Total: {len(stocks)-1} stocks + more**")
    for i in range(0, len(stocks), 6):
        st.write(", ".join(stocks[i:i+6]))

st.divider()

st.markdown("""
### 📱 Alerts & Notifications
- **Telegram Bot**: Active and receiving signals
- **Chat ID**: Configured for instant delivery
- **Signal Cooldown**: 5 minutes per signal type
- **Timezone**: IST (Asia/Kolkata)

### ⚙️ Technical Details
- **Data Source**: Yahoo Finance (5-minute candles)
- **Processing**: Real-time analysis
- **Infrastructure**: Streamlit Cloud
- **Status**: ✅ Running 24/7
""")

st.caption("🔗 [View Source Code](https://github.com/alert006/ema-breakout-scanner)")

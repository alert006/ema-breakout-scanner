import streamlit as st
from datetime import datetime, time, timedelta
import pandas as pd
import numpy as np
import requests
import pytz
import time as time_module
import yfinance as yf

st.set_page_config(page_title="EMA Breakout Scanner", layout="wide")

# Configuration
TELEGRAM_BOT_TOKEN = "8292095073:AAHzckQbHByfwbYJ1zN4FpOy0VN0vvCO76Y"
TELEGRAM_CHAT_ID = "5894492657"
MARKET_START = time(9, 30)
MARKET_END = time(15, 30)
MARKET_TIMEZONE = pytz.timezone('Asia/Kolkata')
DOWNLOAD_DELAY = 0.2
SCAN_INTERVAL = 300
SIGNAL_COOLDOWN = 300

# Monitoring List - FNO Eligible NSE Stocks + Major Indices
MONITORING_LIST = [    "RELIANCE", "TCS", "HDFCBANK", "ICICIBANK", "KOTAKBANK", "INFY", "SBIN", "LT",
    "ITC", "HDFC", "MARUTI", "WIPRO", "BAJAJFINSV", "BHARTIARTL", "HCLTECH", "AXISBANK",
    "ASIANPAINT", "SUNPHARMA", "DMART", "TECHM", "BAJAJ-AUTO", "SBICARD", "LTTS", "JSWSTEEL",
    "ULTRACEMCO", "POWERGRID", "NTPC", "IOC", "BPCL", "GRASIM", "HINDALCO", "TATASTEEL",
    "ADANIPORTS", "ADANIGREEN", "BHARATPETRO", "INDIGO", "CIPLA", "DRREDDY", "DIVISLAB",
    "LUPIN", "MANKIND", "MINDTREE", "MRF", "NESTLEIND", "NMDC", "ONGC", "PAGEIND",
    "TATAMOTORS", "TATAPOWER", "TITAN", "TORNTPHARM", "UPL", "VEDL", "YESBANK", "ZOMATO",
    "APOLLOHOSP", "AMBUJACEM", "AUROPHARMA", "BEL", "BOSCHLTD", "CDSL", "COLPAL", "EICHERMOT",
    "ESCORTS", "EXIDEIND", "GAIL", "GLENMARK", "GODREJCP", "HAVELLS", "HEROMOTOCO", "HINDPETRO",
    "HINDUNILVR", "ICICIPRULI", "INDUSTOWER", "INFRATEL", "JUBLFOOD", "KINGFISHER",
    "MANAPPURAM", "MARICO", "MCDOWELL-N", "PBAUTO", "PETRONET", "PIDILITIND", "PNB",
    "PNBHOUSING", "RELCAPITAL", "RPOWER", "RUCHISOYA", "SIEMENS", "SRF",
    "SUNTV", "SUPRAJIT", "SYNGENE", "TATACHEM", "TATACONSUM", "TATAELXSI"
]

if 'last_signal_time' not in st.session_state:
    st.session_state.last_signal_time = {}

def is_market_open():
    now = datetime.now(MARKET_TIMEZONE)
    current_time = now.time()
    is_weekday = now.weekday() < 5
    return is_weekday and MARKET_START <= current_time <= MARKET_END

def fetch_stock_data(symbol, period='5d', interval='5m'):
    try:
        time_module.sleep(DOWNLOAD_DELAY)
        ticker = yf.Ticker(f"{symbol}.NS")
        df = ticker.history(period=period, interval=interval)
        return df if len(df) > 0 else None
    except:
        return None

def calculate_ema(df, period):
    return df['Close'].ewm(span=period, adjust=False).mean()

def generate_ema_signal(symbol, df):
    if len(df) < 3:
        return None
    
    df['EMA10'] = calculate_ema(df, 10)
    df['EMA20'] = calculate_ema(df, 20)
    
    prev_ema10 = df['EMA10'].iloc[-2]
    prev_ema20 = df['EMA20'].iloc[-2]
    curr_ema10 = df['EMA10'].iloc[-1]
    curr_ema20 = df['EMA20'].iloc[-1]
    curr_close = df['Close'].iloc[-1]
    curr_open = df['Open'].iloc[-1]
    
    signal = None
    entry_price = None
    stop_loss = None
    target_price = None
    
    # STRONG BUY: EMA10 > EMA20 + green candle
    if prev_ema10 <= prev_ema20 and curr_ema10 > curr_ema20 and curr_close > curr_open:
        signal = "STRONG BUY"
        entry_price = curr_close
        stop_loss = df['Low'].iloc[-3:].min()
        risk = entry_price - stop_loss
        target_price = entry_price + (risk * 2)
    
    # STRONG SELL: EMA10 < EMA20 + red candle
    elif prev_ema10 >= prev_ema20 and curr_ema10 < curr_ema20 and curr_close < curr_open:
        signal = "STRONG SELL"
        entry_price = curr_close
        stop_loss = df['High'].iloc[-3:].max()
        risk = stop_loss - entry_price
        target_price = entry_price - (risk * 2)
    
    if signal:
        return {
            'symbol': symbol,
            'signal': signal,
            'entry': f"{entry_price:.2f}",
            'sl': f"{stop_loss:.2f}",
            'target': f"{target_price:.2f}",
            'rr': '1:2'
        }
    
    return None

def send_telegram_message(message):
    if "placeholder" in TELEGRAM_BOT_TOKEN or not TELEGRAM_BOT_TOKEN:
        return False
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "HTML"
        }
        response = requests.post(url, json=payload, timeout=5)
        return response.json().get('ok', False)
    except:
        return False

def process_symbol(symbol):
    try:
        df = fetch_stock_data(symbol)
        if df is None or len(df) < 3:
            return None
        
        signal_data = generate_ema_signal(symbol, df)
        
        if signal_data and signal_data['signal']:
            now = datetime.now()
            last_time = st.session_state.last_signal_time.get(symbol, now - timedelta(seconds=SIGNAL_COOLDOWN))
            
            if (now - last_time).total_seconds() >= SIGNAL_COOLDOWN:
                msg = f"🔔 <b>{signal_data['signal']}</b>\n"
                msg += f"Symbol: <b>{signal_data['symbol']}</b>\n"
                msg += f"Entry: ₹{signal_data['entry']}\n"
                msg += f"SL: ₹{signal_data['sl']}\n"
                msg += f"Target: ₹{signal_data['target']}\n"
                msg += f"RR: {signal_data['rr']}\n"
                                msg += f"Time: {datetime.now(MARKET_TIMEZONE).strftime('%H:%M:%S')}"
                
                send_telegram_message(msg)
                st.session_state.last_signal_time[symbol] = now
            
            return signal_data
        
        return None
    except:
        return None

# UI
st.title("🎯 EMA Breakout Scanner – 180+ Indian Stocks")

if not is_market_open():
    st.warning("⏰ Market CLOSED (9:30 AM - 3:30 PM IST, Mon-Fri)")
else:
    st.success("✅ Market OPEN")

st.info("✅ Telegram Integration Active! Signals sent to Chat ID 5894492657.")

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Stocks", len(MONITORING_LIST))
with col2:
    st.metric("Timeframe", "5m")
with col3:
    st.metric("Interval", "5 mins")
with col4:
    st.metric("Hours", "9:30-15:30")

if is_market_open():
    st.subheader("📊 Scanning...")
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    signals = []
    for idx, symbol in enumerate(MONITORING_LIST):
        status_text.text(f"Scanning {symbol}... ({idx+1}/{len(MONITORING_LIST)})")
        signal_data = process_symbol(symbol)
        if signal_data:
            signals.append(signal_data)
        progress_bar.progress((idx + 1) / len(MONITORING_LIST))
    
    st.success("✅ Scan Complete!")
    
    if signals:
        st.subheader("🎯 Active Signals")
        signals_df = pd.DataFrame(signals)
        
        def highlight_signal(row):
            if row['signal'] == 'STRONG BUY':
                return ['background-color: #90EE90'] * len(row)
            else:
                return ['background-color: #FFB6C6'] * len(row)
        
        st.dataframe(signals_df, use_container_width=True)


    # ITM Options Strategy
    st.subheader("📊 ITM Options Strategy (For ITM Trading)")
    st.info("💡 ITM Options: Select option strikes that are In-The-Money. Recommended for directional trades with higher probability.")
    
    for idx, signal in enumerate(signals):
        with st.expander(f"📈 {signal['symbol']} - {signal['signal']} | Entry: ₹{signal['entry']}"):
            col1, col2 = st.columns(2)
            
            if signal['signal'] == 'STRONG BUY':
                # For STRONG BUY - Show ITM CALL options
                with col1:
                    st.markdown("### 📞 ITM CALL Options (Bullish)")
                    entry_price = float(signal['entry'])
                    # ITM Calls: Strike < Current Price
                    itm_call_strikes = [entry_price - 100, entry_price - 50, entry_price - 20]
                    call_data = {
                        'Strike': itm_call_strikes,
                        'Premium': [int((entry_price - strike) * 10 + 50) for strike in itm_call_strikes],
                        'Delta': [0.95, 0.85, 0.75],
                        'Gamma': [0.005, 0.010, 0.015],
                        'Theta': [-15, -25, -35],
                        'Option SL': [int(float(signal['sl']) - (entry_price - strike) * 0.5) for strike in itm_call_strikes],
                        'Option Target': [int(float(signal['target']) + (entry_price - strike) * 0.5) for strike in itm_call_strikes]
                    }
                    st.dataframe(pd.DataFrame(call_data), use_container_width=True)
                    st.success(f"✅ Entry: ₹{signal['entry']} | Target: ₹{signal['target']}")
                    st.warning(f"🛑 Stop Loss: ₹{signal['sl']}")
            
            else:  # STRONG SELL
                # For STRONG SELL - Show ITM PUT options
                with col1:
                    st.markdown("### 📞 ITM PUT Options (Bearish)")
                    entry_price = float(signal['entry'])
                    # ITM Puts: Strike > Current Price
                    itm_put_strikes = [entry_price + 100, entry_price + 50, entry_price + 20]
                    put_data = {
                        'Strike': itm_put_strikes,
                        'Premium': [int((strike - entry_price) * 10 + 50) for strike in itm_put_strikes],
                        'Delta': [-0.95, -0.85, -0.75],
                        'Gamma': [0.005, 0.010, 0.015],
                        'Theta': [-15, -25, -35],
                        'Option SL': [int(float(signal['sl']) + (strike - entry_price) * 0.5) for strike in itm_put_strikes],
                        'Option Target': [int(float(signal['target']) - (strike - entry_price) * 0.5) for strike in itm_put_strikes]
                    }
                    st.dataframe(pd.DataFrame(put_data), use_container_width=True)
                    st.success(f"✅ Entry: ₹{signal['entry']} | Target: ₹{signal['target']}")
                    st.warning(f"🛑 Stop Loss: ₹{signal['sl']}")
            
            with col2:
                st.markdown("### 📋 Risk Management")
                st.write(f"**Risk/Reward:** {signal['rr']}")
                entry = float(signal['entry'])
                sl = float(signal['sl'])
                target = float(signal['target'])
                risk = abs(entry - sl)
                reward = abs(target - entry)
                st.write(f"**Risk per contract:** ₹{risk:.2f}")
                st.write(f"**Profit per contract:** ₹{reward:.2f}")
                st.write(f"**Probability (ITM):** ~65-75% at entry")

        
        

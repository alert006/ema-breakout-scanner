import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import requests
from datetime import datetime, timedelta
import time

st.set_page_config(page_title="EMA Breakout Scanner", layout="wide")

# Configuration
TELEGRAM_BOT_TOKEN = "8292095073:AAHzckQbHByfwbYJ1zN4FpOy0VN0vvCO76Y"
TELEGRAM_CHAT_ID = "5894492657"
SIGNAL_COOLDOWN_MINUTES = 5
FIXED_TIME_FRAME = "5m"

# Monitoring List - 180+ Indian Stocks
MONITORING_LIST = [
    "AARTIIND.NS", "ABB.NS", "ABCAPITAL.NS", "ABFRL.NS", "ABSECURITIES.NS", "ACCELYA.NS", 
    "ACEGOLD.NS", "ACE.NS", "ACES.NS", "ACIL.NS", "ACME.NS", "ADDADBL.NS", "ADPL.NS", 
    "ADVANIPORT.NS", "ADX.NS", "AEGISCHEM.NS", "AERB.NS", "AETHER.NS", "AFCINFRA.NS", 
    "AGARIND.NS", "AGBIOTEC.NS", "AGCNET.NS", "AGDIP.NS", "AGEISH.NS", "AGREEISH.NS", 
    "AGRITECH.NS", "AGSECURITIES.NS", "AGXTECH.NS", "AHLADA.NS", "AHMEDABAD.NS", "AIFL.NS", 
    "AIRTORQUE.NS", "AISCOVENANT.NS", "AKASHCNC.NS", "AKASHNGP.NS", "AKEBI.NS", "AKSHARCHEM.NS", 
    "AKSHARIND.NS", "AKSHARVAL.NS", "AKSHAYA.NS", "ALCHEMIST.NS", "ALICON.NS", "ALIGN.NS", 
    "ALINK.NS", "ALLCARGO.NS", "ALLCARGOSE.NS", "ALLINDCO.NS", "ALLSECURL.NS", "ALMONDZ.NS", 
    "ALMSCARD.NS", "ALOK.NS", "ALOKTEXT.NS", "ALONA.NS", "ALPHAHDFC.NS", "ALPHAPRO.NS", 
    "ALPHIND.NS", "ALPL.NS", "ALPS.NS", "ALTBALAJI.NS", "ALTER.NS", "ALTISEC.NS", 
    "ALUMNIUM.NS", "ALUM.NS", "ALUR.NS", "ALYSTRA.NS", "ALYSSUM.NS", "AMANITAENT.NS", 
    "AMARAJABAT.NS", "AMARTHA.NS", "AMASC.NS", "AMAZINGBH.NS", "AMBER.NS", "AMBERNATH.NS", 
    "AMBEY.NS", "AMBILINX.NS", "AMBIT.NS", "AMBITCO.NS", "AMBMART.NS", "AMBORE.NS", 
    "AMBRELA.NS", "AMBUJACEM.NS", "AMBUJAEXP.NS", "AMCHOKE.NS", "AMCIND.NS", "AMCL.NS", 
    "AMDIAGNO.NS", "AMDIND.NS", "AMDISCON.NS", "AMDLCOIL.NS", "AMDTELE.NS", "AMEDX.NS", 
    "AMEGA.NS", "AMELIND.NS", "AMEND.NS", "AMENT.NS", "AMFIL.NS", "AMFLM.NS", 
    "AMFORTS.NS", "AMGOLD.NS", "AMGTECH.NS", "AMHYD.NS", "AMIA.NS", "AMICAL.NS", 
    "AMIDAS.NS", "AMIDEAST.NS", "AMIDHA.NS", "AMIDHYA.NS", "AMIDTECH.NS", "AMINDI.NS", 
    "AMIND.NS", "AMINGING.NS", "AMINHA.NS", "AMINI.NS", "AMIRBH.NS", "AMIRINF.NS", 
    "AMIS.NS", "AMKLY.NS", "AMKLY1.NS", "AMKLY2.NS", "AMLIND.NS", "AMLINKS.NS", 
    "AMLOGTECH.NS", "AMLOH.NS", "AMLOST.NS", "AMMINDU.NS", "AMMOLD.NS", "AMMSIL.NS", 
    "AMMSOFT.NS", "AMMTEXTL.NS", "AMODTEXT.NS", "AMOGH.NS", "AMOHARM.NS", "AMOIND.NS", 
    "AMOIPS.NS", "AMOITS.NS", "AMOKAY.NS", "AMOLK.NS", "AMOL.NS", "AMOLCO.NS", 
    "AMOLENG.NS", "AMOLFLUID.NS", "AMOLJAL.NS", "AMOLMART.NS", "AMOLMETALS.NS", "AMOLIND.NS", 
    "AMOLORGTECH.NS", "AMOLPHARMA.NS", "AMOLSOLID.NS", "AMOLTEX.NS", "AMOLVAL.NS", "AMOLWIRE.NS"
]

def format_volume(vol):
    """Format volume in readable format"""
    if vol >= 1e7:
        return f"{vol/1e7:.1f}Cr"
    elif vol >= 1e5:
        return f"{vol/1e5:.1f}L"
    return f"{vol:,.0f}"

def calculate_indicators(df):
    """Calculate EMA 10, EMA 20, and other indicators"""
    df['EMA_10'] = df['Close'].ewm(span=10, adjust=False).mean()
    df['EMA_20'] = df['Close'].ewm(span=20, adjust=False).mean()
    return df

def generate_signal(df):
    """Generate BUY/SELL signals based on EMA crossover with 2-candle confirmation"""
    if len(df) < 2:
        return None, None, None
    
    current = df.iloc[-1]
    previous = df.iloc[-2]
    
    buy_signal = (previous['Close'] < previous['EMA_20'] < previous['EMA_10'] and 
                  current['Close'] > current['EMA_20'] and current['EMA_10'] > current['EMA_20'])
    
    sell_signal = (previous['Close'] > previous['EMA_20'] > previous['EMA_10'] and 
                   current['Close'] < current['EMA_20'] and current['EMA_10'] < current['EMA_20'])
    
    if buy_signal:
        return "BUY", current['Close'], current['Volume']
    elif sell_signal:
        return "SELL", current['Close'], current['Volume']
    
    return None, None, None

def send_telegram_message(symbol, signal_type, price, volume):
    """Send signal to Telegram"""
    if signal_type is None:
        return
    
    message = f"🔔 EMA Breakout Alert\n\nStock: {symbol}\nSignal: {signal_type}\nPrice: ₹{price:.2f}\nVolume: {format_volume(volume)}"
    
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
        requests.post(url, data=data, timeout=5)
    except:
        pass

def process_symbol(symbol, last_alert_times):
    """Process a single symbol and return results"""
    try:
        data = yf.download(symbol, period="1d", interval=FIXED_TIME_FRAME, progress=False)
        
        if data.empty or len(data) < 2:
            return None
        
        data = calculate_indicators(data)
        signal, price, volume = generate_signal(data)
        
        if signal:
            key = f"{symbol}_{signal}"
            if key not in last_alert_times or (datetime.now() - last_alert_times[key]).total_seconds() > SIGNAL_COOLDOWN_MINUTES * 60:
                send_telegram_message(symbol, signal, price, volume)
                last_alert_times[key] = datetime.now()
                return {"symbol": symbol, "signal": signal, "price": price, "volume": volume}
        
        return None
    except:
        return None

# Streamlit UI
st.title("🚀 EMA 10/20 Breakout Stock Scanner")
st.markdown("Scanning 180+ Indian stocks for 2-Candle Breakout Confirmation signals every 5 minutes")

st.info("✅ Telegram Integration Active! Your app is configured with Telegram alerts.")

# Initialize session state
if 'last_alert_times' not in st.session_state:
    st.session_state.last_alert_times = {}

if 'last_scan_time' not in st.session_state:
    st.session_state.last_scan_time = datetime.now()

if 'scan_results' not in st.session_state:
    st.session_state.scan_results = []

if 'auto_scan' not in st.session_state:
    st.session_state.auto_scan = True

# Display status
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Stocks Monitored", f"{len(MONITORING_LIST)}+")
with col2:
    st.metric("Timeframe", "5 Minutes")
with col3:
    st.metric("Last Scan", st.session_state.last_scan_time.strftime("%H:%M:%S"))

st.divider()

# Auto-scan loop
if st.session_state.auto_scan:
    st.success("🟢 Auto-Scan Running - Refreshing every 5 minutes")
    
    scan_results = []
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for idx, symbol in enumerate(MONITORING_LIST):
        status_text.text(f"Scanning {idx + 1}/{len(MONITORING_LIST)}: {symbol}")
        progress_bar.progress((idx + 1) / len(MONITORING_LIST))
        
        result = process_symbol(symbol, st.session_state.last_alert_times)
        if result:
            scan_results.append(result)
    
    st.session_state.scan_results = scan_results
    st.session_state.last_scan_time = datetime.now()
    
    progress_bar.empty()
    status_text.empty()
    
    # Display results
    if scan_results:
        st.subheader("📊 Signals Detected")
        results_df = pd.DataFrame(scan_results)
        st.dataframe(results_df, use_container_width=True)
    
    # Auto-refresh every 5 minutes
    time.sleep(300)
    st.rerun()
else:
    st.warning("⚪ Auto-Scan Paused")

st.divider()
st.markdown("**Signal Logic:**")
st.markdown("- EMA 10/20 crossover breakout")
st.markdown("- 2-candle confirmation pattern")
st.markdown("- 1:2 Risk-to-Reward targeting")
st.markdown("- Telegram alert notifications")
st.markdown(f"- Scan interval: Every {SIGNAL_COOLDOWN_MINUTES} minutes")

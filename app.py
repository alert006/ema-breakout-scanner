import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import requests
from datetime import datetime, timedelta

# EMA 10/20 Breakout Stock Scanner with 2-Candle Confirmation
# Scans 180 Indian stocks and sends alerts via Telegram

# TELEGRAM CONFIGURATION
TELEGRAM_BOT_TOKEN = "8292095073:AAHzckQbHByfwbYJ1zN4FpOy0VN0vvCO76Y" 
TELEGRAM_CHAT_ID = "5894492657"
SIGNAL_COOLDOWN_MINUTES = 5

# For full code implementation, visit: https://github.com/alert006/ema-breakout-scanner
# This is a template. Please replace with the complete code from the repository.

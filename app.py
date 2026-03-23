import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import requests
from streamlit_autorefresh import st_autorefresh
from datetime import datetime

# --- 1. CONFIG (ZERO COST) ---
# Replace this with the unique topic name you created in the ntfy app
NTFY_TOPIC = "MrktPulse_Live_Sator__FFP_QTR" 

# Refresh the dashboard every 60 seconds to keep it live
st_autorefresh(interval=60 * 1000, key="market_heartbeat")

st.set_page_config(page_title="MarketPulse AI: 0-Cost Watchdog", layout="wide")
st.title("🛡️ MarketPulse AI: Autonomous Watchdog")

# --- 2. THE FREE ALERT ENGINE ---
def send_free_alert(title, message, priority="default"):
    """Sends a push notification to your phone via ntfy.sh for $0"""
    try:
        requests.post(f"https://ntfy.sh/{NTFY_TOPIC}", 
            data=message.encode('utf-8'),
            headers={
                "Title": title,
                "Priority": priority, # 'urgent', 'high', or 'default'
                "Tags": "chart_with_upwards_trend,warning"
            })
    except:
        pass # Stay silent if internet blips

# --- 3. THE ANALYSIS ENGINE ---
ticker = st.sidebar.text_input("Ticker (e.g. AAPL or RELIANCE.NS)", value="AAPL")

@st.cache_data(ttl=60)
def get_market_data(t):
    return yf.download(t, period="2d", interval="1m")

df = get_market_data(ticker)

if not df.empty:
    current_p = round(df['Close'].iloc[-1].item(), 2)
    
    # Simple probability math: if price drops 2% in an hour, it's a "Bear Event"
    price_1h_ago = df['Close'].iloc[-60].item() if len(df) > 60 else df['Close'].iloc[0].item()
    change_pct = ((current_p - price_1h_ago) / price_1h_ago) * 100

    # UI Display
    col1, col2 = st.columns([2, 1])
    with col1:
        st.metric(f"Live {ticker} Price", f"{current_p}", f"{round(change_pct, 2)}% (1h)")
        fig = go.Figure(data=[go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'])])
        st.plotly_chart(fig, use_container_width=True)

    # --- THE WATCHDOG (Unsupervised) ---
    if change_pct <= -2.0: # If it drops more than 2% in an hour
        alert_text = f"{ticker} is crashing! Down {round(change_pct, 2)}% in the last hour. Price: {current_p}"
        send_free_alert("⚠️ MARKET CRASH ALERT", alert_text, priority="urgent")
        st.error("🚨 ALERT SENT TO PHONE")

else:
    st.info("Waiting for market data... check if the ticker is correct.")

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import requests
from streamlit_autorefresh import st_autorefresh
from datetime import datetime

# --- 1. CONFIG ---
NTFY_TOPIC = "MrktPulse_Live_Sator__FFP_QTR" 

# Refresh every 60 seconds
st_autorefresh(interval=60 * 1000, key="market_heartbeat")

st.set_page_config(page_title="MarketPulse AI: Pro Watchdog", layout="wide")

# Custom CSS to make it look "Finished" and Pro
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stMetric { background-color: #161b22; border: 1px solid #30363d; padding: 15px; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🛡️ MarketPulse AI: Autonomous Watchdog")

# --- 2. THE FREE ALERT ENGINE ---
def send_free_alert(title, message, priority="default"):
    try:
        requests.post(f"https://ntfy.sh/{NTFY_TOPIC}", 
            data=message.encode('utf-8'),
            headers={
                "Title": title,
                "Priority": priority,
                "Tags": "chart_with_upwards_trend,warning"
            })
    except:
        pass

# --- 3. THE ANALYSIS ENGINE ---
st.sidebar.header("Settings")
ticker = st.sidebar.text_input("Ticker Symbol", value="AAPL").upper()
threshold = st.sidebar.slider("Alert Threshold (%)", -5.0, -0.5, -2.0)

@st.cache_data(ttl=30) # Reduced cache to keep it fresh
def get_market_data(t):
    # Changed to 5d to ensure we always have data even over weekends
    return yf.download(t, period="5d", interval="1m")

df = get_market_data(ticker)

if df is not None and not df.empty:
    # Handle the "Multi-index" issue some versions of yfinance have
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    current_p = round(float(df['Close'].iloc[-1]), 2)
    
    # Calculate change over the last 60 rows (minutes)
    price_start = df['Close'].iloc[-60] if len(df) >= 60 else df['Close'].iloc[0]
    change_pct = ((current_p - price_start) / price_start) * 100

    # --- UI DISPLAY ---
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.subheader(f"Live Intelligence: {ticker}")
        fig = go.Figure(data=[go.Candlestick(
            x=df.index,
            open=df['Open'], high=df['High'],
            low=df['Low'], close=df['Close'],
            increasing_line_color='#26a69a', decreasing_line_color='#ef5350'
        )])
        
        fig.update_layout(
            template="plotly_dark",
            xaxis_rangeslider_visible=False,
            height=500,
            margin=dict(l=10, r=10, t=10, b=10),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.metric("Current Price", f"${current_p}", f"{round(change_pct, 2)}% (1h)")
        st.write("---")
        st.write("**Watchdog Status:** 🟢 Active")
        st.write(f"**Last Sync:** {datetime.now().strftime('%H:%M:%S')}")
        st.caption("Monitoring for drops exceeding your threshold.")

    # --- THE WATCHDOG (Unsupervised) ---
    if change_pct <= threshold:
        alert_text = f"{ticker} CRASH: Down {round(change_pct, 2)}% in 1h. Price: ${current_p}"
        send_free_alert("🚨 MARKET ALARM", alert_text, priority="urgent")
        st.error(f"🚨 CRITICAL DROP DETECTED. Alert sent to phone.")

else:
    st.warning(f"📈 No live data found for **{ticker}**. This usually means the market is currently closed or the ticker is mistyped.")
    st.info("💡 Note: US Markets open at 9:30 AM EST. NSE Markets open at 9:15 AM IST.")

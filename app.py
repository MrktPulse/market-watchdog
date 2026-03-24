import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import requests
from streamlit_autorefresh import st_autorefresh
from datetime import datetime

# --- 1. SETTINGS & REFRESH ---
NTFY_TOPIC = "MrktPulse_Live_Sator__FFP_QTR"
st_autorefresh(interval=60 * 1000, key="market_heartbeat")

st.set_page_config(page_title="MarketPulse AI: Command Center", layout="wide")

# Professional Dark Theme CSS
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    div[data-testid="stMetricValue"] { font-size: 1.6rem; color: #00ffcc; }
    .stTable { background-color: #161b22; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. CORE FUNCTIONS ---

@st.cache_data(ttl=300)
def get_top_movers():
    """Fetches a quick snapshot of global leaders for the leaderboard."""
    watch_list = ["AAPL", "TSLA", "NVDA", "RELIANCE.NS", "TCS.NS", "INFY.NS", "BTC-USD"]
    try:
        data = yf.download(watch_list, period="1d", interval="1m", progress=False)
        # Handle new yfinance MultiIndex columns
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)
            
        movers = []
        for t in watch_list:
            ticker_data = yf.Ticker(t).history(period="1d")
            if not ticker_data.empty:
                open_p = ticker_data['Open'].iloc[0]
                close_p = ticker_data['Close'].iloc[-1]
                change = ((close_p - open_p) / open_p) * 100
                movers.append({"Ticker": t, "Price": round(close_p, 2), "Change %": round(change, 2)})
        return pd.DataFrame(movers).sort_values(by="Change %", ascending=False)
    except:
        return pd.DataFrame(columns=["Ticker", "Price", "Change %"])

def run_monte_carlo(current_price, vol, days=7):
    """Fixed Monte Carlo: Ensures math works with raw numbers, not tables."""
    price_raw = float(current_price) 
    sims = 1000
    daily_returns = np.random.normal(0, vol, (sims, days))
    price_paths = price_raw * np.exp(np.cumsum(daily_returns, axis=1))
    return np.percentile(price_paths[:, -1], [95, 50, 5])

# --- 3. SIDEBAR & SEARCH ---
st.sidebar.title("🔍 Global Command")
search_query = st.sidebar.text_input("Search Ticker (e.g. RELIANCE.NS, TSLA)", value="TSLA").upper()
watchlist = st.sidebar.multiselect("Active Watchlist", 
                                   ["AAPL", "NVDA", "TSLA", "RELIANCE.NS", "TCS.NS", "BTC-USD", "ETH-USD"],
                                   default=["AAPL", "TSLA", "RELIANCE.NS"])

# --- 4. TOP WINNERS & LOSERS ---
st.header("🏆 Live Market Leaderboard")
movers_df = get_top_movers()
if not movers_df.empty:
    col_gain, col_loss = st.columns(2)
    with col_gain:
        st.success("Top Gainers")
        st.dataframe(movers_df.head(3), hide_index=True, use_container_width=True)
    with col_loss:
        st.error("Top Losers")
        st.dataframe(movers_df.tail(3).sort_values(by="Change %"), hide_index=True, use_container_width=True)

st.write("---")

# --- 5. CHART GALLERY GRID ---
st.header("📊 Market Gallery")
all_tickers = list(dict.fromkeys([search_query] + watchlist)) # Unique list

# Build the grid (2 columns wide)
for i in range(0, len(all_tickers), 2):
    cols = st.columns(2)
    for j in range(2):
        if i + j < len(all_tickers):
            t = all_tickers[i + j]
            with cols[j]:
                st.subheader(f"📈 {t}")
                df = yf.download(t, period="5d", interval="1m", progress=False)
                
                if not df.empty:
                    # Fix for MultiIndex Columns
                    if isinstance(df.columns, pd.MultiIndex):
                        df.columns = df.columns.get_level_values(0)
                    
                    # Charting
                    fig = go.Figure(data=[go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'])])
                    fig.update_layout(template="plotly_dark", height=350, margin=dict(l=0,r=0,t=0,b=0), xaxis_rangeslider_visible=False)
                    st.plotly_chart(fig, use_container_width=True, key=f"chart_{t}_{i}_{j}")
                    
                    # Simulation Math
                    curr_price = float(df['Close'].iloc[-1])
                    returns = df['Close'].pct_change().dropna()
                    vol = returns.std()
                    
                    if not np.isnan(vol) and vol > 0:
                        bull, base, bear = run_monte_carlo(curr_price, vol)
                        st.write(f"**7-Day Prediction:** 🐂 Bull: ${round(bull,2)} | 🏠 Base: ${round(base,2)} | 🐻 Bear: ${round(bear,2)}")
                    else:
                        st.caption("Insufficient volatility data for simulation.")
                else:
                    st.warning(f"No data for {t}. Is the market open?")

# --- 6. AUTO-ALERT LOGIC ---
# (Alerts you via ntfy if the searched ticker drops > 2%)
if not df.empty and 'change_pct' in locals():
    if change_pct <= -2.0:
        requests.post(f"https://ntfy.sh/{NTFY_TOPIC}", data=f"CRITICAL: {search_query} dropped {round(change_pct,2)}%!")

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import requests
from streamlit_autorefresh import st_autorefresh
from datetime import datetime

# --- 1. CONFIG & REFRESH ---
NTFY_TOPIC = "MrktPulse_Live_Sator__FFP_QTR"
st_autorefresh(interval=60 * 1000, key="market_heartbeat")

st.set_page_config(page_title="MarketPulse AI: Command Center", layout="wide")

# Professional Dark Theme CSS
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    div[data-testid="stMetricValue"] { font-size: 1.8rem; color: #00ffcc; }
    .chart-container { border: 1px solid #30363d; border-radius: 10px; padding: 10px; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATA FUNCTIONS ---
@st.cache_data(ttl=300)
def get_top_movers():
    # Pre-defined list of major global/Indian tickers to track for the leaderboard
    watch_list = ["RELIANCE.NS", "TCS.NS", "INFY.NS", "AAPL", "TSLA", "NVDA", "MSFT", "HDFCBANK.NS", "ICICIBANK.NS", "AMZN"]
    data = yf.download(watch_list, period="1d", group_by='ticker')
    movers = []
    for t in watch_list:
        try:
            hist = data[t]
            change = ((hist['Close'].iloc[-1] - hist['Open'].iloc[0]) / hist['Open'].iloc[0]) * 100
            movers.append({"Ticker": t, "Price": round(hist['Close'].iloc[-1], 2), "Change": round(change, 2)})
        except: continue
    df_movers = pd.DataFrame(movers).sort_values(by="Change", ascending=False)
    return df_movers

def run_monte_carlo(current_price, vol, days=7):
    # 1000 random walks for the simulation part
    sims = 1000
    results = current_price * np.exp(np.cumsum(np.random.normal(0, vol, (sims, days)), axis=1))
    return np.percentile(results[:, -1], [95, 50, 5]) # Bull, Base, Bear

# --- 3. SIDEBAR & SEARCH ---
st.sidebar.title("🔍 Global Search")
search_query = st.sidebar.text_input("Enter Ticker (e.g. RELIANCE.NS, GOOG)", value="AAPL").upper()
multi_select = st.sidebar.multiselect("Select Watchlist Charts", 
                                    ["AAPL", "TSLA", "NVDA", "RELIANCE.NS", "TCS.NS", "BTC-USD", "ETH-USD", "MSFT", "AMZN", "GOOGL"],
                                    default=["AAPL", "TSLA", "RELIANCE.NS"])

# --- 4. TOP WINNERS & LOSERS ---
st.header("🏆 Live Market Leaderboard")
movers_df = get_top_movers()
col_gain, col_loss = st.columns(2)

with col_gain:
    st.success("Top Gainers")
    st.table(movers_df.head(5))

with col_loss:
    st.error("Top Losers")
    st.table(movers_df.tail(5).iloc[::-1])

st.write("---")

# --- 5. THE CHART GALLERY (Scrollable Grid) ---
st.header("📊 Market Gallery (Live Previews)")
gallery_tickers = list(set(multi_select + [search_query])) # Combine search and selection

# Create a grid of charts (2 per row)
rows = (len(gallery_tickers) + 1) // 2
for i in range(rows):
    cols = st.columns(2)
    for j in range(2):
        idx = i * 2 + j
        if idx < len(gallery_tickers):
            t = gallery_tickers[idx]
            with cols[j]:
                with st.container():
                    st.markdown(f"**{t}**")
                    df = yf.download(t, period="5d", interval="1m", progress=False)
                    if not df.empty:
                        fig = go.Figure(data=[go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'])])
                        fig.update_layout(template="plotly_dark", height=300, margin=dict(l=0,r=0,t=0,b=0), xaxis_rangeslider_visible=False)
                        st.plotly_chart(fig, use_container_width=True, key=f"chart_{t}")
                        
                        # --- 6. SIMULATION LOGIC ---
                        vol = df['Close'].pct_change().std()
                        curr = df['Close'].iloc[-1]
                        bull, base, bear = run_monte_carlo(curr, vol)
                        st.caption(f"🎯 7-Day Forecast: Bull: ${round(bull,2)} | Base: ${round(base,2)} | Bear: ${round(bear,2)}")
                    else:
                        st.warning(f"No data for {t}")

st.write("---")
st.info("💡 Tip: Use '.NS' for Indian stocks (NSE) and '.BO' for BSE. Example: RELIANCE.NS")

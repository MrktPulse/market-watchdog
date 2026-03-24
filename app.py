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

# UI Polish
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    div[data-testid="stMetricValue"] { font-size: 1.6rem; color: #00ffcc; }
    .stDataFrame { border: 1px solid #30363d; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. CORE FUNCTIONS ---
@st.cache_data(ttl=300)
def get_top_movers():
    watch_list = ["AAPL", "TSLA", "NVDA", "RELIANCE.NS", "TCS.NS", "BTC-USD"]
    movers = []
    for t in watch_list:
        try:
            tk = yf.Ticker(t)
            # Use 1d data for the leaderboard for speed
            inf = tk.fast_info
            change = ((inf['last_price'] - inf['open']) / inf['open']) * 100
            movers.append({"Ticker": t, "Price": round(inf['last_price'], 2), "Change %": round(change, 2)})
        except: continue
    return pd.DataFrame(movers).sort_values(by="Change %", ascending=False)

def run_monte_carlo(current_price, vol, days=7):
    price_raw = float(current_price) 
    sims = 1000
    daily_returns = np.random.normal(0, vol, (sims, days))
    price_paths = price_raw * np.exp(np.cumsum(daily_returns, axis=1))
    return np.percentile(price_paths[:, -1], [95, 50, 5])

# --- 3. SIDEBAR & SEARCH ---
st.sidebar.title("🔍 Global Command")
search_query = st.sidebar.text_input("Search Ticker", value="TSLA").upper()
watchlist = st.sidebar.multiselect("Active Watchlist", 
                                   ["AAPL", "NVDA", "TSLA", "RELIANCE.NS", "TCS.NS", "BTC-USD", "ETH-USD"],
                                   default=["AAPL", "TSLA", "RELIANCE.NS"])

# --- 4. LEADERBOARD ---
st.header("🏆 Live Market Leaderboard")
movers_df = get_top_movers()
if not movers_df.empty:
    c1, c2 = st.columns(2)
    c1.success("Top Gainers")
    c1.dataframe(movers_df.head(3), hide_index=True, use_container_width=True)
    c2.error("Top Losers")
    c2.dataframe(movers_df.tail(3).sort_values(by="Change %"), hide_index=True, use_container_width=True)

st.write("---")

# --- 5. CHART GALLERY ---
st.header("📊 Market Gallery")
all_tickers = list(dict.fromkeys([search_query] + watchlist))

for i in range(0, len(all_tickers), 2):
    cols = st.columns(2)
    for j in range(2):
        if i + j < len(all_tickers):
            t = all_tickers[i + j]
            with cols[j]:
                st.subheader(f"📈 {t}")
                # 15m interval fixed the "Ghost Gaps" in 5-day charts
                df = yf.download(t, period="5d", interval="15m", progress=False)
                
                if not df.empty:
                    if isinstance(df.columns, pd.MultiIndex):
                        df.columns = df.columns.get_level_values(0)
                    
                    # Modern Candlestick Design
                    fig = go.Figure(data=[go.Candlestick(
                        x=df.index, open=df['Open'], high=df['High'], 
                        low=df['Low'], close=df['Close'],
                        increasing_line_color='#26a69a', decreasing_line_color='#ef5350'
                    )])
                    fig.update_layout(template="plotly_dark", height=380, margin=dict(l=0,r=0,t=0,b=0), xaxis_rangeslider_visible=False)
                    st.plotly_chart(fig, use_container_width=True, key=f"chart_{t}_{i}_{j}")
                    
                    # Simulation
                    curr_price = float(df['Close'].iloc[-1])
                    vol = df['Close'].pct_change().std()
                    
                    if not np.isnan(vol) and vol > 0:
                        bull, base, bear = run_monte_carlo(curr_price, vol)
                        st.write(f"**7-Day Prediction:** 🟢 Bull: ${round(bull,2)} | ⚪ Base: ${round(base,2)} | 🔴 Bear: ${round(bear,2)}")
                else:
                    st.warning(f"No data for {t}. Market might be closed.")

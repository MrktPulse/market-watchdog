import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh
from datetime import datetime

# --- 1. SYSTEM CONFIG ---
st_autorefresh(interval=60 * 1000, key="market_heartbeat")
st.set_page_config(page_title="Market Pulse | Institutional Dashboard", layout="wide", initial_sidebar_state="collapsed")

# --- 2. PROFESSIONAL CSS (Corporate/Bloomberg Style) ---
st.markdown("""
    <style>
    /* Corporate Dark Theme */
    .stApp { background-color: #0b0f19; color: #e2e8f0; }
    
    /* Clean up input boxes and multiselect */
    .stMultiSelect div[data-baseweb="select"] {
        background-color: #1e293b; border: 1px solid #334155; border-radius: 8px;
    }
    
    /* Professional Metrics styling */
    div[data-testid="stMetricValue"] { font-size: 1.8rem; color: #f8fafc; font-weight: 600; }
    div[data-testid="stMetricDelta"] { font-size: 1.1rem; }
    
    /* Chart container borders */
    .chart-box {
        background: #121826; border: 1px solid #1e293b; 
        border-radius: 8px; padding: 15px; margin-bottom: 20px;
    }
    
    /* Headers */
    h1, h2, h3 { color: #f8fafc; font-weight: 400; font-family: 'Inter', sans-serif; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. CORE ANALYTICS ENGINE ---
def run_monte_carlo(current_price, vol, days=7):
    """Calculates 7-day probability targets based on real volatility."""
    price_raw = float(current_price) 
    sims = 1000
    daily_returns = np.random.normal(0, vol, (sims, days))
    price_paths = price_raw * np.exp(np.cumsum(daily_returns, axis=1))
    return np.percentile(price_paths[:, -1], [95, 50, 5]) # Bull, Base, Bear

# Top 100 Master List for Search Dropdown
indian_tickers = [f"{s}.NS" for s in ["RELIANCE", "TCS", "HDFCBANK", "ICICIBANK", "INFY", "BHARTIARTL", "SBI", "LIC", "ITC", "HINDUNILVR", "L&T", "BAJFINANCE", "MARUTI", "TATAMOTORS", "SUNPHARMA"]]
us_tickers = ["AAPL", "TSLA", "NVDA", "MSFT", "AMZN", "GOOGL", "META", "BRK-B", "UNH", "JNJ", "V", "WMT", "JPM", "PG", "MA", "HD", "CVX", "LLY", "BAC", "PFE"]
crypto = ["BTC-USD", "ETH-USD", "SOL-USD"]
all_100 = us_tickers + indian_tickers + crypto

# --- 4. HEADER & SMART SEARCH ---
st.markdown("<h1>📊 Market Pulse <span style='font-size: 1.2rem; color: #64748b;'>| Global Intelligence Terminal</span></h1>", unsafe_allow_html=True)
st.write("---")

# This is the new Smart Search: Icon, dropdown, type-to-filter, and multi-select all in one.
selected_tickers = st.multiselect(
    "🔍 Search & Compare Markets (Type ticker to filter, select multiple to compare)",
    options=all_100,
    default=["NVDA", "RELIANCE.NS"], # Loads these two by default so you see the comparison instantly
    help="Type any stock symbol. Select multiple to stack charts."
)

if not selected_tickers:
    st.info("👆 Please select at least one ticker from the search bar above to begin analysis.")
    st.stop()

# --- 5. DYNAMIC COMPARISON BOARD ---
# This loop builds a high-end analysis block for every ticker you selected.
for t in selected_tickers:
    st.markdown(f"<div class='chart-box'>", unsafe_allow_html=True)
    st.subheader(f"Ticker: {t}")
    
    # Download data
    df = yf.download(t, period="5d", interval="15m", progress=False)
    
    if not df.empty:
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        
        # 1. CHART RENDERING
        fig = go.Figure(data=[go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
                                           increasing_line_color='#10b981', decreasing_line_color='#ef4444')]) # Pro green/red
        
        fig.update_xaxes(rangebreaks=[dict(bounds=["sat", "mon"]), dict(bounds=[16, 9.5], pattern="hour")])
        fig.update_layout(template="plotly_dark", height=450, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                          margin=dict(l=10, r=10, t=10, b=10), xaxis_rangeslider_visible=False)
        st.plotly_chart(fig, use_container_width=True)
        
        # 2. THE PREDICTION ENGINE (Now Highly Visible)
        curr_price = float(df['Close'].iloc[-1].item())
        returns = df['Close'].pct_change().dropna()
        vol = returns.std()
        
        if not np.isnan(vol) and vol > 0:
            bull, base, bear = run_monte_carlo(curr_price, vol)
            
            # Calculate percentages for the UI
            bull_pct = ((bull - curr_price) / curr_price) * 100
            base_pct = ((base - curr_price) / curr_price) * 100
            bear_pct = ((bear - curr_price) / curr_price) * 100
            
            st.markdown("#### 🎯 Market Pulse 7-Day Statistical Forecast")
            c1, c2, c3, c4 = st.columns(4)
            
            c1.metric("Current Live Price", f"${curr_price:,.2f}")
            c2.metric("🟢 Bull Target (95%)", f"${bull:,.2f}", f"+{bull_pct:.1f}%")
            c3.metric("⚪ Base Target (50%)", f"${base:,.2f}", f"{base_pct:.1f}%")
            c4.metric("🔴 Bear Target (5%)", f"${bear:,.2f}", f"{bear_pct:.1f}%")
            
            # AI Trend Summary
            trend = "Bullish Outlook" if base_pct > 0 else "Bearish Pressure"
            color = "normal" if base_pct > 0 else "inverse"
            st.success(f"**Insight:** Based on current volatility ({round(vol*100, 2)}%), the mathematical model projects a **{trend}** over the next 5 trading sessions.")
            
        else:
            st.caption("Not enough volatility data to generate statistical predictions.")
            
    else:
        st.warning(f"Market data stream for {t} is currently unavailable. Market may be closed or ticker is invalid.")
        
    st.markdown("</div>", unsafe_allow_html=True)
    st.write("---") # Separator between compared charts

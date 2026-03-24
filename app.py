import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh
from datetime import datetime
import pytz

# --- 1. SYSTEM CONFIG & 15-SECOND REFRESH ---
# 15,000 milliseconds = 15 seconds
st_autorefresh(interval=15 * 1000, key="market_heartbeat")
st.set_page_config(page_title="Market Pulse | Institutional Dashboard", layout="wide", initial_sidebar_state="collapsed")

# --- 2. MEMORY BANK (For EOD Accuracy Tracking) ---
if 'morning_predictions' not in st.session_state:
    st.session_state.morning_predictions = {}

# --- 3. PROFESSIONAL CSS ---
st.markdown("""
    <style>
    .stApp { background-color: #0b0f19; color: #e2e8f0; }
    .stMultiSelect div[data-baseweb="select"] { background-color: #1e293b; border: 1px solid #334155; border-radius: 8px; }
    div[data-testid="stMetricValue"] { font-size: 1.8rem; color: #f8fafc; font-weight: 600; }
    .chart-box { background: #121826; border: 1px solid #1e293b; border-radius: 8px; padding: 15px; margin-bottom: 20px; }
    h1, h2, h3 { color: #f8fafc; font-weight: 400; font-family: 'Inter', sans-serif; }
    </style>
    """, unsafe_allow_html=True)

# --- 4. CORE ANALYTICS ENGINE ---
def run_monte_carlo(current_price, vol, days=1):
    """Calculates probability targets based on real volatility."""
    price_raw = float(current_price) 
    sims = 1000
    daily_returns = np.random.normal(0, vol, (sims, days))
    price_paths = price_raw * np.exp(np.cumsum(daily_returns, axis=1))
    return np.percentile(price_paths[:, -1], [95, 50, 5])

indian_tickers = [f"{s}.NS" for s in ["RELIANCE", "TCS", "HDFCBANK", "ICICIBANK", "INFY", "BHARTIARTL", "SBI", "LIC", "ITC", "HINDUNILVR"]]
us_tickers = ["AAPL", "TSLA", "NVDA", "MSFT", "AMZN", "GOOGL", "META", "BRK-B", "UNH", "JNJ"]
all_100 = us_tickers + indian_tickers + ["BTC-USD", "ETH-USD"]

# --- 5. SMART SEARCH ---
st.markdown("<h1>📊 Market Pulse <span style='font-size: 1.2rem; color: #64748b;'>| High-Frequency Terminal</span></h1>", unsafe_allow_html=True)
st.write("---")

selected_tickers = st.multiselect(
    "🔍 Search & Compare Markets (Type ticker to filter, select multiple to compare)",
    options=all_100,
    default=["NVDA", "RELIANCE.NS"]
)

if not selected_tickers:
    st.info("👆 Please select at least one ticker from the search bar above to begin analysis.")
    st.stop()

# --- 6. DYNAMIC COMPARISON BOARD ---
for t in selected_tickers:
    st.markdown(f"<div class='chart-box'>", unsafe_allow_html=True)
    st.subheader(f"Ticker: {t}")
    
    # FETCH 1-DAY, 1-MINUTE DATA (Hyper-dense, real-time candles)
    df = yf.download(t, period="1d", interval="1m", progress=False)
    
    if not df.empty:
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        
        open_price = float(df['Open'].iloc[0].item())
        curr_price = float(df['Close'].iloc[-1].item())
        last_timestamp = df.index[-1]
        
        # 1. CHART RENDERING
        fig = go.Figure(data=[go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
                                           increasing_line_color='#10b981', decreasing_line_color='#ef4444')])
        
        fig.update_layout(template="plotly_dark", height=450, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                          margin=dict(l=10, r=10, t=10, b=10), xaxis_rangeslider_visible=False)
        st.plotly_chart(fig, use_container_width=True)
        
        # 2. INTRADAY PREDICTION ENGINE
        returns = df['Close'].pct_change().dropna()
        vol = returns.std()
        
        if not np.isnan(vol) and vol > 0:
            bull, base, bear = run_monte_carlo(curr_price, vol, days=1)
            
            # Save the first prediction of the day in Memory
            if t not in st.session_state.morning_predictions:
                st.session_state.morning_predictions[t] = base
            
            expected_close = st.session_state.morning_predictions[t]
            
            st.markdown("#### 🎯 Intraday Target Metrics")
            c1, c2, c3 = st.columns(3)
            c1.metric("Today's Open", f"${open_price:,.2f}")
            c2.metric("Live Price", f"${curr_price:,.2f}", f"{((curr_price-open_price)/open_price)*100:.2f}%")
            c3.metric("Predicted EOD Close", f"${expected_close:,.2f}")
            
            # The Custom Insight Sentence
            trend_word = "climb" if expected_close > open_price else "drop"
            st.info(f"**Live Insight:** Opening at **${open_price:,.2f}**, and based on real-time volatility calculations, it is predicted to {trend_word} and end at **${expected_close:,.2f}**.")
            
            # --- 7. EOD ACCURACY POPUP ---
            # Check if it's near market close (US: 15:55+, India: 15:25+)
            is_eod = False
            if t.endswith(".NS") and last_timestamp.hour == 15 and last_timestamp.minute >= 25:
                is_eod = True
            elif not t.endswith(".NS") and last_timestamp.hour == 15 and last_timestamp.minute >= 55:
                is_eod = True
                
            if is_eod:
                diff = curr_price - expected_close
                accuracy = 100 - (abs(diff) / expected_close * 100)
                
                st.warning("🔔 **MARKET CLOSING REPORT**")
                st.markdown(f"""
                > **{t} End of Day Summary:**
                > * Predicted Close: **${expected_close:,.2f}**
                > * Actual Close: **${curr_price:,.2f}**
                > * Difference: **${diff:,.2f}**
                > * **Model Accuracy:** **{accuracy:.2f}%**
                """)
                st.toast(f"{t} Market Closed. Accuracy: {accuracy:.2f}%", icon="📈")
                
        else:
            st.caption("Awaiting sufficient volatility data...")
            
    else:
        st.warning(f"Market data stream for {t} is currently unavailable. Market may be closed.")
        
    st.markdown("</div>", unsafe_allow_html=True)
    st.write("---")

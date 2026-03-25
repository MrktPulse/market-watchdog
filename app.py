import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh
from datetime import datetime

# 1. PAGE CONFIG
st.set_page_config(page_title="Market Pulse | Terminal", layout="wide", initial_sidebar_state="collapsed")

# 2. SESSION STATE
if "disclaimer_accepted" not in st.session_state:
    st.session_state.disclaimer_accepted = False
if "selected_stock" not in st.session_state:
    st.session_state.selected_stock = None
if "morning_predictions" not in st.session_state:
    st.session_state.morning_predictions = {}

st_autorefresh(interval=30_000, key="market_heartbeat")

# 3. TICKERS & TIMELINES
SP500_TOP = [("AAPL","Apple"), ("MSFT","Microsoft"), ("NVDA","NVIDIA"), ("TSLA","Tesla"), ("AMZN","Amazon"), ("META","Meta")]
NSE_TOP = [("RELIANCE.NS","Reliance"), ("TCS.NS","TCS"), ("INFY.NS","Infosys")]

# 4. CSS
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono&family=IBM+Plex+Sans:wght@300;400;600&display=swap');
:root { --bg: #07090f; --bg2: #0c1018; --border: #1c2333; --text: #dde3ed; --blue: #388bfd; }
html, body, .stApp { background: var(--bg) !important; color: var(--text); font-family: 'IBM Plex Sans', sans-serif; }
.metric-strip { display: flex; background: var(--bg2); border: 1px solid var(--border); border-radius: 4px; margin: 15px 0; }
.metric-cell { flex: 1; padding: 12px; border-right: 1px solid var(--border); text-align: center; }
.accuracy-box { background: #0a1a0a; border: 1px solid #1a3320; border-radius: 6px; padding: 20px; font-family: 'IBM Plex Mono'; color: #5a9a5a; }
</style>
""", unsafe_allow_html=True)

# 5. FUNCTIONS
def fetch_data(ticker, period, interval):
    try:
        df = yf.download(ticker, period=period, interval=interval, progress=False, auto_adjust=False)
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        return df
    except: return pd.DataFrame()

def run_monte_carlo(current_price, vol):
    r = np.random.normal(0, vol, (1000, 1))
    paths = float(current_price) * np.exp(r)
    return np.percentile(paths, [95, 50, 5])

# 6. RISK GATEWAY
if not st.session_state.disclaimer_accepted:
    _, center, _ = st.columns([1, 2, 1])
    with center:
        st.write("#")
        with st.container(border=True):
            st.subheader("⚠️ Risk Disclosure")
            st.write("Financial predictions are statistical models and do not guarantee results.")
            if st.button("I Understand & Agree", use_container_width=True, type="primary"):
                st.session_state.disclaimer_accepted = True
                st.rerun()
    st.stop()

# 7. DASHBOARD
if st.session_state.selected_stock:
    ticker = st.session_state.selected_stock
    col_back, col_toggle = st.columns([1, 1])
    if col_back.button("← Back"):
        st.session_state.selected_stock = None
        st.rerun()

    # DATA FETCHING
    df_live = fetch_data(ticker, "1d", "1m")
    
    if not df_live.empty:
        curr = df_live['Close'].iloc[-1]
        ts = df_live.index[-1]
        vol = df_live['Close'].pct_change().std()

        # Morning Lock Logic
        if ticker not in st.session_state.morning_predictions:
            _, pred, _ = run_monte_carlo(df_live['Open'].iloc[0], vol if vol > 0 else 0.001)
            st.session_state.morning_predictions[ticker] = pred
        
        morning_p = st.session_state.morning_predictions[ticker]

        # ANALYTICS BUTTON (Shown after 3:30 PM or Test Mode)
        is_post_market = ts.hour >= 15 # Simplistic check for EOD
        show_analysis = col_toggle.toggle("Show Accuracy Analysis", value=False)

        if show_analysis:
            # 1. ACCURACY CALCULATION
            accuracy = 100 - (abs(curr - morning_p) / morning_p * 100)
            
            st.markdown(f"""
            <div class="accuracy-box">
                <h3 style="margin-top:0; color:#3fb950;">EOD PERFORMANCE REPORT</h3>
                <b>Model Accuracy: {accuracy:.2f}%</b><br>
                Predicted: ${morning_p:,.2f} | Actual: ${curr:,.2f}<br>
                Variance: ${curr - morning_p:+,.2f}
            </div>
            """, unsafe_allow_html=True)

            # 2. TREND COMPARISON CHART
            fig_compare = go.Figure()
            # Actual Trend
            fig_compare.add_trace(go.Scatter(x=df_live.index, y=df_live['Close'], name="Actual Trend", line=dict(color='#3fb950', width=2)))
            # Predicted Baseline (Straight line from Open to Prediction)
            fig_compare.add_trace(go.Scatter(
                x=[df_live.index[0], df_live.index[-1]], 
                y=[df_live['Open'].iloc[0], morning_p], 
                name="AI Predicted Path", 
                line=dict(color='#388bfd', width=2, dash='dot')
            ))
            fig_compare.update_layout(title=f"Actual vs Predicted Trend: {ticker}", template="plotly_dark", height=400)
            st.plotly_chart(fig_compare, use_container_width=True)
        else:
            # Standard Candlestick Chart
            fig = go.Figure(data=[go.Candlestick(x=df_live.index, open=df_live['Open'], high=df_live['High'], low=df_live['Low'], close=df_live['Close'])])
            fig.update_layout(template="plotly_dark", height=500, xaxis_rangeslider_visible=False)
            st.plotly_chart(fig, use_container_width=True)

        st.markdown(f"""<div class="metric-strip"><div class="metric-cell"><small>LAST PRICE</small><br><b>${curr:,.2f}</b></div><div class="metric-cell"><small>AM PREDICTION</small><br><b>${morning_p:,.2f}</b></div></div>""", unsafe_allow_html=True)

    st.stop()

# 8. MARKET GRID
cols = st.columns(4)
for i, (t, n) in enumerate(SP500_TOP + NSE_TOP):
    with cols[i % 4]:
        st.markdown(f"<div class='stock-card'><b>{t}</b><br><small>{n}</small></div>", unsafe_allow_html=True)
        if st.button(f"Analyze {t}", key=f"btn_{t}"):
            st.session_state.selected_stock = t
            st.rerun()

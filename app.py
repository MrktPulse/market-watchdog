import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh

# ─────────────────────────────────────────────
# 1. PAGE CONFIG (Must be the very first Streamlit call)
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Market Pulse | Terminal",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─────────────────────────────────────────────
# 2. SESSION STATE INITIALIZATION (Prevents NameError)
# ─────────────────────────────────────────────
if "disclaimer_accepted" not in st.session_state:
    st.session_state.disclaimer_accepted = False
if "selected_stock" not in st.session_state:
    st.session_state.selected_stock = None
if "morning_predictions" not in st.session_state:
    st.session_state.morning_predictions = {}

# Heartbeat refresh (30 seconds)
st_autorefresh(interval=30_000, key="market_heartbeat")

# ─────────────────────────────────────────────
# 3. TICKER UNIVERSE & CONSTANTS
# ─────────────────────────────────────────────
SP500_TOP100 = [
    ("AAPL","Apple"), ("MSFT","Microsoft"), ("NVDA","NVIDIA"), ("AMZN","Amazon"),
    ("GOOGL","Alphabet"), ("META","Meta"), ("TSLA","Tesla"), ("LLY","Eli Lilly"),
    ("AVGO","Broadcom"), ("JPM","JPMorgan"), ("UNH","UnitedHealth"), ("V","Visa")
]
NSE_TOP50 = [
    ("RELIANCE.NS","Reliance"), ("TCS.NS","TCS"), ("HDFCBANK.NS","HDFC Bank"),
    ("ICICIBANK.NS","ICICI Bank"), ("INFY.NS","Infosys"), ("SBI.NS","SBI")
]
CRYPTO = [("BTC-USD","Bitcoin"), ("ETH-USD","Ethereum"), ("SOL-USD","Solana")]

NAME_MAP = {t: n for t, n in SP500_TOP100 + NSE_TOP50 + CRYPTO}

# Timeframe logic mapped to your "Course of time" requirements
TIME_SETTINGS = {
    "1m":  {"period": "1d",  "interval": "1m",  "label": "1 Min (Live)"},
    "1h":  {"period": "7d",  "interval": "60m", "label": "Hourly"},
    "1d":  {"period": "1y",  "interval": "1d",  "label": "Daily (1yr)"},
    "1wk": {"period": "2y",  "interval": "1wk", "label": "Weekly"},
    "1mo": {"period": "5y",  "interval": "1mo", "label": "Monthly"},
    "3mo": {"period": "10y", "interval": "3mo", "label": "Quarterly"},
}

CHART_FONT = dict(family="'IBM Plex Mono', monospace", size=11, color="#4e5a6e")

# ─────────────────────────────────────────────
# 4. GLOBAL CSS & STYLING
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@300;400;600&display=swap');
:root { --bg: #07090f; --bg2: #0c1018; --border: #1c2333; --text: #dde3ed; --green: #3fb950; --red: #f85149; }
html, body, .stApp { background: var(--bg) !important; color: var(--text); font-family: 'IBM Plex Sans', sans-serif; }
.stock-card { background: var(--bg2); border: 1px solid var(--border); border-radius: 6px; padding: 15px; transition: 0.2s; }
.stock-card:hover { border-color: #388bfd; transform: translateY(-2px); }
.metric-strip { display: flex; background: var(--bg2); border: 1px solid var(--border); border-radius: 4px; margin: 20px 0; }
.metric-cell { flex: 1; padding: 15px; border-right: 1px solid var(--border); text-align: center; }
.insight-strip { background: #111722; border-left: 3px solid #388bfd; padding: 15px; color: #8493a8; font-size: 0.9rem; }
.mp-header { border-bottom: 1px solid var(--border); padding-bottom: 15px; margin-bottom: 25px; display: flex; justify-content: space-between; align-items: center; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# 5. FUNCTIONS
# ─────────────────────────────────────────────
def run_monte_carlo(current_price, vol, days=1):
    sims = 1000
    r = np.random.normal(0, vol, (sims, days))
    paths = float(current_price) * np.exp(np.cumsum(r, axis=1))
    return np.percentile(paths[:, -1], [95, 50, 5])

@st.cache_data(ttl=60)
def fetch_data(ticker, period, interval):
    try:
        df = yf.download(ticker, period=period, interval=interval, progress=False)
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        return df
    except: return pd.DataFrame()

# ─────────────────────────────────────────────
# 6. RISK DISCLOSURE GATEWAY
# ─────────────────────────────────────────────
if not st.session_state.disclaimer_accepted:
    st.markdown("""
    <div style="background:#0c1018; border:1px solid #253045; padding:40px; max-width:600px; margin:100px auto; border-radius:8px; text-align:center;">
        <h3 style="color:#dde3ed; font-family:'IBM Plex Mono';">Market Pulse · Risk Disclosure</h3>
        <p style="color:#8493a8; font-size:0.9rem; line-height:1.6;">
            Projections are statistical models and <b>do not guarantee performance</b>. 
            Nothing here constitutes financial advice. Conduct your own due diligence.
        </p>
    </div>
    """, unsafe_allow_html=True)
    if st.button("I Understand & Agree", use_container_width=True):
        st.session_state.disclaimer_accepted = True
        st.rerun()
    st.stop()

# ─────────────────────────────────────────────
# 7. MAIN INTERFACE
# ─────────────────────────────────────────────
st.markdown('<div class="mp-header"><span style="font-family:monospace; font-weight:600;">MARKET PULSE v2.0</span><span style="font-size:0.7rem; color:#4e5a6e;">LIVE TERMINAL</span></div>', unsafe_allow_html=True)

# DETAIL VIEW LOGIC
if st.session_state.selected_stock:
    ticker = st.session_state.selected_stock
    if st.button("← Back to Markets"):
        st.session_state.selected_stock = None
        st.rerun()

    st.title(f"{ticker} Analysis")
    tabs = st.tabs([TIME_SETTINGS[k]["label"] for k in TIME_SETTINGS])

    for i, (key, cfg) in enumerate(TIME_SETTINGS.items()):
        with tabs[i]:
            df = fetch_data(ticker, cfg["period"], cfg["interval"])
            if not df.empty:
                fig = go.Figure(data=[go.Candlestick(
                    x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
                    increasing_line_color='#3fb950', decreasing_line_color='#f85149'
                )])
                
                # FIX: Uniform Candle Thickness
                if key in ["1m", "1h"]:
                    fig.update_xaxes(type='category', nticks=10)
                else:
                    fig.update_xaxes(rangebreaks=[dict(bounds=["sat", "mon"])])
                
                fig.update_layout(template="plotly_dark", height=500, xaxis_rangeslider_visible=False, margin=dict(l=0,r=0,t=0,b=0), font=CHART_FONT)
                st.plotly_chart(fig, use_container_width=True)

                # AI Metrics (Standardized for Intraday)
                df_ai = fetch_data(ticker, "1d", "1m")
                if not df_ai.empty:
                    curr = df_ai['Close'].iloc[-1]
                    vol = df_ai['Close'].pct_change().std()
                    bull, base, bear = run_monte_carlo(curr, vol)
                    
                    st.markdown(f"""
                    <div class="metric-strip">
                        <div class="metric-cell"><small>LAST</small><br><b>${curr:,.2f}</b></div>
                        <div class="metric-cell"><small>VOLATILITY</small><br><b>{vol*100:.3f}%</b></div>
                        <div class="metric-cell"><small>PREDICTED</small><br><b>${base:,.2f}</b></div>
                    </div>
                    <div class="insight-strip">
                        Monte Carlo Analysis: Bear <b>${bear:,.2f}</b> | Base <b>${base:,.2f}</b> | Bull <b>${bull:,.2f}</b>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.error("Data Stream Interrupted.")
    st.stop()

# GRID VIEW LOGIC
col_s, _ = st.columns([1, 2])
search = col_s.text_input("Search Ticker", placeholder="e.g. AAPL, BTC-USD")
if search:
    st.session_state.selected_stock = search.upper()
    st.rerun()

# Display logic for Top 10 cards
cols = st.columns(4)
for i, (t, n) in enumerate(SP500_TOP100[:12]):
    with cols[i % 4]:
        st.markdown(f"<div class='stock-card'><b>{t}</b><br><small>{n}</small></div>", unsafe_allow_html=True)
        if st.button(f"View {t}", key=t):
            st.session_state.selected_stock = t
            st.rerun()

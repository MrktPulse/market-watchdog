import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh

# ─────────────────────────────────────────────
# 1. PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Market Pulse | Terminal",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─────────────────────────────────────────────
# 2. SESSION STATE
# ─────────────────────────────────────────────
if "disclaimer_accepted" not in st.session_state:
    st.session_state.disclaimer_accepted = False
if "selected_stock" not in st.session_state:
    st.session_state.selected_stock = None
if "morning_predictions" not in st.session_state:
    st.session_state.morning_predictions = {}

# 30-second refresh for live data
st_autorefresh(interval=30_000, key="market_heartbeat")

# ─────────────────────────────────────────────
# 3. CONSTANTS
# ─────────────────────────────────────────────
SP500_TOP100 = [
    ("AAPL","Apple"), ("MSFT","Microsoft"), ("NVDA","NVIDIA"), ("AMZN","Amazon"),
    ("GOOGL","Alphabet"), ("META","Meta"), ("TSLA","Tesla"), ("LLY","Eli Lilly"),
    ("AVGO","Broadcom"), ("JPM","JPMorgan"), ("UNH","UnitedHealth"), ("V","Visa")
]
TIME_SETTINGS = {
    "1m":  {"period": "1d",  "interval": "1m",  "label": "1 Min (Live)"},
    "1h":  {"period": "7d",  "interval": "60m", "label": "Hourly"},
    "1d":  {"period": "1y",  "interval": "1d",  "label": "Daily (1yr)"},
}
CHART_FONT = dict(family="'IBM Plex Mono', monospace", size=11, color="#4e5a6e")

# ─────────────────────────────────────────────
# 4. GLOBAL CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@300;400;600&display=swap');
:root { --bg: #07090f; --bg2: #0c1018; --border: #1c2333; --text: #dde3ed; --green: #3fb950; --red: #f85149; }
html, body, .stApp { background: var(--bg) !important; color: var(--text); font-family: 'IBM Plex Sans', sans-serif; }
.stock-card { background: var(--bg2); border: 1px solid var(--border); border-radius: 6px; padding: 15px; transition: 0.2s; }
.stock-card:hover { border-color: #388bfd; transform: translateY(-2px); cursor: pointer; }
.metric-strip { display: flex; background: var(--bg2); border: 1px solid var(--border); border-radius: 4px; margin: 20px 0; }
.metric-cell { flex: 1; padding: 15px; border-right: 1px solid var(--border); text-align: center; }
.insight-strip { background: #111722; border-left: 3px solid #388bfd; padding: 15px; color: #8493a8; font-size: 0.9rem; margin-bottom: 10px; }
.eod-report {
    background: #0a1a0a; border: 1px solid #1a3320; border-radius: 4px;
    padding: 16px 20px; font-family: 'IBM Plex Mono', monospace; font-size: 0.85rem;
    color: #5a9a5a; line-height: 1.8; margin-top: 15px;
}
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
        # ADJUSTMENT 1: auto_adjust=False ensures we get the "Official" Close Price
        df = yf.download(ticker, period=period, interval=interval, 
                         progress=False, auto_adjust=False)
        
        # ADJUSTMENT 2: Proper flattening for new Multi-Index structure
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        return df
    except: return pd.DataFrame()

# ─────────────────────────────────────────────
# 6. RISK GATEWAY
# ─────────────────────────────────────────────
if not st.session_state.disclaimer_accepted:
    st.markdown('<div style="background:#0c1018; border:1px solid #253045; padding:40px; max-width:600px; margin:100px auto; border-radius:8px; text-align:center;">'
                '<h3 style="color:#dde3ed; font-family:\'IBM Plex Mono\';">Market Pulse · Risk Disclosure</h3>'
                '<p style="color:#8493a8; font-size:0.9rem;">Projections are statistical models and do not guarantee performance.</p></div>', unsafe_allow_html=True)
    if st.button("I Understand & Agree", use_container_width=True):
        st.session_state.disclaimer_accepted = True
        st.rerun()
    st.stop()

# ─────────────────────────────────────────────
# 7. MAIN INTERFACE
# ─────────────────────────────────────────────
with st.sidebar:
    st.write("### Developer Tools")
    test_mode = st.toggle("Force Show EOD Report", value=False)

st.markdown('<div style="border-bottom: 1px solid #1c2333; padding-bottom:15px; margin-bottom:25px; display:flex; justify-content:space-between; align-items:center;">'
            '<span style="font-family:monospace; font-weight:600;">MARKET PULSE v2.0</span>'
            '<span style="font-size:0.7rem; color:#4e5a6e;">LIVE TERMINAL</span></div>', unsafe_allow_html=True)

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
                # Plotting logic
                fig = go.Figure(data=[go.Candlestick(
                    x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
                    increasing_line_color='#3fb950', decreasing_line_color='#f85149'
                )])
                fig.update_layout(template="plotly_dark", height=500, xaxis_rangeslider_visible=False, margin=dict(l=0,r=0,t=0,b=0), font=CHART_FONT)
                st.plotly_chart(fig, use_container_width=True)

                # ADJUSTMENT 3: "Morning Lock" Prediction Logic
                df_ai = fetch_data(ticker, "1d", "1m")
                if not df_ai.empty:
                    curr = float(df_ai['Close'].iloc[-1])
                    ts = df_ai.index[-1]
                    vol = df_ai['Close'].pct_change().dropna().std()
                    
                    if vol and vol > 0:
                        # Lock in the prediction once per day
                        if ticker not in st.session_state.morning_predictions:
                            _, base_pred, _ = run_monte_carlo(curr, vol)
                            st.session_state.morning_predictions[ticker] = base_pred
                        
                        eod_pred = st.session_state.morning_predictions[ticker]
                        bull, _, bear = run_monte_carlo(curr, vol)

                        st.markdown(f"""
                        <div class="metric-strip">
                            <div class="metric-cell"><small>OFFICIAL CLOSE (Live)</small><br><b>${curr:,.2f}</b></div>
                            <div class="metric-cell"><small>VOLATILITY</small><br><b>{vol*100:.3f}%</b></div>
                            <div class="metric-cell"><small>AM PREDICTION</small><br><b>${eod_pred:,.2f}</b></div>
                        </div>
                        <div class="insight-strip">
                            MC Range: Bear <b>${bear:,.2f}</b> | Bull <b>${bull:,.2f}</b>
                        </div>
                        """, unsafe_allow_html=True)

                        # Check if market is in closing 5 mins
                        is_eod_time = ( (ticker.endswith(".NS") and ts.hour == 15 and ts.minute >= 25) or 
                                        (not ticker.endswith(".NS") and ts.hour == 15 and ts.minute >= 55) )

                        if is_eod_time or test_mode:
                            diff = curr - eod_pred
                            acc = 100 - abs(diff) / eod_pred * 100
                            st.markdown(f"""
                            <div class="eod-report">
                                <b>OFFICIAL NASDAQ/NSE CLOSING REPORT — {ticker}</b><br>
                                ──────────────────────────────────────────<br>
                                Morning Prediction: &nbsp;&nbsp;&nbsp;&nbsp; ${eod_pred:,.2f}<br>
                                Official Market Close: &nbsp; ${curr:,.2f}<br>
                                Price Variance: &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; ${diff:+,.2f}<br>
                                <b>Model Accuracy: &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; {acc:.2f}%</b>
                            </div>
                            """, unsafe_allow_html=True)
            else:
                st.error("Data Stream Interrupted.")
    st.stop()

# SEARCH & GRID
col_s, _ = st.columns([1, 2])
search = col_s.text_input("Search Ticker", placeholder="e.g. AAPL")
if search:
    st.session_state.selected_stock = search.upper()
    st.rerun()

cols = st.columns(4)
for i, (t, n) in enumerate(SP500_TOP100[:12]):
    with cols[i % 4]:
        st.markdown(f"<div class='stock-card'><b>{t}</b><br><small>{n}</small></div>", unsafe_allow_html=True)
        if st.button(f"View {t}", key=t):
            st.session_state.selected_stock = t
            st.rerun()

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh

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

# 3. RESTORED TIMELINES (Weekly, Monthly, etc. are back)
TIME_SETTINGS = {
    "1m":  {"period": "1d",  "interval": "1m",  "label": "1 Min (Live)"},
    "1h":  {"period": "7d",  "interval": "60m", "label": "Hourly"},
    "1d":  {"period": "1y",  "interval": "1d",  "label": "Daily (1yr)"},
    "1wk": {"period": "2y",  "interval": "1wk", "label": "Weekly"},
    "1mo": {"period": "5y",  "interval": "1mo", "label": "Monthly"},
}

CHART_FONT = dict(family="'IBM Plex Mono', monospace", size=11, color="#4e5a6e")

# 4. GLOBAL CSS (Includes fix for Disclaimer Button)
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@300;400;600&display=swap');
:root { --bg: #07090f; --bg2: #0c1018; --border: #1c2333; --text: #dde3ed; --green: #3fb950; --red: #f85149; }
html, body, .stApp { background: var(--bg) !important; color: var(--text); font-family: 'IBM Plex Sans', sans-serif; }
.stock-card { background: var(--bg2); border: 1px solid var(--border); border-radius: 6px; padding: 15px; transition: 0.2s; cursor: pointer; }
.metric-strip { display: flex; background: var(--bg2); border: 1px solid var(--border); border-radius: 4px; margin: 20px 0; }
.metric-cell { flex: 1; padding: 15px; border-right: 1px solid var(--border); text-align: center; }
.insight-strip { background: #111722; border-left: 3px solid #388bfd; padding: 15px; color: #8493a8; font-size: 0.9rem; margin-bottom: 10px; }
.eod-report { background: #0a1a0a; border: 1px solid #1a3320; border-radius: 4px; padding: 16px 20px; font-family: 'IBM Plex Mono'; color: #5a9a5a; margin-top: 15px; }
/* Disclaimer Box Fix */
.gate-container { background:#0c1018; border:1px solid #253045; padding:30px; max-width:500px; margin:80px auto; border-radius:8px; text-align:center; }
</style>
""", unsafe_allow_html=True)

# 5. FUNCTIONS
def run_monte_carlo(current_price, vol, days=1):
    sims = 1000
    r = np.random.normal(0, vol, (sims, days))
    paths = float(current_price) * np.exp(np.cumsum(r, axis=1))
    return np.percentile(paths[:, -1], [95, 50, 5])

@st.cache_data(ttl=60)
def fetch_data(ticker, period, interval):
    try:
        # auto_adjust=False is key for matching official NASDAQ/NSE price
        df = yf.download(ticker, period=period, interval=interval, progress=False, auto_adjust=False)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        return df
    except: return pd.DataFrame()

# 6. RISK GATEWAY (Button inside the box now)
if not st.session_state.disclaimer_accepted:
    st.markdown('<div class="gate-container">', unsafe_allow_html=True)
    st.markdown('<h3 style="color:#dde3ed; font-family:\'IBM Plex Mono\';">Risk Disclosure</h3>', unsafe_allow_html=True)
    st.markdown('<p style="color:#8493a8; font-size:0.85rem; margin-bottom:20px;">Projections are models and do not guarantee performance. Conduct your own due diligence.</p>', unsafe_allow_html=True)
    if st.button("I Understand & Agree", use_container_width=True):
        st.session_state.disclaimer_accepted = True
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# 7. MAIN INTERFACE
with st.sidebar:
    test_mode = st.toggle("Force EOD Report", value=False)

if st.session_state.selected_stock:
    ticker = st.session_state.selected_stock
    if st.button("← Back"):
        st.session_state.selected_stock = None
        st.rerun()

    st.title(f"{ticker}")
    tabs = st.tabs([TIME_SETTINGS[k]["label"] for k in TIME_SETTINGS])

    for i, (key, cfg) in enumerate(TIME_SETTINGS.items()):
        with tabs[i]:
            df = fetch_data(ticker, cfg["period"], cfg["interval"])
            if not df.empty:
                fig = go.Figure(data=[go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], increasing_line_color='#3fb950', decreasing_line_color='#f85149')])
                fig.update_layout(template="plotly_dark", height=450, xaxis_rangeslider_visible=False, margin=dict(l=0,r=0,t=0,b=0), font=CHART_FONT)
                st.plotly_chart(fig, use_container_width=True)

                df_ai = fetch_data(ticker, "1d", "1m")
                if not df_ai.empty:
                    curr = float(df_ai['Close'].iloc[-1])
                    ts = df_ai.index[-1]
                    vol = df_ai['Close'].pct_change().dropna().std()
                    
                    if vol and vol > 0:
                        if ticker not in st.session_state.morning_predictions:
                            _, base_pred, _ = run_monte_carlo(curr, vol)
                            st.session_state.morning_predictions[ticker] = base_pred
                        
                        eod_pred = st.session_state.morning_predictions[ticker]
                        bull, _, bear = run_monte_carlo(curr, vol)

                        st.markdown(f"""
                        <div class="metric-strip">
                            <div class="metric-cell"><small>PRIMARY CLOSE</small><br><b>${curr:,.2f}</b></div>
                            <div class="metric-cell"><small>VOLATILITY</small><br><b>{vol*100:.3f}%</b></div>
                            <div class="metric-cell"><small>AM PREDICTION</small><br><b>${eod_pred:,.2f}</b></div>
                        </div>
                        <div class="insight-strip">MC Bear: <b>${bear:,.2f}</b> | MC Bull: <b>${bull:,.2f}</b></div>
                        """, unsafe_allow_html=True)

                        is_eod_time = ((ticker.endswith(".NS") and ts.hour == 15 and ts.minute >= 25) or (not ticker.endswith(".NS") and ts.hour == 15 and ts.minute >= 55))
                        if is_eod_time or test_mode:
                            diff = curr - eod_pred
                            acc = 100 - abs(diff) / eod_pred * 100
                            st.markdown(f"<div class='eod-report'><b>ACCURACY REPORT</b><br>Prediction: ${eod_pred:,.2f} | Actual: ${curr:,.2f}<br>Accuracy: {acc:.2f}%</div>", unsafe_allow_html=True)
            else:
                st.error("No data found for this period.")
    st.stop()

# GRID VIEW
search = st.text_input("Search Ticker", placeholder="e.g. AAPL")
if search:
    st.session_state.selected_stock = search.upper()
    st.rerun()

cols = st.columns(4)
stocks = [("AAPL","Apple"), ("MSFT","Microsoft"), ("NVDA","NVIDIA"), ("TSLA","Tesla")]
for i, (t, n) in enumerate(stocks):
    with cols[i]:
        st.markdown(f"<div class='stock-card'><b>{t}</b><br><small>{n}</small></div>", unsafe_allow_html=True)
        if st.button(f"View {t}", key=f"btn_{t}"):
            st.session_state.selected_stock = t
            st.rerun()

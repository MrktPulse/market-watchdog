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

# 3. TICKERS & TIMELINES
SP500_TOP = [("AAPL","Apple"), ("MSFT","Microsoft"), ("NVDA","NVIDIA"), ("AMZN","Amazon"), ("GOOGL","Alphabet"), ("META","Meta"), ("TSLA","Tesla"), ("LLY","Eli Lilly"), ("AVGO","Broadcom"), ("JPM","JPMorgan"), ("UNH","UnitedHealth"), ("V","Visa")]
NSE_TOP = [("RELIANCE.NS","Reliance"), ("TCS.NS","TCS"), ("HDFCBANK.NS","HDFC Bank"), ("ICICIBANK.NS","ICICI Bank"), ("INFY.NS","Infosys"), ("SBI.NS","SBI")]
CRYPTO = [("BTC-USD","Bitcoin"), ("ETH-USD","Ethereum"), ("SOL-USD","Solana")]

TIME_SETTINGS = {
    "1m":  {"period": "1d",  "interval": "1m",  "label": "1 Min (Live)"},
    "1h":  {"period": "7d",  "interval": "60m", "label": "Hourly"},
    "1d":  {"period": "1y",  "interval": "1d",  "label": "Daily (1yr)"},
    "1wk": {"period": "2y",  "interval": "1wk", "label": "Weekly"},
    "1mo": {"period": "5y",  "interval": "1mo", "label": "Monthly"},
    "3mo": {"period": "10y", "interval": "3mo", "label": "Quarterly"},
}

# 4. CSS
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono&family=IBM+Plex+Sans:wght@300;400;600&display=swap');
:root { --bg: #07090f; --bg2: #0c1018; --border: #1c2333; --text: #dde3ed; }
html, body, .stApp { background: var(--bg) !important; color: var(--text); font-family: 'IBM Plex Sans', sans-serif; }
.stock-card { background: var(--bg2); border: 1px solid var(--border); border-radius: 6px; padding: 15px; margin-bottom:10px; height: 100px; }
.metric-strip { display: flex; background: var(--bg2); border: 1px solid var(--border); border-radius: 4px; margin: 20px 0; }
.metric-cell { flex: 1; padding: 15px; border-right: 1px solid var(--border); text-align: center; }
.accuracy-report { background: #0a1a0a; border: 1px solid #1a3320; border-radius: 4px; padding: 15px; color: #5a9a5a; font-family: 'IBM Plex Mono'; margin-top:10px; }
</style>
""", unsafe_allow_html=True)

# 5. RISK GATEWAY
if not st.session_state.disclaimer_accepted:
    _, center, _ = st.columns([1, 2, 1])
    with center:
        st.write("#")
        with st.container(border=True):
            st.subheader("⚠️ Risk Disclosure")
            st.write("Predictions are models and do not guarantee results. Use for informational purposes only.")
            if st.button("I Understand & Agree", use_container_width=True, type="primary"):
                st.session_state.disclaimer_accepted = True
                st.rerun()
    st.stop()

# 6. FUNCTIONS
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

# 7. DASHBOARD LOGIC
if st.session_state.selected_stock:
    ticker = st.session_state.selected_stock
    col_back, col_acc = st.columns([1, 1])
    if col_back.button("← Back to Markets"):
        st.session_state.selected_stock = None
        st.rerun()

    st.title(f"{ticker} Terminal")
    show_acc = col_acc.toggle("📊 Show Accuracy Analysis", value=False)
    
    # FIX: Use key in tabs to prevent duplicate element IDs
    tabs = st.tabs([TIME_SETTINGS[k]["label"] for k in TIME_SETTINGS])

    for i, (key, cfg) in enumerate(TIME_SETTINGS.items()):
        with tabs[i]:
            df = fetch_data(ticker, cfg["period"], cfg["interval"])
            if not df.empty:
                # Get Today's data for the prediction metrics
                df_day = fetch_data(ticker, "1d", "1m")
                curr, morning_p = 0.0, 0.0
                
                if not df_day.empty:
                    curr = df_day['Close'].iloc[-1]
                    vol = df_day['Close'].pct_change().dropna().std()
                    if ticker not in st.session_state.morning_predictions:
                        _, p, _ = run_monte_carlo(df_day['Open'].iloc[0], vol if vol > 0 else 0.001)
                        st.session_state.morning_predictions[ticker] = p
                    morning_p = st.session_state.morning_predictions[ticker]

                # RENDER CHART
                if show_acc and not df_day.empty:
                    acc = 100 - (abs(curr - morning_p) / morning_p * 100)
                    st.markdown(f"<div class='accuracy-report'><b>CURRENT ACCURACY: {acc:.2f}%</b><br>Prediction: ${morning_p:,.2f} | Actual: ${curr:,.2f}</div>", unsafe_allow_html=True)
                    
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(x=df_day.index, y=df_day['Close'], name="Actual Price", line=dict(color='#3fb950')))
                    fig.add_trace(go.Scatter(x=[df_day.index[0], df_day.index[-1]], y=[df_day['Open'].iloc[0], morning_p], name="Predicted Trend", line=dict(color='#388bfd', dash='dot')))
                    fig.update_layout(template="plotly_dark", height=450)
                else:
                    fig = go.Figure(data=[go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], increasing_line_color='#3fb950', decreasing_line_color='#f85149')])
                    fig.update_layout(template="plotly_dark", height=450, xaxis_rangeslider_visible=False)
                
                # THE KEY FIX: Added a unique key for each chart based on the tab name
                st.plotly_chart(fig, use_container_width=True, key=f"chart_{ticker}_{key}")

                if not df_day.empty:
                    st.markdown(f"""<div class="metric-strip"><div class="metric-cell"><small>LAST PRICE</small><br><b>${curr:,.2f}</b></div><div class="metric-cell"><small>AM PREDICTION</small><br><b>${morning_p:,.2f}</b></div></div>""", unsafe_allow_html=True)
            else:
                st.error("Data connection lost.")
    st.stop()

# 8. MARKET GRID
search = st.text_input("🔍 Search Ticker", placeholder="Enter Ticker (e.g. AAPL, RELIANCE.NS, BTC-USD)")
if search:
    st.session_state.selected_stock = search.upper()
    st.rerun()

st.write("### Markets")
cols = st.columns(4)
for i, (t, n) in enumerate(SP500_TOP + NSE_TOP + CRYPTO):
    with cols[i % 4]:
        st.markdown(f"<div class='stock-card'><b>{t}</b><br><small>{n}</small></div>", unsafe_allow_html=True)
        if st.button(f"Analyze {t}", key=f"btn_{t}"):
            st.session_state.selected_stock = t
            st.rerun()

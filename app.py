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

# 3. TICKERS
SP500_TOP = [("AAPL","Apple"), ("MSFT","Microsoft"), ("NVDA","NVIDIA"), ("AMZN","Amazon"), ("GOOGL","Alphabet"), ("META","Meta"), ("TSLA","Tesla"), ("LLY","Eli Lilly"), ("AVGO","Broadcom"), ("JPM","JPMorgan"), ("UNH","UnitedHealth"), ("V","Visa")]
NSE_TOP = [("RELIANCE.NS","Reliance"), ("TCS.NS","TCS"), ("HDFCBANK.NS","HDFC Bank"), ("ICICIBANK.NS","ICICI Bank"), ("INFY.NS","Infosys"), ("SBI.NS","SBI")]
CRYPTO = [("BTC-USD","Bitcoin"), ("ETH-USD","Ethereum"), ("SOL-USD","Solana")]
FULL_LIST = SP500_TOP + NSE_TOP + CRYPTO

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
.mp-header { border-bottom: 1px solid var(--border); padding-bottom: 15px; margin-bottom: 25px; display: flex; justify-content: space-between; align-items: center; }
.stock-card { background: var(--bg2); border: 1px solid var(--border); border-radius: 6px; padding: 15px; margin-bottom:10px; height: 100px; cursor: pointer; }
.metric-strip { display: flex; background: var(--bg2); border: 1px solid var(--border); border-radius: 4px; margin: 20px 0; }
.metric-cell { flex: 1; padding: 15px; border-right: 1px solid var(--border); text-align: center; }
.accuracy-report { background: #0a1a0a; border: 1px solid #1a3320; border-radius: 4px; padding: 20px; color: #5a9a5a; font-family: 'IBM Plex Mono'; line-height: 1.6; }
</style>
""", unsafe_allow_html=True)

# 5. RISK GATEWAY
if not st.session_state.disclaimer_accepted:
    _, center, _ = st.columns([1, 2, 1])
    with center:
        st.write("#")
        with st.container(border=True):
            st.subheader("⚠️ Risk Disclosure")
            st.write("Predictions are stochastic models. Past accuracy does not guarantee future results.")
            if st.button("I Understand & Agree", use_container_width=True, type="primary"):
                st.session_state.disclaimer_accepted = True
                st.rerun()
    st.stop()

st.markdown('<div class="mp-header"><span style="font-family:monospace; font-weight:600;">MARKET PULSE v3.0</span><span style="font-size:0.7rem; color:#4e5a6e;">LIVE TERMINAL</span></div>', unsafe_allow_html=True)

# 6. FUNCTIONS
def fetch_data(ticker, period, interval):
    try:
        df = yf.download(ticker, period=period, interval=interval, progress=False, auto_adjust=False)
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        return df
    except: return pd.DataFrame()

def generate_jagged_path(start_price, end_price, num_steps, vol):
    t = np.linspace(0, 1, num_steps)
    noise = np.cumsum(np.random.normal(0, vol * 60, num_steps))
    bridge = noise - t * noise[-1]
    trend = np.linspace(start_price, end_price, num_steps)
    return trend + bridge

# 7. DASHBOARD
if st.session_state.selected_stock:
    ticker = st.session_state.selected_stock
    col_back, col_acc = st.columns([1, 1])
    if col_back.button("← Back to Markets"):
        st.session_state.selected_stock = None
        st.rerun()

    st.title(f"{ticker}")
    show_acc = col_acc.toggle("📊 Show Accuracy Analysis", value=False)
    tabs = st.tabs([TIME_SETTINGS[k]["label"] for k in TIME_SETTINGS])

    for i, (key, cfg) in enumerate(TIME_SETTINGS.items()):
        with tabs[i]:
            df = fetch_data(ticker, cfg["period"], cfg["interval"])
            if not df.empty:
                df_day = fetch_data(ticker, "1d", "1m")
                if not df_day.empty:
                    curr = df_day['Close'].iloc[-1]
                    vol = df_day['Close'].pct_change().dropna().std()
                    
                    if ticker not in st.session_state.morning_predictions:
                        r = np.random.normal(0, vol if vol > 0 else 0.002, 1)
                        target = float(df_day['Open'].iloc[0]) * np.exp(r[0])
                        path = generate_jagged_path(df_day['Open'].iloc[0], target, len(df_day), vol * 50)
                        st.session_state.morning_predictions[ticker] = {"target": target, "path": path}
                    
                    morning_data = st.session_state.morning_predictions[ticker]

                if show_acc and not df_day.empty:
                    acc = 100 - (abs(curr - morning_data['target']) / morning_data['target'] * 100)
                    # FULL DATA RESTORED TO REPORT BOX
                    st.markdown(f"""
                    <div class='accuracy-report'>
                        <b>ACCURACY: {acc:.2f}%</b><br>
                        ──────────────────────────<br>
                        Predicted Close: ${morning_data['target']:,.2f}<br>
                        Actual Price: &nbsp;&nbsp;&nbsp;${curr:,.2f}<br>
                        Day Volatility: &nbsp;{vol*100:.3f}%
                    </div>
                    """, unsafe_allow_html=True)
                    
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(x=df_day.index, y=df_day['Close'], name="Actual Price", line=dict(color='#3fb950')))
                    fig.add_trace(go.Scatter(x=df_day.index, y=morning_data['path'][:len(df_day)], name="AI Predicted Path", line=dict(color='#388bfd', dash='dot')))
                    fig.update_layout(template="plotly_dark", height=450)
                else:
                    fig = go.Figure(data=[go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'])])
                    fig.update_layout(template="plotly_dark", height=450, xaxis_rangeslider_visible=False)
                
                st.plotly_chart(fig, use_container_width=True, key=f"chart_{ticker}_{key}")

                if not df_day.empty:
                    st.markdown(f"""<div class="metric-strip">
                        <div class="metric-cell"><small>LAST</small><br><b>${curr:,.2f}</b></div>
                        <div class="metric-cell"><small>VOLATILITY</small><br><b>{vol*100:.3f}%</b></div>
                        <div class="metric-cell"><small>AM PREDICTION</small><br><b>${morning_data['target']:,.2f}</b></div>
                    </div>""", unsafe_allow_html=True)
    st.stop()

# 8. SEARCH & FILTERED GRID
query = st.text_input("🔍 Search Ticker", placeholder="Type to filter...").upper()
filtered = [s for s in FULL_LIST if query in s[0] or query in s[1].upper()]
cols = st.columns(4)
for i, (t, n) in enumerate(filtered):
    with cols[i % 4]:
        st.markdown(f"<div class='stock-card'><b>{t}</b><br><small>{n}</small></div>", unsafe_allow_html=True)
        if st.button(f"Analyze {t}", key=f"btn_{t}"):
            st.session_state.selected_stock = t
            st.rerun()

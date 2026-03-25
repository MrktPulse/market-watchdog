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
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@300;400;600&display=swap');
:root { --bg: #07090f; --bg2: #0c1018; --border: #1c2333; --text: #dde3ed; }
html, body, .stApp { background: var(--bg) !important; color: var(--text); font-family: 'IBM Plex Sans', sans-serif; }
.stock-card { background: var(--bg2); border: 1px solid var(--border); border-radius: 6px; padding: 15px; margin-bottom:10px; }
.metric-strip { display: flex; background: var(--bg2); border: 1px solid var(--border); border-radius: 4px; margin: 20px 0; }
.metric-cell { flex: 1; padding: 15px; border-right: 1px solid var(--border); text-align: center; }
</style>
""", unsafe_allow_html=True)

# 5. RISK GATEWAY (FIXED: Uses standard Streamlit elements for clickability)
if not st.session_state.disclaimer_accepted:
    _, center_col, _ = st.columns([1, 2, 1])
    with center_col:
        st.write("#") # Spacer
        st.write("#")
        with st.container(border=True):
            st.subheader("⚠️ Risk Disclosure")
            st.write("Financial markets involve significant risk. All predictions are generated via Monte Carlo statistical simulations and do not guarantee future results.")
            st.info("By clicking below, you acknowledge that this is a simulation tool and not financial advice.")
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
    if st.button("← Back to Markets"):
        st.session_state.selected_stock = None
        st.rerun()

    st.title(f"{ticker}")
    tabs = st.tabs([TIME_SETTINGS[k]["label"] for k in TIME_SETTINGS])

    for i, (key, cfg) in enumerate(TIME_SETTINGS.items()):
        with tabs[i]:
            df = fetch_data(ticker, cfg["period"], cfg["interval"])
            if not df.empty:
                fig = go.Figure(data=[go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], increasing_line_color='#3fb950', decreasing_line_color='#f85149')])
                fig.update_layout(template="plotly_dark", height=500, xaxis_rangeslider_visible=False, margin=dict(l=0,r=0,t=0,b=0))
                st.plotly_chart(fig, use_container_width=True)
                
                df_day = fetch_data(ticker, "1d", "1m")
                if not df_day.empty:
                    curr = df_day['Close'].iloc[-1]
                    vol = df_day['Close'].pct_change().std()
                    if vol > 0:
                        if ticker not in st.session_state.morning_predictions:
                            _, pred, _ = run_monte_carlo(curr, vol)
                            st.session_state.morning_predictions[ticker] = pred
                        
                        p = st.session_state.morning_predictions[ticker]
                        st.markdown(f"""<div class="metric-strip"><div class="metric-cell"><small>LAST</small><br><b>${curr:,.2f}</b></div><div class="metric-cell"><small>AM PREDICTION</small><br><b>${p:,.2f}</b></div></div>""", unsafe_allow_html=True)
    st.stop()

# 8. MARKET GRID
st.write("### S&P 500 Leaders")
cols = st.columns(4)
for i, (t, n) in enumerate(SP500_TOP):
    with cols[i % 4]:
        st.markdown(f"<div class='stock-card'><b>{t}</b><br><small>{n}</small></div>", unsafe_allow_html=True)
        if st.button(f"View {t}", key=f"sp_{t}"):
            st.session_state.selected_stock = t
            st.rerun()

st.write("### NSE & Crypto")
cols2 = st.columns(4)
for i, (t, n) in enumerate(NSE_TOP + CRYPTO):
    with cols2[i % 4]:
        st.markdown(f"<div class='stock-card'><b>{t}</b><br><small>{n}</small></div>", unsafe_allow_html=True)
        if st.button(f"View {t}", key=f"nse_{t}"):
            st.session_state.selected_stock = t
            st.rerun()

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh
from datetime import datetime

# --- 1. SYSTEM CONFIG ---
st_autorefresh(interval=15 * 1000, key="market_heartbeat")
st.set_page_config(
    page_title="Market Pulse | Institutional Dashboard",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 2. MEMORY BANK ---
if 'morning_predictions' not in st.session_state:
    st.session_state.morning_predictions = {}

# --- 3. PROFESSIONAL CSS ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@300;400;500;600&display=swap');

    html, body, .stApp {
        background-color: #080c14;
        color: #c9d1d9;
        font-family: 'IBM Plex Sans', sans-serif;
    }

    /* Header */
    .dashboard-header {
        border-bottom: 1px solid #1a2332;
        padding-bottom: 18px;
        margin-bottom: 24px;
    }
    .dashboard-title {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 1.3rem;
        font-weight: 500;
        color: #e6edf3;
        letter-spacing: 0.05em;
        margin: 0;
    }
    .dashboard-subtitle {
        font-size: 0.8rem;
        color: #4a5568;
        font-family: 'IBM Plex Mono', monospace;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        margin-top: 4px;
    }

    /* Metric cards */
    div[data-testid="stMetricValue"] {
        font-size: 1.4rem;
        color: #e6edf3;
        font-weight: 500;
        font-family: 'IBM Plex Mono', monospace;
    }
    div[data-testid="stMetricLabel"] {
        font-size: 0.72rem;
        color: #4a5568;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        font-family: 'IBM Plex Sans', sans-serif;
    }
    div[data-testid="stMetricDelta"] {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 0.85rem;
    }

    /* Chart container */
    .chart-block {
        background: #0d1117;
        border: 1px solid #1a2332;
        border-radius: 4px;
        padding: 20px 24px;
        margin-bottom: 24px;
    }
    .chart-ticker-label {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 1.05rem;
        font-weight: 500;
        color: #e6edf3;
        letter-spacing: 0.04em;
        margin-bottom: 4px;
    }
    .chart-section-label {
        font-family: 'IBM Plex Sans', sans-serif;
        font-size: 0.72rem;
        color: #4a5568;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin-bottom: 16px;
    }
    .metrics-row {
        background: #0a0f18;
        border: 1px solid #1a2332;
        border-radius: 4px;
        padding: 16px 20px;
        margin-top: 12px;
    }
    .insight-box {
        background: #0a0f18;
        border-left: 2px solid #2a6496;
        border-radius: 0 4px 4px 0;
        padding: 12px 16px;
        margin-top: 12px;
        font-size: 0.88rem;
        color: #8b98a9;
        font-family: 'IBM Plex Sans', sans-serif;
    }
    .insight-box b {
        color: #c9d1d9;
        font-weight: 500;
    }
    .eod-report {
        background: #0d1a0d;
        border: 1px solid #1a3320;
        border-radius: 4px;
        padding: 14px 18px;
        margin-top: 12px;
        font-size: 0.88rem;
        color: #7fbf7f;
        font-family: 'IBM Plex Mono', monospace;
    }

    /* Controls */
    .stMultiSelect div[data-baseweb="select"],
    .stSelectbox div[data-baseweb="select"] {
        background-color: #0d1117;
        border: 1px solid #1a2332;
        border-radius: 4px;
        font-family: 'IBM Plex Sans', sans-serif;
        font-size: 0.88rem;
    }
    label[data-testid="stWidgetLabel"] {
        font-size: 0.72rem;
        color: #4a5568;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        font-family: 'IBM Plex Sans', sans-serif;
        font-weight: 400;
    }

    /* Divider */
    hr { border-color: #1a2332; }

    /* Remove Streamlit default padding */
    .block-container { padding-top: 2rem; }

    /* Caption */
    .stCaption { color: #4a5568; font-size: 0.78rem; }
    </style>
    """, unsafe_allow_html=True)

# --- 4. CORE ANALYTICS ENGINE ---
def run_monte_carlo(current_price, vol, days=1):
    price_raw = float(current_price)
    sims = 1000
    daily_returns = np.random.normal(0, vol, (sims, days))
    price_paths = price_raw * np.exp(np.cumsum(daily_returns, axis=1))
    return np.percentile(price_paths[:, -1], [95, 50, 5])

# --- 5. EXPANDED TICKER UNIVERSE ---

# Top 100 S&P 500 components
sp500_tickers = [
    "AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "GOOG", "META", "BRK-B", "LLY", "AVGO",
    "TSLA", "JPM", "UNH", "XOM", "V", "MA", "JNJ", "PG", "COST", "HD",
    "MRK", "ABBV", "CVX", "CRM", "BAC", "NFLX", "KO", "ORCL", "WMT", "PEP",
    "AMD", "TMO", "MCD", "CSCO", "ABT", "ACN", "ADBE", "LIN", "DHR", "TXN",
    "WFC", "NEE", "PM", "NKE", "INTC", "MS", "UNP", "IBM", "INTU", "RTX",
    "HON", "QCOM", "CAT", "AMGN", "SPGI", "GS", "BLK", "LOW", "ELV", "ISRG",
    "T", "VRTX", "PLD", "MDT", "DE", "AXP", "SYK", "TJX", "ADI", "GILD",
    "REGN", "CB", "BKNG", "CI", "MMC", "CVS", "PGR", "BMY", "LRCX", "BSX",
    "EOG", "SO", "ETN", "MDLZ", "NOC", "MU", "PANW", "KLAC", "ZTS", "CME",
    "GE", "DUK", "WM", "ITW", "FI", "APH", "HCA", "AON", "SHW", "USB"
]

# Top 50 NSE stocks
nse_symbols = [
    "RELIANCE", "TCS", "HDFCBANK", "ICICIBANK", "INFY", "BHARTIARTL", "SBI",
    "LIC", "ITC", "HINDUNILVR", "KOTAKBANK", "AXISBANK", "LT", "BAJFINANCE",
    "HCLTECH", "MARUTI", "ASIANPAINT", "ULTRACEMCO", "WIPRO", "SUNPHARMA",
    "TATAMOTORS", "TITAN", "M&M", "BAJAJFINSV", "POWERGRID", "NTPC", "ONGC",
    "TATASTEEL", "ADANIENT", "JSWSTEEL", "NESTLEIND", "TECHM", "DRREDDY",
    "HINDALCO", "DIVISLAB", "CIPLA", "GRASIM", "COALINDIA", "BRITANNIA",
    "INDUSINDBK", "SBILIFE", "HDFCLIFE", "APOLLOHOSP", "EICHERMOT", "TATACONSUM",
    "HEROMOTOCO", "BPCL", "SHREECEM", "UPL", "BAJAJ-AUTO"
]
nse_tickers = [f"{s}.NS" for s in nse_symbols]

all_tickers = sorted(sp500_tickers) + sorted(nse_tickers) + ["BTC-USD", "ETH-USD", "GC=F", "CL=F"]

# --- 6. HEADER ---
st.markdown("""
<div class="dashboard-header">
    <div class="dashboard-title">Market Pulse</div>
    <div class="dashboard-subtitle">Global Intelligence Terminal &nbsp;|&nbsp; Live Data</div>
</div>
""", unsafe_allow_html=True)

# --- 7. CONTROLS ---
col_search, col_time = st.columns([3, 1])
with col_search:
    selected_tickers = st.multiselect(
        "Search Markets",
        options=all_tickers,
        default=["NVDA", "RELIANCE.NS"]
    )
with col_time:
    view_mode = st.selectbox(
        "Chart Timeframe",
        [
            "1-Minute (Intraday)",
            "Hourly",
            "Daily",
            "Weekly",
            "Monthly",
            "Quarterly",
            "Yearly"
        ]
    )

st.write("---")

if not selected_tickers:
    st.info("Select at least one instrument from the search bar to begin analysis.")
    st.stop()

# --- 8. CORRECTED TIME MAPPINGS ---
# period = total history window | interval = each candle's duration
time_settings = {
    "1-Minute (Intraday)": {"period": "1d",   "interval": "1m"},
    "Hourly":              {"period": "7d",   "interval": "60m"},
    "Daily":               {"period": "1y",   "interval": "1d"},
    "Weekly":              {"period": "2y",   "interval": "1wk"},
    "Monthly":             {"period": "5y",   "interval": "1mo"},
    "Quarterly":           {"period": "10y",  "interval": "3mo"},
    "Yearly":              {"period": "max",  "interval": "3mo"},   # yfinance has no 1y interval; use 3mo over max range
}

# Shared font config for all Plotly charts — keeps candle labels identical
CHART_FONT = dict(family="'IBM Plex Mono', 'Courier New', monospace", size=11, color="#8b98a9")

# --- 9. MAIN RENDER LOOP ---
for t in selected_tickers:
    st.markdown("<div class='chart-block'>", unsafe_allow_html=True)

    # Clean display name
    display_name = t.replace(".NS", "").replace("-USD", "/USD").replace("=F", "")
    st.markdown(f"<div class='chart-ticker-label'>{display_name}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='chart-section-label'>{t} &nbsp;·&nbsp; {view_mode}</div>", unsafe_allow_html=True)

    c_period   = time_settings[view_mode]["period"]
    c_interval = time_settings[view_mode]["interval"]

    df_chart = yf.download(t, period=c_period, interval=c_interval, progress=False)
    df_ai    = yf.download(t, period="1d", interval="1m", progress=False)

    if not df_chart.empty and not df_ai.empty:
        if isinstance(df_chart.columns, pd.MultiIndex):
            df_chart.columns = df_chart.columns.get_level_values(0)
        if isinstance(df_ai.columns, pd.MultiIndex):
            df_ai.columns = df_ai.columns.get_level_values(0)

        # --- CANDLESTICK CHART ---
        fig = go.Figure(data=[go.Candlestick(
            x=df_chart.index,
            open=df_chart['Open'],
            high=df_chart['High'],
            low=df_chart['Low'],
            close=df_chart['Close'],
            increasing_line_color='#3fb950',
            increasing_fillcolor='#1a3a20',
            decreasing_line_color='#f85149',
            decreasing_fillcolor='#3a1a1a',
            line=dict(width=1),
        )])

        # Remove weekend/after-hours gaps for intraday/hourly
        if view_mode in ["1-Minute (Intraday)", "Hourly"]:
            fig.update_xaxes(
                rangebreaks=[
                    dict(bounds=["sat", "mon"]),
                    dict(bounds=[16, 9.5], pattern="hour")
                ]
            )

        fig.update_layout(
            template="plotly_dark",
            height=420,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(8,12,20,1)',
            margin=dict(l=0, r=0, t=8, b=0),
            xaxis_rangeslider_visible=False,
            font=CHART_FONT,
            xaxis=dict(
                gridcolor='#1a2332',
                linecolor='#1a2332',
                tickfont=CHART_FONT,
                showgrid=True,
            ),
            yaxis=dict(
                gridcolor='#1a2332',
                linecolor='#1a2332',
                tickfont=CHART_FONT,
                showgrid=True,
                side='right',
            ),
            hoverlabel=dict(
                bgcolor='#0d1117',
                bordercolor='#1a2332',
                font=CHART_FONT,
            )
        )
        st.plotly_chart(fig, use_container_width=True)

        # --- INTRADAY METRICS & PREDICTION ---
        open_price     = float(df_ai['Open'].iloc[0].item())
        curr_price     = float(df_ai['Close'].iloc[-1].item())
        last_timestamp = df_ai.index[-1]

        returns = df_ai['Close'].pct_change().dropna()
        vol = returns.std()

        if not np.isnan(vol) and vol > 0:
            bull, base, bear = run_monte_carlo(curr_price, vol, days=1)

            if t not in st.session_state.morning_predictions:
                st.session_state.morning_predictions[t] = base

            expected_close = st.session_state.morning_predictions[t]
            pct_change     = ((curr_price - open_price) / open_price) * 100
            trend_word     = "advance" if expected_close > open_price else "decline"

            st.markdown("<div class='metrics-row'>", unsafe_allow_html=True)
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Open",               f"${open_price:,.2f}")
            c2.metric("Last Price",         f"${curr_price:,.2f}", f"{pct_change:+.2f}%")
            c3.metric("Predicted EOD",      f"${expected_close:,.2f}")
            c4.metric("Intraday Volatility", f"{vol*100:.3f}%")
            st.markdown("</div>", unsafe_allow_html=True)

            st.markdown(f"""
            <div class="insight-box">
                Opened at <b>${open_price:,.2f}</b>. Based on real-time volatility modelling,
                the instrument is projected to <b>{trend_word}</b> toward
                <b>${expected_close:,.2f}</b> by market close.
                Bull scenario: <b>${bull:,.2f}</b> &nbsp;|&nbsp; Bear scenario: <b>${bear:,.2f}</b>
            </div>
            """, unsafe_allow_html=True)

            # --- EOD ACCURACY REPORT ---
            is_eod = False
            if t.endswith(".NS") and last_timestamp.hour == 15 and last_timestamp.minute >= 25:
                is_eod = True
            elif not t.endswith(".NS") and last_timestamp.hour == 15 and last_timestamp.minute >= 55:
                is_eod = True

            if is_eod:
                diff     = curr_price - expected_close
                accuracy = 100 - (abs(diff) / expected_close * 100)
                st.markdown(f"""
                <div class="eod-report">
                    MARKET CLOSING REPORT — {display_name}<br><br>
                    Predicted Close &nbsp;&nbsp; {expected_close:,.2f}<br>
                    Actual Close &nbsp;&nbsp;&nbsp;&nbsp;&nbsp; {curr_price:,.2f}<br>
                    Difference &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; {diff:+,.2f}<br>
                    Model Accuracy &nbsp;&nbsp;&nbsp; {accuracy:.2f}%
                </div>
                """, unsafe_allow_html=True)
        else:
            st.caption("Awaiting sufficient intraday data...")

    else:
        st.warning(f"Market data for {t} is currently unavailable.")

    st.markdown("</div>", unsafe_allow_html=True)
    st.write("")

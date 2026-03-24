import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh

# ─────────────────────────────────────────────
# 1. PAGE CONFIG  (must be first Streamlit call)
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Market Pulse",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st_autorefresh(interval=30_000, key="market_heartbeat")

# ─────────────────────────────────────────────
# 2. SESSION STATE DEFAULTS
# ─────────────────────────────────────────────
if "disclaimer_accepted"  not in st.session_state:
    st.session_state.disclaimer_accepted  = False
if "selected_stock"       not in st.session_state:
    st.session_state.selected_stock       = None
if "morning_predictions"  not in st.session_state:
    st.session_state.morning_predictions  = {}

# ─────────────────────────────────────────────
# 3. GLOBAL CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@300;400;500;600&family=IBM+Plex+Sans:wght@300;400;500;600&display=swap');

:root {
    --bg:          #07090f;
    --bg2:         #0c1018;
    --bg3:         #111722;
    --border:      #1c2333;
    --border2:     #253045;
    --text:        #dde3ed;
    --muted:       #4e5a6e;
    --muted2:      #8493a8;
    --green:       #3fb950;
    --green-bg:    #1a3320;
    --red:         #f85149;
    --red-bg:      #3a1010;
    --blue:        #388bfd;
    --mono:        'IBM Plex Mono', 'Courier New', monospace;
    --sans:        'IBM Plex Sans', sans-serif;
}

html, body, .stApp          { background: var(--bg) !important; color: var(--text); font-family: var(--sans); }
.block-container             { padding: 2rem 2.5rem 4rem; max-width: 1600px; }
section[data-testid="stSidebar"] { display: none; }
hr                           { border-color: var(--border); margin: 1.5rem 0; }
h1,h2,h3,h4                 { font-family: var(--mono); font-weight: 500; color: var(--text); }

/* ── HEADER ── */
.mp-header {
    display: flex; align-items: baseline; gap: 14px;
    border-bottom: 1px solid var(--border);
    padding-bottom: 16px; margin-bottom: 28px;
}
.mp-logo    { font-family: var(--mono); font-size: 1.15rem; font-weight: 600;
              color: var(--text); letter-spacing: .06em; }
.mp-tagline { font-family: var(--mono); font-size: .72rem; color: var(--muted);
              letter-spacing: .12em; text-transform: uppercase; }
.mp-dot     { width: 7px; height: 7px; border-radius: 50%; background: var(--green);
              display: inline-block; margin-right: 8px;
              box-shadow: 0 0 8px var(--green);
              animation: pulse-dot 2.2s ease-in-out infinite; }
@keyframes pulse-dot { 0%,100%{opacity:1} 50%{opacity:.3} }

/* ── SECTION LABELS ── */
.section-label {
    font-family: var(--mono); font-size: .68rem; color: var(--muted);
    letter-spacing: .18em; text-transform: uppercase;
    margin-bottom: 10px; margin-top: 4px;
    border-bottom: 1px solid var(--border); padding-bottom: 8px;
}

/* ── CARD GRID ── */
.cards-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
    gap: 10px; margin-bottom: 8px;
}
.stock-card {
    background: var(--bg2); border: 1px solid var(--border);
    border-radius: 5px; padding: 12px 14px 10px;
    transition: border-color .18s, box-shadow .18s, transform .16s;
    position: relative;
}
.stock-card.up   { border-left: 2px solid var(--green); }
.stock-card.down { border-left: 2px solid var(--red);   }
.stock-card:hover {
    border-color: var(--border2);
    box-shadow: 0 0 0 1px var(--border2), 0 8px 32px rgba(0,0,0,.5);
    transform: translateY(-2px);
}
.card-symbol { font-family: var(--mono); font-size: .9rem; font-weight: 600;
               color: var(--text); letter-spacing: .04em; }
.card-name   { font-size: .7rem; color: var(--muted); margin-top: 2px;
               white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.card-price  { font-family: var(--mono); font-size: .92rem; font-weight: 500;
               color: var(--text); margin-top: 6px; }
.card-up     { font-family: var(--mono); font-size: .75rem; color: var(--green); }
.card-down   { font-family: var(--mono); font-size: .75rem; color: var(--red);   }
.card-na     { font-family: var(--mono); font-size: .75rem; color: var(--muted); }

/* ── BREADCRUMB ── */
.breadcrumb     { font-family: var(--mono); font-size: .75rem; color: var(--muted);
                  letter-spacing: .08em; margin-bottom: 18px; }
.breadcrumb span { color: var(--text); }

/* ── DETAIL HEADER ── */
.detail-header  { display: flex; align-items: baseline; gap: 16px; margin-bottom: 20px; }
.detail-symbol  { font-family: var(--mono); font-size: 1.6rem; font-weight: 600;
                  color: var(--text); letter-spacing: .04em; }

/* ── METRIC STRIP ── */
.metric-strip   { display: flex; border: 1px solid var(--border); border-radius: 4px;
                  overflow: hidden; margin-bottom: 16px; }
.metric-cell    { flex: 1; padding: 14px 18px; border-right: 1px solid var(--border);
                  background: var(--bg2); }
.metric-cell:last-child { border-right: none; }
.metric-label   { font-size: .68rem; color: var(--muted); text-transform: uppercase;
                  letter-spacing: .12em; font-family: var(--sans); margin-bottom: 6px; }
.metric-value   { font-family: var(--mono); font-size: 1rem; font-weight: 500; color: var(--text); }
.metric-value.up   { color: var(--green); }
.metric-value.down { color: var(--red); }

/* ── INSIGHT BOX ── */
.insight-strip {
    background: var(--bg2); border: 1px solid var(--border);
    border-left: 2px solid var(--blue); border-radius: 0 4px 4px 0;
    padding: 13px 18px; font-size: .85rem; color: var(--muted2);
    line-height: 1.75; font-family: var(--sans); margin-bottom: 16px;
}
.insight-strip b { color: var(--text); font-weight: 500; }

/* ── EOD REPORT ── */
.eod-report {
    background: #0a1a0a; border: 1px solid #1a3320; border-radius: 4px;
    padding: 16px 20px; font-family: var(--mono); font-size: .83rem;
    color: #5a9a5a; line-height: 2.1; margin-top: 8px;
}

/* ── BUTTONS ── */
div[data-testid="stButton"] > button {
    background: transparent !important; border: 1px solid var(--border2) !important;
    color: var(--text) !important; font-family: var(--mono) !important;
    font-size: .78rem !important; letter-spacing: .06em !important;
    border-radius: 4px !important; padding: 6px 16px !important;
    transition: background .15s, border-color .15s !important;
}
div[data-testid="stButton"] > button:hover {
    background: var(--bg3) !important; border-color: var(--muted2) !important;
}

/* ── INPUTS ── */
.stTextInput input {
    background: var(--bg2) !important; border: 1px solid var(--border) !important;
    border-radius: 4px !important; color: var(--text) !important;
    font-family: var(--mono) !important; font-size: .88rem !important;
}
label[data-testid="stWidgetLabel"] p {
    font-size: .68rem !important; color: var(--muted) !important;
    text-transform: uppercase !important; letter-spacing: .12em !important;
    font-family: var(--sans) !important;
}

/* ── TABS ── */
div[data-baseweb="tab-list"] {
    background: var(--bg2) !important; border: 1px solid var(--border) !important;
    border-radius: 4px !important; gap: 0 !important; padding: 3px !important;
}
div[data-baseweb="tab"] {
    font-family: var(--mono) !important; font-size: .76rem !important;
    color: var(--muted) !important; letter-spacing: .06em !important;
    padding: 7px 16px !important; border-radius: 3px !important;
}
div[data-baseweb="tab"][aria-selected="true"] {
    background: var(--bg3) !important; color: var(--text) !important;
}
div[data-baseweb="tab-highlight"], div[data-baseweb="tab-border"] { display: none !important; }

/* ── FOOTER ── */
.mp-footer {
    margin-top: 48px; border-top: 1px solid var(--border); padding-top: 14px;
    font-family: var(--mono); font-size: .68rem; color: var(--muted);
    letter-spacing: .08em;
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# 4. TICKER UNIVERSE
# ─────────────────────────────────────────────
SP500_TOP100 = [
    ("AAPL","Apple"),        ("MSFT","Microsoft"),   ("NVDA","NVIDIA"),
    ("AMZN","Amazon"),       ("GOOGL","Alphabet"),   ("META","Meta"),
    ("BRK-B","Berkshire"),   ("LLY","Eli Lilly"),    ("AVGO","Broadcom"),
    ("TSLA","Tesla"),        ("JPM","JPMorgan"),      ("UNH","UnitedHealth"),
    ("XOM","ExxonMobil"),    ("V","Visa"),            ("MA","Mastercard"),
    ("JNJ","J&J"),           ("PG","Procter"),        ("COST","Costco"),
    ("HD","Home Depot"),     ("MRK","Merck"),         ("ABBV","AbbVie"),
    ("CVX","Chevron"),       ("CRM","Salesforce"),    ("BAC","Bank of America"),
    ("NFLX","Netflix"),      ("KO","Coca-Cola"),      ("ORCL","Oracle"),
    ("WMT","Walmart"),       ("PEP","PepsiCo"),       ("AMD","AMD"),
    ("TMO","Thermo Fisher"), ("MCD","McDonald's"),    ("CSCO","Cisco"),
    ("ABT","Abbott"),        ("ACN","Accenture"),     ("ADBE","Adobe"),
    ("LIN","Linde"),         ("DHR","Danaher"),       ("TXN","Texas Inst."),
    ("WFC","Wells Fargo"),   ("NEE","NextEra"),       ("PM","Philip Morris"),
    ("NKE","Nike"),          ("INTC","Intel"),        ("MS","Morgan Stanley"),
    ("UNP","Union Pacific"), ("IBM","IBM"),           ("INTU","Intuit"),
    ("RTX","Raytheon"),      ("HON","Honeywell"),     ("QCOM","Qualcomm"),
    ("CAT","Caterpillar"),   ("AMGN","Amgen"),        ("SPGI","S&P Global"),
    ("GS","Goldman Sachs"),  ("BLK","BlackRock"),     ("LOW","Lowe's"),
    ("ELV","Elevance"),      ("ISRG","Intuitive Surg."),("T","AT&T"),
    ("VRTX","Vertex"),       ("PLD","Prologis"),      ("MDT","Medtronic"),
    ("DE","Deere"),          ("AXP","Amex"),          ("SYK","Stryker"),
    ("TJX","TJX Co."),       ("ADI","Analog Dev."),   ("GILD","Gilead"),
    ("REGN","Regeneron"),    ("CB","Chubb"),          ("BKNG","Booking"),
    ("CI","Cigna"),          ("MMC","Marsh McLennan"),("CVS","CVS Health"),
    ("PGR","Progressive"),   ("BMY","Bristol-Myers"), ("LRCX","Lam Research"),
    ("BSX","Boston Sci."),   ("EOG","EOG Res."),      ("SO","Southern Co."),
    ("ETN","Eaton"),         ("MDLZ","Mondelez"),     ("NOC","Northrop"),
    ("MU","Micron"),         ("PANW","Palo Alto"),    ("KLAC","KLA Corp"),
    ("ZTS","Zoetis"),        ("CME","CME Group"),     ("GE","GE"),
    ("DUK","Duke Energy"),   ("WM","Waste Mgmt."),    ("ITW","Illinois Tool"),
    ("FI","Fiserv"),         ("APH","Amphenol"),      ("HCA","HCA Healthcare"),
    ("AON","Aon"),           ("SHW","Sherwin-W."),    ("USB","US Bancorp"),
]

NSE_TOP50 = [
    ("RELIANCE.NS","Reliance"),       ("TCS.NS","TCS"),
    ("HDFCBANK.NS","HDFC Bank"),      ("ICICIBANK.NS","ICICI Bank"),
    ("INFY.NS","Infosys"),            ("BHARTIARTL.NS","Bharti Airtel"),
    ("SBI.NS","SBI"),                 ("ITC.NS","ITC"),
    ("HINDUNILVR.NS","HUL"),          ("KOTAKBANK.NS","Kotak Bank"),
    ("LT.NS","L&T"),                  ("AXISBANK.NS","Axis Bank"),
    ("BAJFINANCE.NS","Bajaj Finance"),("HCLTECH.NS","HCL Tech"),
    ("MARUTI.NS","Maruti Suzuki"),    ("ASIANPAINT.NS","Asian Paints"),
    ("ULTRACEMCO.NS","UltraTech"),    ("WIPRO.NS","Wipro"),
    ("SUNPHARMA.NS","Sun Pharma"),    ("TATAMOTORS.NS","Tata Motors"),
    ("TITAN.NS","Titan"),             ("M&M.NS","M&M"),
    ("BAJAJFINSV.NS","Bajaj Finserv"),("POWERGRID.NS","Power Grid"),
    ("NTPC.NS","NTPC"),               ("ONGC.NS","ONGC"),
    ("TATASTEEL.NS","Tata Steel"),    ("ADANIENT.NS","Adani Ent."),
    ("JSWSTEEL.NS","JSW Steel"),      ("NESTLEIND.NS","Nestle India"),
    ("TECHM.NS","Tech Mahindra"),     ("DRREDDY.NS","Dr. Reddy's"),
    ("HINDALCO.NS","Hindalco"),       ("DIVISLAB.NS","Divi's Labs"),
    ("CIPLA.NS","Cipla"),             ("GRASIM.NS","Grasim"),
    ("COALINDIA.NS","Coal India"),    ("BRITANNIA.NS","Britannia"),
    ("INDUSINDBK.NS","IndusInd Bank"),("SBILIFE.NS","SBI Life"),
    ("HDFCLIFE.NS","HDFC Life"),      ("APOLLOHOSP.NS","Apollo Hosp."),
    ("EICHERMOT.NS","Eicher Motors"), ("TATACONSUM.NS","Tata Consumer"),
    ("HEROMOTOCO.NS","Hero MotoCorp"),("BPCL.NS","BPCL"),
    ("SHREECEM.NS","Shree Cement"),   ("UPL.NS","UPL"),
    ("BAJAJ-AUTO.NS","Bajaj Auto"),
]

CRYPTO = [
    ("BTC-USD","Bitcoin"),
    ("ETH-USD","Ethereum"),
    ("BNB-USD","BNB"),
    ("SOL-USD","Solana"),
]

# ─────────────────────────────────────────────
# 5. SHARED HELPERS
# ─────────────────────────────────────────────
CHART_FONT = dict(
    family="'IBM Plex Mono','Courier New',monospace",
    size=11, color="#4e5a6e"
)

def run_monte_carlo(current_price, vol, days=1):
    sims    = 1000
    r       = np.random.normal(0, vol, (sims, days))
    paths   = float(current_price) * np.exp(np.cumsum(r, axis=1))
    return np.percentile(paths[:, -1], [95, 50, 5])

@st.cache_data(ttl=300, show_spinner=False)
def fetch_card_data(ticker):
    try:
        df = yf.download(ticker, period="5d", interval="1h", progress=False)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        if df.empty:
            return None
        close = df["Close"].dropna()
        op    = float(df["Open"].iloc[0])
        last  = float(close.iloc[-1])
        chg   = (last - op) / op * 100
        return {"close": close.values.tolist(), "last": last, "chg": chg}
    except Exception:
        return None

@st.cache_data(ttl=60, show_spinner=False)
def fetch_detail_data(ticker, period, interval):
    try:
        df = yf.download(ticker, period=period, interval=interval, progress=False)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        return df
    except Exception:
        return pd.DataFrame()

def make_sparkline(close_vals, is_up: bool):
    color = "#3fb950" if is_up else "#f85149"
    fill  = "rgba(63,185,80,.10)" if is_up else "rgba(248,81,73,.10)"
    fig   = go.Figure(go.Scatter(
        y=close_vals, mode="lines",
        line=dict(color=color, width=1.4),
        fill="tozeroy", fillcolor=fill,
    ))
    fig.update_layout(
        height=48, margin=dict(l=0,r=0,t=0,b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        showlegend=False,
    )
    return fig

TIME_SETTINGS = {
    "1m":  {"period": "1d",  "interval": "1m",  "label": "1 Min"},
    "1h":  {"period": "7d",  "interval": "60m", "label": "Hourly"},
    "1d":  {"period": "1y",  "interval": "1d",  "label": "Daily"},
    "1wk": {"period": "2y",  "interval": "1wk", "label": "Weekly"},
    "1mo": {"period": "5y",  "interval": "1mo", "label": "Monthly"},
    "3mo": {"period": "10y", "interval": "3mo", "label": "Quarterly"},
    "max": {"period": "max", "interval": "3mo", "label": "All Time"},
}

NAME_MAP = {t: n for t, n in SP500_TOP100 + NSE_TOP50 + CRYPTO}

# ─────────────────────────────────────────────
# 6. DISCLAIMER GATE
# ─────────────────────────────────────────────
if not st.session_state.disclaimer_accepted:
    st.markdown("""
    <div style="
        position:fixed;inset:0;
        background:rgba(7,9,15,.94);
        backdrop-filter:blur(8px);
        z-index:9999;
        display:flex;align-items:center;justify-content:center;
    ">
      <div style="
          background:#0c1018;
          border:1px solid #253045;
          border-radius:6px;
          padding:44px 52px;
          max-width:540px;width:90%;
          box-shadow:0 32px 96px rgba(0,0,0,.8);
      ">
        <div style="
            font-family:'IBM Plex Mono',monospace;
            font-size:.68rem;color:#4e5a6e;
            letter-spacing:.18em;text-transform:uppercase;
            margin-bottom:10px;
        ">Market Pulse · Risk Disclosure</div>

        <div style="
            font-family:'IBM Plex Mono',monospace;
            font-size:1.05rem;font-weight:600;
            color:#dde3ed;margin-bottom:22px;
        ">Not Financial Advice</div>

        <div style="
            font-size:.87rem;color:#8493a8;
            line-height:1.85;font-family:'IBM Plex Sans',sans-serif;
            margin-bottom:30px;
        ">
          The data, charts, and projections displayed on this platform are provided
          <b style="color:#dde3ed;font-weight:500">for informational and educational
          purposes only</b>. Nothing presented here constitutes financial, investment,
          or trading advice of any kind.<br><br>
          Monte Carlo projections are statistical models and
          <b style="color:#dde3ed;font-weight:500">do not guarantee future
          performance</b>. Markets are inherently unpredictable and past performance
          is not indicative of future results.<br><br>
          Always conduct your own due diligence and consult a qualified financial
          professional before making any investment decisions.
        </div>

        <div style="
            font-size:.72rem;color:#4e5a6e;
            font-family:'IBM Plex Mono',monospace;
            margin-bottom:22px;border-top:1px solid #1c2333;padding-top:16px;
        ">
          By continuing you confirm you have read and understood this disclosure.
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    _, col_btn, _ = st.columns([2, 1, 2])
    with col_btn:
        if st.button("I Understand", key="accept_disclaimer", use_container_width=True):
            st.session_state.disclaimer_accepted = True
            st.rerun()
    st.stop()

# ─────────────────────────────────────────────
# 7. HEADER
# ─────────────────────────────────────────────
st.markdown("""
<div class="mp-header">
  <div><span class="mp-dot"></span><span class="mp-logo">Market Pulse</span></div>
  <div class="mp-tagline">Global Intelligence Terminal &nbsp;·&nbsp; Live Data</div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# 8. DETAIL VIEW
# ─────────────────────────────────────────────
if st.session_state.selected_stock is not None:
    ticker       = st.session_state.selected_stock
    clean_sym    = ticker.replace(".NS","").replace("-USD","")
    display_name = NAME_MAP.get(ticker, clean_sym)

    # Back + breadcrumb
    col_back, col_bread = st.columns([1, 8])
    with col_back:
        if st.button("← Markets", key="back_btn"):
            st.session_state.selected_stock = None
            st.rerun()
    with col_bread:
        st.markdown(
            f'<div class="breadcrumb" style="padding-top:9px">'
            f'Markets &nbsp;/&nbsp; <span>{clean_sym}</span></div>',
            unsafe_allow_html=True
        )

    st.markdown(
        f'<div class="detail-header">'
        f'  <div class="detail-symbol">{clean_sym}</div>'
        f'  <div style="font-family:var(--sans);font-size:.88rem;color:#4e5a6e">{display_name}</div>'
        f'</div>',
        unsafe_allow_html=True
    )

    # Timeframe tabs
    tf_keys   = list(TIME_SETTINGS.keys())
    tf_labels = [TIME_SETTINGS[k]["label"] for k in tf_keys]
    tabs      = st.tabs(tf_labels)

    for i, tab in enumerate(tabs):
        with tab:
            cfg      = TIME_SETTINGS[tf_keys[i]]
            df_chart = fetch_detail_data(ticker, cfg["period"], cfg["interval"])
            df_ai    = fetch_detail_data(ticker, "1d", "1m")

            if df_chart.empty:
                st.warning(f"No data available for {ticker}.")
                continue

            # Candlestick
            fig = go.Figure(data=[go.Candlestick(
                x=df_chart.index,
                open=df_chart["Open"],  high=df_chart["High"],
                low=df_chart["Low"],    close=df_chart["Close"],
                increasing_line_color="#3fb950", increasing_fillcolor="#1a3320",
                decreasing_line_color="#f85149", decreasing_fillcolor="#3a1010",
                line=dict(width=1),
            )])
            if tf_keys[i] in ("1m", "1h"):
                fig.update_xaxes(rangebreaks=[
                    dict(bounds=["sat","mon"]),
                    dict(bounds=[16, 9.5], pattern="hour"),
                ])
            fig.update_layout(
                template="plotly_dark", height=460,
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#07090f",
                margin=dict(l=0,r=0,t=10,b=0),
                xaxis_rangeslider_visible=False,
                font=CHART_FONT,
                xaxis=dict(gridcolor="#1c2333", linecolor="#1c2333",
                           tickfont=CHART_FONT, showgrid=True),
                yaxis=dict(gridcolor="#1c2333", linecolor="#1c2333",
                           tickfont=CHART_FONT, showgrid=True, side="right"),
                hoverlabel=dict(bgcolor="#0c1018", bordercolor="#1c2333", font=CHART_FONT),
            )
            st.plotly_chart(fig, use_container_width=True)

            # Intraday metrics
            if not df_ai.empty:
                op   = float(df_ai["Open"].iloc[0])
                curr = float(df_ai["Close"].iloc[-1])
                ts   = df_ai.index[-1]
                pct  = (curr - op) / op * 100
                vol  = df_ai["Close"].pct_change().dropna().std()
                up   = curr >= op
                cc   = "up" if up else "down"
                cs   = "+" if up else ""

                st.markdown(f"""
                <div class="metric-strip">
                  <div class="metric-cell">
                    <div class="metric-label">Open</div>
                    <div class="metric-value">${op:,.2f}</div>
                  </div>
                  <div class="metric-cell">
                    <div class="metric-label">Last Price</div>
                    <div class="metric-value">${curr:,.2f}</div>
                  </div>
                  <div class="metric-cell">
                    <div class="metric-label">Day Change</div>
                    <div class="metric-value {cc}">{cs}{pct:.2f}%</div>
                  </div>
                  <div class="metric-cell">
                    <div class="metric-label">Intraday Volatility</div>
                    <div class="metric-value">{vol*100:.3f}%</div>
                  </div>
                </div>
                """, unsafe_allow_html=True)

                if not np.isnan(vol) and vol > 0:
                    bull, base, bear = run_monte_carlo(curr, vol)
                    if ticker not in st.session_state.morning_predictions:
                        st.session_state.morning_predictions[ticker] = base
                    eod   = st.session_state.morning_predictions[ticker]
                    trend = "advance toward" if eod > op else "decline toward"

                    st.markdown(f"""
                    <div class="insight-strip">
                        Opened at <b>${op:,.2f}</b>. Volatility model projects the instrument
                        to <b>{trend} ${eod:,.2f}</b> by close.
                        &nbsp;&nbsp;|&nbsp;&nbsp;
                        Bull scenario: <b>${bull:,.2f}</b>
                        &nbsp;&nbsp;·&nbsp;&nbsp;
                        Bear scenario: <b>${bear:,.2f}</b>
                    </div>
                    """, unsafe_allow_html=True)

                    is_eod = (
                        (ticker.endswith(".NS") and ts.hour == 15 and ts.minute >= 25) or
                        (not ticker.endswith(".NS") and ts.hour == 15 and ts.minute >= 55)
                    )
                    if is_eod:
                        diff = curr - eod
                        acc  = 100 - abs(diff) / eod * 100
                        st.markdown(f"""
                        <div class="eod-report">
                        CLOSING REPORT — {clean_sym}<br>
                        ─────────────────────────────<br>
                        Predicted Close &nbsp;&nbsp;&nbsp; ${eod:,.2f}<br>
                        Actual Close &nbsp;&nbsp;&nbsp;&nbsp;&nbsp; ${curr:,.2f}<br>
                        Difference &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; ${diff:+,.2f}<br>
                        Model Accuracy &nbsp;&nbsp;&nbsp; {acc:.2f}%
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.caption("Awaiting sufficient intraday data.")

    st.markdown('<div class="mp-footer">Market Pulse &nbsp;·&nbsp; Data via Yahoo Finance &nbsp;·&nbsp; For informational use only. Not financial advice.</div>', unsafe_allow_html=True)
    st.stop()

# ─────────────────────────────────────────────
# 9. GRID VIEW
# ─────────────────────────────────────────────

# Search bar
col_s, _ = st.columns([2, 3])
with col_s:
    custom = st.text_input(
        "Search any ticker",
        placeholder="e.g. GOOG, INFY.NS, BTC-USD",
        key="custom_search"
    )
if custom.strip():
    st.session_state.selected_stock = custom.strip().upper()
    st.rerun()

st.write("")

def render_section(label, ticker_list):
    st.markdown(f"<div class='section-label'>{label}</div>", unsafe_allow_html=True)

    batch_size = 5
    batches    = [ticker_list[i:i+batch_size] for i in range(0, len(ticker_list), batch_size)]

    for batch in batches:
        cols = st.columns(len(batch))
        for col, (ticker, name) in zip(cols, batch):
            data      = fetch_card_data(ticker)
            clean_sym = ticker.replace(".NS","").replace("-USD","")
            with col:
                # Card header HTML
                if data:
                    up   = data["chg"] >= 0
                    cc   = "card-up" if up else "card-down"
                    cs   = "+" if up else ""
                    cls  = "up" if up else "down"
                    st.markdown(f"""
                    <div class="stock-card {cls}">
                      <div class="card-symbol">{clean_sym}</div>
                      <div class="card-name">{name}</div>
                      <div style="display:flex;justify-content:space-between;
                                  align-items:baseline;margin-top:6px">
                        <div class="card-price">${data['last']:,.2f}</div>
                        <div class="{cc}">{cs}{data['chg']:.2f}%</div>
                      </div>
                    </div>
                    """, unsafe_allow_html=True)
                    if len(data["close"]) > 3:
                        fig = make_sparkline(data["close"], data["chg"] >= 0)
                        st.plotly_chart(fig, use_container_width=True,
                                        config={"displayModeBar": False})
                else:
                    st.markdown(f"""
                    <div class="stock-card">
                      <div class="card-symbol">{clean_sym}</div>
                      <div class="card-name">{name}</div>
                      <div class="card-na" style="margin-top:6px">No data</div>
                    </div>
                    """, unsafe_allow_html=True)

                # Clickable button below each card
                if st.button(f"Analyse", key=f"btn_{ticker}", use_container_width=True):
                    st.session_state.selected_stock = ticker
                    st.rerun()

    st.write("")

render_section("S&P 500 — Top 100", SP500_TOP100)
render_section("NSE — Top 50",      NSE_TOP50)
render_section("Crypto",            CRYPTO)

st.markdown(
    '<div class="mp-footer">Market Pulse &nbsp;·&nbsp; Data via Yahoo Finance &nbsp;·&nbsp; '
    'For informational use only. Not financial advice.</div>',
    unsafe_allow_html=True
)

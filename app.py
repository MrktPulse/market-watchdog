import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh

# ══════════════════════════════════════════════════════
# 1. PAGE CONFIG — must be the very first Streamlit call
# ══════════════════════════════════════════════════════
st.set_page_config(
    page_title="Market Pulse | Terminal",
    layout="wide",
    initial_sidebar_state="collapsed",
)
st_autorefresh(interval=30_000, key="market_heartbeat")

# ══════════════════════════════════════════════════════
# 2. SESSION STATE
# ══════════════════════════════════════════════════════
for key, default in {
    "disclaimer_accepted": False,
    "selected_stock": None,
    "morning_predictions": {},
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# ══════════════════════════════════════════════════════
# 3. TICKER UNIVERSE
# ══════════════════════════════════════════════════════
SP500_TOP100 = [
    ("AAPL","Apple"),          ("MSFT","Microsoft"),      ("NVDA","NVIDIA"),
    ("AMZN","Amazon"),         ("GOOGL","Alphabet"),      ("META","Meta Platforms"),
    ("BRK-B","Berkshire H."),  ("LLY","Eli Lilly"),       ("AVGO","Broadcom"),
    ("TSLA","Tesla"),          ("JPM","JPMorgan"),         ("UNH","UnitedHealth"),
    ("XOM","ExxonMobil"),      ("V","Visa"),               ("MA","Mastercard"),
    ("JNJ","Johnson & J."),    ("PG","Procter & Gamble"), ("COST","Costco"),
    ("HD","Home Depot"),       ("MRK","Merck"),            ("ABBV","AbbVie"),
    ("CVX","Chevron"),         ("CRM","Salesforce"),       ("BAC","Bank of America"),
    ("NFLX","Netflix"),        ("KO","Coca-Cola"),         ("ORCL","Oracle"),
    ("WMT","Walmart"),         ("PEP","PepsiCo"),          ("AMD","AMD"),
    ("TMO","Thermo Fisher"),   ("MCD","McDonald's"),       ("CSCO","Cisco"),
    ("ABT","Abbott"),          ("ACN","Accenture"),        ("ADBE","Adobe"),
    ("LIN","Linde"),           ("DHR","Danaher"),          ("TXN","Texas Instruments"),
    ("WFC","Wells Fargo"),     ("NEE","NextEra Energy"),   ("PM","Philip Morris"),
    ("NKE","Nike"),            ("INTC","Intel"),           ("MS","Morgan Stanley"),
    ("UNP","Union Pacific"),   ("IBM","IBM"),              ("INTU","Intuit"),
    ("RTX","Raytheon"),        ("HON","Honeywell"),        ("QCOM","Qualcomm"),
    ("CAT","Caterpillar"),     ("AMGN","Amgen"),           ("SPGI","S&P Global"),
    ("GS","Goldman Sachs"),    ("BLK","BlackRock"),        ("LOW","Lowe's"),
    ("ELV","Elevance"),        ("ISRG","Intuitive Surg."), ("T","AT&T"),
    ("VRTX","Vertex Pharma"),  ("PLD","Prologis"),         ("MDT","Medtronic"),
    ("DE","Deere & Co."),      ("AXP","American Express"), ("SYK","Stryker"),
    ("TJX","TJX Companies"),   ("ADI","Analog Devices"),   ("GILD","Gilead"),
    ("REGN","Regeneron"),      ("CB","Chubb"),             ("BKNG","Booking Holdings"),
    ("CI","Cigna"),            ("MMC","Marsh McLennan"),   ("CVS","CVS Health"),
    ("PGR","Progressive"),     ("BMY","Bristol-Myers"),    ("LRCX","Lam Research"),
    ("BSX","Boston Scientific"),("EOG","EOG Resources"),   ("SO","Southern Co."),
    ("ETN","Eaton"),           ("MDLZ","Mondelez"),        ("NOC","Northrop Grumman"),
    ("MU","Micron"),           ("PANW","Palo Alto Nets."), ("KLAC","KLA Corp"),
    ("ZTS","Zoetis"),          ("CME","CME Group"),        ("GE","GE Aerospace"),
    ("DUK","Duke Energy"),     ("WM","Waste Management"),  ("ITW","Illinois Tool"),
    ("FI","Fiserv"),           ("APH","Amphenol"),         ("HCA","HCA Healthcare"),
    ("AON","Aon"),             ("SHW","Sherwin-Williams"), ("USB","US Bancorp"),
]

NSE_TOP50 = [
    ("RELIANCE.NS","Reliance"),        ("TCS.NS","TCS"),
    ("HDFCBANK.NS","HDFC Bank"),       ("ICICIBANK.NS","ICICI Bank"),
    ("INFY.NS","Infosys"),             ("BHARTIARTL.NS","Bharti Airtel"),
    ("SBI.NS","SBI"),                  ("ITC.NS","ITC"),
    ("HINDUNILVR.NS","HUL"),           ("KOTAKBANK.NS","Kotak Bank"),
    ("LT.NS","L&T"),                   ("AXISBANK.NS","Axis Bank"),
    ("BAJFINANCE.NS","Bajaj Finance"), ("HCLTECH.NS","HCL Tech"),
    ("MARUTI.NS","Maruti Suzuki"),     ("ASIANPAINT.NS","Asian Paints"),
    ("ULTRACEMCO.NS","UltraTech"),     ("WIPRO.NS","Wipro"),
    ("SUNPHARMA.NS","Sun Pharma"),     ("TATAMOTORS.NS","Tata Motors"),
    ("TITAN.NS","Titan"),              ("M&M.NS","M&M"),
    ("BAJAJFINSV.NS","Bajaj Finserv"), ("POWERGRID.NS","Power Grid"),
    ("NTPC.NS","NTPC"),                ("ONGC.NS","ONGC"),
    ("TATASTEEL.NS","Tata Steel"),     ("ADANIENT.NS","Adani Ent."),
    ("JSWSTEEL.NS","JSW Steel"),       ("NESTLEIND.NS","Nestle India"),
    ("TECHM.NS","Tech Mahindra"),      ("DRREDDY.NS","Dr. Reddy's"),
    ("HINDALCO.NS","Hindalco"),        ("DIVISLAB.NS","Divi's Labs"),
    ("CIPLA.NS","Cipla"),              ("GRASIM.NS","Grasim"),
    ("COALINDIA.NS","Coal India"),     ("BRITANNIA.NS","Britannia"),
    ("INDUSINDBK.NS","IndusInd Bank"), ("SBILIFE.NS","SBI Life"),
    ("HDFCLIFE.NS","HDFC Life"),       ("APOLLOHOSP.NS","Apollo Hosp."),
    ("EICHERMOT.NS","Eicher Motors"),  ("TATACONSUM.NS","Tata Consumer"),
    ("HEROMOTOCO.NS","Hero MotoCorp"), ("BPCL.NS","BPCL"),
    ("SHREECEM.NS","Shree Cement"),    ("UPL.NS","UPL"),
    ("BAJAJ-AUTO.NS","Bajaj Auto"),
]

CRYPTO = [
    ("BTC-USD","Bitcoin"),
    ("ETH-USD","Ethereum"),
    ("BNB-USD","BNB"),
    ("SOL-USD","Solana"),
]

TIME_SETTINGS = {
    "1m":  {"period": "1d",  "interval": "1m",  "label": "1 Min"},
    "1h":  {"period": "7d",  "interval": "60m", "label": "Hourly"},
    "1d":  {"period": "1y",  "interval": "1d",  "label": "Daily"},
    "1wk": {"period": "2y",  "interval": "1wk", "label": "Weekly"},
    "1mo": {"period": "5y",  "interval": "1mo", "label": "Monthly"},
    "3mo": {"period": "10y", "interval": "3mo", "label": "Quarterly"},
}

NAME_MAP = {t: n for t, n in SP500_TOP100 + NSE_TOP50 + CRYPTO}

# ══════════════════════════════════════════════════════
# 4. GLOBAL CSS
# ══════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@300;400;500;600&family=IBM+Plex+Sans:wght@300;400;500;600&display=swap');

:root {
    --bg:       #06080d;
    --bg2:      #0b0f18;
    --bg3:      #10161f;
    --bg4:      #141c28;
    --border:   #192030;
    --border2:  #243040;
    --text:     #d8e0ec;
    --muted:    #48566a;
    --muted2:   #7a8ba0;
    --green:    #2ea84a;
    --green2:   #3dd163;
    --greenbg:  rgba(46,168,74,.08);
    --red:      #d93025;
    --red2:     #f05545;
    --redbg:    rgba(217,48,37,.08);
    --blue:     #2d7dd2;
    --blue2:    #4d9de0;
    --mono:     'IBM Plex Mono', monospace;
    --sans:     'IBM Plex Sans', sans-serif;
}

/* ── BASE ── */
html, body, .stApp            { background: var(--bg) !important; color: var(--text); font-family: var(--sans); }
.block-container               { padding: 1.8rem 2.2rem 4rem !important; max-width: 1640px; }
section[data-testid="stSidebar"] { display: none !important; }
hr                             { border-color: var(--border) !important; }
h1,h2,h3                      { font-family: var(--mono); color: var(--text); }

/* ── HEADER ── */
.mp-header {
    display: flex; align-items: center; justify-content: space-between;
    border-bottom: 1px solid var(--border);
    padding-bottom: 14px; margin-bottom: 26px;
}
.mp-brand   { display: flex; align-items: center; gap: 10px; }
.mp-dot     {
    width: 8px; height: 8px; border-radius: 50%;
    background: var(--green2);
    box-shadow: 0 0 10px var(--green2), 0 0 20px rgba(61,209,99,.3);
    animation: livepulse 2s ease-in-out infinite;
}
@keyframes livepulse { 0%,100%{opacity:1;transform:scale(1)} 50%{opacity:.4;transform:scale(.8)} }
.mp-title   { font-family: var(--mono); font-size: 1rem; font-weight: 600;
              letter-spacing: .1em; color: var(--text); text-transform: uppercase; }
.mp-sub     { font-family: var(--mono); font-size: .65rem; color: var(--muted);
              letter-spacing: .15em; text-transform: uppercase; }

/* ── DISCLAIMER OVERLAY ── */
.disc-overlay {
    position: fixed; inset: 0;
    background: rgba(6,8,13,.96);
    backdrop-filter: blur(10px);
    z-index: 9999;
    display: flex; align-items: center; justify-content: center;
}
.disc-box {
    background: var(--bg2);
    border: 1px solid var(--border2);
    border-top: 2px solid var(--blue2);
    border-radius: 6px;
    padding: 46px 52px;
    max-width: 560px; width: 92%;
    box-shadow: 0 40px 100px rgba(0,0,0,.85);
}

/* ── SECTION HEADER ── */
.section-hdr {
    display: flex; align-items: center; gap: 12px;
    border-bottom: 1px solid var(--border);
    padding-bottom: 10px; margin: 28px 0 16px;
}
.section-hdr-label {
    font-family: var(--mono); font-size: .68rem; font-weight: 500;
    color: var(--muted); letter-spacing: .18em; text-transform: uppercase;
}
.section-hdr-count {
    font-family: var(--mono); font-size: .65rem; color: var(--muted);
    background: var(--bg3); border: 1px solid var(--border);
    border-radius: 20px; padding: 2px 9px;
}

/* ── STOCK CARDS ── */
.scard {
    background: var(--bg2);
    border: 1px solid var(--border);
    border-radius: 5px;
    padding: 13px 15px 8px;
    cursor: pointer;
    transition: border-color .2s ease, box-shadow .2s ease, transform .18s ease, background .2s ease;
    overflow: hidden;
    position: relative;
}
.scard::before {
    content: '';
    position: absolute; inset: 0;
    background: radial-gradient(ellipse at 50% 0%, rgba(45,125,210,.06) 0%, transparent 70%);
    opacity: 0; transition: opacity .25s;
    pointer-events: none;
}
.scard:hover {
    border-color: var(--border2);
    box-shadow: 0 0 0 1px var(--border2),
                0 12px 40px rgba(0,0,0,.55),
                0 0 20px rgba(45,125,210,.06);
    transform: translateY(-3px);
    background: var(--bg3);
}
.scard:hover::before { opacity: 1; }
.scard:active        { transform: translateY(-1px); }
.scard.up   { border-left: 2px solid var(--green); }
.scard.down { border-left: 2px solid var(--red);   }
.scard.neu  { border-left: 2px solid var(--border2); }

.sc-symbol  { font-family: var(--mono); font-size: .88rem; font-weight: 600;
              color: var(--text); letter-spacing: .04em; line-height: 1; }
.sc-name    { font-size: .68rem; color: var(--muted); margin-top: 3px;
              white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.sc-row     { display: flex; justify-content: space-between; align-items: baseline;
              margin-top: 7px; }
.sc-price   { font-family: var(--mono); font-size: .9rem; font-weight: 500; color: var(--text); }
.sc-chg.up  { font-family: var(--mono); font-size: .74rem; color: var(--green2); }
.sc-chg.dn  { font-family: var(--mono); font-size: .74rem; color: var(--red2);   }
.sc-chg.na  { font-family: var(--mono); font-size: .74rem; color: var(--muted);  }
.sc-nodata  { font-family: var(--mono); font-size: .7rem; color: var(--muted);
              margin-top: 14px; padding-bottom: 4px; }

/* ── DETAIL VIEW ── */
.dv-breadcrumb { font-family: var(--mono); font-size: .72rem; color: var(--muted);
                 letter-spacing: .07em; margin-bottom: 16px; padding-top: 2px; }
.dv-breadcrumb span { color: var(--text); }
.dv-title      { font-family: var(--mono); font-size: 1.55rem; font-weight: 600;
                 color: var(--text); letter-spacing: .04em; }
.dv-subtitle   { font-family: var(--sans); font-size: .83rem; color: var(--muted2); margin-top: 2px; }
.dv-header     { margin-bottom: 22px; }

/* ── METRIC STRIP ── */
.mstrip        { display: flex; border: 1px solid var(--border); border-radius: 4px;
                 overflow: hidden; margin: 14px 0; }
.mcell         { flex: 1; padding: 13px 17px; border-right: 1px solid var(--border);
                 background: var(--bg2); }
.mcell:last-child { border-right: none; }
.mlabel        { font-size: .65rem; color: var(--muted); text-transform: uppercase;
                 letter-spacing: .13em; font-family: var(--sans); margin-bottom: 5px; }
.mvalue        { font-family: var(--mono); font-size: .97rem; font-weight: 500; color: var(--text); }
.mvalue.up     { color: var(--green2); }
.mvalue.dn     { color: var(--red2);   }

/* ── INSIGHT BOX ── */
.insight       { background: var(--bg2); border: 1px solid var(--border);
                 border-left: 2px solid var(--blue2);
                 border-radius: 0 4px 4px 0; padding: 12px 17px;
                 font-size: .84rem; color: var(--muted2); line-height: 1.75;
                 font-family: var(--sans); margin-bottom: 14px; }
.insight b     { color: var(--text); font-weight: 500; }

/* ── ACCURACY REPORT ── */
.acc-report    { background: #080f08; border: 1px solid #162316;
                 border-radius: 4px; padding: 15px 19px;
                 font-family: var(--mono); font-size: .81rem;
                 color: #4d8f4d; line-height: 2.1; }

/* ── SEARCH BAR ── */
.stTextInput input {
    background: var(--bg2) !important;
    border: 1px solid var(--border) !important;
    border-radius: 4px !important;
    color: var(--text) !important;
    font-family: var(--mono) !important;
    font-size: .86rem !important;
    padding: 10px 14px !important;
}
.stTextInput input:focus {
    border-color: var(--border2) !important;
    box-shadow: 0 0 0 1px var(--border2) !important;
}
label[data-testid="stWidgetLabel"] p {
    font-size: .65rem !important; color: var(--muted) !important;
    text-transform: uppercase !important; letter-spacing: .13em !important;
    font-family: var(--sans) !important;
}

/* ── BUTTONS ── */
div[data-testid="stButton"] > button {
    background: transparent !important;
    border: 1px solid var(--border2) !important;
    color: var(--muted2) !important;
    font-family: var(--mono) !important;
    font-size: .73rem !important;
    letter-spacing: .07em !important;
    border-radius: 3px !important;
    padding: 5px 14px !important;
    transition: all .15s !important;
    width: 100% !important;
}
div[data-testid="stButton"] > button:hover {
    background: var(--bg4) !important;
    border-color: var(--muted2) !important;
    color: var(--text) !important;
}

/* ── TABS ── */
div[data-baseweb="tab-list"] {
    background: var(--bg2) !important;
    border: 1px solid var(--border) !important;
    border-radius: 4px !important;
    padding: 3px !important; gap: 2px !important;
}
div[data-baseweb="tab"] {
    font-family: var(--mono) !important;
    font-size: .72rem !important;
    color: var(--muted) !important;
    letter-spacing: .06em !important;
    padding: 7px 15px !important;
    border-radius: 3px !important;
    transition: all .15s !important;
}
div[data-baseweb="tab"][aria-selected="true"] {
    background: var(--bg4) !important;
    color: var(--text) !important;
}
div[data-baseweb="tab-highlight"],
div[data-baseweb="tab-border"] { display: none !important; }

/* ── FOOTER ── */
.mp-footer {
    margin-top: 56px; border-top: 1px solid var(--border);
    padding-top: 14px; font-family: var(--mono);
    font-size: .63rem; color: var(--muted); letter-spacing: .09em;
    line-height: 1.9;
}
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════
# 5. HELPERS
# ══════════════════════════════════════════════════════
CHART_FONT = dict(family="'IBM Plex Mono','Courier New',monospace", size=11, color="#48566a")

def run_monte_carlo(current_price, vol, days=1):
    sims  = 1000
    r     = np.random.normal(0, vol, (sims, days))
    paths = float(current_price) * np.exp(np.cumsum(r, axis=1))
    return np.percentile(paths[:, -1], [95, 50, 5])

def generate_jagged_path(start, end, steps, vol):
    t      = np.linspace(0, 1, steps)
    noise  = np.cumsum(np.random.normal(0, vol * 60, steps))
    bridge = noise - t * noise[-1]
    return np.linspace(start, end, steps) + bridge

@st.cache_data(ttl=300, show_spinner=False)
def fetch_card_data(ticker: str):
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
        return {"close": close.tolist(), "last": last, "chg": chg}
    except Exception:
        return None

@st.cache_data(ttl=60, show_spinner=False)
def fetch_detail(ticker: str, period: str, interval: str):
    try:
        df = yf.download(ticker, period=period, interval=interval, progress=False)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        return df
    except Exception:
        return pd.DataFrame()

def sparkline_fig(values, is_up: bool):
    c = "#2ea84a" if is_up else "#d93025"
    f = "rgba(46,168,74,.09)" if is_up else "rgba(217,48,37,.09)"
    fig = go.Figure(go.Scatter(
        y=values, mode="lines",
        line=dict(color=c, width=1.3),
        fill="tozeroy", fillcolor=f,
    ))
    fig.update_layout(
        height=44, margin=dict(l=0,r=0,t=0,b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(visible=False), yaxis=dict(visible=False),
        showlegend=False,
    )
    return fig

def candle_fig(df, tf_key):
    fig = go.Figure(data=[go.Candlestick(
        x=df.index,
        open=df["Open"], high=df["High"],
        low=df["Low"],   close=df["Close"],
        increasing_line_color="#2ea84a", increasing_fillcolor="#122210",
        decreasing_line_color="#d93025", decreasing_fillcolor="#200e0e",
        line=dict(width=1),
    )])
    if tf_key in ("1m", "1h"):
        fig.update_xaxes(rangebreaks=[
            dict(bounds=["sat","mon"]),
            dict(bounds=[16, 9.5], pattern="hour"),
        ])
    fig.update_layout(
        template="plotly_dark", height=460,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#06080d",
        margin=dict(l=0,r=0,t=8,b=0),
        xaxis_rangeslider_visible=False,
        font=CHART_FONT,
        xaxis=dict(gridcolor="#192030", linecolor="#192030",
                   tickfont=CHART_FONT, showgrid=True),
        yaxis=dict(gridcolor="#192030", linecolor="#192030",
                   tickfont=CHART_FONT, showgrid=True, side="right"),
        hoverlabel=dict(bgcolor="#0b0f18", bordercolor="#192030", font=CHART_FONT),
    )
    return fig

def clean(ticker: str) -> str:
    return ticker.replace(".NS","").replace("-USD","")

# ══════════════════════════════════════════════════════
# 6. DISCLAIMER  (fires every fresh session)
# ══════════════════════════════════════════════════════
if not st.session_state.disclaimer_accepted:
    st.markdown("""
    <div class="disc-overlay">
      <div class="disc-box">
        <div style="font-family:'IBM Plex Mono',monospace;font-size:.62rem;
                    color:#48566a;letter-spacing:.2em;text-transform:uppercase;
                    margin-bottom:8px;">
          Market Pulse &nbsp;·&nbsp; Risk Disclosure
        </div>
        <div style="font-family:'IBM Plex Mono',monospace;font-size:1.05rem;
                    font-weight:600;color:#d8e0ec;margin-bottom:20px;
                    letter-spacing:.03em;">
          Not Financial Advice
        </div>
        <div style="font-size:.86rem;color:#7a8ba0;line-height:1.9;
                    font-family:'IBM Plex Sans',sans-serif;margin-bottom:28px;">
          The data, charts, projections, and analysis on this platform are provided
          <strong style="color:#d8e0ec;font-weight:500">for informational and
          educational purposes only</strong>. Nothing here constitutes financial,
          investment, or trading advice of any kind.<br><br>
          Monte Carlo simulations are statistical models —
          <strong style="color:#d8e0ec;font-weight:500">they do not guarantee
          future performance</strong>. Markets are inherently unpredictable.
          Past performance is not indicative of future results.<br><br>
          Always conduct your own due diligence and consult a qualified
          financial professional before making any investment decisions.
        </div>
        <div style="font-size:.68rem;color:#48566a;font-family:'IBM Plex Mono',monospace;
                    border-top:1px solid #192030;padding-top:16px;margin-bottom:20px;">
          By continuing you acknowledge you have read and understood this disclosure.
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    _, col_btn, _ = st.columns([1.9, 1, 1.9])
    with col_btn:
        if st.button("I Understand", key="disc_accept", use_container_width=True):
            st.session_state.disclaimer_accepted = True
            st.rerun()
    st.stop()

# ══════════════════════════════════════════════════════
# 7. PERSISTENT HEADER
# ══════════════════════════════════════════════════════
st.markdown("""
<div class="mp-header">
  <div class="mp-brand">
    <div class="mp-dot"></div>
    <div>
      <div class="mp-title">Market Pulse</div>
    </div>
  </div>
  <div class="mp-sub">Global Intelligence Terminal &nbsp;·&nbsp; Live Data</div>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════
# 8. DETAIL VIEW
# ══════════════════════════════════════════════════════
if st.session_state.selected_stock is not None:
    ticker = st.session_state.selected_stock
    sym    = clean(ticker)
    name   = NAME_MAP.get(ticker, sym)

    col_back, col_bc = st.columns([1, 7])
    with col_back:
        if st.button("← Markets", key="back_btn"):
            st.session_state.selected_stock = None
            st.rerun()
    with col_bc:
        st.markdown(
            f'<div class="dv-breadcrumb" style="padding-top:9px">'
            f'Markets &nbsp;/&nbsp; <span>{sym}</span></div>',
            unsafe_allow_html=True
        )

    st.markdown(
        f'<div class="dv-header">'
        f'  <div class="dv-title">{sym}</div>'
        f'  <div class="dv-subtitle">{name}</div>'
        f'</div>',
        unsafe_allow_html=True
    )

    show_acc = st.toggle("Accuracy Analysis", value=False, key="acc_toggle")

    tf_keys   = list(TIME_SETTINGS.keys())
    tf_labels = [TIME_SETTINGS[k]["label"] for k in tf_keys]
    tabs      = st.tabs(tf_labels)

    for i, tab in enumerate(tabs):
        with tab:
            tf_key   = tf_keys[i]
            cfg      = TIME_SETTINGS[tf_key]
            df_chart = fetch_detail(ticker, cfg["period"], cfg["interval"])
            df_day   = fetch_detail(ticker, "1d", "1m")

            if df_chart.empty:
                st.warning(f"No data available for {ticker}.")
                continue

            if not df_day.empty:
                op   = float(df_day["Open"].iloc[0])
                curr = float(df_day["Close"].iloc[-1])
                vol  = float(df_day["Close"].pct_change().dropna().std())

                if ticker not in st.session_state.morning_predictions:
                    r      = np.random.normal(0, vol if vol > 0 else 0.002)
                    target = op * np.exp(r)
                    path   = generate_jagged_path(op, target, len(df_day), vol * 50)
                    st.session_state.morning_predictions[ticker] = {
                        "target": target, "path": path
                    }
                mp = st.session_state.morning_predictions[ticker]

            if show_acc and not df_day.empty:
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=df_day.index, y=df_day["Close"],
                    name="Actual", mode="lines",
                    line=dict(color="#2ea84a", width=1.5),
                ))
                fig.add_trace(go.Scatter(
                    x=df_day.index,
                    y=mp["path"][:len(df_day)],
                    name="Predicted Path", mode="lines",
                    line=dict(color="#4d9de0", width=1.3, dash="dot"),
                ))
                fig.update_layout(
                    template="plotly_dark", height=460,
                    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#06080d",
                    margin=dict(l=0,r=0,t=8,b=0),
                    font=CHART_FONT,
                    xaxis=dict(gridcolor="#192030", linecolor="#192030",
                               tickfont=CHART_FONT),
                    yaxis=dict(gridcolor="#192030", linecolor="#192030",
                               tickfont=CHART_FONT, side="right"),
                    hoverlabel=dict(bgcolor="#0b0f18", bordercolor="#192030",
                                    font=CHART_FONT),
                    legend=dict(font=CHART_FONT, bgcolor="rgba(0,0,0,0)",
                                bordercolor="rgba(0,0,0,0)"),
                )
            else:
                fig = candle_fig(df_chart, tf_key)

            st.plotly_chart(fig, use_container_width=True, key=f"chart_{ticker}_{tf_key}")

            if not df_day.empty:
                pct = (curr - op) / op * 100
                up  = curr >= op
                cc  = "up" if up else "dn"
                cs  = "+" if up else ""

                st.markdown(f"""
                <div class="mstrip">
                  <div class="mcell">
                    <div class="mlabel">Open</div>
                    <div class="mvalue">${op:,.2f}</div>
                  </div>
                  <div class="mcell">
                    <div class="mlabel">Last Price</div>
                    <div class="mvalue">${curr:,.2f}</div>
                  </div>
                  <div class="mcell">
                    <div class="mlabel">Day Change</div>
                    <div class="mvalue {cc}">{cs}{pct:.2f}%</div>
                  </div>
                  <div class="mcell">
                    <div class="mlabel">Intraday Vol</div>
                    <div class="mvalue">{vol*100:.3f}%</div>
                  </div>
                  <div class="mcell">
                    <div class="mlabel">EOD Target</div>
                    <div class="mvalue">${mp['target']:,.2f}</div>
                  </div>
                </div>
                """, unsafe_allow_html=True)

                if vol > 0:
                    bull, _, bear = run_monte_carlo(curr, vol)
                    trend = "advance toward" if mp["target"] > op else "decline toward"
                    st.markdown(f"""
                    <div class="insight">
                        Opened at <b>${op:,.2f}</b>. Volatility model projects the
                        instrument to <b>{trend} ${mp['target']:,.2f}</b> by close.
                        &nbsp;&nbsp;|&nbsp;&nbsp;
                        Bull: <b>${bull:,.2f}</b> &nbsp;·&nbsp; Bear: <b>${bear:,.2f}</b>
                    </div>
                    """, unsafe_allow_html=True)

                if show_acc:
                    acc = 100 - abs(curr - mp["target"]) / mp["target"] * 100
                    st.markdown(f"""
                    <div class="acc-report">
                    ACCURACY REPORT — {sym}<br>
                    ──────────────────────────────<br>
                    Predicted Close &nbsp;&nbsp;&nbsp; ${mp['target']:,.2f}<br>
                    Actual Price &nbsp;&nbsp;&nbsp;&nbsp;&nbsp; ${curr:,.2f}<br>
                    Difference &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; ${curr - mp['target']:+,.2f}<br>
                    Day Volatility &nbsp;&nbsp;&nbsp; {vol*100:.3f}%<br>
                    Model Accuracy &nbsp;&nbsp;&nbsp; {acc:.2f}%
                    </div>
                    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="mp-footer">
      Market Pulse &nbsp;·&nbsp; Data via Yahoo Finance &nbsp;·&nbsp;
      For informational use only &nbsp;·&nbsp; Not financial advice
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# ══════════════════════════════════════════════════════
# 9. GRID VIEW
# ══════════════════════════════════════════════════════
col_srch, _ = st.columns([2, 3])
with col_srch:
    custom = st.text_input(
        "Search any ticker",
        placeholder="e.g.  GOOG   ·   INFY.NS   ·   BTC-USD",
        key="custom_search"
    )
if custom.strip():
    st.session_state.selected_stock = custom.strip().upper()
    st.rerun()

def render_section(label: str, ticker_list: list):
    count = len(ticker_list)
    st.markdown(f"""
    <div class="section-hdr">
      <span class="section-hdr-label">{label}</span>
      <span class="section-hdr-count">{count}</span>
    </div>
    """, unsafe_allow_html=True)

    COLS = 5
    for row_start in range(0, len(ticker_list), COLS):
        batch = ticker_list[row_start : row_start + COLS]
        cols  = st.columns(COLS)

        for col, (ticker, name) in zip(cols, batch):
            data = fetch_card_data(ticker)
            sym  = clean(ticker)

            with col:
                if data:
                    up   = data["chg"] >= 0
                    cls  = "up" if up else "down"
                    cchg = "up" if up else "dn"
                    sign = "+" if up else ""

                    st.markdown(f"""
                    <div class="scard {cls}">
                      <div class="sc-symbol">{sym}</div>
                      <div class="sc-name">{name}</div>
                      <div class="sc-row">
                        <div class="sc-price">${data['last']:,.2f}</div>
                        <div class="sc-chg {cchg}">{sign}{data['chg']:.2f}%</div>
                      </div>
                    </div>
                    """, unsafe_allow_html=True)

                    if len(data["close"]) > 3:
                        fig = sparkline_fig(data["close"], up)
                        st.plotly_chart(
                            fig, use_container_width=True,
                            config={"displayModeBar": False},
                            key=f"spark_{ticker}_{row_start}"
                        )
                else:
                    st.markdown(f"""
                    <div class="scard neu">
                      <div class="sc-symbol">{sym}</div>
                      <div class="sc-name">{name}</div>
                      <div class="sc-nodata">— unavailable —</div>
                    </div>
                    """, unsafe_allow_html=True)

                if st.button("Analyse", key=f"btn_{ticker}_{row_start}"):
                    st.session_state.selected_stock = ticker
                    st.rerun()

render_section("S&P 500 — Top 100", SP500_TOP100)
render_section("NSE — Top 50",      NSE_TOP50)
render_section("Crypto",            CRYPTO)

st.markdown("""
<div class="mp-footer">
  Market Pulse &nbsp;·&nbsp; Data via Yahoo Finance &nbsp;·&nbsp;
  For informational use only &nbsp;·&nbsp; Not financial advice
</div>
""", unsafe_allow_html=True)

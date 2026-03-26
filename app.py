import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from streamlit_autorefresh import st_autorefresh
from datetime import datetime, timedelta

# ══════════════════════════════════════════════════════════════════════
# 1. PAGE CONFIG
# ══════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Market Pulse | Terminal",
    layout="wide",
    initial_sidebar_state="collapsed",
)
st_autorefresh(interval=30_000, key="market_heartbeat")

# ══════════════════════════════════════════════════════════════════════
# 2. SESSION STATE
# ══════════════════════════════════════════════════════════════════════
for k, v in {
    "disclaimer_accepted": False,
    "selected_stock": None,
    "morning_predictions": {},
    "active_view": "grid",          # "grid" | "detail" | "strategy"
    "strategy_ticker": None,
    "strategy_result": None,
    "last_strat_name": None,
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ══════════════════════════════════════════════════════════════════════
# 3. TICKER UNIVERSE
# ══════════════════════════════════════════════════════════════════════
SP500_TOP100 = [
    ("AAPL","Apple"),           ("MSFT","Microsoft"),      ("NVDA","NVIDIA"),
    ("AMZN","Amazon"),          ("GOOGL","Alphabet"),      ("META","Meta Platforms"),
    ("BRK-B","Berkshire H."),   ("LLY","Eli Lilly"),       ("AVGO","Broadcom"),
    ("TSLA","Tesla"),           ("JPM","JPMorgan"),         ("UNH","UnitedHealth"),
    ("XOM","ExxonMobil"),       ("V","Visa"),               ("MA","Mastercard"),
    ("JNJ","Johnson & J."),     ("PG","Procter & Gamble"), ("COST","Costco"),
    ("HD","Home Depot"),        ("MRK","Merck"),            ("ABBV","AbbVie"),
    ("CVX","Chevron"),          ("CRM","Salesforce"),       ("BAC","Bank of America"),
    ("NFLX","Netflix"),         ("KO","Coca-Cola"),         ("ORCL","Oracle"),
    ("WMT","Walmart"),          ("PEP","PepsiCo"),          ("AMD","AMD"),
    ("TMO","Thermo Fisher"),    ("MCD","McDonald's"),       ("CSCO","Cisco"),
    ("ABT","Abbott"),           ("ACN","Accenture"),        ("ADBE","Adobe"),
    ("LIN","Linde"),            ("DHR","Danaher"),          ("TXN","Texas Instruments"),
    ("WFC","Wells Fargo"),      ("NEE","NextEra Energy"),   ("PM","Philip Morris"),
    ("NKE","Nike"),             ("INTC","Intel"),           ("MS","Morgan Stanley"),
    ("UNP","Union Pacific"),    ("IBM","IBM"),              ("INTU","Intuit"),
    ("RTX","Raytheon"),         ("HON","Honeywell"),        ("QCOM","Qualcomm"),
    ("CAT","Caterpillar"),      ("AMGN","Amgen"),           ("SPGI","S&P Global"),
    ("GS","Goldman Sachs"),     ("BLK","BlackRock"),        ("LOW","Lowe's"),
    ("ELV","Elevance"),         ("ISRG","Intuitive Surg."), ("T","AT&T"),
    ("VRTX","Vertex Pharma"),   ("PLD","Prologis"),         ("MDT","Medtronic"),
    ("DE","Deere & Co."),       ("AXP","American Express"), ("SYK","Stryker"),
    ("TJX","TJX Companies"),    ("ADI","Analog Devices"),   ("GILD","Gilead"),
    ("REGN","Regeneron"),       ("CB","Chubb"),             ("BKNG","Booking Holdings"),
    ("CI","Cigna"),             ("MMC","Marsh McLennan"),   ("CVS","CVS Health"),
    ("PGR","Progressive"),      ("BMY","Bristol-Myers"),    ("LRCX","Lam Research"),
    ("BSX","Boston Scientific"),("EOG","EOG Resources"),    ("SO","Southern Co."),
    ("ETN","Eaton"),            ("MDLZ","Mondelez"),        ("NOC","Northrop Grumman"),
    ("MU","Micron"),            ("PANW","Palo Alto Nets."), ("KLAC","KLA Corp"),
    ("ZTS","Zoetis"),           ("CME","CME Group"),        ("GE","GE Aerospace"),
    ("DUK","Duke Energy"),      ("WM","Waste Management"),  ("ITW","Illinois Tool"),
    ("FI","Fiserv"),            ("APH","Amphenol"),         ("HCA","HCA Healthcare"),
    ("AON","Aon"),              ("SHW","Sherwin-Williams"), ("USB","US Bancorp"),
]
NSE_TOP50 = [
    ("RELIANCE.NS","Reliance"),         ("TCS.NS","TCS"),
    ("HDFCBANK.NS","HDFC Bank"),        ("ICICIBANK.NS","ICICI Bank"),
    ("INFY.NS","Infosys"),              ("BHARTIARTL.NS","Bharti Airtel"),
    ("SBI.NS","SBI"),                   ("ITC.NS","ITC"),
    ("HINDUNILVR.NS","HUL"),            ("KOTAKBANK.NS","Kotak Bank"),
    ("LT.NS","L&T"),                    ("AXISBANK.NS","Axis Bank"),
    ("BAJFINANCE.NS","Bajaj Finance"),  ("HCLTECH.NS","HCL Tech"),
    ("MARUTI.NS","Maruti Suzuki"),      ("ASIANPAINT.NS","Asian Paints"),
    ("ULTRACEMCO.NS","UltraTech"),      ("WIPRO.NS","Wipro"),
    ("SUNPHARMA.NS","Sun Pharma"),      ("TATAMOTORS.NS","Tata Motors"),
    ("TITAN.NS","Titan"),               ("M&M.NS","M&M"),
    ("BAJAJFINSV.NS","Bajaj Finserv"),  ("POWERGRID.NS","Power Grid"),
    ("NTPC.NS","NTPC"),                 ("ONGC.NS","ONGC"),
    ("TATASTEEL.NS","Tata Steel"),      ("ADANIENT.NS","Adani Ent."),
    ("JSWSTEEL.NS","JSW Steel"),        ("NESTLEIND.NS","Nestle India"),
    ("TECHM.NS","Tech Mahindra"),       ("DRREDDY.NS","Dr. Reddy's"),
    ("HINDALCO.NS","Hindalco"),         ("DIVISLAB.NS","Divi's Labs"),
    ("CIPLA.NS","Cipla"),               ("GRASIM.NS","Grasim"),
    ("COALINDIA.NS","Coal India"),      ("BRITANNIA.NS","Britannia"),
    ("INDUSINDBK.NS","IndusInd Bank"),  ("SBILIFE.NS","SBI Life"),
    ("HDFCLIFE.NS","HDFC Life"),        ("APOLLOHOSP.NS","Apollo Hosp."),
    ("EICHERMOT.NS","Eicher Motors"),   ("TATACONSUM.NS","Tata Consumer"),
    ("HEROMOTOCO.NS","Hero MotoCorp"),  ("BPCL.NS","BPCL"),
    ("SHREECEM.NS","Shree Cement"),     ("UPL.NS","UPL"),
    ("BAJAJ-AUTO.NS","Bajaj Auto"),
]
CRYPTO = [
    ("BTC-USD","Bitcoin"), ("ETH-USD","Ethereum"),
    ("BNB-USD","BNB"),     ("SOL-USD","Solana"),
]
NAME_MAP = {t: n for t, n in SP500_TOP100 + NSE_TOP50 + CRYPTO}

TIME_SETTINGS = {
    "1m":  {"period": "1d",  "interval": "1m",  "label": "1 Min"},
    "1h":  {"period": "7d",  "interval": "60m", "label": "Hourly"},
    "1d":  {"period": "1y",  "interval": "1d",  "label": "Daily"},
    "1wk": {"period": "2y",  "interval": "1wk", "label": "Weekly"},
    "1mo": {"period": "5y",  "interval": "1mo", "label": "Monthly"},
    "3mo": {"period": "10y", "interval": "3mo", "label": "Quarterly"},
}

# ══════════════════════════════════════════════════════════════════════
# 4. CSS
# ══════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@300;400;500;600&family=IBM+Plex+Sans:wght@300;400;500;600&display=swap');

:root {
    --bg:      #06080d; --bg2: #0b0f18; --bg3: #10161f; --bg4: #141c28;
    --border:  #192030; --border2: #243040;
    --text:    #d8e0ec; --muted: #48566a; --muted2: #7a8ba0;
    --green:   #2ea84a; --green2: #3dd163; --greenbg: rgba(46,168,74,.08);
    --red:     #d93025; --red2:   #f05545; --redbg:   rgba(217,48,37,.08);
    --blue:    #2d7dd2; --blue2:  #4d9de0; --amber:   #d4a017; --amber2: #f0c040;
    --mono:    'IBM Plex Mono', monospace; --sans: 'IBM Plex Sans', sans-serif;
}

html, body, .stApp            { background: var(--bg) !important; color: var(--text); font-family: var(--sans); }
.block-container               { padding: 1.8rem 2.2rem 4rem !important; max-width: 1640px; }
section[data-testid="stSidebar"] { display: none !important; }
hr                             { border-color: var(--border) !important; }
h1,h2,h3                      { font-family: var(--mono); color: var(--text); }

/* ── Header ── */
.mp-header { display:flex; align-items:center; justify-content:space-between;
             border-bottom:1px solid var(--border); padding-bottom:14px; margin-bottom:26px; }
.mp-brand  { display:flex; align-items:center; gap:10px; }
.mp-dot    { width:8px; height:8px; border-radius:50%; background:var(--green2);
             box-shadow:0 0 10px var(--green2),0 0 20px rgba(61,209,99,.3);
             animation:livepulse 2s ease-in-out infinite; }
@keyframes livepulse { 0%,100%{opacity:1;transform:scale(1)} 50%{opacity:.4;transform:scale(.8)} }
.mp-title  { font-family:var(--mono); font-size:1rem; font-weight:600;
             letter-spacing:.1em; color:var(--text); text-transform:uppercase; }
.mp-sub    { font-family:var(--mono); font-size:.65rem; color:var(--muted);
             letter-spacing:.15em; text-transform:uppercase; }

/* ── Disclaimer Overlay ── */
.disc-overlay { position:fixed; inset:0; background:rgba(6,8,13,.97);
                backdrop-filter:blur(12px); z-index:9999;
                display:flex; align-items:center; justify-content:center; }
.disc-box { background:var(--bg2); border:1px solid var(--border2);
            border-top:3px solid var(--blue2); border-radius:6px;
            padding:46px 52px; max-width:580px; width:92%;
            box-shadow:0 40px 120px rgba(0,0,0,.9); }
.disc-title { font-family:var(--mono); font-size:1rem; font-weight:600;
              letter-spacing:.12em; color:var(--text); text-transform:uppercase;
              margin-bottom:6px; }
.disc-sub   { font-family:var(--mono); font-size:.62rem; color:var(--blue2);
              letter-spacing:.15em; text-transform:uppercase; margin-bottom:28px; }
.disc-body  { font-size:.84rem; color:var(--muted2); line-height:1.85;
              font-family:var(--sans); margin-bottom:28px; }
.disc-body b { color:var(--text); font-weight:500; }
.disc-warn  { background:rgba(217,48,37,.08); border:1px solid rgba(217,48,37,.18);
              border-radius:4px; padding:12px 16px; font-family:var(--mono);
              font-size:.72rem; color:var(--red2); margin-bottom:28px; line-height:1.7; }

/* ── Stock Cards with Sparkline ── */
.scard { background:var(--bg2); border:1px solid var(--border); border-radius:5px;
         padding:13px 15px 6px; cursor:pointer; position:relative; overflow:hidden;
         transition:border-color .2s,box-shadow .2s,transform .18s,background .2s; }
.scard::before { content:''; position:absolute; inset:0;
                 background:radial-gradient(ellipse at 50% 0%,rgba(45,125,210,.06) 0%,transparent 70%);
                 opacity:0; transition:opacity .25s; pointer-events:none; }
.scard:hover   { border-color:var(--border2);
                 box-shadow:0 0 0 1px var(--border2),0 12px 40px rgba(0,0,0,.55);
                 transform:translateY(-3px); background:var(--bg3); }
.scard:hover::before { opacity:1; }
.scard.up   { border-left:2px solid var(--green); }
.scard.down { border-left:2px solid var(--red); }
.scard.neu  { border-left:2px solid var(--border2); }

.sc-header  { display:flex; justify-content:space-between; align-items:flex-start; }
.sc-symbol  { font-family:var(--mono); font-size:.88rem; font-weight:600;
              color:var(--text); letter-spacing:.04em; }
.sc-badge   { font-family:var(--mono); font-size:.6rem; padding:2px 7px;
              border-radius:20px; font-weight:500; }
.sc-badge.up   { background:var(--greenbg); color:var(--green2); border:1px solid rgba(61,209,99,.2); }
.sc-badge.dn   { background:var(--redbg);   color:var(--red2);   border:1px solid rgba(240,85,69,.2); }
.sc-badge.neu  { background:var(--bg3);     color:var(--muted);  border:1px solid var(--border); }
.sc-name    { font-size:.67rem; color:var(--muted); margin-top:3px;
              white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.sc-row     { display:flex; justify-content:space-between; align-items:baseline; margin-top:5px; }
.sc-price   { font-family:var(--mono); font-size:.92rem; font-weight:500; color:var(--text); }
.sc-chg.up  { font-family:var(--mono); font-size:.74rem; color:var(--green2); }
.sc-chg.dn  { font-family:var(--mono); font-size:.74rem; color:var(--red2); }
.sc-nodata  { font-family:var(--mono); font-size:.7rem; color:var(--muted); margin-top:14px; }

/* ── Pulsing sparkline container ── */
.spark-wrap { margin-top:6px; border-radius:3px; overflow:hidden;
              animation:sparkpulse 3s ease-in-out infinite; }
@keyframes sparkpulse {
  0%,100% { opacity:1; }
  50%     { opacity:.7; }
}
.spark-wrap.up   { box-shadow: 0 0 8px rgba(46,168,74,.15); }
.spark-wrap.down { box-shadow: 0 0 8px rgba(217,48,37,.15); }

/* ── Detail View ── */
.dv-breadcrumb { font-family:var(--mono); font-size:.72rem; color:var(--muted);
                 letter-spacing:.07em; margin-bottom:16px; padding-top:2px; }
.dv-breadcrumb span { color:var(--text); }
.dv-title  { font-family:var(--mono); font-size:1.55rem; font-weight:600;
             color:var(--text); letter-spacing:.04em; }
.dv-subtitle { font-family:var(--sans); font-size:.83rem; color:var(--muted2);
               margin-top:2px; margin-bottom:20px; }

.mstrip  { display:flex; border:1px solid var(--border); border-radius:4px;
           overflow:hidden; margin:14px 0; }
.mcell   { flex:1; padding:13px 17px; border-right:1px solid var(--border); background:var(--bg2); }
.mcell:last-child { border-right:none; }
.mlabel  { font-size:.65rem; color:var(--muted); text-transform:uppercase;
           letter-spacing:.13em; font-family:var(--sans); margin-bottom:5px; }
.mvalue  { font-family:var(--mono); font-size:.97rem; font-weight:500; color:var(--text); }
.mvalue.up    { color:var(--green2); }
.mvalue.dn    { color:var(--red2); }
.mvalue.amber { color:var(--amber2); }

.insight     { background:var(--bg2); border:1px solid var(--border);
               border-left:2px solid var(--blue2); border-radius:0 4px 4px 0;
               padding:12px 17px; font-size:.84rem; color:var(--muted2);
               line-height:1.75; font-family:var(--sans); margin-bottom:14px; }
.insight b   { color:var(--text); font-weight:500; }
.insight.warn { border-left-color:var(--amber2); }
.insight.good { border-left-color:var(--green2); }
.insight.bad  { border-left-color:var(--red2); }

.prob-box    { background:var(--bg2); border:1px solid var(--border); border-radius:4px;
               padding:16px 20px; margin-bottom:14px; }
.prob-title  { font-family:var(--mono); font-size:.68rem; color:var(--muted);
               text-transform:uppercase; letter-spacing:.15em; margin-bottom:12px; }
.prob-row    { display:flex; justify-content:space-between; align-items:center;
               padding:6px 0; border-bottom:1px solid var(--border); }
.prob-row:last-child { border-bottom:none; }
.prob-label  { font-family:var(--sans); font-size:.8rem; color:var(--muted2); }
.prob-val    { font-family:var(--mono); font-size:.88rem; font-weight:500; }

/* ── Strategy ── */
.strat-card  { background:var(--bg2); border:1px solid var(--border); border-radius:5px;
               padding:16px 18px; margin-bottom:0; cursor:pointer;
               transition:border-color .2s,transform .15s; }
.strat-card:hover { border-color:var(--border2); transform:translateY(-2px); }
.strat-title { font-family:var(--mono); font-size:.88rem; font-weight:600;
               color:var(--text); margin-bottom:4px; }
.strat-desc  { font-size:.75rem; color:var(--muted2); line-height:1.6; }
.strat-badge { display:inline-block; font-family:var(--mono); font-size:.62rem;
               padding:2px 8px; border-radius:20px; margin-top:8px;
               text-transform:uppercase; letter-spacing:.1em; }
.strat-badge.momentum { background:rgba(77,157,224,.12);  color:var(--blue2);  border:1px solid rgba(77,157,224,.2); }
.strat-badge.reversal { background:rgba(240,196,64,.1);   color:var(--amber2); border:1px solid rgba(240,196,64,.2); }
.strat-badge.trend    { background:rgba(61,209,99,.1);    color:var(--green2); border:1px solid rgba(61,209,99,.2); }
.strat-badge.swing    { background:rgba(240,85,69,.1);    color:var(--red2);   border:1px solid rgba(240,85,69,.2); }

.trade-table { width:100%; border-collapse:collapse; font-family:var(--mono);
               font-size:.78rem; margin-top:12px; }
.trade-table th { border-bottom:1px solid var(--border2); padding:8px 12px;
                  color:var(--muted); text-transform:uppercase; letter-spacing:.1em;
                  font-size:.65rem; text-align:left; font-weight:400; background:var(--bg3); }
.trade-table td { padding:9px 12px; border-bottom:1px solid var(--border); color:var(--text); }
.trade-table tr:hover td { background:var(--bg3); }
.td-profit { color:var(--green2); }
.td-loss   { color:var(--red2); }

.eod-report   { background:var(--bg2); border:1px solid var(--border);
                border-top:2px solid var(--blue2); border-radius:4px;
                padding:20px 24px; font-family:var(--mono); font-size:.82rem;
                line-height:2.1; color:var(--muted2); }
.eod-report b { color:var(--text); font-weight:500; }
.eod-report .profit { color:var(--green2); }
.eod-report .loss   { color:var(--red2); }

/* ── Streamlit overrides ── */
.stTextInput input, .stNumberInput input {
    background:var(--bg2) !important; border:1px solid var(--border) !important;
    border-radius:4px !important; color:var(--text) !important;
    font-family:var(--mono) !important; font-size:.86rem !important; }
.stTextInput input:focus, .stNumberInput input:focus {
    border-color:var(--border2) !important; box-shadow:0 0 0 1px var(--border2) !important; }
label[data-testid="stWidgetLabel"] p {
    font-size:.65rem !important; color:var(--muted) !important;
    text-transform:uppercase !important; letter-spacing:.13em !important;
    font-family:var(--sans) !important; }
div[data-testid="stButton"] > button {
    background:transparent !important; border:1px solid var(--border2) !important;
    color:var(--muted2) !important; font-family:var(--mono) !important;
    font-size:.73rem !important; letter-spacing:.07em !important;
    border-radius:3px !important; padding:5px 14px !important;
    transition:all .15s !important; }
div[data-testid="stButton"] > button:hover {
    background:var(--bg4) !important; border-color:var(--muted2) !important;
    color:var(--text) !important; }
div[data-baseweb="tab-list"] { background:var(--bg2) !important;
    border:1px solid var(--border) !important; border-radius:4px !important;
    padding:3px !important; gap:2px !important; }
div[data-baseweb="tab"] { font-family:var(--mono) !important; font-size:.72rem !important;
    color:var(--muted) !important; letter-spacing:.06em !important;
    padding:7px 15px !important; border-radius:3px !important; }
div[data-baseweb="tab"][aria-selected="true"] { background:var(--bg4) !important; color:var(--text) !important; }
div[data-baseweb="tab-highlight"], div[data-baseweb="tab-border"] { display:none !important; }
.stSelectbox div[data-baseweb="select"] > div {
    background:var(--bg2) !important; border:1px solid var(--border) !important;
    border-radius:4px !important; color:var(--text) !important;
    font-family:var(--mono) !important; font-size:.84rem !important; }

/* ── Section Headers ── */
.section-hdr { display:flex; align-items:center; gap:12px;
               border-bottom:1px solid var(--border); padding-bottom:10px; margin:28px 0 16px; }
.section-hdr-label { font-family:var(--mono); font-size:.68rem; font-weight:500;
                     color:var(--muted); letter-spacing:.18em; text-transform:uppercase; }
.section-hdr-count { font-family:var(--mono); font-size:.65rem; color:var(--muted);
                     background:var(--bg3); border:1px solid var(--border);
                     border-radius:20px; padding:2px 9px; }

/* ── Footer ── */
.mp-footer { margin-top:56px; border-top:1px solid var(--border); padding-top:14px;
             font-family:var(--mono); font-size:.63rem; color:var(--muted); letter-spacing:.09em; }
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════
# 5. DATA HELPERS
# ══════════════════════════════════════════════════════════════════════
CHART_FONT = dict(family="'IBM Plex Mono','Courier New',monospace", size=11, color="#48566a")

def clean(ticker: str) -> str:
    return ticker.replace(".NS","").replace("-USD","")

def asset_class(ticker: str) -> str:
    if "USD" in ticker:
        return "crypto"
    if ".NS" in ticker:
        return "nse"
    return "sp500"

@st.cache_data(ttl=300, show_spinner=False)
def fetch_card_data(ticker: str):
    try:
        df = yf.download(ticker, period="5d", interval="1h", progress=False, auto_adjust=False)
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        if df.empty: return None
        close = df["Close"].dropna()
        op    = float(df["Open"].iloc[0])
        last  = float(close.iloc[-1])
        chg   = (last - op) / op * 100
        return {"close": close.tolist(), "last": last, "chg": chg}
    except Exception:
        return None

@st.cache_data(ttl=60, show_spinner=False)
def fetch_ohlcv(ticker: str, period: str, interval: str) -> pd.DataFrame:
    try:
        df = yf.download(ticker, period=period, interval=interval,
                         progress=False, auto_adjust=False)
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        return df
    except Exception:
        return pd.DataFrame()

@st.cache_data(ttl=300, show_spinner=False)
def fetch_5mo(ticker: str) -> pd.DataFrame:
    return fetch_ohlcv(ticker, "5mo", "1d")

# ══════════════════════════════════════════════════════════════════════
# 6. HONEST PREDICTION ENGINE
# ══════════════════════════════════════════════════════════════════════
VOL_CAPS = {"crypto": 0.08, "nse": 0.04, "sp500": 0.03}

def honest_eod_prediction(ticker: str, df_day: pd.DataFrame):
    returns  = df_day["Close"].pct_change().dropna()
    n_obs    = len(returns)
    vol_raw  = float(returns.std()) if n_obs > 1 else 0.01

    ac       = asset_class(ticker)
    cap      = VOL_CAPS[ac]
    vol_used = min(vol_raw, cap)

    if n_obs < 30:     confidence = "low"
    elif n_obs < 120:  confidence = "medium"
    else:              confidence = "high"

    n_sims   = 10_000
    day_open = float(df_day["Open"].iloc[0])
    draws    = np.random.normal(0, vol_used, n_sims)
    eod_dist = day_open * np.exp(draws)

    bull, median, bear = np.percentile(eod_dist, [95, 50, 5])

    warning = None
    if vol_raw > cap:
        warning = (
            f"Raw intraday volatility ({vol_raw*100:.2f}%) exceeds the "
            f"{ac.upper()} asset-class cap ({cap*100:.0f}%). "
            f"Cap applied — prediction range intentionally narrowed."
        )
    if confidence == "low":
        warning = (warning or "") + (
            " Prediction confidence is LOW — treat this range as indicative only."
        )

    return {
        "median": median, "bull": bull, "bear": bear,
        "vol_raw": vol_raw, "vol_used": vol_used,
        "confidence": confidence, "n_sims": n_sims,
        "warning": warning, "day_open": day_open,
    }

# ══════════════════════════════════════════════════════════════════════
# 7. TECHNICAL INDICATORS
# ══════════════════════════════════════════════════════════════════════
def compute_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain  = delta.clip(lower=0).rolling(period).mean()
    loss  = (-delta.clip(upper=0)).rolling(period).mean()
    rs    = gain / loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))

def compute_macd(series: pd.Series, fast=12, slow=26, signal=9):
    ema_fast    = series.ewm(span=fast, adjust=False).mean()
    ema_slow    = series.ewm(span=slow, adjust=False).mean()
    macd_line   = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    hist        = macd_line - signal_line
    return macd_line, signal_line, hist

def compute_bollinger(series: pd.Series, period=20, std_dev=2):
    mid   = series.rolling(period).mean()
    sigma = series.rolling(period).std()
    return mid + std_dev * sigma, mid, mid - std_dev * sigma

# ══════════════════════════════════════════════════════════════════════
# 8. STRATEGY BACKTESTER  — FIXED
# ══════════════════════════════════════════════════════════════════════
STRATEGIES = {
    "RSI Mean Reversion": {
        "desc": "Buy when RSI drops below 30 (oversold). Sell when RSI rises above 70 (overbought).",
        "badge": "reversal",
        "params": {"rsi_period": 14, "oversold": 30, "overbought": 70},
        "logic": "rsi",
    },
    "MACD Crossover": {
        "desc": "Buy when MACD line crosses above Signal line. Sell on the reverse cross.",
        "badge": "trend",
        "params": {"fast": 12, "slow": 26, "signal": 9},
        "logic": "macd",
    },
    "Bollinger Band Breakout": {
        "desc": "Buy when price touches the lower band. Sell at the middle band or upper band.",
        "badge": "momentum",
        "params": {"period": 20, "std_dev": 2},
        "logic": "bollinger",
    },
    "Dual Moving Average": {
        "desc": "Buy when the 10-day SMA crosses above the 30-day SMA. Sell on the Death Cross.",
        "badge": "trend",
        "params": {"fast_ma": 10, "slow_ma": 30},
        "logic": "dma",
    },
}

# ── FIX: entry/exit reasons now take logic + strategy_key (not params) ──
def _entry_reason(logic: str, strategy_key: str) -> str:
    p = STRATEGIES[strategy_key]["params"]
    if logic == "rsi":       return f"RSI < {p['oversold']}"
    if logic == "macd":      return "MACD Bullish Cross"
    if logic == "bollinger": return "Touched Lower Band"
    if logic == "dma":       return "Golden Cross"
    return ""

def _exit_reason(logic: str, strategy_key: str) -> str:
    p = STRATEGIES[strategy_key]["params"]
    if logic == "rsi":       return f"RSI > {p['overbought']}"
    if logic == "macd":      return "MACD Bearish Cross"
    if logic == "bollinger": return "Touched Mid Band"
    if logic == "dma":       return "Death Cross"
    return ""

def backtest(df: pd.DataFrame, strategy_key: str, capital: float) -> dict:
    if df.empty or len(df) < 35:
        return {"error": "Insufficient historical data (need at least 35 trading days)."}

    close  = df["Close"].squeeze()
    dates  = df.index
    logic  = STRATEGIES[strategy_key]["logic"]
    params = STRATEGIES[strategy_key]["params"]

    buy_signals  = pd.Series(False, index=dates)
    sell_signals = pd.Series(False, index=dates)

    if logic == "rsi":
        rsi          = compute_rsi(close, params["rsi_period"])
        buy_signals  = (rsi < params["oversold"])   & (rsi.shift(1) >= params["oversold"])
        sell_signals = (rsi > params["overbought"]) & (rsi.shift(1) <= params["overbought"])
    elif logic == "macd":
        macd, sig, _ = compute_macd(close, params["fast"], params["slow"], params["signal"])
        buy_signals  = (macd > sig) & (macd.shift(1) <= sig.shift(1))
        sell_signals = (macd < sig) & (macd.shift(1) >= sig.shift(1))
    elif logic == "bollinger":
        upper, mid, lower = compute_bollinger(close, params["period"], params["std_dev"])
        buy_signals  = (close < lower) & (close.shift(1) >= lower.shift(1))
        sell_signals = (close > mid)   & (close.shift(1) <= mid.shift(1))
    elif logic == "dma":
        sma_fast     = close.rolling(params["fast_ma"]).mean()
        sma_slow     = close.rolling(params["slow_ma"]).mean()
        buy_signals  = (sma_fast > sma_slow) & (sma_fast.shift(1) <= sma_slow.shift(1))
        sell_signals = (sma_fast < sma_slow) & (sma_fast.shift(1) >= sma_slow.shift(1))

    trades, equity_curve = [], [capital]
    cash, position = capital, 0.0
    entry_price, entry_date = None, None

    for i, date in enumerate(dates):
        px = float(close.iloc[i])
        if buy_signals.iloc[i] and position == 0 and cash > 0:
            position, entry_price, entry_date, cash = cash / px, px, date, 0.0
        elif sell_signals.iloc[i] and position > 0:
            proceeds = position * px
            trades.append({
                "entry_date":  entry_date.strftime("%d %b %Y"),
                "exit_date":   date.strftime("%d %b %Y"),
                "entry_price": entry_price,
                "exit_price":  px,
                "shares":      round(position, 4),
                "pnl":         proceeds - (position * entry_price),
                "pnl_pct":     (px - entry_price) / entry_price * 100,
                "why_entry":   _entry_reason(logic, strategy_key),   # ← FIXED
                "why_exit":    _exit_reason(logic, strategy_key),    # ← FIXED
            })
            cash, position = proceeds, 0.0
        equity_curve.append(cash + position * px)

    final_price = float(close.iloc[-1])
    if position > 0:
        trades.append({
            "entry_date":  entry_date.strftime("%d %b %Y"),
            "exit_date":   "OPEN",
            "entry_price": entry_price,
            "exit_price":  final_price,
            "shares":      round(position, 4),
            "pnl":         position * final_price - position * entry_price,
            "pnl_pct":     (final_price - entry_price) / entry_price * 100,
            "why_entry":   _entry_reason(logic, strategy_key),       # ← FIXED
            "why_exit":    "Position open",
        })

    total_value = cash + position * final_price
    n_trades    = len([t for t in trades if t["exit_date"] != "OPEN"])
    n_wins      = sum(1 for t in trades if t["pnl"] > 0 and t["exit_date"] != "OPEN")

    return {
        "trades":       trades,
        "equity_curve": equity_curve,
        "total_pnl":    total_value - capital,
        "total_pnl_pct":(total_value - capital) / capital * 100,
        "final_value":  total_value,
        "n_trades":     n_trades,
        "win_rate":     (n_wins / n_trades * 100) if n_trades > 0 else 0,
        "buy_signals":  buy_signals,
        "sell_signals": sell_signals,
        "close":        close,
        "dates":        dates,
        "capital":      capital,
        "error":        None,
    }

# ══════════════════════════════════════════════════════════════════════
# 9. CHART BUILDERS
# ══════════════════════════════════════════════════════════════════════
def sparkline_fig(values, is_up: bool):
    c = "#2ea84a" if is_up else "#d93025"
    f = "rgba(46,168,74,.12)" if is_up else "rgba(217,48,37,.12)"
    fig = go.Figure(go.Scatter(
        y=values, mode="lines",
        line=dict(color=c, width=1.6),
        fill="tozeroy", fillcolor=f,
    ))
    fig.update_layout(
        height=50,
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        showlegend=False,
    )
    return fig

def candle_fig(df: pd.DataFrame, tf_key: str) -> go.Figure:
    fig = go.Figure(data=[go.Candlestick(
        x=df.index, open=df["Open"], high=df["High"], low=df["Low"], close=df["Close"],
        increasing_line_color="#2ea84a", decreasing_line_color="#d93025",
    )])
    fig.update_layout(
        template="plotly_dark", height=460,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#06080d",
        xaxis_rangeslider_visible=False, font=CHART_FONT,
    )
    return fig

def accuracy_fig(df_day, pred):
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df_day.index, y=df_day["Close"].squeeze(),
        name="Actual", line=dict(color="#2ea84a"),
    ))
    fig.add_trace(go.Scatter(
        x=[df_day.index[0], df_day.index[-1]],
        y=[pred["day_open"], pred["median"]],
        name="Median", line=dict(color="#4d9de0", dash="dash"),
    ))
    fig.update_layout(
        template="plotly_dark", height=460,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#06080d",
        font=CHART_FONT,
    )
    return fig

def strategy_fig(result: dict, strategy_key: str) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=result["dates"], y=result["close"],
        name="Price", line=dict(color="#7a8ba0"),
    ))
    fig.add_trace(go.Scatter(
        x=result["dates"][result["buy_signals"]],
        y=result["close"][result["buy_signals"]],
        name="Buy", mode="markers",
        marker=dict(symbol="triangle-up", size=10, color="#3dd163"),
    ))
    fig.add_trace(go.Scatter(
        x=result["dates"][result["sell_signals"]],
        y=result["close"][result["sell_signals"]],
        name="Sell", mode="markers",
        marker=dict(symbol="triangle-down", size=10, color="#f05545"),
    ))
    fig.update_layout(
        template="plotly_dark", height=420,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#06080d",
        font=CHART_FONT,
    )
    return fig

def equity_fig(result: dict) -> go.Figure:
    fig = go.Figure(go.Scatter(
        y=result["equity_curve"], mode="lines",
        fill="tozeroy", line=dict(color="#3dd163"),
    ))
    fig.update_layout(
        template="plotly_dark", height=220,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#06080d",
        font=CHART_FONT, showlegend=False,
    )
    return fig


# ══════════════════════════════════════════════════════════════════════
# 11. PERSISTENT HEADER
# ══════════════════════════════════════════════════════════════════════
st.markdown(
    '<div class="mp-header">'
    '  <div class="mp-brand"><div class="mp-dot"></div>'
    '    <div><div class="mp-title">Market Pulse</div>'
    '    <div class="mp-sub">Live Terminal</div></div>'
    '  </div>'
    f' <div class="mp-sub">{datetime.now().strftime("%d %b %Y  %H:%M")}</div>'
    '</div>',
    unsafe_allow_html=True,
)

# ══════════════════════════════════════════════════════════════════════
# 12. STRATEGY VIEW
# ══════════════════════════════════════════════════════════════════════
if st.session_state.active_view == "strategy":
    ticker = st.session_state.strategy_ticker

    col_back, col_title = st.columns([1, 8])
    with col_back:
        if st.button("← Detail"):
            st.session_state.active_view = "detail"
            st.rerun()
    with col_title:
        st.markdown(f"<div class='dv-title'>{clean(ticker)} Strategy Simulator</div>", unsafe_allow_html=True)

    col_s, col_c = st.columns([2, 1])
    with col_s:
        strat_name = st.selectbox("Select Strategy", list(STRATEGIES.keys()))
    with col_c:
        capital = st.number_input("Starting Capital ($)", value=10000.0, min_value=100.0, step=500.0)

    # Strategy cards
    st.markdown('<div class="section-hdr"><span class="section-hdr-label">Strategy Library</span></div>', unsafe_allow_html=True)
    scols = st.columns(4)
    for i, (sname, smeta) in enumerate(STRATEGIES.items()):
        with scols[i]:
            selected_marker = "▶ " if sname == strat_name else ""
            st.markdown(f"""
            <div class="strat-card">
              <div class="strat-title">{selected_marker}{sname}</div>
              <div class="strat-desc">{smeta['desc']}</div>
              <span class="strat-badge {smeta['badge']}">{smeta['badge']}</span>
            </div>""", unsafe_allow_html=True)

    st.markdown("")
    if st.button("▶  Run Backtest", type="primary"):
        with st.spinner("Running simulation…"):
            df5 = fetch_5mo(ticker)
            result = backtest(df5, strat_name, capital)
            st.session_state.strategy_result = result
            st.session_state.last_strat_name = strat_name

    res = st.session_state.strategy_result
    if res:
        if res.get("error"):
            st.error(res["error"])
        else:
            # Summary metrics
            pnl_col = "up" if res["total_pnl"] >= 0 else "dn"
            pnl_sign = "+" if res["total_pnl"] >= 0 else ""
            st.markdown(f"""
            <div class="mstrip">
              <div class="mcell"><div class="mlabel">Final Value</div>
                <div class="mvalue">${res['final_value']:,.2f}</div></div>
              <div class="mcell"><div class="mlabel">Total P&L</div>
                <div class="mvalue {pnl_col}">{pnl_sign}${res['total_pnl']:,.2f} ({pnl_sign}{res['total_pnl_pct']:.2f}%)</div></div>
              <div class="mcell"><div class="mlabel">Total Trades</div>
                <div class="mvalue">{res['n_trades']}</div></div>
              <div class="mcell"><div class="mlabel">Win Rate</div>
                <div class="mvalue {'up' if res['win_rate']>=50 else 'dn'}">{res['win_rate']:.1f}%</div></div>
            </div>""", unsafe_allow_html=True)

            st.plotly_chart(strategy_fig(res, strat_name), use_container_width=True)

            st.markdown('<div class="section-hdr"><span class="section-hdr-label">Equity Curve</span></div>', unsafe_allow_html=True)
            st.plotly_chart(equity_fig(res), use_container_width=True)

            # Trade log
            if res["trades"]:
                st.markdown('<div class="section-hdr"><span class="section-hdr-label">Trade Log</span></div>', unsafe_allow_html=True)
                rows = ""
                for t in res["trades"]:
                    css = "td-profit" if t["pnl"] >= 0 else "td-loss"
                    sign = "+" if t["pnl"] >= 0 else ""
                    rows += f"""<tr>
                        <td>{t['entry_date']}</td><td>{t['exit_date']}</td>
                        <td>{t['entry_price']:.2f}</td><td>{t['exit_price']:.2f}</td>
                        <td>{t['shares']}</td>
                        <td class="{css}">{sign}${t['pnl']:.2f} ({sign}{t['pnl_pct']:.2f}%)</td>
                        <td>{t['why_entry']}</td><td>{t['why_exit']}</td>
                    </tr>"""
                st.markdown(f"""
                <table class="trade-table">
                  <thead><tr>
                    <th>Entry Date</th><th>Exit Date</th><th>Entry $</th><th>Exit $</th>
                    <th>Shares</th><th>P&L</th><th>Entry Signal</th><th>Exit Signal</th>
                  </tr></thead>
                  <tbody>{rows}</tbody>
                </table>""", unsafe_allow_html=True)
    st.stop()

# ══════════════════════════════════════════════════════════════════════
# 13. DETAIL VIEW
# ══════════════════════════════════════════════════════════════════════
if st.session_state.active_view == "detail":
    ticker = st.session_state.selected_stock
    name   = NAME_MAP.get(ticker, clean(ticker))

    col_back, col_sim = st.columns([1, 1])
    with col_back:
        if st.button("← Markets"):
            st.session_state.active_view = "grid"
            st.rerun()
    with col_sim:
        if st.button("Strategy Simulator →"):
            st.session_state.active_view = "strategy"
            st.session_state.strategy_ticker = ticker
            st.session_state.strategy_result = None
            st.rerun()

    st.markdown(f"<div class='dv-breadcrumb'>MARKETS / <span>{clean(ticker)}</span></div>", unsafe_allow_html=True)
    st.markdown(f"<div class='dv-title'>{clean(ticker)}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='dv-subtitle'>{name}</div>", unsafe_allow_html=True)

    # Time-frame tabs
    tf_tabs = st.tabs([v["label"] for v in TIME_SETTINGS.values()])
    tf_keys = list(TIME_SETTINGS.keys())

    for idx, tab in enumerate(tf_tabs):
        with tab:
            tf = tf_keys[idx]
            cfg = TIME_SETTINGS[tf]
            df_tf = fetch_ohlcv(ticker, cfg["period"], cfg["interval"])
            if not df_tf.empty:
                st.plotly_chart(candle_fig(df_tf, tf), use_container_width=True)

    # Intraday prediction
    st.markdown('<div class="section-hdr"><span class="section-hdr-label">EOD Prediction</span></div>', unsafe_allow_html=True)
    df_day = fetch_ohlcv(ticker, "1d", "1m")
    if not df_day.empty:
        if ticker not in st.session_state.morning_predictions:
            st.session_state.morning_predictions[ticker] = honest_eod_prediction(ticker, df_day)
        pred = st.session_state.morning_predictions[ticker]

        last_price = float(df_day["Close"].iloc[-1])
        delta_pct  = (last_price - pred["day_open"]) / pred["day_open"] * 100
        chg_cls    = "up" if delta_pct >= 0 else "dn"
        sign       = "+" if delta_pct >= 0 else ""

        st.markdown(f"""
        <div class="mstrip">
          <div class="mcell"><div class="mlabel">Day Open</div>
            <div class="mvalue">${pred['day_open']:,.2f}</div></div>
          <div class="mcell"><div class="mlabel">Last</div>
            <div class="mvalue">${last_price:,.2f}</div></div>
          <div class="mcell"><div class="mlabel">Change</div>
            <div class="mvalue {chg_cls}">{sign}{delta_pct:.2f}%</div></div>
          <div class="mcell"><div class="mlabel">EOD Median</div>
            <div class="mvalue">${pred['median']:,.2f}</div></div>
          <div class="mcell"><div class="mlabel">Bull / Bear</div>
            <div class="mvalue">${pred['bull']:,.2f} / ${pred['bear']:,.2f}</div></div>
          <div class="mcell"><div class="mlabel">Confidence</div>
            <div class="mvalue {'amber' if pred['confidence']=='low' else ('up' if pred['confidence']=='high' else '')}">{pred['confidence'].upper()}</div></div>
        </div>""", unsafe_allow_html=True)

        if pred["warning"]:
            st.markdown(f"<div class='insight warn'>{pred['warning']}</div>", unsafe_allow_html=True)

        st.plotly_chart(accuracy_fig(df_day, pred), use_container_width=True)
    else:
        st.markdown("<div class='insight warn'>No intraday data available for this ticker.</div>", unsafe_allow_html=True)

    st.stop()

# ══════════════════════════════════════════════════════════════════════
# 14. GRID VIEW  — with sparkline mini-charts + pulse + colour badges
# ══════════════════════════════════════════════════════════════════════
search = st.text_input("🔍  Search Ticker (e.g. AAPL, BTC-USD)", placeholder="Enter ticker symbol…").upper().strip()
if search:
    st.session_state.selected_stock = search
    st.session_state.active_view    = "detail"
    st.rerun()

def render_grid(section_label: str, tickers: list, cols_n: int = 5):
    count = len(tickers)
    st.markdown(
        f'<div class="section-hdr">'
        f'  <span class="section-hdr-label">{section_label}</span>'
        f'  <span class="section-hdr-count">{count}</span>'
        f'</div>',
        unsafe_allow_html=True,
    )
    cols = st.columns(cols_n)
    for i, (ticker, name) in enumerate(tickers):
        with cols[i % cols_n]:
            data = fetch_card_data(ticker)
            if data is None:
                st.markdown(
                    f'<div class="scard neu">'
                    f'  <div class="sc-symbol">{clean(ticker)}</div>'
                    f'  <div class="sc-name">{name}</div>'
                    f'  <div class="sc-nodata">No data</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
            else:
                chg     = data["chg"]
                is_up   = chg >= 0
                card_cls = "up" if is_up else "down"
                chg_cls  = "up" if is_up else "dn"
                sign     = "▲" if is_up else "▼"
                price_fmt = f"${data['last']:,.2f}"
                chg_fmt   = f"{sign} {abs(chg):.2f}%"

                # Header card HTML
                st.markdown(
                    f'<div class="scard {card_cls}">'
                    f'  <div class="sc-header">'
                    f'    <div>'
                    f'      <div class="sc-symbol">{clean(ticker)}</div>'
                    f'      <div class="sc-name">{name}</div>'
                    f'    </div>'
                    f'    <span class="sc-badge {chg_cls}">{chg_fmt}</span>'
                    f'  </div>'
                    f'  <div class="sc-row">'
                    f'    <span class="sc-price">{price_fmt}</span>'
                    f'  </div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

                # Pulsing sparkline rendered via Plotly (sits below the HTML card)
                spark_cls = "up" if is_up else "down"
                st.markdown(f'<div class="spark-wrap {spark_cls}">', unsafe_allow_html=True)
                st.plotly_chart(
                    sparkline_fig(data["close"], is_up),
                    use_container_width=True,
                    config={"displayModeBar": False, "staticPlot": True},
                    key=f"spark_{ticker}",
                )
                st.markdown('</div>', unsafe_allow_html=True)

                # Analyse button
                if st.button("Analyse →", key=f"btn_{ticker}"):
                    st.session_state.selected_stock = ticker
                    st.session_state.active_view    = "detail"
                    st.rerun()

render_grid("S&P 500", SP500_TOP100[:20])
render_grid("NSE Top 50", NSE_TOP50[:10])
render_grid("Crypto", CRYPTO, cols_n=4)

# ══════════════════════════════════════════════════════════════════════
# 15. FOOTER
# ══════════════════════════════════════════════════════════════════════
st.markdown(
    '<div class="mp-footer">'
    'MARKET PULSE TERMINAL &nbsp;·&nbsp; FOR EDUCATIONAL USE ONLY &nbsp;·&nbsp; '
    'NOT FINANCIAL ADVICE &nbsp;·&nbsp; DATA VIA YAHOO FINANCE'
    '</div>',
    unsafe_allow_html=True,
)

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh
from datetime import datetime

# ══════════════════════════════════════════════════════════════════════
# PAGE CONFIG  ·  2-min auto refresh
# ══════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Market Pulse",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed",
)
st_autorefresh(interval=120_000, key="pulse")

# ══════════════════════════════════════════════════════════════════════
# SESSION STATE
# ══════════════════════════════════════════════════════════════════════
for k, v in {
    "view": "home",     # home | detail
    "ticker": None,
    "predictions": {},
    "home_tab": "Markets",
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

def go_detail(t):
    st.session_state.ticker = t
    st.session_state.view   = "detail"
    st.rerun()

def go_home():
    st.session_state.view = "home"
    st.rerun()

# ══════════════════════════════════════════════════════════════════════
# TICKERS
# ══════════════════════════════════════════════════════════════════════
SP500 = [
    ("AAPL","Apple"),("MSFT","Microsoft"),("NVDA","NVIDIA"),("AMZN","Amazon"),
    ("GOOGL","Alphabet"),("META","Meta"),("TSLA","Tesla"),("JPM","JPMorgan"),
    ("V","Visa"),("MA","Mastercard"),("UNH","UnitedHealth"),("XOM","ExxonMobil"),
    ("JNJ","Johnson & J."),("PG","Procter & G."),("HD","Home Depot"),
    ("COST","Costco"),("BAC","Bank of Amer."),("NFLX","Netflix"),
    ("AMD","AMD"),("ADBE","Adobe"),
]
NSE = [
    ("RELIANCE.NS","Reliance"),("TCS.NS","TCS"),("HDFCBANK.NS","HDFC Bank"),
    ("ICICIBANK.NS","ICICI Bank"),("INFY.NS","Infosys"),("BHARTIARTL.NS","Airtel"),
    ("SBI.NS","SBI"),("ITC.NS","ITC"),("KOTAKBANK.NS","Kotak Bank"),("LT.NS","L&T"),
]
CRYPTO = [
    ("BTC-USD","Bitcoin"),("ETH-USD","Ethereum"),
    ("BNB-USD","BNB"),("SOL-USD","Solana"),
]
ALL_TICKERS = SP500 + NSE + CRYPTO
NAME_MAP = {t: n for t, n in ALL_TICKERS}

def clean(t): return t.replace(".NS","").replace("-USD","")
def aclass(t):
    if "USD" in t: return "crypto"
    if ".NS"  in t: return "nse"
    return "sp500"

TIME_TABS = {
    "1D":  ("1d",  "1m"),
    "1W":  ("7d",  "60m"),
    "1M":  ("1mo", "1d"),
    "6M":  ("6mo", "1d"),
    "1Y":  ("1y",  "1d"),
}

SCREENER_FILTERS = [
    "All Signals",
    "RSI Oversold (<30)",
    "RSI Overbought (>70)",
    "MACD Bullish Cross",
    "MACD Bearish Cross",
    "Golden Cross (SMA20>SMA50)",
    "Bollinger Squeeze",
    "High Volume (>2× avg)",
    "Near 52-Week High",
    "Near 52-Week Low",
]

# ══════════════════════════════════════════════════════════════════════
# CSS  ·  iOS-inspired: true black, glass cards, spring animations
# ══════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=JetBrains+Mono:wght@300;400;500;600&display=swap');

:root {
  /* iOS dark palette */
  --bg:          #000000;
  --s1:          #1c1c1e;
  --s2:          #2c2c2e;
  --s3:          #3a3a3c;
  --sep:         rgba(84,84,88,0.55);
  --sep-solid:   #38383a;

  /* Text */
  --t1: #ffffff;
  --t2: #aeaeb2;
  --t3: #636366;

  /* Accents */
  --blue:   #0a84ff;
  --green:  #30d158;
  --red:    #ff453a;
  --amber:  #ffd60a;
  --orange: #ff9f0a;
  --purple: #bf5af2;

  /* Transparent fills */
  --green-fill: rgba(48,209,88,.12);
  --red-fill:   rgba(255,69,58,.12);
  --blue-fill:  rgba(10,132,255,.12);
  --amber-fill: rgba(255,214,10,.10);

  /* Type */
  --font: 'Outfit', -apple-system, system-ui, sans-serif;
  --mono: 'JetBrains Mono', ui-monospace, monospace;

  /* Geometry */
  --r-sm: 8px;
  --r-md: 12px;
  --r-lg: 16px;
  --r-xl: 22px;

  --spring: cubic-bezier(0.34,1.56,0.64,1);
  --ease:   cubic-bezier(0.25,0.46,0.45,0.94);
}

/* ─── Global ─── */
html,body,.stApp { background: var(--bg) !important; color: var(--t1); font-family: var(--font); }
.block-container  { padding: 1.6rem 2rem 5rem !important; max-width: 1560px; }
section[data-testid="stSidebar"] { display: none !important; }
hr { border-color: var(--sep-solid) !important; margin: 20px 0 !important; }

/* ─── Header ─── */
.pulse-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 0 0 18px; border-bottom: 1px solid var(--sep-solid); margin-bottom: 24px;
}
.pulse-logo { display: flex; align-items: center; gap: 10px; }
.pulse-dot  {
  width: 9px; height: 9px; border-radius: 50%; background: var(--green);
  box-shadow: 0 0 12px var(--green), 0 0 24px rgba(48,209,88,.35);
  animation: breathe 2.4s ease-in-out infinite;
}
@keyframes breathe { 0%,100%{opacity:1;transform:scale(1)} 50%{opacity:.5;transform:scale(.75)} }
.pulse-name { font-size: 1rem; font-weight: 700; letter-spacing: .06em;
              text-transform: uppercase; color: var(--t1); }
.pulse-time { font-family: var(--mono); font-size: .65rem; color: var(--t3);
              letter-spacing: .1em; }

/* ─── Section label ─── */
.sec-label {
  font-size: .65rem; font-weight: 600; letter-spacing: .18em;
  text-transform: uppercase; color: var(--t3); margin: 28px 0 14px;
  display: flex; align-items: center; gap: 10px;
}
.sec-label::after { content:''; flex:1; height:1px; background:var(--sep-solid); }
.pill {
  font-size: .58rem; font-weight: 600; letter-spacing: .1em; text-transform: uppercase;
  padding: 3px 9px; border-radius: 20px;
}
.pill-green  { background:var(--green-fill); color:var(--green); }
.pill-red    { background:var(--red-fill);   color:var(--red); }
.pill-blue   { background:var(--blue-fill);  color:var(--blue); }
.pill-amber  { background:var(--amber-fill); color:var(--amber); }
.pill-gray   { background:var(--s2); color:var(--t2); }

/* ─── Stock card (HTML header) ─── */
.sc {
  background: var(--s1); border: 1px solid var(--sep); border-radius: var(--r-lg) var(--r-lg) 0 0;
  border-bottom: none; padding: 14px 15px 10px; overflow: hidden;
}
.sc.up   { border-left: 3px solid var(--green); }
.sc.down { border-left: 3px solid var(--red); }
.sc-row  { display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:2px; }
.sc-sym  { font-family:var(--mono); font-size:.84rem; font-weight:600; color:var(--t1); letter-spacing:.03em; }
.sc-chg  { font-family:var(--mono); font-size:.62rem; padding:3px 7px; border-radius:6px; font-weight:500; }
.sc-chg.up   { background:var(--green-fill); color:var(--green); }
.sc-chg.down { background:var(--red-fill);   color:var(--red); }
.sc-name { font-size:.66rem; color:var(--t3); margin-bottom:6px;
           white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.sc-price { font-family:var(--mono); font-size:.95rem; font-weight:500; color:var(--t1); }
.sc-spark { line-height:0; }
/* Open button — merges with card */
.sc-open > div[data-testid="stButton"] > button {
  width:100% !important; background:var(--s1) !important;
  border:1px solid var(--sep) !important; border-top:1px solid var(--sep-solid) !important;
  border-radius:0 0 var(--r-lg) var(--r-lg) !important;
  color:var(--blue) !important; font-family:var(--font) !important;
  font-size:.72rem !important; font-weight:500 !important;
  padding:9px 14px !important; text-align:center !important;
  transition: background .15s var(--ease), color .15s var(--ease) !important;
  letter-spacing:.04em !important; margin-bottom:6px !important;
}
.sc-open > div[data-testid="stButton"] > button:hover {
  background:var(--s2) !important; color:var(--t1) !important;
}

/* ─── Stat strip ─── */
.strip { display:flex; gap:0; background:var(--s1); border:1px solid var(--sep);
         border-radius:var(--r-lg); overflow:hidden; margin:14px 0; }
.strip-cell { flex:1; padding:14px 18px; border-right:1px solid var(--sep-solid); }
.strip-cell:last-child { border-right:none; }
.strip-label { font-size:.62rem; font-weight:500; letter-spacing:.12em;
               text-transform:uppercase; color:var(--t3); margin-bottom:5px; }
.strip-val   { font-family:var(--mono); font-size:.95rem; font-weight:500; color:var(--t1); }
.strip-val.up   { color:var(--green); }
.strip-val.dn   { color:var(--red); }
.strip-val.blue { color:var(--blue); }
.strip-val.amber{ color:var(--amber); }

/* ─── Panel (big card) ─── */
.panel {
  background:var(--s1); border:1px solid var(--sep);
  border-radius:var(--r-xl); padding:22px 24px; margin-bottom:16px;
}
.panel-title {
  font-size:.65rem; font-weight:700; letter-spacing:.15em; text-transform:uppercase;
  color:var(--t3); margin-bottom:16px; display:flex; align-items:center; gap:10px;
}
.panel-title span { color:var(--t3); }

/* ─── Best Move panel (prominent) ─── */
.bm-panel {
  background: linear-gradient(135deg, rgba(10,132,255,.08) 0%, rgba(48,209,88,.06) 100%);
  border: 1px solid rgba(10,132,255,.25);
  border-radius: var(--r-xl); padding: 24px 26px; margin-bottom: 16px;
}
.bm-regime {
  font-size: 1.4rem; font-weight: 700; color: var(--t1); margin-bottom: 6px;
  display: flex; align-items: center; gap: 12px;
}
.bm-sub    { font-size: .82rem; color: var(--t2); margin-bottom: 20px; }
.bm-points { list-style: none; padding: 0; margin: 0 0 18px; }
.bm-points li { font-size: .83rem; color: var(--t2); padding: 5px 0;
                display: flex; align-items: flex-start; gap: 10px; line-height: 1.5; }
.bm-points li span { color: var(--t1); font-weight: 500; }
.bm-bottom {
  font-size: .78rem; color: var(--t3); line-height: 1.7;
  border-top: 1px solid var(--sep-solid); padding-top: 14px;
}
.bm-bottom b { color: var(--t2); font-weight: 500; }
.conf-bar {
  background: var(--s3); border-radius: 4px; height: 5px;
  overflow: hidden; margin: 8px 0 4px; width: 100%;
}
.conf-fill { height: 100%; border-radius: 4px; transition: width .6s var(--ease); }

/* ─── MTF alignment ─── */
.mtf-row { display:flex; gap:8px; margin-bottom:6px; flex-wrap:wrap; }
.mtf-chip {
  display:flex; align-items:center; gap:6px; padding:8px 14px;
  border-radius:var(--r-md); border:1px solid var(--sep); background:var(--s2);
  font-size:.75rem; font-family:var(--mono); font-weight:500;
}
.mtf-chip.bull { background:var(--green-fill); border-color:rgba(48,209,88,.25); color:var(--green); }
.mtf-chip.bear { background:var(--red-fill);   border-color:rgba(255,69,58,.25);  color:var(--red); }
.mtf-chip.neut { background:var(--s2);         border-color:var(--sep);           color:var(--t3); }

/* ─── Indicator grid ─── */
.ind-grid { display:grid; grid-template-columns:1fr 1fr 1fr; gap:10px; }
.ind-cell {
  background:var(--s2); border:1px solid var(--sep); border-radius:var(--r-md);
  padding:13px 15px;
}
.ind-name  { font-size:.62rem; color:var(--t3); text-transform:uppercase; letter-spacing:.1em; margin-bottom:6px; }
.ind-val   { font-family:var(--mono); font-size:.95rem; font-weight:600; color:var(--t1); margin-bottom:3px; }
.ind-val.up   { color:var(--green); }
.ind-val.dn   { color:var(--red); }
.ind-val.amber{ color:var(--amber); }
.ind-hint  { font-size:.68rem; color:var(--t3); line-height:1.4; }

/* ─── News sentiment ─── */
.news-item {
  display:flex; justify-content:space-between; align-items:center;
  padding:10px 0; border-bottom:1px solid var(--sep-solid); gap:12px;
}
.news-item:last-child { border-bottom:none; }
.news-title { font-size:.78rem; color:var(--t2); line-height:1.4; flex:1; }
.news-src   { font-size:.63rem; color:var(--t3); white-space:nowrap; }
.sent-dot   { width:7px; height:7px; border-radius:50%; flex-shrink:0; }
.sent-dot.bull { background:var(--green); box-shadow:0 0 6px var(--green); }
.sent-dot.bear { background:var(--red);   box-shadow:0 0 6px var(--red); }
.sent-dot.neut { background:var(--t3); }

/* ─── Screener table ─── */
.scr-row {
  display:flex; align-items:center; gap:12px; padding:11px 16px;
  border-bottom:1px solid var(--sep-solid); cursor:pointer;
  transition: background .15s var(--ease);
}
.scr-row:hover   { background:var(--s2); }
.scr-row:last-child { border-bottom:none; }
.scr-sym  { font-family:var(--mono); font-size:.82rem; font-weight:600; color:var(--t1); width:70px; }
.scr-name { font-size:.76rem; color:var(--t2); flex:1; }
.scr-price{ font-family:var(--mono); font-size:.8rem; color:var(--t1); width:80px; text-align:right; }
.scr-chg  { font-family:var(--mono); font-size:.75rem; width:65px; text-align:right; }

/* ─── Prob box (prediction) ─── */
.prob-panel {
  background:var(--s1); border:1px solid var(--sep);
  border-radius:var(--r-xl); padding:20px 22px; margin-bottom:16px;
}
.prob-title { font-size:.65rem; font-weight:700; letter-spacing:.15em;
              text-transform:uppercase; color:var(--t3); margin-bottom:14px; }
.prob-row { display:flex; justify-content:space-between; align-items:center;
            padding:8px 0; border-bottom:1px solid var(--sep-solid); }
.prob-row:last-child { border-bottom:none; }
.prob-lbl { font-size:.78rem; color:var(--t2); }
.prob-val { font-family:var(--mono); font-size:.85rem; font-weight:600; }

/* ─── Streamlit overrides ─── */
div[data-testid="stButton"] > button {
  background:var(--s2) !important; border:1px solid var(--sep) !important;
  border-radius:var(--r-md) !important; color:var(--t2) !important;
  font-family:var(--font) !important; font-size:.75rem !important;
  font-weight:500 !important; padding:8px 18px !important;
  transition: all .15s var(--ease) !important;
}
div[data-testid="stButton"] > button:hover {
  background:var(--s3) !important; color:var(--t1) !important;
  transform: scale(0.98) !important;
}
div[data-baseweb="tab-list"] {
  background:var(--s1) !important; border:1px solid var(--sep) !important;
  border-radius:var(--r-md) !important; padding:3px !important; gap:2px !important;
}
div[data-baseweb="tab"] {
  font-family:var(--font) !important; font-size:.74rem !important; font-weight:500 !important;
  color:var(--t3) !important; padding:7px 16px !important; border-radius:var(--r-sm) !important;
}
div[data-baseweb="tab"][aria-selected="true"] {
  background:var(--s3) !important; color:var(--t1) !important;
}
div[data-baseweb="tab-highlight"], div[data-baseweb="tab-border"] { display:none !important; }
.stTextInput input, .stSelectbox div[data-baseweb="select"]>div {
  background:var(--s1) !important; border:1px solid var(--sep) !important;
  border-radius:var(--r-md) !important; color:var(--t1) !important;
  font-family:var(--font) !important; font-size:.84rem !important;
}
label[data-testid="stWidgetLabel"] p {
  font-size:.62rem !important; color:var(--t3) !important;
  text-transform:uppercase !important; letter-spacing:.12em !important; font-weight:600 !important;
}
.js-plotly-plot .plotly .modebar { display:none !important; }
.mp-footer {
  margin-top:60px; border-top:1px solid var(--sep-solid); padding-top:14px;
  font-size:.62rem; color:var(--t3); letter-spacing:.08em;
  display:flex; justify-content:space-between; align-items:center;
}
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════
# DATA FETCHING
# ══════════════════════════════════════════════════════════════════════
CF = dict(family="'JetBrains Mono', monospace", size=10, color="#636366")

@st.cache_data(ttl=120, show_spinner=False)
def card_data(ticker):
    try:
        df = yf.download(ticker, period="5d", interval="1h", progress=False, auto_adjust=False)
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        if df.empty: return None
        c = df["Close"].dropna()
        op, last = float(df["Open"].iloc[0]), float(c.iloc[-1])
        return {"vals": c.tolist(), "last": last, "chg": (last-op)/op*100}
    except: return None

@st.cache_data(ttl=60, show_spinner=False)
def ohlcv(ticker, period, interval):
    try:
        df = yf.download(ticker, period=period, interval=interval,
                         progress=False, auto_adjust=False)
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        return df
    except: return pd.DataFrame()

@st.cache_data(ttl=120, show_spinner=False)
def hist(ticker): return ohlcv(ticker, "6mo", "1d")

@st.cache_data(ttl=300, show_spinner=False)
def fetch_news(ticker):
    try:
        t = yf.Ticker(ticker)
        return t.news[:8] if t.news else []
    except: return []

# ══════════════════════════════════════════════════════════════════════
# INDICATORS
# ══════════════════════════════════════════════════════════════════════
def rsi(s, n=14):
    d=s.diff(); g=d.clip(lower=0).rolling(n).mean()
    l=(-d.clip(upper=0)).rolling(n).mean()
    return 100-100/(1+g/l.replace(0,np.nan))

def macd(s, f=12, sl=26, sg=9):
    m = s.ewm(span=f,adjust=False).mean()-s.ewm(span=sl,adjust=False).mean()
    sig = m.ewm(span=sg,adjust=False).mean()
    return m, sig, m-sig

def bb(s, n=20, k=2):
    mid=s.rolling(n).mean(); std=s.rolling(n).std()
    return mid+k*std, mid, mid-k*std

def atr(df, n=14):
    h,l,c=df["High"],df["Low"],df["Close"]
    tr=pd.concat([h-l,(h-c.shift()).abs(),(l-c.shift()).abs()],axis=1).max(axis=1)
    return tr.rolling(n).mean()

def adx(df, n=14):
    h,l,c=df["High"],df["Low"],df["Close"]
    up=h.diff(); dn=-l.diff()
    pdm=up.where((up>dn)&(up>0),0); ndm=dn.where((dn>up)&(dn>0),0)
    tr_=atr(df,n)
    pdi=100*pdm.ewm(span=n,adjust=False).mean()/tr_.replace(0,np.nan)
    ndi=100*ndm.ewm(span=n,adjust=False).mean()/tr_.replace(0,np.nan)
    dx=100*(pdi-ndi).abs()/(pdi+ndi+1e-9)
    return dx.ewm(span=n,adjust=False).mean(), pdi, ndi

def cur(s): return float(s.iloc[-1]) if len(s)>0 and not s.empty else 0.0

# ══════════════════════════════════════════════════════════════════════
# MARKET REGIME DETECTOR
# ══════════════════════════════════════════════════════════════════════
def detect_regime(df):
    if df.empty or len(df) < 50: return None
    c = df["Close"].squeeze()
    r14=rsi(c,14); ml,sg,_=macd(c); adx_,pdi,ndi=adx(df,14)
    up_bb,_,lo_bb=bb(c); a_=atr(df,14)
    s10=c.rolling(10).mean(); s20=c.rolling(20).mean(); s50=c.rolling(50).mean()

    price=cur(c); cur_rsi=cur(r14); cur_ml=cur(ml); cur_sg=cur(sg)
    cur_adx=cur(adx_); cur_pdi=cur(pdi); cur_ndi=cur(ndi)
    cur_atr=cur(a_); cur_s10=cur(s10); cur_s20=cur(s20); cur_s50=cur(s50)
    cur_upper=cur(up_bb); cur_lower=cur(lo_bb)
    roc10 = (price/float(c.iloc[-11])-1)*100 if len(c)>=11 else 0

    # ATR vs 90-day average → volatility regime
    atr_avg = float(a_.rolling(90,min_periods=20).mean().iloc[-1])
    high_vol = cur_atr > 1.5*atr_avg

    # Trend signals (each +1 bullish, -1 bearish, 0 neutral)
    signals = {
        "price_vs_sma20": 1 if price>cur_s20 else -1,
        "price_vs_sma50": 1 if price>cur_s50 else -1,
        "sma10_vs_sma20": 1 if cur_s10>cur_s20 else -1,
        "macd_direction": 1 if cur_ml>cur_sg else -1,
        "rsi_side":       1 if cur_rsi>50 else -1,
        "di_direction":   1 if cur_pdi>cur_ndi else -1,
        "roc_direction":  1 if roc10>0 else -1,
    }
    score = sum(signals.values())  # -7 to +7

    if high_vol:
        regime, regime_color = "⚡ High Volatility", "amber"
        summary = "Price swings are abnormally large right now. Signals are less reliable."
    elif score >= 5:
        regime, regime_color = "↑ Strong Uptrend", "green"
        summary = "Most indicators align bullishly. Trend-following conditions are strong."
    elif score >= 2:
        regime, regime_color = "↗ Mild Uptrend", "green"
        summary = "Bias is bullish but not all signals agree. Lower-conviction environment."
    elif score <= -5:
        regime, regime_color = "↓ Strong Downtrend", "red"
        summary = "Most indicators align bearishly. Trend-following conditions favour downside."
    elif score <= -2:
        regime, regime_color = "↘ Mild Downtrend", "red"
        summary = "Bias is bearish but mixed signals. Lower-conviction environment."
    else:
        regime, regime_color = "↔ Ranging / Sideways", "amber"
        summary = "No clear directional edge. Mean-reversion conditions may apply."

    # RSI state
    if cur_rsi < 30:   rsi_state="Oversold"
    elif cur_rsi > 70: rsi_state="Overbought"
    else:              rsi_state=f"{cur_rsi:.0f} — Neutral"

    # Bollinger position
    if price > cur_upper: bb_state="Above upper band (extended)"
    elif price < cur_lower: bb_state="Below lower band (oversold)"
    else: bb_state="Inside bands"

    return dict(
        regime=regime, regime_color=regime_color, summary=summary,
        score=score, signals=signals, high_vol=high_vol,
        price=price, cur_rsi=cur_rsi, cur_ml=cur_ml, cur_sg=cur_sg,
        cur_adx=cur_adx, cur_pdi=cur_pdi, cur_ndi=cur_ndi,
        cur_s20=cur_s20, cur_s50=cur_s50, cur_atr=cur_atr,
        cur_upper=cur_upper, cur_lower=cur_lower,
        rsi_state=rsi_state, bb_state=bb_state, roc10=roc10,
        adx_strong=cur_adx>25,
    )

# ══════════════════════════════════════════════════════════════════════
# MULTI-TIMEFRAME ALIGNMENT
# ══════════════════════════════════════════════════════════════════════
@st.cache_data(ttl=120, show_spinner=False)
def mtf_alignment(ticker):
    frames = {
        "1H":  ohlcv(ticker,"7d","60m"),
        "Daily": ohlcv(ticker,"1y","1d"),
        "Weekly": ohlcv(ticker,"2y","1wk"),
    }
    result = {}
    for tf, df in frames.items():
        if df.empty or len(df)<20:
            result[tf]="neut"; continue
        c=df["Close"].squeeze()
        ema20=c.ewm(span=20,adjust=False).mean()
        ml,sg,_=macd(c)
        price=cur(c); cur_ema=cur(ema20); cur_ml=cur(ml); cur_sg=cur(sg)
        bull_count = (1 if price>cur_ema else 0) + (1 if cur_ml>cur_sg else 0)
        result[tf] = "bull" if bull_count>=2 else ("bear" if bull_count==0 else "neut")
    return result

# ══════════════════════════════════════════════════════════════════════
# NEWS SENTIMENT
# ══════════════════════════════════════════════════════════════════════
BULL_W = {"surge","rally","gain","gains","rise","rises","high","record","strong","beat","beats",
          "upgrade","positive","growth","profit","profits","boost","outperform","bullish",
          "buy","soars","soar","breakthrough","recovery","recovers","exceed","exceeds"}
BEAR_W = {"fall","falls","drop","drops","decline","declines","loss","losses","miss","misses",
          "downgrade","sell","weak","crash","plunge","plunges","cut","cuts","layoff","layoffs",
          "warning","risk","concern","concerns","debt","bearish","lawsuit","investigation",
          "recall","fraud","breach","default","worse","worsen"}

def score_headline(title):
    words = set(title.lower().split())
    b = len(words & BULL_W); bear = len(words & BEAR_W)
    if b > bear: return "bull"
    if bear > b: return "bear"
    return "neut"

def sentiment_summary(news):
    if not news: return "neut", 0, 0, 0
    scores = [score_headline(n.get("title","")) for n in news]
    b=scores.count("bull"); bear=scores.count("bear"); n=scores.count("neut")
    if b>bear+1:   overall="bull"
    elif bear>b+1: overall="bear"
    else:          overall="neut"
    return overall, b, bear, n

# ══════════════════════════════════════════════════════════════════════
# BEST MOVE ENGINE  (honest, clear, data-grounded)
# ══════════════════════════════════════════════════════════════════════
def best_move(reg, mtf, sent_overall, ticker):
    if not reg: return None
    score = reg["score"]    # -7 to +7
    mtf_vals = list(mtf.values())
    mtf_bull = mtf_vals.count("bull")
    mtf_bear = mtf_vals.count("bear")

    # Confidence: how strongly do signals agree?
    agreement = abs(score)/7          # 0-1
    mtf_edge  = max(mtf_bull, mtf_bear)/3  # 0-1
    sent_edge  = 0.5 if sent_overall=="neut" else (1 if sent_overall in ("bull","bear") else 0)
    raw_conf   = (agreement*0.6 + mtf_edge*0.3 + sent_edge*0.1)
    conf_pct   = int(raw_conf*100)

    if conf_pct >= 70:   conf_label, conf_color = "High", "green"
    elif conf_pct >= 45: conf_label, conf_color = "Medium", "amber"
    else:                conf_label, conf_color = "Low", "red"

    # Supporting evidence bullets
    evidence = []
    if score >= 5:    evidence.append(("✅","Price above all key moving averages — clear uptrend structure"))
    elif score >= 2:  evidence.append(("🟡","Price above short-term MAs, mixed on longer ones"))
    elif score <= -5: evidence.append(("❌","Price below all key moving averages — clear downtrend structure"))
    else:             evidence.append(("⚪","Price between key moving averages — no directional bias"))

    rsi_v = reg["cur_rsi"]
    if rsi_v < 30:     evidence.append(("✅",f"RSI {rsi_v:.0f} — historically oversold territory, bounce potential"))
    elif rsi_v > 70:   evidence.append(("⚠️",f"RSI {rsi_v:.0f} — overbought territory, elevated pullback risk"))
    elif score > 0:    evidence.append(("✅",f"RSI {rsi_v:.0f} — positive momentum, not yet overbought"))
    else:              evidence.append(("⚪",f"RSI {rsi_v:.0f} — neutral momentum zone"))

    if reg["cur_ml"] > reg["cur_sg"]: evidence.append(("✅","MACD above signal line — bullish momentum confirmed"))
    else:                             evidence.append(("❌","MACD below signal line — bearish momentum"))

    if reg["adx_strong"]:   evidence.append(("✅",f"ADX {reg['cur_adx']:.0f} — trend is strong (>25 threshold), not noise"))
    else:                   evidence.append(("⚪",f"ADX {reg['cur_adx']:.0f} — trend strength is weak, signals less reliable"))

    # MTF alignment
    if mtf_bull == 3:   evidence.append(("✅","All 3 timeframes bullish — rare high-confidence alignment"))
    elif mtf_bull == 2: evidence.append(("🟡","2 of 3 timeframes bullish — partial alignment"))
    elif mtf_bear == 3: evidence.append(("❌","All 3 timeframes bearish — aligned downside pressure"))
    elif mtf_bear == 2: evidence.append(("🟡","2 of 3 timeframes bearish — partial downside alignment"))
    else:               evidence.append(("⚪","Timeframes conflict — mixed directional bias"))

    # Sentiment
    if sent_overall == "bull":   evidence.append(("✅","Recent news headlines trending positive"))
    elif sent_overall == "bear": evidence.append(("⚠️","Recent news headlines trending negative — watch for catalyst risk"))
    else:                        evidence.append(("⚪","News sentiment neutral"))

    # Risk factors
    risks = []
    if reg["high_vol"]:     risks.append("Volatility is abnormally high — price swings may be unpredictable")
    if rsi_v > 65:          risks.append(f"RSI at {rsi_v:.0f} — if buying, limited room before overbought")
    if abs(reg["price"]-reg["cur_upper"])/reg["price"]<0.02:
                            risks.append("Price near upper Bollinger Band — potential short-term resistance")
    if not reg["adx_strong"]:risks.append("Weak ADX means the 'trend' may be noise rather than real momentum")
    if conf_pct < 50:       risks.append("Low signal agreement — this environment offers no statistical edge")
    if mtf_bull > 0 and mtf_bear > 0: risks.append("Timeframes disagree — reduces reliability of any signal")
    if not risks:           risks.append("No extreme warning flags at this time — standard market risk still applies")

    # Bottom line (honest)
    if conf_pct >= 65 and score >= 4:
        bottom = "Conditions historically associated with continued upward momentum. Not a guarantee — markets can always reverse. If you were considering a long position, conditions are relatively favourable."
    elif conf_pct >= 65 and score <= -4:
        bottom = "Conditions historically associated with continued downward pressure. Not a guarantee. If you hold a position, conditions warrant reviewing your risk exposure."
    elif rsi_v < 30 and score > -3:
        bottom = "The asset is in oversold territory while the broader trend is not strongly bearish. This has historically produced above-average short-term rebounds, though not always."
    elif rsi_v > 70 and score > 3:
        bottom = "Strong trend but overbought momentum. Historically, chasing at these RSI levels leads to worse short-term entries. Waiting for a pullback has historically improved outcomes."
    else:
        bottom = "No statistically strong edge is present right now. The signals conflict or are too weak to favour any direction with confidence. Patience is a valid strategy."

    return dict(
        conf_pct=conf_pct, conf_label=conf_label, conf_color=conf_color,
        evidence=evidence, risks=risks, bottom=bottom,
    )

# ══════════════════════════════════════════════════════════════════════
# EOD PREDICTION (Monte Carlo)
# ══════════════════════════════════════════════════════════════════════
VOL_CAPS = {"crypto":.08,"nse":.04,"sp500":.03}

def mc_predict(ticker, df_intra):
    ret  = df_intra["Close"].pct_change().dropna()
    vraw = float(ret.std()) if len(ret)>1 else .01
    cap  = VOL_CAPS[aclass(ticker)]
    vuse = min(vraw, cap)
    op   = float(df_intra["Open"].iloc[0])
    dist = op * np.exp(np.random.normal(0, vuse, 10_000))
    p5,p25,p50,p75,p95 = np.percentile(dist, [5,25,50,75,95])
    return dict(op=op, p5=p5, p25=p25, p50=p50, p75=p75, p95=p95,
                up_prob=float(np.mean(dist>op)*100),
                vraw=vraw, vuse=vuse,
                warn=(vraw>cap or len(ret)<30))

# ══════════════════════════════════════════════════════════════════════
# SCREENER
# ══════════════════════════════════════════════════════════════════════
@st.cache_data(ttl=180, show_spinner=False)
def run_screener(filter_name):
    results = []
    for ticker, name in ALL_TICKERS:
        try:
            df = hist(ticker)
            if df.empty or len(df)<30: continue
            c=df["Close"].squeeze(); price=cur(c)
            r=rsi(c,14); ml,sg,_=macd(c)
            up_bb,_,lo_bb=bb(c); s20=c.rolling(20).mean(); s50=c.rolling(50).mean()
            vol=df.get("Volume",pd.Series())
            vol_avg = float(vol.rolling(20).mean().iloc[-1]) if len(vol)>20 else 0
            vol_cur = float(vol.iloc[-1]) if len(vol)>0 else 0
            hi52 = float(c.rolling(252,min_periods=20).max().iloc[-1])
            lo52 = float(c.rolling(252,min_periods=20).min().iloc[-1])
            bw = float((up_bb-lo_bb).iloc[-1]); bw_min = float((up_bb-lo_bb).rolling(120,min_periods=20).min().iloc[-1])
            chg1d = (price/float(c.iloc[-2])-1)*100 if len(c)>1 else 0

            passes = False
            if filter_name == "All Signals": passes = True
            elif filter_name == "RSI Oversold (<30)":   passes = cur(r) < 30
            elif filter_name == "RSI Overbought (>70)": passes = cur(r) > 70
            elif filter_name == "MACD Bullish Cross":
                passes = (cur(ml)>cur(sg)) and (float(ml.iloc[-2])<float(sg.iloc[-2]))
            elif filter_name == "MACD Bearish Cross":
                passes = (cur(ml)<cur(sg)) and (float(ml.iloc[-2])>float(sg.iloc[-2]))
            elif filter_name == "Golden Cross (SMA20>SMA50)":
                passes = (cur(s20)>cur(s50)) and (float(s20.iloc[-2])<float(s50.iloc[-2]))
            elif filter_name == "Bollinger Squeeze":
                passes = bw <= bw_min * 1.1
            elif filter_name == "High Volume (>2× avg)":
                passes = vol_avg > 0 and vol_cur > 2*vol_avg
            elif filter_name == "Near 52-Week High":
                passes = price >= hi52 * 0.97
            elif filter_name == "Near 52-Week Low":
                passes = price <= lo52 * 1.03

            if passes:
                results.append(dict(ticker=ticker, name=name, price=price,
                                    chg=chg1d, rsi=cur(r)))
        except: pass
    return sorted(results, key=lambda x: abs(x["chg"]), reverse=True)

# ══════════════════════════════════════════════════════════════════════
# SVG SPARKLINE  (inline, inside card HTML)
# ══════════════════════════════════════════════════════════════════════
def sparkline(vals, is_up, w=200, h=46):
    v=[x for x in vals if x and not (isinstance(x,float) and np.isnan(x))]
    if len(v)<2: return ""
    mn,mx=min(v),max(v); rng=mx-mn or 1
    xs=[i/(len(v)-1)*w for i in range(len(v))]
    ys=[h-((x-mn)/rng)*(h-6)-3 for x in v]
    pts=" ".join(f"{x:.1f},{y:.1f}" for x,y in zip(xs,ys))
    fp=f"0,{h} {pts} {w},{h}"
    col="#30d158" if is_up else "#ff453a"
    fc="rgba(48,209,88,.1)" if is_up else "rgba(255,69,58,.1)"
    return (f'<svg viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg" '
            f'preserveAspectRatio="none" style="width:100%;height:{h}px;display:block">'
            f'<polygon points="{fp}" fill="{fc}"/>'
            f'<polyline points="{pts}" fill="none" stroke="{col}" stroke-width="1.8" '
            f'stroke-linejoin="round" stroke-linecap="round"/></svg>')

# ══════════════════════════════════════════════════════════════════════
# CHART BUILDERS
# ══════════════════════════════════════════════════════════════════════
def candle(df):
    fig=go.Figure(go.Candlestick(
        x=df.index, open=df["Open"], high=df["High"], low=df["Low"], close=df["Close"],
        increasing_line_color="#30d158", decreasing_line_color="#ff453a",
        increasing_fillcolor="#30d158", decreasing_fillcolor="#ff453a"))
    fig.update_layout(template="plotly_dark", height=420,
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#1c1c1e",
                      xaxis_rangeslider_visible=False, font=CF,
                      margin=dict(l=0,r=0,t=0,b=24),
                      xaxis=dict(gridcolor="#2c2c2e",showgrid=True),
                      yaxis=dict(gridcolor="#2c2c2e",showgrid=True))
    return fig

def pred_chart(df_intra, pred):
    c=df_intra["Close"].squeeze()
    fig=go.Figure()
    # Cone fills
    fig.add_trace(go.Scatter(x=[df_intra.index[-1]]*2, y=[pred["p5"],pred["p95"]],
        fill="toself", fillcolor="rgba(255,255,255,0.03)",
        line=dict(color="rgba(0,0,0,0)"), showlegend=False, hoverinfo="skip"))
    fig.add_trace(go.Scatter(
        x=df_intra.index, y=c, name="Price",
        line=dict(color="#0a84ff", width=2.2), fill=None))
    def hl(y, col, dash, w, lbl):
        fig.add_hline(y=y, line=dict(color=col, dash=dash, width=w),
                      annotation_text=lbl, annotation_position="right",
                      annotation_font=dict(color=col, size=9, family="JetBrains Mono"))
    hl(pred["p95"],"rgba(48,209,88,.85)","dot",1.2,"Bull 95%")
    hl(pred["p75"],"rgba(48,209,88,.4)", "dot",1.0,"")
    hl(pred["p50"],"rgba(255,214,10,.9)","dash",1.8,"Median")
    hl(pred["p25"],"rgba(255,69,58,.4)", "dot",1.0,"")
    hl(pred["p5"], "rgba(255,69,58,.85)","dot",1.2,"Bear 5%")
    hl(pred["op"], "rgba(100,100,100,.6)","dash",1.0,"Open")
    fig.update_layout(template="plotly_dark", height=360,
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#1c1c1e",
                      font=CF, showlegend=False, margin=dict(l=0,r=72,t=0,b=24),
                      xaxis=dict(gridcolor="#2c2c2e"),
                      yaxis=dict(gridcolor="#2c2c2e"))
    return fig

# ══════════════════════════════════════════════════════════════════════
# HEADER
# ══════════════════════════════════════════════════════════════════════
st.markdown(
    f'<div class="pulse-header">'
    f'  <div class="pulse-logo"><div class="pulse-dot"></div>'
    f'  <div class="pulse-name">Market Pulse</div></div>'
    f'  <div class="pulse-time">{datetime.now().strftime("%d %b %Y  ·  %H:%M")}  ·  Auto-refresh 2min</div>'
    f'</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════
# DETAIL VIEW
# ══════════════════════════════════════════════════════════════════════
if st.session_state.view == "detail":
    ticker = st.session_state.ticker
    name   = NAME_MAP.get(ticker, clean(ticker))

    # Nav
    c1, c2 = st.columns([1, 8])
    with c1:
        if st.button("← Back"): go_home()

    st.markdown(f"<div style='font-size:.65rem;color:var(--t3);letter-spacing:.1em;text-transform:uppercase;margin-bottom:6px'>Markets / {clean(ticker)}</div>", unsafe_allow_html=True)

    # Price hero
    df_intra = ohlcv(ticker, "1d", "1m")
    df_6mo   = hist(ticker)
    last_price = float(df_intra["Close"].iloc[-1]) if not df_intra.empty else 0
    day_open   = float(df_intra["Open"].iloc[0])   if not df_intra.empty else 0
    chg_pct    = (last_price-day_open)/day_open*100 if day_open else 0
    chg_col    = "var(--green)" if chg_pct>=0 else "var(--red)"
    arrow      = "▲" if chg_pct>=0 else "▼"

    st.markdown(
        f'<div style="margin-bottom:6px">'
        f'  <div style="font-size:.78rem;color:var(--t3);letter-spacing:.08em">{name}</div>'
        f'  <div style="display:flex;align-items:baseline;gap:14px;margin-top:4px">'
        f'    <span style="font-family:var(--mono);font-size:2.6rem;font-weight:700;color:var(--t1)">${last_price:,.2f}</span>'
        f'    <span style="font-family:var(--mono);font-size:1rem;color:{chg_col}">{arrow} {abs(chg_pct):.2f}%</span>'
        f'  </div>'
        f'</div>', unsafe_allow_html=True)

    # Charts
    tf_keys = list(TIME_TABS.keys())
    tf_tabs  = st.tabs(tf_keys)
    for i, tab in enumerate(tf_tabs):
        with tab:
            p, iv = TIME_TABS[tf_keys[i]]
            df_t = ohlcv(ticker, p, iv)
            if not df_t.empty:
                st.plotly_chart(candle(df_t), use_container_width=True, config={"displayModeBar":False})

    # ── ANALYSIS ENGINE ──────────────────────────────────────────────
    reg = detect_regime(df_6mo)
    mtf = mtf_alignment(ticker)
    news= fetch_news(ticker)
    sent_overall, b_cnt, bear_cnt, n_cnt = sentiment_summary(news)
    bm  = best_move(reg, mtf, sent_overall, ticker)

    # ── BEST MOVE CARD (most prominent) ─────────────────────────────
    st.markdown('<div class="sec-label">Intelligence Summary</div>', unsafe_allow_html=True)

    if bm and reg:
        regime_col_map = {"green":"var(--green)","red":"var(--red)","amber":"var(--amber)"}
        reg_col = regime_col_map.get(reg["regime_color"],"var(--t2)")
        conf_fill_col = "#30d158" if bm["conf_color"]=="green" else ("#ffd60a" if bm["conf_color"]=="amber" else "#ff453a")

        # Build evidence HTML
        ev_html = "".join(
            f'<li>{icon} <span>{text}</span></li>'
            for icon, text in bm["evidence"]
        )
        risk_html = "".join(
            f'<li>⚠️ <span>{r}</span></li>'
            for r in bm["risks"]
        )

        st.markdown(f"""
        <div class="bm-panel">
          <div class="bm-regime">
            <span style="color:{reg_col}">{reg['regime']}</span>
          </div>
          <div class="bm-sub">{reg['summary']}</div>

          <div style="margin-bottom:16px">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px">
              <span style="font-size:.65rem;font-weight:600;letter-spacing:.12em;text-transform:uppercase;color:var(--t3)">Signal Confidence</span>
              <span style="font-family:var(--mono);font-size:.82rem;font-weight:600;color:{conf_fill_col}">{bm['conf_label']} — {bm['conf_pct']}%</span>
            </div>
            <div class="conf-bar"><div class="conf-fill" style="width:{bm['conf_pct']}%;background:{conf_fill_col}"></div></div>
            <div style="font-size:.64rem;color:var(--t3)">Based on {abs(reg['score'])}/7 signals aligned  ·  Timeframes: {list(mtf.values()).count('bull')}↑ {list(mtf.values()).count('bear')}↓ {list(mtf.values()).count('neut')}→</div>
          </div>

          <div style="display:grid;grid-template-columns:1fr 1fr;gap:0 20px;margin-bottom:18px">
            <div>
              <div style="font-size:.63rem;font-weight:700;letter-spacing:.14em;text-transform:uppercase;color:var(--t3);margin-bottom:8px">What the data shows</div>
              <ul class="bm-points">{ev_html}</ul>
            </div>
            <div>
              <div style="font-size:.63rem;font-weight:700;letter-spacing:.14em;text-transform:uppercase;color:var(--t3);margin-bottom:8px">Risk factors</div>
              <ul class="bm-points">{risk_html}</ul>
            </div>
          </div>

          <div class="bm-bottom">
            <b>Bottom line:</b> {bm['bottom']}<br><br>
            ⚠️ <b>Data honesty:</b> This analysis is derived from 6 months of price history and standard technical indicators. It reflects patterns — not prophecy. Past conditions that looked similar may have resolved differently. This is not financial advice. Always consider your own risk tolerance and seek professional guidance before trading.
          </div>
        </div>
        """, unsafe_allow_html=True)

    # ── MULTI-TIMEFRAME ALIGNMENT ────────────────────────────────────
    st.markdown('<div class="sec-label">Timeframe Alignment</div>', unsafe_allow_html=True)
    mtf_labels = {"bull":"Bullish","bear":"Bearish","neut":"Neutral"}
    mtf_icons  = {"bull":"↑","bear":"↓","neut":"→"}
    chips = "".join(
        f'<div class="mtf-chip {v}">{mtf_icons[v]} {tf} — {mtf_labels[v]}</div>'
        for tf, v in mtf.items()
    )
    all_agree = len(set(mtf.values()))==1
    agree_txt = "All timeframes agree" if all_agree else "Timeframes mixed"
    st.markdown(f'<div class="mtf-row">{chips}<div class="mtf-chip neut" style="opacity:.6">{agree_txt}</div></div>', unsafe_allow_html=True)
    st.markdown(
        '<div style="font-size:.72rem;color:var(--t3);margin-top:6px;margin-bottom:4px">'
        'When all timeframes agree, signal quality is historically higher. '
        'Conflicts between timeframes reduce reliability significantly.</div>',
        unsafe_allow_html=True)

    # ── TECHNICAL INDICATORS ─────────────────────────────────────────
    st.markdown('<div class="sec-label">Technical Indicators — 6 Month Data</div>', unsafe_allow_html=True)
    if reg:
        def ind_color(val, lo, hi):
            if val<lo: return "dn"
            if val>hi: return "up"
            return ""
        # Row 1
        r1a, r1b, r1c = st.columns(3)
        rsi_c  = "dn" if reg["cur_rsi"]<35 else ("up" if reg["cur_rsi"]>65 else "amber")
        rsi_h  = ("Oversold zone — watch for bounce" if reg["cur_rsi"]<35
                  else "Overbought — pullback risk elevated" if reg["cur_rsi"]>70
                  else "Neutral zone — no momentum extreme")
        r1a.markdown(f"""<div class="ind-cell">
          <div class="ind-name">RSI (14)</div>
          <div class="ind-val {rsi_c}">{reg['cur_rsi']:.1f}</div>
          <div class="ind-hint">{rsi_h}</div></div>""", unsafe_allow_html=True)

        macd_c = "up" if reg["cur_ml"]>reg["cur_sg"] else "dn"
        macd_h = "Bullish — MACD above signal" if reg["cur_ml"]>reg["cur_sg"] else "Bearish — MACD below signal"
        r1b.markdown(f"""<div class="ind-cell">
          <div class="ind-name">MACD (12/26/9)</div>
          <div class="ind-val {macd_c}">{reg['cur_ml']:.3f}</div>
          <div class="ind-hint">{macd_h}</div></div>""", unsafe_allow_html=True)

        adx_c  = "up" if reg["cur_adx"]>25 else "amber"
        adx_h  = ("Strong trend — signals more reliable" if reg["cur_adx"]>25
                  else "Weak trend — signals less reliable")
        r1c.markdown(f"""<div class="ind-cell">
          <div class="ind-name">ADX</div>
          <div class="ind-val {adx_c}">{reg['cur_adx']:.1f}</div>
          <div class="ind-hint">{adx_h}</div></div>""", unsafe_allow_html=True)

        # Row 2
        r2a, r2b, r2c = st.columns(3)
        bb_col = "amber" if reg["cur_rsi"]>70 else ("up" if reg["cur_rsi"]<30 else "")
        r2a.markdown(f"""<div class="ind-cell">
          <div class="ind-name">Bollinger Band</div>
          <div class="ind-val {bb_col}" style="font-size:.78rem">{reg['bb_state']}</div>
          <div class="ind-hint">Upper ${reg['cur_upper']:.2f}  ·  Lower ${reg['cur_lower']:.2f}</div></div>""", unsafe_allow_html=True)

        s20_c = "up" if reg["price"]>reg["cur_s20"] else "dn"
        s50_c = "up" if reg["price"]>reg["cur_s50"] else "dn"
        r2b.markdown(f"""<div class="ind-cell">
          <div class="ind-name">Moving Averages</div>
          <div class="ind-val {s20_c}" style="font-size:.82rem">Price vs SMA20: {'▲ Above' if reg['price']>reg['cur_s20'] else '▼ Below'}</div>
          <div class="ind-hint">SMA20 ${reg['cur_s20']:.2f}  ·  SMA50 ${reg['cur_s50']:.2f}</div></div>""", unsafe_allow_html=True)

        roc_c = "up" if reg["roc10"]>0 else "dn"
        r2c.markdown(f"""<div class="ind-cell">
          <div class="ind-name">10-Day Momentum</div>
          <div class="ind-val {roc_c}">{reg['roc10']:+.2f}%</div>
          <div class="ind-hint">ATR (volatility): {reg['cur_atr']:.2f}</div></div>""", unsafe_allow_html=True)

    # ── NEWS SENTIMENT ───────────────────────────────────────────────
    st.markdown('<div class="sec-label">News Sentiment</div>', unsafe_allow_html=True)
    sent_col_map = {"bull":"var(--green)","bear":"var(--red)","neut":"var(--t3)"}
    sent_lbl_map = {"bull":f"Positive ({b_cnt} bullish headlines)","bear":f"Negative ({bear_cnt} bearish headlines)","neut":"Neutral"}
    sent_col = sent_col_map[sent_overall]

    st.markdown(
        f'<div style="font-family:var(--mono);font-size:.82rem;font-weight:600;color:{sent_col};margin-bottom:12px">'
        f'Overall: {sent_lbl_map[sent_overall]}'
        f'<span style="font-size:.65rem;color:var(--t3);font-weight:400;margin-left:12px">'
        f'Simple keyword scoring · {len(news)} headlines · not a financial signal</span></div>',
        unsafe_allow_html=True)

    if news:
        items_html = ""
        for n in news:
            title = n.get("title","")
            pub   = n.get("publisher","")
            s     = score_headline(title)
            dot_c = "bull" if s=="bull" else ("bear" if s=="bear" else "neut")
            items_html += (f'<div class="news-item">'
                          f'<div class="sent-dot {dot_c}"></div>'
                          f'<div class="news-title">{title}</div>'
                          f'<div class="news-src">{pub}</div>'
                          f'</div>')
        st.markdown(f'<div class="panel">{items_html}</div>', unsafe_allow_html=True)
        st.markdown('<div style="font-size:.68rem;color:var(--t3);margin-top:4px">🟢 Bullish keyword  ·  🔴 Bearish keyword  ·  ⚪ Neutral  ·  Source: Yahoo Finance news feed</div>', unsafe_allow_html=True)

    # ── EOD PREDICTION ───────────────────────────────────────────────
    st.markdown('<div class="sec-label">End-of-Day Prediction — Monte Carlo</div>', unsafe_allow_html=True)
    if not df_intra.empty:
        if ticker not in st.session_state.predictions:
            st.session_state.predictions[ticker] = mc_predict(ticker, df_intra)
        pred = st.session_state.predictions[ticker]
        last = float(df_intra["Close"].iloc[-1])
        chg  = (last-pred["op"])/pred["op"]*100
        chg_c= "up" if chg>=0 else "dn"

        # Metrics strip
        st.markdown(f"""<div class="strip">
          <div class="strip-cell"><div class="strip-label">Day Open</div>
            <div class="strip-val">${pred['op']:,.2f}</div></div>
          <div class="strip-cell"><div class="strip-label">Current</div>
            <div class="strip-val">${last:,.2f}</div></div>
          <div class="strip-cell"><div class="strip-label">Intraday</div>
            <div class="strip-val {chg_c}">{'+'if chg>=0 else ''}{chg:.2f}%</div></div>
          <div class="strip-cell"><div class="strip-label">EOD Median</div>
            <div class="strip-val">${pred['p50']:,.2f}</div></div>
          <div class="strip-cell"><div class="strip-label">Up Probability</div>
            <div class="strip-val {'up' if pred['up_prob']>50 else 'dn'}">{pred['up_prob']:.1f}%</div></div>
        </div>""", unsafe_allow_html=True)

        if pred["warn"]:
            st.markdown('<div style="font-size:.72rem;color:var(--amber);background:var(--amber-fill);border-radius:var(--r-sm);padding:8px 12px;margin-bottom:10px">⚠️ Limited data or high volatility detected — prediction range is less reliable than usual</div>', unsafe_allow_html=True)

        st.plotly_chart(pred_chart(df_intra, pred), use_container_width=True, config={"displayModeBar":False})

        st.markdown(f"""<div class="prob-panel">
          <div class="prob-title">Probability Distribution — 10,000 Simulations (Geometric Brownian Motion)</div>
          <div class="prob-row"><span class="prob-lbl">🟢 Bull Case (95th percentile)</span>
            <span class="prob-val" style="color:var(--green)">${pred['p95']:,.2f}</span></div>
          <div class="prob-row"><span class="prob-lbl">🔵 75th Percentile</span>
            <span class="prob-val" style="color:var(--blue)">${pred['p75']:,.2f}</span></div>
          <div class="prob-row"><span class="prob-lbl">🎯 Median (50th percentile)</span>
            <span class="prob-val" style="color:var(--amber)">${pred['p50']:,.2f}</span></div>
          <div class="prob-row"><span class="prob-lbl">🟠 25th Percentile</span>
            <span class="prob-val" style="color:var(--orange)">${pred['p25']:,.2f}</span></div>
          <div class="prob-row"><span class="prob-lbl">🔴 Bear Case (5th percentile)</span>
            <span class="prob-val" style="color:var(--red)">${pred['p5']:,.2f}</span></div>
          <div class="prob-row"><span class="prob-lbl">Probability of finishing above open</span>
            <span class="prob-val" style="color:{'var(--green)' if pred['up_prob']>50 else 'var(--red)'}">{pred['up_prob']:.1f}%</span></div>
          <div class="prob-row"><span class="prob-lbl">Volatility used / raw</span>
            <span class="prob-val" style="color:var(--t3)">{pred['vuse']*100:.3f}% / {pred['vraw']*100:.3f}%</span></div>
        </div>""", unsafe_allow_html=True)

        st.markdown(
            '<div style="font-size:.7rem;color:var(--t3);line-height:1.7;padding:12px 16px;'
            'background:var(--s1);border:1px solid var(--sep);border-radius:var(--r-md)">'
            '⚠️ <strong style="color:var(--t2)">Model honesty:</strong> This uses Geometric Brownian Motion with '
            'historical intraday volatility. The model assumes normally distributed returns — real markets are not normal. '
            'Black swan events, earnings announcements, and macro shocks can make any prediction irrelevant. '
            'Treat all percentile ranges as approximate probability bands, not price targets.'
            '</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div style="font-size:.8rem;color:var(--t3);padding:16px">No intraday data available today.</div>', unsafe_allow_html=True)

    st.markdown('<div class="mp-footer"><span>MARKET PULSE · EDUCATIONAL USE ONLY · NOT FINANCIAL ADVICE</span><span>DATA: YAHOO FINANCE · REFRESH: 2MIN</span></div>', unsafe_allow_html=True)
    st.stop()

# ══════════════════════════════════════════════════════════════════════
# HOME VIEW  (Markets + Screener)
# ══════════════════════════════════════════════════════════════════════
search = st.text_input("", placeholder="🔍  Search any ticker — AAPL, BTC-USD, RELIANCE.NS …").upper().strip()
if search:
    st.session_state.ticker = search
    st.session_state.view   = "detail"
    st.rerun()

home_tab_markets, home_tab_screener = st.tabs(["  📊  Markets  ", "  🔍  Screener  "])

# ── MARKETS TAB ──────────────────────────────────────────────────────
with home_tab_markets:

    def render_section(label, tickers, n_cols=5):
        st.markdown(f'<div class="sec-label">{label}</div>', unsafe_allow_html=True)
        cols = st.columns(n_cols)
        for i, (ticker, name) in enumerate(tickers):
            with cols[i % n_cols]:
                data = card_data(ticker)
                is_up = (data["chg"] >= 0) if data else True
                cls   = "up" if is_up else "down"
                badge = "up" if is_up else "down"
                arrow = "▲" if is_up else "▼"

                if data:
                    spark = sparkline(data["vals"], is_up)
                    st.markdown(
                        f'<div class="sc {cls}">'
                        f'  <div class="sc-row">'
                        f'    <div class="sc-sym">{clean(ticker)}</div>'
                        f'    <span class="sc-chg {badge}">{arrow}{abs(data["chg"]):.2f}%</span>'
                        f'  </div>'
                        f'  <div class="sc-name">{name}</div>'
                        f'  <div class="sc-price">${data["last"]:,.2f}</div>'
                        f'  <div class="sc-spark">{spark}</div>'
                        f'</div>',
                        unsafe_allow_html=True)
                else:
                    st.markdown(
                        f'<div class="sc">'
                        f'  <div class="sc-sym">{clean(ticker)}</div>'
                        f'  <div class="sc-name">{name}</div>'
                        f'  <div class="sc-price" style="color:var(--t3)">—</div>'
                        f'</div>', unsafe_allow_html=True)

                # Open button — visually merged with card above
                st.markdown('<div class="sc-open">', unsafe_allow_html=True)
                if st.button("Open  →", key=f"o_{ticker}"):
                    go_detail(ticker)
                st.markdown('</div>', unsafe_allow_html=True)

    render_section("S&P 500", SP500)
    render_section("NSE Top 10", NSE)
    render_section("Crypto", CRYPTO, n_cols=4)

# ── SCREENER TAB ─────────────────────────────────────────────────────
with home_tab_screener:
    st.markdown('<div class="sec-label">Live Market Screener — updated every 3 min</div>', unsafe_allow_html=True)
    st.markdown(
        '<div style="font-size:.75rem;color:var(--t3);margin-bottom:18px;line-height:1.7">'
        'Scans S&P 500, NSE, and Crypto for stocks matching the selected condition. '
        'Results are sorted by absolute 1-day change. Click any row to open the full analysis.'
        '</div>', unsafe_allow_html=True)

    scr_col, _ = st.columns([2, 3])
    with scr_col:
        scr_filter = st.selectbox("Filter", SCREENER_FILTERS)

    with st.spinner("Scanning markets…"):
        hits = run_screener(scr_filter)

    if not hits:
        st.markdown(
            f'<div style="text-align:center;padding:40px;color:var(--t3);font-size:.85rem">'
            f'No stocks matched <strong style="color:var(--t2)">{scr_filter}</strong> right now.</div>',
            unsafe_allow_html=True)
    else:
        st.markdown(
            f'<div style="font-size:.7rem;color:var(--t3);margin-bottom:10px">'
            f'{len(hits)} result{"s" if len(hits)!=1 else ""} for <strong style="color:var(--t2)">{scr_filter}</strong></div>',
            unsafe_allow_html=True)

        rows_html = ""
        for h in hits:
            chg_col = "var(--green)" if h["chg"]>=0 else "var(--red)"
            arrow   = "▲" if h["chg"]>=0 else "▼"
            rows_html += (
                f'<div class="scr-row">'
                f'  <div class="scr-sym">{clean(h["ticker"])}</div>'
                f'  <div class="scr-name">{h["name"]}</div>'
                f'  <div style="font-family:var(--mono);font-size:.68rem;color:var(--t3)">RSI {h["rsi"]:.0f}</div>'
                f'  <div class="scr-price">${h["price"]:,.2f}</div>'
                f'  <div class="scr-chg" style="color:{chg_col}">{arrow} {abs(h["chg"]):.2f}%</div>'
                f'</div>')
        st.markdown(f'<div class="panel" style="padding:0">{rows_html}</div>', unsafe_allow_html=True)

        # Click to open from screener — buttons below the visual
        st.markdown('<div style="margin-top:14px;display:flex;flex-wrap:wrap;gap:8px">', unsafe_allow_html=True)
        btn_cols = st.columns(min(len(hits), 8))
        for i, h in enumerate(hits[:8]):
            with btn_cols[i]:
                if st.button(clean(h["ticker"]), key=f"scr_{h['ticker']}"):
                    go_detail(h["ticker"])
        st.markdown('</div>', unsafe_allow_html=True)

# ── FOOTER ───────────────────────────────────────────────────────────
st.markdown(
    '<div class="mp-footer">'
    '<span>MARKET PULSE · FOR EDUCATIONAL USE ONLY · NOT FINANCIAL ADVICE</span>'
    '<span>DATA: YAHOO FINANCE · SIGNALS: 6-MONTH HISTORY · AUTO-REFRESH 2MIN</span>'
    '</div>', unsafe_allow_html=True)

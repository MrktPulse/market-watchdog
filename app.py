import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from streamlit_autorefresh import st_autorefresh
from datetime import datetime

# ══════════════════════════════════════════════════════════════════════
# 1. PAGE CONFIG
# ══════════════════════════════════════════════════════════════════════
st.set_page_config(page_title="Market Pulse | Terminal", layout="wide",
                   initial_sidebar_state="collapsed")
st_autorefresh(interval=30_000, key="market_heartbeat")

# ══════════════════════════════════════════════════════════════════════
# 2. SESSION STATE
# ══════════════════════════════════════════════════════════════════════
for k, v in {
    "disclaimer_accepted": False,
    "selected_stock": None,
    "morning_predictions": {},
    "active_view": "grid",
    "strategy_ticker": None,
    "strategy_result": None,
    "last_strat_name": None,
    "sim_step": 0,
    "sim_running": False,
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ══════════════════════════════════════════════════════════════════════
# 3. TICKER UNIVERSE
# ══════════════════════════════════════════════════════════════════════
SP500_TOP100 = [
    ("AAPL","Apple"),("MSFT","Microsoft"),("NVDA","NVIDIA"),("AMZN","Amazon"),
    ("GOOGL","Alphabet"),("META","Meta Platforms"),("BRK-B","Berkshire H."),
    ("LLY","Eli Lilly"),("AVGO","Broadcom"),("TSLA","Tesla"),("JPM","JPMorgan"),
    ("UNH","UnitedHealth"),("XOM","ExxonMobil"),("V","Visa"),("MA","Mastercard"),
    ("JNJ","Johnson & J."),("PG","Procter & Gamble"),("COST","Costco"),
    ("HD","Home Depot"),("MRK","Merck"),("ABBV","AbbVie"),("CVX","Chevron"),
    ("CRM","Salesforce"),("BAC","Bank of America"),("NFLX","Netflix"),
    ("KO","Coca-Cola"),("ORCL","Oracle"),("WMT","Walmart"),("PEP","PepsiCo"),
    ("AMD","AMD"),("TMO","Thermo Fisher"),("MCD","McDonald's"),("CSCO","Cisco"),
    ("ABT","Abbott"),("ACN","Accenture"),("ADBE","Adobe"),("LIN","Linde"),
    ("DHR","Danaher"),("TXN","Texas Instruments"),("WFC","Wells Fargo"),
    ("NEE","NextEra Energy"),("PM","Philip Morris"),("NKE","Nike"),
    ("INTC","Intel"),("MS","Morgan Stanley"),("UNP","Union Pacific"),
    ("IBM","IBM"),("INTU","Intuit"),("RTX","Raytheon"),("HON","Honeywell"),
    ("QCOM","Qualcomm"),("CAT","Caterpillar"),("AMGN","Amgen"),
    ("SPGI","S&P Global"),("GS","Goldman Sachs"),("BLK","BlackRock"),
    ("LOW","Lowe's"),("ELV","Elevance"),("ISRG","Intuitive Surg."),("T","AT&T"),
    ("VRTX","Vertex Pharma"),("PLD","Prologis"),("MDT","Medtronic"),
    ("DE","Deere & Co."),("AXP","American Express"),("SYK","Stryker"),
    ("TJX","TJX Companies"),("ADI","Analog Devices"),("GILD","Gilead"),
    ("REGN","Regeneron"),("CB","Chubb"),("BKNG","Booking Holdings"),
    ("CI","Cigna"),("MMC","Marsh McLennan"),("CVS","CVS Health"),
    ("PGR","Progressive"),("BMY","Bristol-Myers"),("LRCX","Lam Research"),
    ("BSX","Boston Scientific"),("EOG","EOG Resources"),("SO","Southern Co."),
    ("ETN","Eaton"),("MDLZ","Mondelez"),("NOC","Northrop Grumman"),
    ("MU","Micron"),("PANW","Palo Alto Nets."),("KLAC","KLA Corp"),
    ("ZTS","Zoetis"),("CME","CME Group"),("GE","GE Aerospace"),
    ("DUK","Duke Energy"),("WM","Waste Management"),("ITW","Illinois Tool"),
    ("FI","Fiserv"),("APH","Amphenol"),("HCA","HCA Healthcare"),
    ("AON","Aon"),("SHW","Sherwin-Williams"),("USB","US Bancorp"),
]
NSE_TOP50 = [
    ("RELIANCE.NS","Reliance"),("TCS.NS","TCS"),("HDFCBANK.NS","HDFC Bank"),
    ("ICICIBANK.NS","ICICI Bank"),("INFY.NS","Infosys"),("BHARTIARTL.NS","Bharti Airtel"),
    ("SBI.NS","SBI"),("ITC.NS","ITC"),("HINDUNILVR.NS","HUL"),
    ("KOTAKBANK.NS","Kotak Bank"),("LT.NS","L&T"),("AXISBANK.NS","Axis Bank"),
    ("BAJFINANCE.NS","Bajaj Finance"),("HCLTECH.NS","HCL Tech"),
    ("MARUTI.NS","Maruti Suzuki"),("ASIANPAINT.NS","Asian Paints"),
    ("ULTRACEMCO.NS","UltraTech"),("WIPRO.NS","Wipro"),("SUNPHARMA.NS","Sun Pharma"),
    ("TATAMOTORS.NS","Tata Motors"),("TITAN.NS","Titan"),("M&M.NS","M&M"),
    ("BAJAJFINSV.NS","Bajaj Finserv"),("POWERGRID.NS","Power Grid"),
    ("NTPC.NS","NTPC"),("ONGC.NS","ONGC"),("TATASTEEL.NS","Tata Steel"),
    ("ADANIENT.NS","Adani Ent."),("JSWSTEEL.NS","JSW Steel"),
    ("NESTLEIND.NS","Nestle India"),("TECHM.NS","Tech Mahindra"),
    ("DRREDDY.NS","Dr. Reddy's"),("HINDALCO.NS","Hindalco"),
    ("DIVISLAB.NS","Divi's Labs"),("CIPLA.NS","Cipla"),("GRASIM.NS","Grasim"),
    ("COALINDIA.NS","Coal India"),("BRITANNIA.NS","Britannia"),
    ("INDUSINDBK.NS","IndusInd Bank"),("SBILIFE.NS","SBI Life"),
    ("HDFCLIFE.NS","HDFC Life"),("APOLLOHOSP.NS","Apollo Hosp."),
    ("EICHERMOT.NS","Eicher Motors"),("TATACONSUM.NS","Tata Consumer"),
    ("HEROMOTOCO.NS","Hero MotoCorp"),("BPCL.NS","BPCL"),
    ("SHREECEM.NS","Shree Cement"),("UPL.NS","UPL"),("BAJAJ-AUTO.NS","Bajaj Auto"),
]
CRYPTO = [("BTC-USD","Bitcoin"),("ETH-USD","Ethereum"),("BNB-USD","BNB"),("SOL-USD","Solana")]
NAME_MAP = {t: n for t, n in SP500_TOP100 + NSE_TOP50 + CRYPTO}

TIME_SETTINGS = {
    "1m":  {"period":"1d",  "interval":"1m",  "label":"1 Min"},
    "1h":  {"period":"7d",  "interval":"60m", "label":"Hourly"},
    "1d":  {"period":"1y",  "interval":"1d",  "label":"Daily"},
    "1wk": {"period":"2y",  "interval":"1wk", "label":"Weekly"},
    "1mo": {"period":"5y",  "interval":"1mo", "label":"Monthly"},
    "3mo": {"period":"10y", "interval":"3mo", "label":"Quarterly"},
}

# ══════════════════════════════════════════════════════════════════════
# 4. CSS
# ══════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@300;400;500;600&family=IBM+Plex+Sans:wght@300;400;500;600&display=swap');
:root {
    --bg:#06080d;--bg2:#0b0f18;--bg3:#10161f;--bg4:#141c28;
    --border:#192030;--border2:#243040;
    --text:#d8e0ec;--muted:#48566a;--muted2:#7a8ba0;
    --green:#2ea84a;--green2:#3dd163;--greenbg:rgba(46,168,74,.08);
    --red:#d93025;--red2:#f05545;--redbg:rgba(217,48,37,.08);
    --blue:#2d7dd2;--blue2:#4d9de0;--amber:#d4a017;--amber2:#f0c040;
    --mono:'IBM Plex Mono',monospace;--sans:'IBM Plex Sans',sans-serif;
}
html,body,.stApp{background:var(--bg)!important;color:var(--text);font-family:var(--sans);}
.block-container{padding:1.8rem 2.2rem 4rem!important;max-width:1640px;}
section[data-testid="stSidebar"]{display:none!important;}
hr{border-color:var(--border)!important;}
h1,h2,h3{font-family:var(--mono);color:var(--text);}

/* HEADER */
.mp-header{display:flex;align-items:center;justify-content:space-between;
           border-bottom:1px solid var(--border);padding-bottom:14px;margin-bottom:26px;}
.mp-brand{display:flex;align-items:center;gap:10px;}
.mp-dot{width:8px;height:8px;border-radius:50%;background:var(--green2);
        box-shadow:0 0 10px var(--green2),0 0 20px rgba(61,209,99,.3);
        animation:livepulse 2s ease-in-out infinite;}
@keyframes livepulse{0%,100%{opacity:1;transform:scale(1)}50%{opacity:.4;transform:scale(.8)}}
.mp-title{font-family:var(--mono);font-size:1rem;font-weight:600;
          letter-spacing:.1em;color:var(--text);text-transform:uppercase;}
.mp-sub{font-family:var(--mono);font-size:.65rem;color:var(--muted);
        letter-spacing:.15em;text-transform:uppercase;}

/* DISCLAIMER */
.disc-overlay{position:fixed;inset:0;background:rgba(6,8,13,.97);
              backdrop-filter:blur(12px);z-index:9999;
              display:flex;align-items:center;justify-content:center;}
.disc-box{background:var(--bg2);border:1px solid var(--border2);
          border-top:3px solid var(--blue2);border-radius:6px;
          padding:46px 52px;max-width:580px;width:92%;
          box-shadow:0 40px 120px rgba(0,0,0,.9);}
.disc-title{font-family:var(--mono);font-size:1rem;font-weight:600;
            letter-spacing:.12em;color:var(--text);text-transform:uppercase;margin-bottom:6px;}
.disc-sub{font-family:var(--mono);font-size:.62rem;color:var(--blue2);
          letter-spacing:.15em;text-transform:uppercase;margin-bottom:28px;}
.disc-body{font-size:.84rem;color:var(--muted2);line-height:1.85;
           font-family:var(--sans);margin-bottom:28px;}
.disc-body b{color:var(--text);font-weight:500;}
.disc-warn{background:rgba(217,48,37,.08);border:1px solid rgba(217,48,37,.18);
           border-radius:4px;padding:12px 16px;font-family:var(--mono);
           font-size:.72rem;color:var(--red2);margin-bottom:28px;line-height:1.7;}

/* STOCK CARDS */
.scard{background:var(--bg2);border:1px solid var(--border);border-radius:6px;
       padding:12px 13px 8px;cursor:pointer;position:relative;overflow:hidden;
       transition:border-color .2s,box-shadow .2s,transform .18s,background .2s;
       display:block;width:100%;box-sizing:border-box;}
.scard:hover{border-color:var(--border2);
             box-shadow:0 0 0 1px var(--border2),0 12px 40px rgba(0,0,0,.55);
             transform:translateY(-2px);background:var(--bg3);}
.scard.up{border-left:3px solid var(--green);}
.scard.down{border-left:3px solid var(--red);}
.scard.neu{border-left:3px solid var(--border2);}
.sc-top{display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:2px;}
.sc-symbol{font-family:var(--mono);font-size:.86rem;font-weight:600;
           color:var(--text);letter-spacing:.04em;}
.sc-badge{font-family:var(--mono);font-size:.58rem;padding:2px 6px;
          border-radius:20px;font-weight:500;white-space:nowrap;}
.sc-badge.up{background:var(--greenbg);color:var(--green2);border:1px solid rgba(61,209,99,.25);}
.sc-badge.dn{background:var(--redbg);color:var(--red2);border:1px solid rgba(240,85,69,.25);}
.sc-name{font-size:.65rem;color:var(--muted);margin-bottom:4px;
         white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
.sc-price{font-family:var(--mono);font-size:.92rem;font-weight:500;
          color:var(--text);display:block;margin-bottom:6px;}
.sc-spark{width:100%;height:40px;display:block;border-radius:3px;overflow:hidden;line-height:0;}
.sc-spark svg{width:100%!important;height:40px!important;display:block;}
/* pulse the spark line */
@keyframes sparkglow{0%,100%{opacity:1}50%{opacity:.6}}
.scard .sc-spark polyline{animation:sparkglow 3s ease-in-out infinite;}
.sc-nodata{font-family:var(--mono);font-size:.7rem;color:var(--muted);margin-top:10px;}

/* SECTION HEADERS */
.section-hdr{display:flex;align-items:center;gap:12px;border-bottom:1px solid var(--border);
             padding-bottom:10px;margin:28px 0 16px;}
.section-hdr-label{font-family:var(--mono);font-size:.68rem;font-weight:500;
                   color:var(--muted);letter-spacing:.18em;text-transform:uppercase;}
.section-hdr-count{font-family:var(--mono);font-size:.65rem;color:var(--muted);
                   background:var(--bg3);border:1px solid var(--border);
                   border-radius:20px;padding:2px 9px;}

/* DETAIL */
.dv-breadcrumb{font-family:var(--mono);font-size:.72rem;color:var(--muted);
               letter-spacing:.07em;margin-bottom:16px;padding-top:2px;}
.dv-breadcrumb span{color:var(--text);}
.dv-title{font-family:var(--mono);font-size:1.55rem;font-weight:600;
          color:var(--text);letter-spacing:.04em;}
.dv-subtitle{font-family:var(--sans);font-size:.83rem;color:var(--muted2);
             margin-top:2px;margin-bottom:20px;}
.mstrip{display:flex;border:1px solid var(--border);border-radius:4px;overflow:hidden;margin:14px 0;}
.mcell{flex:1;padding:13px 17px;border-right:1px solid var(--border);background:var(--bg2);}
.mcell:last-child{border-right:none;}
.mlabel{font-size:.65rem;color:var(--muted);text-transform:uppercase;
        letter-spacing:.13em;font-family:var(--sans);margin-bottom:5px;}
.mvalue{font-family:var(--mono);font-size:.97rem;font-weight:500;color:var(--text);}
.mvalue.up{color:var(--green2);}
.mvalue.dn{color:var(--red2);}
.mvalue.amber{color:var(--amber2);}

/* INSIGHT */
.insight{background:var(--bg2);border:1px solid var(--border);
         border-left:2px solid var(--blue2);border-radius:0 4px 4px 0;
         padding:12px 17px;font-size:.84rem;color:var(--muted2);
         line-height:1.75;font-family:var(--sans);margin-bottom:14px;}
.insight b{color:var(--text);font-weight:500;}
.insight.warn{border-left-color:var(--amber2);}
.insight.good{border-left-color:var(--green2);}
.insight.bad{border-left-color:var(--red2);}

/* PROBABILITY */
.prob-box{background:var(--bg2);border:1px solid var(--border);border-radius:4px;
          padding:16px 20px;margin-bottom:14px;}
.prob-title{font-family:var(--mono);font-size:.68rem;color:var(--muted);
            text-transform:uppercase;letter-spacing:.15em;margin-bottom:12px;}
.prob-row{display:flex;justify-content:space-between;align-items:center;
          padding:6px 0;border-bottom:1px solid var(--border);}
.prob-row:last-child{border-bottom:none;}
.prob-label{font-family:var(--sans);font-size:.8rem;color:var(--muted2);}
.prob-val{font-family:var(--mono);font-size:.88rem;font-weight:500;}

/* STRATEGY */
.strat-card{background:var(--bg2);border:1px solid var(--border);border-radius:5px;
            padding:12px 14px;height:100%;}
.strat-card.selected{background:var(--bg3);border-color:var(--blue2);}
.strat-title{font-family:var(--mono);font-size:.78rem;font-weight:600;
             color:var(--text);margin-bottom:4px;}
.strat-desc{font-size:.7rem;color:var(--muted2);line-height:1.5;margin-bottom:6px;}
.strat-badge{display:inline-block;font-family:var(--mono);font-size:.56rem;
             padding:2px 6px;border-radius:20px;text-transform:uppercase;letter-spacing:.1em;}
.strat-badge.momentum{background:rgba(77,157,224,.12);color:var(--blue2);border:1px solid rgba(77,157,224,.2);}
.strat-badge.reversal{background:rgba(240,196,64,.1);color:var(--amber2);border:1px solid rgba(240,196,64,.2);}
.strat-badge.trend{background:rgba(61,209,99,.1);color:var(--green2);border:1px solid rgba(61,209,99,.2);}
.strat-badge.swing{background:rgba(240,85,69,.1);color:var(--red2);border:1px solid rgba(240,85,69,.2);}
.strat-badge.volatility{background:rgba(212,160,23,.1);color:var(--amber);border:1px solid rgba(212,160,23,.2);}

/* TRADE TABLE */
.trade-table{width:100%;border-collapse:collapse;font-family:var(--mono);font-size:.75rem;margin-top:12px;}
.trade-table th{border-bottom:1px solid var(--border2);padding:7px 10px;color:var(--muted);
                text-transform:uppercase;letter-spacing:.1em;font-size:.6rem;
                text-align:left;font-weight:400;background:var(--bg3);}
.trade-table td{padding:7px 10px;border-bottom:1px solid var(--border);color:var(--text);}
.trade-table tr:hover td{background:var(--bg3);}
.td-profit{color:var(--green2);}
.td-loss{color:var(--red2);}

/* SIM PROGRESS BAR */
.sim-bar-wrap{background:var(--bg3);border:1px solid var(--border);border-radius:4px;
              height:6px;overflow:hidden;margin:8px 0;}
.sim-bar{height:100%;background:linear-gradient(90deg,var(--blue),var(--blue2));
         transition:width .3s ease;border-radius:4px;}

/* STREAMLIT OVERRIDES */
.stTextInput input,.stNumberInput input{
    background:var(--bg2)!important;border:1px solid var(--border)!important;
    border-radius:4px!important;color:var(--text)!important;
    font-family:var(--mono)!important;font-size:.86rem!important;}
label[data-testid="stWidgetLabel"] p{
    font-size:.65rem!important;color:var(--muted)!important;
    text-transform:uppercase!important;letter-spacing:.13em!important;
    font-family:var(--sans)!important;}
div[data-testid="stButton"]>button{
    background:transparent!important;border:1px solid var(--border2)!important;
    color:var(--muted2)!important;font-family:var(--mono)!important;
    font-size:.73rem!important;letter-spacing:.07em!important;
    border-radius:3px!important;padding:5px 14px!important;transition:all .15s!important;}
div[data-testid="stButton"]>button:hover{
    background:var(--bg4)!important;border-color:var(--muted2)!important;color:var(--text)!important;}
div[data-baseweb="tab-list"]{background:var(--bg2)!important;border:1px solid var(--border)!important;
    border-radius:4px!important;padding:3px!important;gap:2px!important;}
div[data-baseweb="tab"]{font-family:var(--mono)!important;font-size:.72rem!important;
    color:var(--muted)!important;letter-spacing:.06em!important;
    padding:7px 15px!important;border-radius:3px!important;}
div[data-baseweb="tab"][aria-selected="true"]{background:var(--bg4)!important;color:var(--text)!important;}
div[data-baseweb="tab-highlight"],div[data-baseweb="tab-border"]{display:none!important;}
.stSelectbox div[data-baseweb="select"]>div{
    background:var(--bg2)!important;border:1px solid var(--border)!important;
    border-radius:4px!important;color:var(--text)!important;
    font-family:var(--mono)!important;font-size:.84rem!important;}
.js-plotly-plot .plotly .modebar{display:none!important;}

.mp-footer{margin-top:56px;border-top:1px solid var(--border);padding-top:14px;
           font-family:var(--mono);font-size:.63rem;color:var(--muted);letter-spacing:.09em;}
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════
# 5. HELPERS
# ══════════════════════════════════════════════════════════════════════
CHART_FONT = dict(family="'IBM Plex Mono','Courier New',monospace", size=11, color="#48566a")

def clean(ticker):
    return ticker.replace(".NS","").replace("-USD","")

def asset_class(ticker):
    if "USD" in ticker: return "crypto"
    if ".NS"  in ticker: return "nse"
    return "sp500"

@st.cache_data(ttl=300, show_spinner=False)
def fetch_card_data(ticker):
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
def fetch_ohlcv(ticker, period, interval):
    try:
        df = yf.download(ticker, period=period, interval=interval,
                         progress=False, auto_adjust=False)
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        return df
    except Exception:
        return pd.DataFrame()

@st.cache_data(ttl=300, show_spinner=False)
def fetch_history(ticker, period="1y"):
    return fetch_ohlcv(ticker, period, "1d")

# ══════════════════════════════════════════════════════════════════════
# 6. INLINE SVG SPARKLINE — embedded inside card HTML
# ══════════════════════════════════════════════════════════════════════
def build_sparkline_svg(values, is_up, width=200, height=40):
    vals = [v for v in values if v is not None and not (isinstance(v, float) and np.isnan(v))]
    if len(vals) < 2:
        return ""
    mn, mx = min(vals), max(vals)
    rng = mx - mn if mx != mn else 1
    xs  = [i / (len(vals)-1) * width for i in range(len(vals))]
    ys  = [height - ((v - mn) / rng) * (height - 6) - 3 for v in vals]
    pts = " ".join(f"{x:.1f},{y:.1f}" for x, y in zip(xs, ys))
    fill_pts = f"0,{height} " + pts + f" {width},{height}"
    color      = "#2ea84a" if is_up else "#d93025"
    fill_color = "rgba(46,168,74,0.14)" if is_up else "rgba(217,48,37,0.14)"
    return (
        f'<svg viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg" '
        f'preserveAspectRatio="none" style="width:100%;height:{height}px;display:block;">'
        f'<polygon points="{fill_pts}" fill="{fill_color}" />'
        f'<polyline points="{pts}" fill="none" stroke="{color}" stroke-width="1.7" '
        f'stroke-linejoin="round" stroke-linecap="round"/>'
        f'</svg>'
    )

# ══════════════════════════════════════════════════════════════════════
# 7. PREDICTION ENGINE
# ══════════════════════════════════════════════════════════════════════
VOL_CAPS = {"crypto": 0.08, "nse": 0.04, "sp500": 0.03}

def honest_eod_prediction(ticker, df_day):
    returns  = df_day["Close"].pct_change().dropna()
    n_obs    = len(returns)
    vol_raw  = float(returns.std()) if n_obs > 1 else 0.01
    ac       = asset_class(ticker)
    cap      = VOL_CAPS[ac]
    vol_used = min(vol_raw, cap)
    confidence = "low" if n_obs < 30 else ("medium" if n_obs < 120 else "high")
    n_sims   = 10_000
    day_open = float(df_day["Open"].iloc[0])
    draws    = np.random.normal(0, vol_used, n_sims)
    eod_dist = day_open * np.exp(draws)
    bull, p75, median, p25, bear = np.percentile(eod_dist, [95, 75, 50, 25, 5])
    up_prob  = float(np.mean(eod_dist > day_open) * 100)
    warning  = None
    if vol_raw > cap:
        warning = (f"Raw volatility ({vol_raw*100:.2f}%) exceeds {ac.upper()} cap "
                   f"({cap*100:.0f}%). Cap applied — range narrowed.")
    if confidence == "low":
        warning = (warning or "") + " LOW confidence — indicative only."
    return {
        "median": median, "bull": bull, "bear": bear, "p75": p75, "p25": p25,
        "vol_raw": vol_raw, "vol_used": vol_used,
        "confidence": confidence, "n_sims": n_sims,
        "warning": warning, "day_open": day_open, "up_prob": up_prob,
    }

# ══════════════════════════════════════════════════════════════════════
# 8. TECHNICAL INDICATORS
# ══════════════════════════════════════════════════════════════════════
def rsi(s, n=14):
    d = s.diff(); g = d.clip(lower=0).rolling(n).mean()
    l = (-d.clip(upper=0)).rolling(n).mean()
    return 100 - 100/(1 + g/l.replace(0, np.nan))

def macd(s, fast=12, slow=26, sig=9):
    m = s.ewm(span=fast,adjust=False).mean() - s.ewm(span=slow,adjust=False).mean()
    sg = m.ewm(span=sig,adjust=False).mean()
    return m, sg, m - sg

def bollinger(s, n=20, k=2):
    mid = s.rolling(n).mean(); std = s.rolling(n).std()
    return mid+k*std, mid, mid-k*std

def atr(df, n=14):
    h,l,c = df["High"],df["Low"],df["Close"]
    tr = pd.concat([h-l,(h-c.shift()).abs(),(l-c.shift()).abs()],axis=1).max(axis=1)
    return tr.rolling(n).mean()

def stochastic(df, k=14, d=3):
    lo = df["Low"].rolling(k).min(); hi = df["High"].rolling(k).max()
    k_pct = 100*(df["Close"]-lo)/(hi-lo+1e-9)
    return k_pct, k_pct.rolling(d).mean()

def cci(df, n=20):
    tp = (df["High"]+df["Low"]+df["Close"])/3
    return (tp - tp.rolling(n).mean()) / (0.015*tp.rolling(n).std())

def williams_r(df, n=14):
    hi = df["High"].rolling(n).max(); lo = df["Low"].rolling(n).min()
    return -100*(hi-df["Close"])/(hi-lo+1e-9)

def adx_calc(df, n=14):
    h,l,c = df["High"],df["Low"],df["Close"]
    up = h.diff(); dn = -l.diff()
    pdm = up.where((up>dn)&(up>0),0); ndm = dn.where((dn>up)&(dn>0),0)
    tr_ = atr(df, n)
    pdi = 100*pdm.ewm(span=n,adjust=False).mean()/tr_.replace(0,np.nan)
    ndi = 100*ndm.ewm(span=n,adjust=False).mean()/tr_.replace(0,np.nan)
    dx  = 100*(pdi-ndi).abs()/(pdi+ndi+1e-9)
    return dx.ewm(span=n,adjust=False).mean(), pdi, ndi

def obv(df):
    direction = np.sign(df["Close"].diff().fillna(0))
    return (direction * df["Volume"]).cumsum()

def vwap(df):
    tp = (df["High"]+df["Low"]+df["Close"])/3
    vol = df["Volume"].replace(0,np.nan)
    return (tp*vol).cumsum()/vol.cumsum()

# ══════════════════════════════════════════════════════════════════════
# 9. 25 STRATEGIES REGISTRY
# ══════════════════════════════════════════════════════════════════════
STRATEGIES = {
    "Dual MA (10/30)":          {"desc":"Golden/Death Cross 10 & 30-day SMAs","badge":"trend","logic":"dma_10_30","how":"BUY when SMA-10 crosses above SMA-30 (Golden Cross). SELL when it crosses below (Death Cross). Classic trend-following that catches sustained moves."},
    "Dual MA (20/50)":          {"desc":"Longer-period Golden/Death Cross 20 & 50-day","badge":"trend","logic":"dma_20_50","how":"BUY on 20-SMA crossing above 50-SMA. SELL on reverse. More reliable signals, fewer false entries than the 10/30."},
    "EMA Crossover (9/21)":     {"desc":"Fast EMA-9 / Slow EMA-21 crossover","badge":"trend","logic":"ema_9_21","how":"EMA gives more weight to recent prices. BUY when EMA-9 crosses above EMA-21. SELL on reverse. Reacts faster than SMA."},
    "Triple MA (5/10/20)":      {"desc":"All three MAs must align for entry","badge":"trend","logic":"triple_ma","how":"BUY only when SMA-5 > SMA-10 > SMA-20 (full bullish alignment). SELL when fast drops below mid. Reduces false signals."},
    "ADX Trend Filter":         {"desc":"Only trade when ADX>25 confirms strong trend","badge":"trend","logic":"adx_trend","how":"BUY when ADX > 25 AND +DI crosses above -DI. SELL when -DI takes over. Avoids choppy, sideways markets."},
    "MACD Crossover":           {"desc":"Classic MACD (12,26,9) signal-line cross","badge":"trend","logic":"macd_classic","how":"BUY when MACD line crosses above Signal line. SELL on reverse. Histogram width shows momentum strength."},
    "MACD Histogram Flip":      {"desc":"Histogram flip gives earlier entry than line cross","badge":"trend","logic":"macd_hist","how":"BUY when histogram flips negative→positive. SELL on flip back. Enters 1-3 bars earlier than standard MACD."},
    "RSI Oversold/Overbought":  {"desc":"RSI-14: buy at 30 oversold, sell at 70 overbought","badge":"reversal","logic":"rsi_classic","how":"BUY when RSI crosses above 30 from below. SELL when RSI crosses below 70 from above. Best in ranging markets."},
    "RSI Midline Cross":        {"desc":"RSI crossing 50 = momentum shift signal","badge":"momentum","logic":"rsi_50","how":"BUY when RSI crosses above 50 (bulls take control). SELL when RSI crosses below 50. More frequent signals."},
    "Stochastic Cross":         {"desc":"Stochastic %K/%D cross in extreme zones","badge":"reversal","logic":"stoch","how":"BUY when %K crosses above %D in oversold zone (<20). SELL when %K crosses below %D in overbought zone (>80)."},
    "CCI Breakout ±100":        {"desc":"CCI breaking ±100 signals strong momentum","badge":"momentum","logic":"cci","how":"BUY when CCI breaks above +100 (strong upside momentum). SELL when it drops below -100. Uses 20-period cycle."},
    "Williams %R":              {"desc":"Fast oscillator — oversold/overbought entries","badge":"reversal","logic":"williams","how":"BUY when %R crosses above -80 (leaves oversold). SELL when it drops below -20 (enters overbought)."},
    "Rate of Change (ROC)":     {"desc":"Price momentum crossing zero","badge":"momentum","logic":"roc","how":"BUY when 10-day ROC crosses above 0 (positive momentum). SELL when it crosses below 0. Pure price-momentum signal."},
    "Bollinger Band Touch":     {"desc":"Mean reversion from lower to middle band","badge":"reversal","logic":"bb_touch","how":"BUY when price touches the lower Bollinger Band. SELL when it returns to the middle band (20-SMA). Classic mean-reversion."},
    "Bollinger Squeeze":        {"desc":"Low volatility squeeze precedes breakout","badge":"volatility","logic":"bb_squeeze","how":"When bands narrow to a 120-day low (squeeze), BUY on break above upper band. Catches volatility expansion moves."},
    "ATR Breakout":             {"desc":"Price moving >1.5× ATR signals breakout","badge":"momentum","logic":"atr_breakout","how":"BUY when today's close is >1.5 ATR above prior close. SELL on reverse. Catches explosive single-session moves."},
    "Keltner Channel":          {"desc":"ATR-based channel around EMA-20","badge":"volatility","logic":"keltner","how":"BUY when price crosses above upper Keltner Channel (EMA±2×ATR). SELL when it drops below EMA. Smoother than Bollinger."},
    "OBV Trend":                {"desc":"On-Balance Volume crossing its own SMA","badge":"momentum","logic":"obv_trend","how":"BUY when OBV crosses above its 10-day SMA (buying pressure rising). SELL on reverse. Volume leads price."},
    "Volume Spike":             {"desc":"2× average volume signals institutional activity","badge":"momentum","logic":"vol_spike","how":"BUY on bullish volume spike (vol > 2× 20-day avg AND close > open). SELL on bearish spike. Follows smart money."},
    "Donchian Breakout (20)":   {"desc":"Turtle Trader: buy 20-day highs, sell 20-day lows","badge":"swing","logic":"donchian","how":"BUY when price breaks above 20-day high. SELL when it breaks below 20-day low. Trend-following with clear levels."},
    "Higher High / Lower Low":  {"desc":"Price action structure breakouts","badge":"swing","logic":"hhhl","how":"BUY when close breaks above rolling 5-day high. SELL when it breaks below 5-day low. Pure price structure, no lagging indicators."},
    "VWAP Crossover":           {"desc":"VWAP is institutional fair value — bias shift","badge":"momentum","logic":"vwap_cross","how":"BUY when close crosses above VWAP. SELL on reverse. Heavily used by institutional traders and day-trading algorithms."},
    "Parabolic SAR":            {"desc":"Stop-and-reverse dots track active trend","badge":"trend","logic":"psar","how":"BUY when SAR flips below price (dots move under candles). SELL when SAR flips above. Provides built-in trailing stop logic."},
    "Z-Score Reversion":        {"desc":"Statistically extreme price reverts to mean","badge":"reversal","logic":"zscore","how":"BUY when 20-day Z-score drops below -2 (statistically cheap). SELL when it rises above +1. Statistical arbitrage approach."},
    "RSI + MACD Confluence":    {"desc":"Dual confirmation: RSI oversold AND MACD cross","badge":"momentum","logic":"rsi_macd","how":"BUY only when RSI < 40 AND MACD crosses above signal. SELL when RSI > 65 OR MACD bearish cross. Higher-quality, fewer signals."},
}

# ══════════════════════════════════════════════════════════════════════
# 10. SIGNAL GENERATORS
# ══════════════════════════════════════════════════════════════════════
def generate_signals(df, logic):
    c = df["Close"].squeeze()
    b = pd.Series(False, index=df.index)
    s = pd.Series(False, index=df.index)

    if logic == "dma_10_30":
        f,sl = c.rolling(10).mean(), c.rolling(30).mean()
        b=(f>sl)&(f.shift(1)<=sl.shift(1)); s=(f<sl)&(f.shift(1)>=sl.shift(1))
    elif logic == "dma_20_50":
        f,sl = c.rolling(20).mean(), c.rolling(50).mean()
        b=(f>sl)&(f.shift(1)<=sl.shift(1)); s=(f<sl)&(f.shift(1)>=sl.shift(1))
    elif logic == "ema_9_21":
        f=c.ewm(span=9,adjust=False).mean(); sl=c.ewm(span=21,adjust=False).mean()
        b=(f>sl)&(f.shift(1)<=sl.shift(1)); s=(f<sl)&(f.shift(1)>=sl.shift(1))
    elif logic == "triple_ma":
        a,m,sl=c.rolling(5).mean(),c.rolling(10).mean(),c.rolling(20).mean()
        aligned=(a>m)&(m>sl); prev=(a.shift(1)>m.shift(1))&(m.shift(1)>sl.shift(1))
        b=aligned&~prev; s=(a<m)&(a.shift(1)>=m.shift(1))
    elif logic == "adx_trend":
        adx_,pdi,ndi=adx_calc(df,14)
        b=(adx_>25)&(pdi>ndi)&(pdi.shift(1)<=ndi.shift(1))
        s=(pdi<ndi)&(pdi.shift(1)>=ndi.shift(1))
    elif logic == "macd_classic":
        ml,sg,_=macd(c); b=(ml>sg)&(ml.shift(1)<=sg.shift(1)); s=(ml<sg)&(ml.shift(1)>=sg.shift(1))
    elif logic == "macd_hist":
        _,_,hist=macd(c); b=(hist>0)&(hist.shift(1)<=0); s=(hist<0)&(hist.shift(1)>=0)
    elif logic == "rsi_classic":
        r=rsi(c,14); b=(r>30)&(r.shift(1)<=30); s=(r<70)&(r.shift(1)>=70)
    elif logic == "rsi_50":
        r=rsi(c,14); b=(r>50)&(r.shift(1)<=50); s=(r<50)&(r.shift(1)>=50)
    elif logic == "stoch":
        k,d=stochastic(df,14,3)
        b=(k>d)&(k.shift(1)<=d.shift(1))&(k<25); s=(k<d)&(k.shift(1)>=d.shift(1))&(k>75)
    elif logic == "cci":
        cc=cci(df,20); b=(cc>100)&(cc.shift(1)<=100); s=(cc<-100)&(cc.shift(1)>=-100)
    elif logic == "williams":
        wr=williams_r(df,14); b=(wr>-80)&(wr.shift(1)<=-80); s=(wr<-20)&(wr.shift(1)>=-20)
    elif logic == "roc":
        r=c.pct_change(10)*100; b=(r>0)&(r.shift(1)<=0); s=(r<0)&(r.shift(1)>=0)
    elif logic == "bb_touch":
        _,mid,lo=bollinger(c,20,2)
        b=(c<lo)&(c.shift(1)>=lo.shift(1)); s=(c>mid)&(c.shift(1)<=mid.shift(1))
    elif logic == "bb_squeeze":
        up,mid,lo=bollinger(c,20,2); bw=up-lo
        bw_min=bw.rolling(120,min_periods=20).min(); squeeze=bw<=bw_min*1.1
        b=(c>up)&squeeze.shift(1).fillna(False); s=(c<lo)
    elif logic == "atr_breakout":
        a=atr(df,14); b=(c-c.shift(1))>1.5*a; s=(c.shift(1)-c)>1.5*a
    elif logic == "keltner":
        ema20=c.ewm(span=20,adjust=False).mean(); a=atr(df,14); upper=ema20+2*a
        b=(c>upper)&(c.shift(1)<=upper.shift(1)); s=(c<ema20)&(c.shift(1)>=ema20.shift(1))
    elif logic == "obv_trend":
        o=obv(df); osma=o.rolling(10).mean()
        b=(o>osma)&(o.shift(1)<=osma.shift(1)); s=(o<osma)&(o.shift(1)>=osma.shift(1))
    elif logic == "vol_spike":
        vol=df["Volume"]; avg=vol.rolling(20).mean()
        b=(vol>2*avg)&(c>df["Open"].squeeze()); s=(vol>2*avg)&(c<df["Open"].squeeze())
    elif logic == "donchian":
        hi=c.rolling(20).max(); lo=c.rolling(20).min()
        b=(c>hi.shift(1))&(c.shift(1)<=hi.shift(2)); s=(c<lo.shift(1))&(c.shift(1)>=lo.shift(2))
    elif logic == "hhhl":
        b=(c>c.rolling(5).max().shift(1)); s=(c<c.rolling(5).min().shift(1))
    elif logic == "vwap_cross":
        vw=vwap(df); b=(c>vw)&(c.shift(1)<=vw.shift(1)); s=(c<vw)&(c.shift(1)>=vw.shift(1))
    elif logic == "psar":
        sar=c.rolling(5).min().shift(1)
        b=(c>sar)&(c.shift(1)<=sar.shift(1)); s=(c<sar)&(c.shift(1)>=sar.shift(1))
    elif logic == "zscore":
        mu=c.rolling(20).mean(); sd=c.rolling(20).std(); z=(c-mu)/sd.replace(0,np.nan)
        b=(z<-2)&(z.shift(1)>=-2); s=(z>1)&(z.shift(1)<=1)
    elif logic == "rsi_macd":
        r=rsi(c,14); ml,sg,_=macd(c)
        b=(r<40)&(ml>sg)&(ml.shift(1)<=sg.shift(1))
        s=(r>65)&(ml<sg)

    return b.fillna(False), s.fillna(False)

# ══════════════════════════════════════════════════════════════════════
# 11. BACKTESTER
# ══════════════════════════════════════════════════════════════════════
def backtest(df, strategy_key, capital):
    if df.empty or len(df) < 50:
        return {"error": "Need at least 50 trading days of data."}
    close = df["Close"].squeeze()
    dates = df.index
    logic = STRATEGIES[strategy_key]["logic"]
    buy_s, sell_s = generate_signals(df, logic)

    trades, equity_curve = [], [capital]
    cash, position, entry_price, entry_date = capital, 0.0, None, None

    for i, date in enumerate(dates):
        px = float(close.iloc[i])
        if buy_s.iloc[i] and position == 0 and cash > 0:
            position, entry_price, entry_date, cash = cash/px, px, date, 0.0
        elif sell_s.iloc[i] and position > 0:
            proceeds = position * px
            trades.append({
                "entry_date": entry_date.strftime("%d %b %Y"),
                "exit_date":  date.strftime("%d %b %Y"),
                "entry_price": entry_price, "exit_price": px,
                "shares": round(position,4),
                "pnl": proceeds - position*entry_price,
                "pnl_pct": (px-entry_price)/entry_price*100,
            })
            cash, position = proceeds, 0.0
        equity_curve.append(cash + position*px)

    final_px = float(close.iloc[-1])
    if position > 0:
        trades.append({
            "entry_date": entry_date.strftime("%d %b %Y"), "exit_date": "OPEN",
            "entry_price": entry_price, "exit_price": final_px,
            "shares": round(position,4),
            "pnl": position*final_px - position*entry_price,
            "pnl_pct": (final_px-entry_price)/entry_price*100,
        })

    total_val = cash + position*final_px
    closed    = [t for t in trades if t["exit_date"] != "OPEN"]
    n_wins    = sum(1 for t in closed if t["pnl"] > 0)
    bh_return = (final_px/float(close.iloc[0])-1)*100

    return {
        "trades": trades, "equity_curve": equity_curve,
        "total_pnl": total_val - capital,
        "total_pnl_pct": (total_val-capital)/capital*100,
        "final_value": total_val, "n_trades": len(closed),
        "win_rate": (n_wins/len(closed)*100) if closed else 0,
        "buy_signals": buy_s, "sell_signals": sell_s,
        "close": close, "dates": dates, "capital": capital,
        "bh_return": bh_return, "error": None,
    }

# ══════════════════════════════════════════════════════════════════════
# 12. CHART BUILDERS
# ══════════════════════════════════════════════════════════════════════
def candle_fig(df):
    fig = go.Figure(go.Candlestick(
        x=df.index, open=df["Open"], high=df["High"], low=df["Low"], close=df["Close"],
        increasing_line_color="#2ea84a", decreasing_line_color="#d93025",
        increasing_fillcolor="#2ea84a", decreasing_fillcolor="#d93025",
    ))
    fig.update_layout(
        template="plotly_dark", height=460,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#06080d",
        xaxis_rangeslider_visible=False, font=CHART_FONT,
        margin=dict(l=10,r=10,t=10,b=30),
    )
    return fig

def prediction_fig(df_day, pred):
    close = df_day["Close"].squeeze()
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df_day.index, y=close, name="Price",
                             line=dict(color="#4d9de0",width=2)))
    fig.add_hline(y=pred["bull"],    line=dict(color="#3dd163",dash="dot",width=1),   annotation_text="Bull 95%", annotation_position="right")
    fig.add_hline(y=pred["p75"],     line=dict(color="#3dd163",dash="dot",width=1,opacity=0.45))
    fig.add_hline(y=pred["median"],  line=dict(color="#f0c040",dash="dash",width=1.5),annotation_text="Median",  annotation_position="right")
    fig.add_hline(y=pred["p25"],     line=dict(color="#f05545",dash="dot",width=1,opacity=0.45))
    fig.add_hline(y=pred["bear"],    line=dict(color="#f05545",dash="dot",width=1),   annotation_text="Bear 5%", annotation_position="right")
    fig.add_hline(y=pred["day_open"],line=dict(color="#7a8ba0",dash="dash",width=1),  annotation_text="Open",    annotation_position="right")
    fig.update_layout(
        template="plotly_dark", height=400,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#06080d",
        font=CHART_FONT, showlegend=True,
        margin=dict(l=10,r=80,t=10,b=30),
        legend=dict(bgcolor="rgba(0,0,0,0)",font=dict(size=10)),
    )
    return fig

def strategy_chart(result, strategy_key):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=result["dates"], y=result["close"],
                             name="Price", line=dict(color="#7a8ba0",width=1.5)))
    fig.add_trace(go.Scatter(
        x=result["dates"][result["buy_signals"]], y=result["close"][result["buy_signals"]],
        name="Buy", mode="markers",
        marker=dict(symbol="triangle-up",size=11,color="#3dd163",line=dict(color="#1a6632",width=1))))
    fig.add_trace(go.Scatter(
        x=result["dates"][result["sell_signals"]], y=result["close"][result["sell_signals"]],
        name="Sell", mode="markers",
        marker=dict(symbol="triangle-down",size=11,color="#f05545",line=dict(color="#8b1e1a",width=1))))
    fig.update_layout(
        template="plotly_dark", height=420,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#06080d",
        font=CHART_FONT, margin=dict(l=10,r=10,t=10,b=30),
    )
    return fig

def equity_chart(result):
    close = result["close"]
    bh    = [result["capital"]*(float(close.iloc[i])/float(close.iloc[0])) for i in range(len(close))]
    curve = result["equity_curve"]
    color = "#3dd163" if curve[-1]>=curve[0] else "#f05545"
    fill  = "rgba(61,209,99,0.08)" if color=="#3dd163" else "rgba(240,85,69,0.08)"
    fig = go.Figure()
    fig.add_trace(go.Scatter(y=bh, mode="lines", name="Buy & Hold",
                             line=dict(color="#4d9de0",dash="dash",width=1.2)))
    fig.add_trace(go.Scatter(y=curve, mode="lines", fill="tozeroy",
                             fillcolor=fill, name="Strategy",
                             line=dict(color=color,width=2)))
    fig.update_layout(
        template="plotly_dark", height=220,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#06080d",
        font=CHART_FONT, showlegend=True,
        legend=dict(bgcolor="rgba(0,0,0,0)",font=dict(size=10)),
        margin=dict(l=10,r=10,t=10,b=30),
    )
    return fig

def live_sim_chart(result, step):
    close = result["close"]; dates = result["dates"]
    n     = min(step, len(close))
    sub_c = close.iloc[:n]; sub_d = dates[:n]
    eq    = result["equity_curve"][:n+1]
    fig   = make_subplots(rows=2, cols=1, row_heights=[0.65,0.35],
                          shared_xaxes=True, vertical_spacing=0.04)
    fig.add_trace(go.Scatter(x=sub_d, y=sub_c, name="Price",
                             line=dict(color="#7a8ba0",width=1.5)), row=1,col=1)
    bm = result["buy_signals"].iloc[:n]; sm = result["sell_signals"].iloc[:n]
    if bm.any():
        fig.add_trace(go.Scatter(x=sub_d[bm], y=sub_c[bm], name="Buy", mode="markers",
                                 marker=dict(symbol="triangle-up",size=11,color="#3dd163")), row=1,col=1)
    if sm.any():
        fig.add_trace(go.Scatter(x=sub_d[sm], y=sub_c[sm], name="Sell", mode="markers",
                                 marker=dict(symbol="triangle-down",size=11,color="#f05545")), row=1,col=1)
    if n > 0:
        fig.add_hline(y=float(sub_c.iloc[-1]), line=dict(color="#f0c040",dash="dot",width=1), row=1,col=1)
    fig.add_trace(go.Scatter(y=eq, mode="lines", fill="tozeroy",
                             fillcolor="rgba(61,209,99,0.08)", name="Equity",
                             line=dict(color="#3dd163",width=1.8)), row=2,col=1)
    fig.update_layout(
        template="plotly_dark", height=520,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#06080d",
        font=CHART_FONT, showlegend=True,
        legend=dict(bgcolor="rgba(0,0,0,0)",font=dict(size=10)),
        margin=dict(l=10,r=10,t=10,b=30),
    )
    return fig


# ══════════════════════════════════════════════════════════════════════
# 14. HEADER
# ══════════════════════════════════════════════════════════════════════
st.markdown(
    f'<div class="mp-header"><div class="mp-brand"><div class="mp-dot"></div>'
    f'<div><div class="mp-title">Market Pulse</div><div class="mp-sub">Live Terminal</div></div>'
    f'</div><div class="mp-sub">{datetime.now().strftime("%d %b %Y  %H:%M")}</div></div>',
    unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════
# 15. STRATEGY VIEW
# ══════════════════════════════════════════════════════════════════════
if st.session_state.active_view == "strategy":
    ticker = st.session_state.strategy_ticker
    col_back, _ = st.columns([1,8])
    with col_back:
        if st.button("← Detail"):
            st.session_state.active_view = "detail"; st.rerun()

    st.markdown(f"<div class='dv-title'>{clean(ticker)} — Strategy Simulator</div>", unsafe_allow_html=True)
    st.markdown("<div class='dv-subtitle'>25 strategies · full backtest + live step-through simulation</div>", unsafe_allow_html=True)

    col_s, col_c, col_p = st.columns([3,2,1])
    with col_s: strat_name = st.selectbox("Select Strategy", list(STRATEGIES.keys()))
    with col_c: capital = st.number_input("Starting Capital ($)", value=10_000.0, min_value=100.0, step=500.0)
    with col_p: period_choice = st.selectbox("Period", ["6mo","1y","2y"], index=1)

    # Strategy library cards
    st.markdown('<div class="section-hdr"><span class="section-hdr-label">Strategy Library</span><span class="section-hdr-count">25</span></div>', unsafe_allow_html=True)
    keys = list(STRATEGIES.keys())
    for row_start in range(0, len(keys), 5):
        row_keys = keys[row_start:row_start+5]
        rcols = st.columns(5)
        for ci, sk in enumerate(row_keys):
            with rcols[ci]:
                meta = STRATEGIES[sk]; sel = "selected" if sk==strat_name else ""
                st.markdown(f"""<div class="strat-card {sel}">
                  <div class="strat-title">{"▶ " if sel else ""}{sk}</div>
                  <div class="strat-desc">{meta['desc']}</div>
                  <span class="strat-badge {meta['badge']}">{meta['badge']}</span>
                </div>""", unsafe_allow_html=True)

    st.markdown(f"<div class='insight'><b>How it works —</b> {STRATEGIES[strat_name]['how']}</div>", unsafe_allow_html=True)

    col_run, col_live = st.columns(2)
    run_btn  = col_run.button("▶  Run Full Backtest", type="primary")
    live_btn = col_live.button("▶  Live Simulation")

    if run_btn:
        with st.spinner("Running backtest…"):
            df_h = fetch_history(ticker, period_choice)
            res  = backtest(df_h, strat_name, capital)
            st.session_state.strategy_result = res
            st.session_state.last_strat_name = strat_name
            st.session_state.sim_running     = False
            st.session_state.sim_step        = len(res["close"]) if not res.get("error") else 0

    if live_btn:
        with st.spinner("Loading data…"):
            df_h = fetch_history(ticker, period_choice)
            res  = backtest(df_h, strat_name, capital)
            st.session_state.strategy_result = res
            st.session_state.last_strat_name = strat_name
            st.session_state.sim_running     = True
            st.session_state.sim_step        = 30

    res = st.session_state.strategy_result
    if res:
        if res.get("error"):
            st.error(res["error"])
        else:
            total_bars = len(res["close"])
            if st.session_state.sim_running:
                step = st.session_state.sim_step
                pct  = int(step/total_bars*100)
                st.markdown(f'<div class="sim-bar-wrap"><div class="sim-bar" style="width:{pct}%"></div></div>', unsafe_allow_html=True)
                st.caption(f"Replay: bar {step} / {total_bars}  ({pct}%)")
                c1,c2,c3,c4 = st.columns(4)
                if c1.button("⏩ +10"):  st.session_state.sim_step=min(step+10,total_bars);  st.rerun()
                if c2.button("⏩ +50"):  st.session_state.sim_step=min(step+50,total_bars);  st.rerun()
                if c3.button("⏩ +100"): st.session_state.sim_step=min(step+100,total_bars); st.rerun()
                if c4.button("⏭ End"):
                    st.session_state.sim_step=total_bars; st.session_state.sim_running=False; st.rerun()
                st.plotly_chart(live_sim_chart(res, st.session_state.sim_step), use_container_width=True, config={"displayModeBar":False})
                eq_now  = res["equity_curve"][min(st.session_state.sim_step, len(res["equity_curve"])-1)]
                pnl_now = eq_now - capital
                sign    = "+" if pnl_now>=0 else ""
                st.markdown(f"""<div class="mstrip">
                  <div class="mcell"><div class="mlabel">Current Value</div><div class="mvalue">${eq_now:,.2f}</div></div>
                  <div class="mcell"><div class="mlabel">P&L So Far</div><div class="mvalue {'up' if pnl_now>=0 else 'dn'}">{sign}${pnl_now:,.2f}</div></div>
                  <div class="mcell"><div class="mlabel">Bars Played</div><div class="mvalue">{st.session_state.sim_step}</div></div>
                  <div class="mcell"><div class="mlabel">Progress</div><div class="mvalue">{pct}%</div></div>
                </div>""", unsafe_allow_html=True)
            else:
                pnl_c = "up" if res["total_pnl"]>=0 else "dn"
                sign  = "+" if res["total_pnl"]>=0 else ""
                bh_c  = "up" if res["bh_return"]>=0 else "dn"
                alpha = res["total_pnl_pct"] - res["bh_return"]
                a_c   = "up" if alpha>=0 else "dn"
                st.markdown(f"""<div class="mstrip">
                  <div class="mcell"><div class="mlabel">Final Value</div><div class="mvalue">${res['final_value']:,.2f}</div></div>
                  <div class="mcell"><div class="mlabel">Total P&L</div><div class="mvalue {pnl_c}">{sign}${res['total_pnl']:,.2f} ({sign}{res['total_pnl_pct']:.2f}%)</div></div>
                  <div class="mcell"><div class="mlabel">Buy & Hold</div><div class="mvalue {bh_c}">{'+' if res['bh_return']>=0 else ''}{res['bh_return']:.2f}%</div></div>
                  <div class="mcell"><div class="mlabel">Alpha</div><div class="mvalue {a_c}">{'+' if alpha>=0 else ''}{alpha:.2f}%</div></div>
                  <div class="mcell"><div class="mlabel">Trades</div><div class="mvalue">{res['n_trades']}</div></div>
                  <div class="mcell"><div class="mlabel">Win Rate</div><div class="mvalue {'up' if res['win_rate']>=50 else 'dn'}">{res['win_rate']:.1f}%</div></div>
                </div>""", unsafe_allow_html=True)
                st.plotly_chart(strategy_chart(res, strat_name), use_container_width=True)
                st.markdown('<div class="section-hdr"><span class="section-hdr-label">Equity Curve vs Buy & Hold</span></div>', unsafe_allow_html=True)
                st.plotly_chart(equity_chart(res), use_container_width=True)
                if res["trades"]:
                    st.markdown('<div class="section-hdr"><span class="section-hdr-label">Trade Log</span></div>', unsafe_allow_html=True)
                    rows = ""
                    for t in res["trades"]:
                        css  = "td-profit" if t["pnl"]>=0 else "td-loss"
                        sign2= "+" if t["pnl"]>=0 else ""
                        rows += (f"<tr><td>{t['entry_date']}</td><td>{t['exit_date']}</td>"
                                 f"<td>{t['entry_price']:.2f}</td><td>{t['exit_price']:.2f}</td>"
                                 f"<td>{t['shares']}</td>"
                                 f"<td class='{css}'>{sign2}${t['pnl']:.2f} ({sign2}{t['pnl_pct']:.2f}%)</td></tr>")
                    st.markdown(f"""<table class="trade-table"><thead><tr>
                      <th>Entry</th><th>Exit</th><th>Entry $</th><th>Exit $</th>
                      <th>Shares</th><th>P&L</th></tr></thead><tbody>{rows}</tbody></table>""", unsafe_allow_html=True)
    st.stop()

# ══════════════════════════════════════════════════════════════════════
# 16. DETAIL VIEW
# ══════════════════════════════════════════════════════════════════════
if st.session_state.active_view == "detail":
    ticker = st.session_state.selected_stock
    name   = NAME_MAP.get(ticker, clean(ticker))

    c1,c2 = st.columns([1,1])
    with c1:
        if st.button("← Markets"):
            st.session_state.active_view = "grid"; st.rerun()
    with c2:
        if st.button("Strategy Simulator →"):
            st.session_state.active_view="strategy"; st.session_state.strategy_ticker=ticker
            st.session_state.strategy_result=None; st.rerun()

    st.markdown(f"<div class='dv-breadcrumb'>MARKETS / <span>{clean(ticker)}</span></div>", unsafe_allow_html=True)
    st.markdown(f"<div class='dv-title'>{clean(ticker)}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='dv-subtitle'>{name}</div>", unsafe_allow_html=True)

    tf_tabs = st.tabs([v["label"] for v in TIME_SETTINGS.values()])
    for idx, tab in enumerate(tf_tabs):
        with tab:
            tf  = list(TIME_SETTINGS.keys())[idx]
            cfg = TIME_SETTINGS[tf]
            df_tf = fetch_ohlcv(ticker, cfg["period"], cfg["interval"])
            if not df_tf.empty:
                st.plotly_chart(candle_fig(df_tf), use_container_width=True)
            else:
                st.info("No data for this timeframe.")

    # ── EOD PREDICTION — full analysis ──────────────────────────────
    st.markdown('<div class="section-hdr"><span class="section-hdr-label">EOD Prediction & Analysis</span></div>', unsafe_allow_html=True)
    df_day   = fetch_ohlcv(ticker, "1d", "1m")
    df_daily = fetch_history(ticker, "3mo")

    if not df_day.empty:
        if ticker not in st.session_state.morning_predictions:
            st.session_state.morning_predictions[ticker] = honest_eod_prediction(ticker, df_day)
        pred       = st.session_state.morning_predictions[ticker]
        last_price = float(df_day["Close"].iloc[-1])
        delta_pct  = (last_price - pred["day_open"]) / pred["day_open"] * 100
        chg_cls    = "up" if delta_pct>=0 else "dn"
        sign       = "+" if delta_pct>=0 else ""
        conf_cls   = "amber" if pred["confidence"]=="low" else ("up" if pred["confidence"]=="high" else "")

        st.markdown(f"""<div class="mstrip">
          <div class="mcell"><div class="mlabel">Day Open</div><div class="mvalue">${pred['day_open']:,.2f}</div></div>
          <div class="mcell"><div class="mlabel">Last Price</div><div class="mvalue">${last_price:,.2f}</div></div>
          <div class="mcell"><div class="mlabel">Intraday Chg</div><div class="mvalue {chg_cls}">{sign}{delta_pct:.2f}%</div></div>
          <div class="mcell"><div class="mlabel">EOD Median</div><div class="mvalue">${pred['median']:,.2f}</div></div>
          <div class="mcell"><div class="mlabel">Up Probability</div><div class="mvalue {'up' if pred['up_prob']>50 else 'dn'}">{pred['up_prob']:.1f}%</div></div>
          <div class="mcell"><div class="mlabel">Confidence</div><div class="mvalue {conf_cls}">{pred['confidence'].upper()}</div></div>
        </div>""", unsafe_allow_html=True)

        if pred["warning"]:
            st.markdown(f"<div class='insight warn'>{pred['warning']}</div>", unsafe_allow_html=True)

        st.plotly_chart(prediction_fig(df_day, pred), use_container_width=True)

        upside_pct   = (pred["median"]-pred["day_open"])/pred["day_open"]*100
        downside_pct = (pred["bear"]-pred["day_open"])/pred["day_open"]*100
        st.markdown(f"""<div class="prob-box">
          <div class="prob-title">Monte Carlo Breakdown ({pred['n_sims']:,} simulations)</div>
          <div class="prob-row"><span class="prob-label">🎯 Median EOD Target</span>
            <span class="prob-val" style="color:var(--amber2)">${pred['median']:,.2f} ({upside_pct:+.2f}%)</span></div>
          <div class="prob-row"><span class="prob-label">🟢 Bull Case (95th pct)</span>
            <span class="prob-val" style="color:var(--green2)">${pred['bull']:,.2f}</span></div>
          <div class="prob-row"><span class="prob-label">🔵 75th Percentile</span>
            <span class="prob-val" style="color:var(--blue2)">${pred['p75']:,.2f}</span></div>
          <div class="prob-row"><span class="prob-label">🟠 25th Percentile</span>
            <span class="prob-val" style="color:var(--amber2)">${pred['p25']:,.2f}</span></div>
          <div class="prob-row"><span class="prob-label">🔴 Bear Case (5th pct)</span>
            <span class="prob-val" style="color:var(--red2)">${pred['bear']:,.2f} ({downside_pct:+.2f}%)</span></div>
          <div class="prob-row"><span class="prob-label">📊 Volatility Used / Raw</span>
            <span class="prob-val" style="color:var(--muted2)">{pred['vol_used']*100:.3f}% / {pred['vol_raw']*100:.3f}%</span></div>
        </div>""", unsafe_allow_html=True)

        # Technical signal dashboard
        if not df_daily.empty and len(df_daily) >= 20:
            close_d = df_daily["Close"].squeeze()
            r_vals  = rsi(close_d, 14)
            ml,sg,_ = macd(close_d)
            up_bb,mid_bb,lo_bb = bollinger(close_d)
            cur_rsi   = float(r_vals.iloc[-1])  if not r_vals.empty else 50
            cur_macd  = float(ml.iloc[-1])       if not ml.empty    else 0
            cur_sig   = float(sg.iloc[-1])       if not sg.empty    else 0
            cur_price = float(close_d.iloc[-1])
            cur_upper = float(up_bb.iloc[-1])    if not up_bb.empty else cur_price*1.02
            cur_lower = float(lo_bb.iloc[-1])    if not lo_bb.empty else cur_price*0.98
            cur_mid   = float(mid_bb.iloc[-1])   if not mid_bb.empty else cur_price
            sma20     = float(close_d.rolling(20).mean().iloc[-1])
            sma50     = float(close_d.rolling(50).mean().iloc[-1]) if len(close_d)>=50 else sma20

            st.markdown('<div class="section-hdr"><span class="section-hdr-label">Technical Signal Dashboard</span></div>', unsafe_allow_html=True)
            t1,t2,t3 = st.columns(3)

            rsi_cls = "bad" if cur_rsi<35 else ("warn" if cur_rsi>65 else "good")
            rsi_txt = "Oversold — potential bounce" if cur_rsi<35 else ("Overbought — potential pullback" if cur_rsi>65 else "Neutral zone")
            t1.markdown(f"<div class='insight {rsi_cls}'><b>RSI-14: {cur_rsi:.1f}</b><br>{rsi_txt}</div>", unsafe_allow_html=True)

            macd_cls = "good" if cur_macd>cur_sig else "bad"
            macd_txt = "Bullish — MACD above signal" if cur_macd>cur_sig else "Bearish — MACD below signal"
            t2.markdown(f"<div class='insight {macd_cls}'><b>MACD: {cur_macd:.3f}</b><br>{macd_txt}</div>", unsafe_allow_html=True)

            if cur_price>cur_upper:
                bb_cls,bb_txt="warn",f"Above upper band (${cur_upper:.2f}) — extended"
            elif cur_price<cur_lower:
                bb_cls,bb_txt="good",f"Below lower band (${cur_lower:.2f}) — oversold"
            else:
                bb_cls,bb_txt="good",f"Inside bands — mid band ${cur_mid:.2f}"
            t3.markdown(f"<div class='insight {bb_cls}'><b>Bollinger Band</b><br>{bb_txt}</div>", unsafe_allow_html=True)

            t4,t5,t6 = st.columns(3)
            ma_cls = "good" if cur_price>sma20>sma50 else ("bad" if cur_price<sma20<sma50 else "warn")
            ma_txt = ("Bullish: Price > SMA20 > SMA50" if cur_price>sma20>sma50
                      else ("Bearish: Price < SMA20 < SMA50" if cur_price<sma20<sma50 else "Mixed MA alignment"))
            t4.markdown(f"<div class='insight {ma_cls}'><b>MA Trend</b><br>{ma_txt}</div>", unsafe_allow_html=True)

            roc10 = float((close_d.iloc[-1]-close_d.iloc[-11])/close_d.iloc[-11]*100) if len(close_d)>=11 else 0
            roc_c = "good" if roc10>2 else ("bad" if roc10<-2 else "warn")
            t5.markdown(f"<div class='insight {roc_c}'><b>10-day ROC: {roc10:+.2f}%</b><br>{'Positive momentum' if roc10>0 else 'Negative momentum'}</div>", unsafe_allow_html=True)

            signals = sum([cur_rsi<50, cur_macd>cur_sig, cur_price>sma20, roc10>0])
            ov_cls  = "good" if signals>=3 else ("bad" if signals<=1 else "warn")
            ov_txt  = ["Strong Bear","Bearish","Neutral","Bullish","Strong Bull"][signals]
            t6.markdown(f"<div class='insight {ov_cls}'><b>Overall: {ov_txt}</b><br>{signals}/4 bullish indicators active</div>", unsafe_allow_html=True)
    else:
        st.markdown("<div class='insight warn'>No intraday data available for this ticker.</div>", unsafe_allow_html=True)

    st.stop()

# ══════════════════════════════════════════════════════════════════════
# 17. GRID VIEW — clickable card + sparkline inside card HTML
# ══════════════════════════════════════════════════════════════════════
search = st.text_input("🔍  Search Ticker (e.g. AAPL, BTC-USD, RELIANCE.NS)",
                       placeholder="Type ticker and press Enter…").upper().strip()
if search:
    st.session_state.selected_stock = search
    st.session_state.active_view    = "detail"
    st.rerun()

def render_grid(section_label, tickers, cols_n=5):
    st.markdown(
        f'<div class="section-hdr"><span class="section-hdr-label">{section_label}</span>'
        f'<span class="section-hdr-count">{len(tickers)}</span></div>',
        unsafe_allow_html=True)
    cols = st.columns(cols_n)
    for i, (ticker, name) in enumerate(tickers):
        with cols[i % cols_n]:
            data = fetch_card_data(ticker)
            if data is None:
                # No-data card + click button
                st.markdown(
                    f'<div class="scard neu"><div class="sc-top"><div class="sc-symbol">{clean(ticker)}</div></div>'
                    f'<div class="sc-name">{name}</div><div class="sc-nodata">No data</div></div>',
                    unsafe_allow_html=True)
                if st.button("Open", key=f"btn_{ticker}"):
                    st.session_state.selected_stock=ticker; st.session_state.active_view="detail"; st.rerun()
            else:
                chg       = data["chg"]
                is_up     = chg >= 0
                card_cls  = "up" if is_up else "down"
                badge_cls = "up" if is_up else "dn"
                arrow     = "▲" if is_up else "▼"
                spark_svg = build_sparkline_svg(data["close"], is_up)

                # Full card as one HTML block — sparkline IS inside the card
                st.markdown(
                    f'<div class="scard {card_cls}">'
                    f'  <div class="sc-top">'
                    f'    <div><div class="sc-symbol">{clean(ticker)}</div>'
                    f'         <div class="sc-name">{name}</div></div>'
                    f'    <span class="sc-badge {badge_cls}">{arrow} {abs(chg):.2f}%</span>'
                    f'  </div>'
                    f'  <span class="sc-price">${data["last"]:,.2f}</span>'
                    f'  <div class="sc-spark">{spark_svg}</div>'
                    f'</div>',
                    unsafe_allow_html=True)

                # "Analyse" button sits flush below card
                if st.button("Analyse", key=f"btn_{ticker}", help=f"Analyse {clean(ticker)}"):
                    st.session_state.selected_stock = ticker
                    st.session_state.active_view    = "detail"
                    st.rerun()

render_grid("S&P 500", SP500_TOP100[:20])
render_grid("NSE Top 50", NSE_TOP50[:10])
render_grid("Crypto", CRYPTO, cols_n=4)

# ══════════════════════════════════════════════════════════════════════
# 18. FOOTER
# ══════════════════════════════════════════════════════════════════════
st.markdown(
    '<div class="mp-footer">MARKET PULSE TERMINAL &nbsp;·&nbsp; FOR EDUCATIONAL USE ONLY '
    '&nbsp;·&nbsp; NOT FINANCIAL ADVICE &nbsp;·&nbsp; DATA VIA YAHOO FINANCE</div>',
    unsafe_allow_html=True)

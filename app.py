import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime
import pytz
from streamlit_autorefresh import st_autorefresh

# 1. Page Configuration & Elite Dark Terminal UI
st.set_page_config(
    page_title="Pharma2Tech Alpha", 
    page_icon="⚡", 
    layout="wide"
)

# Custom Institutional CSS Styling
st.markdown("""
    <style>
    .main { background-color: #0b0e14; }
    div[data-testid="stMetricValue"] { font-size: 26px; font-weight: 700; color: #ffffff; }
    .stAlert { background-color: #161b22; border: 1px solid #30363d; }
    h1 { font-family: 'Inter', sans-serif; font-weight: 800; letter-spacing: -0.5px; }
    div[data-testid="stDataFrame"] { border: 1px solid #30363d; border-radius: 6px; }
    </style>
""", unsafe_allow_html=True)

# Auto-Refresh Dashboard Every 60 seconds for live tracking
st_autorefresh(interval=60 * 1000, key="alpha_refresh")

st.title("⚡ Alpha Terminal")
st.caption("Institutional Grade Volatility & Liquidity Flow Monitor")

# 50 Component Stocks
STOCKS = [
    "RELIANCE.NS", "INFY.NS", "TCS.NS", "ICICIBANK.NS", "HCLTECH.NS", 
    "BHARTIARTL.NS", "M&M.NS", "MARUTI.NS", "SBIN.NS", "TECHM.NS", 
    "TRENT.NS", "KOTAKBANK.NS", "ADANIENT.NS", "WIPRO.NS", "NTPC.NS", 
    "AXISBANK.NS", "TATASTEEL.NS", "LT.NS", "JIOFIN.NS", "INDIGO.NS", 
    "EICHERMOT.NS", "BEL.NS", "TITAN.NS", "ITC.NS", "HINDUNILVR.NS",
    "POWERGRID.NS", "MAXHEALTH.NS", "HDFCLIFE.NS", "TATACONSUM.NS", "COALINDIA.NS", 
    "APOLLOHOSP.NS", "SHRIRAMFIN.NS", "BAJAJFINSV.NS", "HDFCBANK.NS", "MUTHOOTFIN.NS", 
    "ASIANPAINT.NS", "CIPLA.NS", "ONGC.NS", "GRASIM.NS", "DRREDDY.NS", 
    "JSWSTEEL.NS", "SBILIFE.NS", "BAJFINANCE.NS", "PFC.NS", "CHOLAFIN.NS", 
    "LICHSGFIN.NS", "HEROMOTOCO.NS", "EXIDEIND.NS", "ASHOKLEY.NS", "SONACOMS.NS"
]

@st.cache_data(ttl=30)
def fetch_market_data():
    try:
        return yf.download(tickers=STOCKS, period="5d", interval="5m", group_by='ticker', progress=False)
    except:
        return None

# Time Zone Configurations (IST)
tz_ist = pytz.timezone('Asia/Kolkata')
current_time_ist = datetime.now(tz_ist).strftime('%I:%M %p')

st.info(f"🟢 Server Connected | Live Feed Sync: {current_time_ist}")

results = []

with st.spinner("Syncing matrix..."):
    bulk_data = fetch_market_data()
    
    if bulk_data is not None and not bulk_data.empty:
        sample_index = bulk_data.index
        latest_trading_day = pd.to_datetime(sample_index).date[-1]
        
        for stock in STOCKS:
            try:
                if stock in bulk_data.columns.levels[0]:
                    df = bulk_data[stock].copy().dropna()
                    if df.empty or len(df) < 2:
                        continue
                    
                    df.index = df.index.tz_convert('Asia/Kolkata')
                    df['Date'] = df.index.date
                    
                    df_today = df[df['Date'] == latest_trading_day]
                    if df_today.empty:
                        continue
                    
                    # 1st Candle Range (Hidden from UI)
                    first_candle = df_today.iloc[0]
                    oHigh = float(first_candle['High'])
                    oLow = float(first_candle['Low'])
                    
                    for idx in range(1, len(df_today)):
                        row = df_today.iloc[idx]
                        c_close = float(row['Close'])
                        c_high = float(row['High'])
                        c_low = float(row['Low'])
                        
                        candle_time_12h = row.name.strftime('%I:%M %p')
                        
                        # Bearish Alert -> Pure Institutional Action Label
                        if c_high > oHigh and c_close <= oHigh:
                            results.append({
                                "Ticker": stock.replace(".NS", ""),
                                "Action": "SHORT",
                                "Timestamp": candle_time_12h
                            })
                            
                        # Bullish Alert -> Pure Institutional Action Label
                        if c_low < oLow and c_close >= oLow:
                            results.append({
                                "Ticker": stock.replace(".NS", ""),
                                "Action": "LONG",
                                "Timestamp": candle_time_12h
                            })
            except:
                continue

# Render Clean Professional Terminal UI
if results:
    res_df = pd.DataFrame(results)
    
    # Quick Summary Statistics Block
    st.metric("Total Active Triggers", len(res_df))
    st.write("") # Spacer
        
    # Micro-styling definition for absolute premium look
    def apply_terminal_theme(val):
        if "LONG" in val:
            return 'background-color: #0e622b; color: #ffffff; font-weight: bold; text-align: center;'
        elif "SHORT" in val:
            return 'background-color: #842029; color: #ffffff; font-weight: bold; text-align: center;'
        return ''
        
    # Render final ultra-clean table without index or internal logic reveal
    st.dataframe(
        res_df.style.map(apply_terminal_theme, subset=['Action']), 
        use_container_width=True,
        hide_index=True
    )
else:
    st.info("🎯 Scanner Active | Waiting for directional structural breaks.")

import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# 1. Page Config & Professional Theme
st.set_page_config(
    page_title="Pharma2Tech | Alpha Scanner", 
    page_icon="📊", 
    layout="wide"
)

# Custom Premium CSS Styling
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    div[data-testid="stMetricValue"] { font-size: 24px; font-weight: bold; }
    .reportview-container .main .block-container { padding-top: 2rem; }
    h1 { color: #ffffff; font-family: 'Inter', sans-serif; }
    </style>
""", unsafe_allow_html=True)

# 2. Auto-Refresh Setup (Triggers every 60 seconds automatically for LIVE tracking)
st_autorefresh(interval=60 * 1000, key="datarefresh")

st.title("📊 Alpha Range Scanner")
st.caption("Advanced 5-Minute Opening Range & Liquidity Sweep Dashboard")

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

# Cache engine for smooth requests
@st.cache_data(ttl=30)
def fetch_market_data():
    try:
        return yf.download(tickers=STOCKS, period="5d", interval="5m", group_by='ticker', progress=False)
    except:
        return None

# Top status layout
col_time, col_empty = st.columns([1, 3])
with col_time:
    st.info(f"⏱️ System Time: {datetime.now().strftime('%H:%M:%S')}")

results = []

with st.spinner("Analyzing structural data blocks..."):
    bulk_data = fetch_market_data()
    
    if bulk_data is not None and not bulk_data.empty:
        available_dates = pd.to_datetime(bulk_data.index).date
        latest_trading_day = available_dates[-1]
        
        st.markdown(f"📡 **Active Session:** {latest_trading_day.strftime('%Y-%m-%d')} (Live Feed Auto-Refreshes)")
        
        for stock in STOCKS:
            try:
                if stock in bulk_data.columns.levels[0]:
                    df = bulk_data[stock].copy().dropna()
                    if df.empty or len(df) < 2:
                        continue
                        
                    df['Date'] = df.index.date
                    df_today = df[df['Date'] == latest_trading_day]
                    
                    if df_today.empty:
                        continue
                        
                    # Core Strategy Calculations
                    first_candle = df_today.iloc[0]
                    oHigh = float(first_candle['High'])
                    oLow = float(first_candle['Low'])
                    
                    bSweep, sSweep = False, False
                    tLow, tHigh = 0.0, 0.0
                    current_status = "Scanning"
                    
                    for idx in range(1, len(df_today)):
                        row = df_today.iloc[idx]
                        c_close = float(row['Close'])
                        c_high = float(row['High'])
                        c_low = float(row['Low'])
                        
                        if c_high > oHigh and c_close <= oHigh and not sSweep:
                            sSweep = True
                            tLow = c_low
                            current_status = "Bearish Sweep Formed"
                            
                        if c_low < oLow and c_close >= oLow and not bSweep:
                            bSweep = True
                            tHigh = c_high
                            current_status = "Bullish Sweep Formed"
                            
                        if sSweep and tLow > 0.0 and c_close < tLow:
                            current_status = "SELL SIGNAL CONFIRMED"
                        if bSweep and tHigh > 0.0 and c_close > tHigh:
                            current_status = "BUY SIGNAL CONFIRMED"
                            
                    if current_status != "Scanning":
                        results.append({
                            "Ticker": stock.replace(".NS", ""),
                            "Market Structure Status": current_status
                        })
            except:
                continue

# Render Modern Grid Interface
if results:
    res_df = pd.DataFrame(results)
    
    # Calculate quick statistics
    total_triggers = len(res_df)
    confirmed_signals = len(res_df[res_df["Market Structure Status"].str.contains("CONFIRMED")])
    
    col_m1, col_m2 = st.columns(2)
    with col_m1:
        st.metric("Total Active Watches", total_triggers)
    with col_m2:
        st.metric("Confirmed Executions", confirmed_signals)
        
    # Micro-styling structure definitions
    def apply_premium_color(val):
        if "BUY SIGNAL" in val:
            return 'background-color: #1e7e34; color: #ffffff; font-weight: bold; border-radius: 4px;'
        elif "SELL SIGNAL" in val:
            return 'background-color: #bd2130; color: #ffffff; font-weight: bold; border-radius: 4px;'
        elif "Bullish" in val:
            return 'background-color: #28a745; color: #ffffff; opacity: 0.8;'
        elif "Bearish" in val:
            return 'background-color: #dc3545; color: #ffffff; opacity: 0.8;'
        return ''
        
    st.dataframe(
        res_df.style.map(apply_premium_color, subset=['Market Structure Status']), 
        use_container_width=True,
        hide_index=True
    )
else:
    st.info("🎯 Absolute equilibrium. No structural liquidity sweeps or directional breaks detected at this time.")

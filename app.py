import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime
import pytz
from streamlit_autorefresh import st_autorefresh

# 1. Page Configuration & Dark Theme UI
st.set_page_config(
    page_title="Pharma2Tech | Alpha Multi-Scanner", 
    page_icon="📊", 
    layout="wide"
)

st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    div[data-testid="stMetricValue"] { font-size: 24px; font-weight: bold; }
    h1 { color: #ffffff; font-family: 'Inter', sans-serif; }
    </style>
""", unsafe_allow_html=True)

# Auto-Refresh Dashboard Every 60 seconds
st_autorefresh(interval=60 * 1000, key="datarefresh")

st.title("📊 Alpha Liquidity Sweep Tracker")
st.caption("Accurate Multi-Signal 5-Min Opening Range Scanner with Precision Timestamps & Reference Levels")

# Nifty 50 Active Stocks
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
        # Fetching 5 days to safely fallback to latest trading session
        return yf.download(tickers=STOCKS, period="5d", interval="5m", group_by='ticker', progress=False)
    except:
        return None

# Standard Time Zone Fix (Kolkata IST)
tz_ist = pytz.timezone('Asia/Kolkata')
current_time_ist = datetime.now(tz_ist).strftime('%I:%M:%S %p')

st.info(f"⏱️ Dashboard Last Updated (IST 12-Hour): {current_time_ist}")

results = []

with st.spinner("Processing structural order books and charts..."):
    bulk_data = fetch_market_data()
    
    if bulk_data is not None and not bulk_data.empty:
        # Step 1: Detect the exact latest active market date in data
        sample_index = bulk_data.index
        latest_trading_day = pd.to_datetime(sample_index).date[-1]
        
        st.markdown(f"📡 **Active Feed Session:** {latest_trading_day.strftime('%Y-%m-%d')}")
        
        for stock in STOCKS:
            try:
                if stock in bulk_data.columns.levels[0]:
                    df = bulk_data[stock].copy().dropna()
                    if df.empty or len(df) < 2:
                        continue
                    
                    # Convert yfinance international index timestamps to clear India IST
                    df.index = df.index.tz_convert('Asia/Kolkata')
                    df['Date'] = df.index.date
                    
                    # Filter data strictly for the current active day
                    df_today = df[df['Date'] == latest_trading_day]
                    if df_today.empty:
                        continue
                    
                    # Extract 1st 5-min reference range boundaries
                    first_candle = df_today.iloc[0]
                    oHigh = float(first_candle['High'])
                    oLow = float(first_candle['Low'])
                    
                    # Loop through all subsequent candles to capture EVERY valid signal
                    for idx in range(1, len(df_today)):
                        row = df_today.iloc[idx]
                        c_close = float(row['Close'])
                        c_high = float(row['High'])
                        c_low = float(row['Low'])
                        
                        # Format timestamp into user preferred 12-hour clock (e.g., 10:15 AM)
                        candle_time_12h = row.name.strftime('%I:%M %p')
                        
                        # A. BEARISH SWEEP (Sell Plan Logic)
                        if c_high > oHigh and c_close <= oHigh:
                            results.append({
                                "Ticker": stock.replace(".NS", ""),
                                "Liquidity Event": "BEARISH SWEEP (SELL PLAN)",
                                "Trigger Time (IST)": candle_time_12h,
                                "Opening High Reference": round(oHigh, 2),
                                "Opening Low Reference": round(oLow, 2),
                                "Candle High/Low Reached": f"High: {round(c_high, 2)}"
                            })
                            
                        # B. BULLISH SWEEP (Buy Plan Logic)
                        if c_low < oLow and c_close >= oLow:
                            results.append({
                                "Ticker": stock.replace(".NS", ""),
                                "Liquidity Event": "BULLISH SWEEP (BUY PLAN)",
                                "Trigger Time (IST)": candle_time_12h,
                                "Opening High Reference": round(oHigh, 2),
                                "Opening Low Reference": round(oLow, 2),
                                "Candle High/Low Reached": f"Low: {round(c_low, 2)}"
                            })
            except:
                continue

# Render Modern Visual Table Engine
if results:
    # Sort results chronologically by token/time for structured viewing
    res_df = pd.DataFrame(results)
    
    st.metric("Total Liquidity Events Logged", len(res_df))
        
    def apply_premium_color(val):
        if "BULLISH" in val:
            return 'background-color: #1e7e34; color: #ffffff; font-weight: bold; border-radius: 4px;'
        elif "BEARISH" in val:
            return 'background-color: #bd2130; color: #ffffff; font-weight: bold; border-radius: 4px;'
        return ''
        
    st.dataframe(
        res_df.style.map(apply_premium_color, subset=['Liquidity Event']), 
        use_container_width=True,
        hide_index=True
    )
else:
    st.info("🎯 Absolute market equilibrium. No historical or live 5-min sweeps found for this session.")

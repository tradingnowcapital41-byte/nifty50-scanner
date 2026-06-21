import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime
import pytz
from streamlit_autorefresh import st_autorefresh

# 1. Page Config & Professional Dark Theme
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

# Auto-Refresh Setup (Every 60 seconds for live tracking)
st_autorefresh(interval=60 * 1000, key="datarefresh")

st.title("📊 Alpha Liquidity Scanner")
st.caption("Real-time 5-Minute Opening Range Liquidity Sweep Monitor with Timestamp")

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

# IST Time Conversion Helper
ist = pytz.timezone('Asia/Kolkata')
current_time_ist = datetime.now(ist).strftime('%H:%M:%S')

col_time, _ = st.columns([1, 3])
with col_time:
    st.info(f"⏱️ System Time (IST): {current_time_ist}")

results = []

with st.spinner("Analyzing structural data blocks..."):
    bulk_data = fetch_market_data()
    
    if bulk_data is not None and not bulk_data.empty:
        available_dates = pd.to_datetime(bulk_data.index).date
        latest_trading_day = available_dates[-1]
        
        st.markdown(f"📡 **Active Session:** {latest_trading_day.strftime('%Y-%m-%d')} (Live Tracking Enabled)")
        
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
                        
                    # Get First 5-min Candle Range
                    first_candle = df_today.iloc[0]
                    oHigh = float(first_candle['High'])
                    oLow = float(first_candle['Low'])
                    
                    current_status = "Scanning"
                    event_time = "N/A"
                    
                    # Track Sweep Formations and log the exact time
                    for idx in range(1, len(df_today)):
                        row = df_today.iloc[idx]
                        c_close = float(row['Close'])
                        c_high = float(row['High'])
                        c_low = float(row['Low'])
                        
                        # Get formatted candle time in IST
                        candle_time = row.name.astimezone(ist).strftime('%H:%M') if hasattr(row.name, 'astimezone') else row.name.strftime('%H:%M')
                        
                        # BEARISH SWEEP (Sell Plan): High crosses oHigh but closes inside/below it
                        if c_high > oHigh and c_close <= oHigh:
                            current_status = "BEARISH SWEEP (SELL PLAN)"
                            event_time = candle_time
                            
                        # BULLISH SWEEP (Buy Plan): Low crosses oLow but closes inside/above it
                        if c_low < oLow and c_close >= oLow:
                            current_status = "BULLISH SWEEP (BUY PLAN)"
                            event_time = candle_time
                            
                    if current_status != "Scanning":
                        results.append({
                            "Ticker": stock.replace(".NS", ""),
                            "Liquidity Event": current_status,
                            "Event Time (IST)": event_time
                        })
            except:
                continue

# Render Modern Table Interface
if results:
    res_df = pd.DataFrame(results)
    
    # Calculate quick metrics
    total_sweeps = len(res_df)
    st.metric("Total Liquidity Sweeps", total_sweeps)
        
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
    st.info("🎯 Absolute equilibrium. No opening range liquidity sweeps detected at this time.")

import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime

# Page Configuration
st.set_page_config(page_title="Pharma2Tech Stock Scanner", layout="wide")
st.title("📊 Live 5-Min Strategy Scanner (Nifty 50)")

# 50 Stocks List (.NS for Yahoo Finance)
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

# Optimize Data Fetching: Multi-stock bulk download (Fast & No Timeout)
@st.cache_data(ttl=60)  # Cache data for 60 seconds to prevent getting blocked
def fetch_bulk_data():
    try:
        data = yf.download(tickers=STOCKS, period="2d", interval="5m", group_by='ticker', progress=False)
        return data
    except Exception as e:
        st.error(f"डेटा मिळवताना अडचण आली: {e}")
        return None

# App refresh time info
st.write(f"Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

results = []

with st.spinner("सर्व ५० स्टॉक्स एकाच वेळी स्कॅन होत आहेत..."):
    bulk_data = fetch_bulk_data()
    
    if bulk_data is not None and not bulk_data.empty:
        today = datetime.now().date()
        
        for stock in STOCKS:
            try:
                # Extract individual stock dataframe from bulk data safely
                if stock in bulk_data.columns.levels[0]:
                    df = bulk_data[stock].dropna()
                    if df.empty or len(df) < 2:
                        continue
                        
                    df['Date'] = df.index.date
                    df_today = df[df['Date'] == today]
                    
                    if df_today.empty:
                        continue
                        
                    # Strategy logic: Get first 5-min candle
                    first_candle = df_today.iloc[0]
                    oHigh = float(first_candle['High'])
                    oLow = float(first_candle['Low'])
                    
                    bSweep = False
                    sSweep = False
                    tLow = None
                    tHigh = None
                    current_status = "Waiting"
                    
                    # Loop through subsequent candles
                    for idx in range(1, len(df_today)):
                        row = df_today.iloc[idx]
                        c_close = float(row['Close'])
                        c_high = float(row['High'])
                        c_low = float(row['Low'])
                        
                        # Short Sweep Logic
                        if c_high > oHigh and c_close <= oHigh and not sSweep:
                            sSweep = True
                            tLow = c_low
                            current_status = "❌ Sweep Formed (Bearish)"
                            
                        # Long Sweep Logic
                        if c_low < oLow and c_close >= oLow and not bSweep:
                            bSweep = True
                            tHigh = c_high
                            current_status = "🟢 Sweep Formed (Bullish)"
                            
                        # Trigger Cross Logic
                        if sSweep and tLow and c_close < tLow:
                            current_status = "🚨 SELL SIGNAL VALID"
                        if bSweep and tHigh and c_close > tHigh:
                            current_status = "🔥 BUY SIGNAL VALID"
                            
                    # Add to list if it has active signal status
                    if current_status != "Waiting":
                        results.append({
                            "Stock Name": stock.replace(".NS", ""),
                            "Signal Status": current_status
                        })
            except:
                continue

# Display Results UI Table
if results:
    res_df = pd.DataFrame(results)
    
    def style_signals(val):
        if "VALID" in val:
            return 'background-color: #2ecc71; color: white; font-weight: bold;'
        elif "Sweep" in val:
            return 'background-color: #f39c12; color: white;'
        return ''
        
    st.dataframe(res_df.style.applymap(style_signals, subset=['Signal Status']), use_container_width=True)
else:
    st.info("🎯 सध्या कोणत्याही स्टॉकमध्ये Sweep किंवा Signal तयार झालेला नाही. मार्केट शांत आहे!")

# Auto-Refresh button
if st.button("🔄 मॅन्युअली रिफ्रेश करा"):
    st.rerun()

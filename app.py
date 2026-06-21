import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime

# Page Configuration
st.set_page_config(page_title="Pharma2Tech Stock Scanner", layout="wide")
st.title("📊 Live 5-Min Strategy Scanner (Nifty 50)")
st.write(f"Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# Image मधून घेतलेले ५० मुख्य स्टॉक्स (Yahoo Finance Format: .NS)
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

def check_strategy(ticker):
    try:
        # ५ मिनिटांचा डेटा डाऊनलोड करणे (आजचा आणि कालचा)
        df = yf.download(tickers=ticker, period="2d", interval="5m", progress=False)
        if df.empty or len(df) < 5:
            return None
        
        # आजचा डेटा वेगळा करणे
        df['Date'] = df.index.date
        today = datetime.now().date()
        df_today = df[df['Date'] == today]
        
        if df_today.empty:
            return None
            
        # ०९:१५ ची पहिली ५ मिनिटांची कॅंडल शोधणे
        first_candle = df_today.iloc[0]
        oHigh = first_candle['High'].values[0] if isinstance(first_candle['High'], pd.Series) else first_candle['High']
        oLow = first_candle['Low'].values[0] if isinstance(first_candle['Low'], pd.Series) else first_candle['Low']
        
        bSweep = False
        sSweep = False
        tLow = None
        tHigh = None
        current_status = "Waiting"
        
        # पहिल्या कॅंडल सोडून बाकी कॅंडल्सवर लूप फिरवणे
        for idx in range(1, len(df_today)):
            row = df_today.iloc[idx]
            c_close = row['Close'].values[0] if isinstance(row['Close'], pd.Series) else row['Close']
            c_high = row['High'].values[0] if isinstance(row['High'], pd.Series) else row['High']
            c_low = row['Low'].values[0] if isinstance(row['Low'], pd.Series) else row['Low']
            
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
                
            # Trigger Cross Logic (Final Signal)
            if sSweep and tLow and c_close < tLow:
                current_status = "🚨 SELL SIGNAL VALID"
            if bSweep and tHigh and c_close > tHigh:
                current_status = "🔥 BUY SIGNAL VALID"
                
        return current_status
    except:
        return None

# UI Table साठी डेटा तयार करणे
results = []

with st.spinner("सर्व ५० स्टॉक्स स्कॅन होत आहेत... कृपया थांबा..."):
    for stock in STOCKS:
        status = check_strategy(stock)
        # तुझी अट: फक्त सिग्नल्स असलेले (Waiting नसलेले) स्टॉक्स दाखवणे
        if status and status != "Waiting":
            results.append({
                "Stock Name": stock.replace(".NS", ""),
                "Signal Status": status
            })

# निकाल डिस्प्ले करणे
if results:
    res_df = pd.DataFrame(results)
    
    # स्टाईलिंग (रंग भरणे)
    def style_signals(val):
        if "VALID" in val:
            return 'background-color: #2ecc71; color: white; font-weight: bold;'
        elif "Sweep" in val:
            return 'background-color: #f39c12; color: white;'
        return ''
        
    st.dataframe(res_df.style.applymap(style_signals, subset=['Signal Status']), use_container_width=True)
else:
    st.info("🎯 सध्या कोणत्याही स्टॉकमध्ये Sweep किंवा Signal तयार झालेला नाही. मार्केट शांत आहे!")

# ऑटो रिफ्रेश बटन
if st.button("🔄 मॅन्युअली रिफ्रेश करा"):
    st.rerun()

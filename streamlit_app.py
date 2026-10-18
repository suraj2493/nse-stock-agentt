import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf

# Page Configuration
st.set_page_config(
    page_title="NSE Stock Analyzer",
    page_icon="📈",
    layout="wide"
)

st.title("🇮🇳 NSE Smart Stock Analyzer")
st.markdown("Analyze any NSE-listed stock using its complete historical data to calculate **Buying Prices, Targets, and Stoploss** levels.")

# Sidebar Controls
st.sidebar.header("Configuration")
stock_input = st.sidebar.text_input("Enter NSE Ticker Symbol:", value="RELIANCE").strip().upper()

# Automatically append .NS if user forgot it
if not stock_input.endswith(".NS") and not stock_input.endswith(".BO"):
    ticker_symbol = f"{stock_input}.NS"
else:
    ticker_symbol = stock_input

timeframe = st.sidebar.selectbox(
    "Select Historical Data Horizon:",
    ["Max (All Past Data)", "5 Years", "2 Years", "1 Year"],
    index=0
)

# Map timeframe to yfinance period
period_map = {
    "Max (All Past Data)": "max",
    "5 Years": "5y",
    "2 Years": "2y",
    "1 Year": "1y"
}

@st.cache_data(ttl=3600)
def load_stock_data(ticker, period):
    try:
        df = yf.download(ticker, period=period, auto_adjust=True)
        if df.empty:
            return None
        # Handle multi-index columns if returned by newer yfinance versions
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        return df
    except Exception as e:
        return None

# Fetch Data Button
if st.sidebar.button("Run Analysis", type="primary"):
    with st.spinner(f"Fetching historical data for {ticker_symbol}..."):
        data = load_stock_data(ticker_symbol, period_map[timeframe])
        
    if data is None or len(data) < 30:
        st.error(f"Could not retrieve valid data for `{ticker_symbol}`. Please check if the NSE symbol is correct (e.g., `TCS`, `INFY`, `TATAMOTORS`).")
    else:
        st.success(f"Successfully loaded {len(data)} rows of past trading data!")
        
        # Calculations
        current_price = float(data['Close'].iloc[-1])
        prev_close = float(data['Close'].iloc[-2])
        price_change = current_price - prev_close
        pct_change = (price_change / prev_close) * 100
        
        # Moving averages
        data['SMA_50'] = data['Close'].rolling(window=50).mean()
        data['SMA_200'] = data['Close'].rolling(window=200).mean()
        
        # Volatility (ATR Approximation using High-Low)
        data['HL_Diff'] = data['High'] - data['Low']
        atr = float(data['HL_Diff'].rolling(window=14).mean().iloc[-1])
        
        sma_50 = float(data['SMA_50'].iloc[-1]) if not np.isnan(data['SMA_50'].iloc[-1]) else current_price
        sma_200 = float(data['SMA_200'].iloc[-1]) if not np.isnan(data['SMA_200'].iloc[-1]) else current_price

        # Strategic Levels Calculation (Swing Trading Setup)
        # Stoploss placed safely below recent volatility or 50 SMA
        stop_loss = round(current_price - (1.5 * atr), 2)
        # Buying Price recommendation near support/current levels
        buy_price_ideal = round(current_price * 0.985, 2) # Slight dip entry or current
        # Target calculations based on Risk-Reward Ratio (1:2)
        risk = current_price - stop_loss
        target_1 = round(current_price + (risk * 1.5), 2)
        target_2 = round(current_price + (risk * 2.5), 2)

        # Metrics Overview
        st.markdown("---")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Current Price", f"₹{current_price:.2f}", f"{pct_change:+.2f}%")
        col2.metric("50-Day SMA", f"₹{sma_50:.2f}")
        col3.metric("200-Day SMA", f"₹{sma_200:.2f}")
        col4.metric("Average True Range (14)", f"₹{atr:.2f}")

        # Action Plan Section
        st.markdown("### 🎯 Automated Trade Setup (AI / Technical Guardrails)")
        
        t_col1, t_col2, t_col3 = st.columns(3)
        with t_col1:
            st.info(f"**Recommended Buy Zone**\n\n ₹{buy_price_ideal} – ₹{current_price:.2f}\n*(Accumulate on dips)*")
        with t_col2:
            st.warning(f"**Stoploss (Risk Control)**\n\n ₹{stop_loss}\n*(Exit if price breaks below this support)*")
        with t_col3:
            st.success(f"**Target Prices**\n\n **T1:** ₹{target_1}\n **T2:** ₹{target_2}\n*(Book partial profits here)*")

        # Visualizing past data using Native Streamlit Charts
        st.markdown("---")
        st.subheader("📊 Complete Historical Price & Trend Analysis")
        
        chart_data = pd.DataFrame({
            'Close Price': data['Close'],
            '50 SMA': data['SMA_50'],
            '200 SMA': data['SMA_200']
        }).dropna()
        
        st.line_chart(chart_data)

        # Volume Chart
        st.subheader("📉 Historical Trading Volume")
        st.bar_chart(data['Volume'])

        # Raw Table View
        with st.expander("View Raw Historical Data Table"):
            st.dataframe(data.sort_index(ascending=False))
else:
    st.info("👈 Enter an NSE ticker on the left sidebar (e.g., `RELIANCE`, `TCS`, `INFY`) and click **Run Analysis**.")

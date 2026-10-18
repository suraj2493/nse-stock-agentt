import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import yfinance as yf

# Page Config
st.set_page_config(
    page_title="NSE Stock Technical Engine", page_icon="📈", layout="wide"
)

st.title("📈 NSE Stock Technical Engine & Risk Calculator")
st.caption(
    "100% Free & Open-Source (No LLM or API keys required) | Data source: NSE via"
    " yfinance"
)


def analyze_stock(symbol: str):
  clean_symbol = symbol.strip().upper().replace(".NS", "")
  nse_symbol = f"{clean_symbol}.NS"

  ticker = yf.Ticker(nse_symbol)
  df = ticker.history(period="6mo")

  if df.empty:
    return None, f"Could not fetch data for NSE Ticker '{clean_symbol}'."

  # Current Market Price
  cmp = round(float(df["Close"].iloc[-1]), 2)

  # Technical Calculations
  df["H-L"] = df["High"] - df["Low"]
  df["H-PC"] = abs(df["High"] - df["Close"].shift(1))
  df["L-PC"] = abs(df["Low"] - df["Close"].shift(1))
  df["TR"] = df[["H-L", "H-PC", "L-PC"]].max(axis=1)
  df["ATR"] = df["TR"].rolling(14).mean()
  atr = round(
      float(df["ATR"].iloc[-1])
      if not pd.isna(df["ATR"].iloc[-1])
      else cmp * 0.02,
      2,
  )

  df["SMA_20"] = df["Close"].rolling(20).mean()
  df["SMA_50"] = df["Close"].rolling(50).mean()
  sma_20 = round(float(df["SMA_20"].iloc[-1]), 2)
  sma_50 = round(float(df["SMA_50"].iloc[-1]), 2)

  delta = df["Close"].diff()
  gain = (delta.where(delta > 0, 0)).rolling(14).mean()
  loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
  rs = gain / loss
  rsi = round(float((100 - (100 / (1 + rs))).iloc[-1]), 2)

  # Risk Logic
  stop_loss = round(cmp - (1.5 * atr), 2)
  risk = cmp - stop_loss
  target_1 = round(cmp + (1.5 * risk), 2)
  target_2 = round(cmp + (2.5 * risk), 2)

  if cmp > sma_20 and rsi >= 45 and rsi <= 70:
    action = "BUY / ACCUMULATE"
    action_color = "green"
  elif cmp < sma_20 and rsi < 40:
    action = "AVOID / BEARISH"
    action_color = "red"
  else:
    action = "HOLD / NEUTRAL"
    action_color = "orange"

  return {
      "symbol": clean_symbol,
      "cmp": cmp,
      "atr": atr,
      "sma_20": sma_20,
      "sma_50": sma_50,
      "rsi": rsi,
      "stop_loss": stop_loss,
      "target_1": target_1,
      "target_2": target_2,
      "action": action,
      "action_color": action_color,
      "df": df,
  }, None


# UI Layout
symbol_input = st.sidebar.text_input(
    "Enter NSE Ticker Symbol:", value="RELIANCE"
)

st.sidebar.markdown("**Quick Presets:**")
cols = st.sidebar.columns(2)
if cols[0].button("RELIANCE"):
  symbol_input = "RELIANCE"
if cols[1].button("TCS"):
  symbol_input = "TCS"

if st.sidebar.button("Run Technical Analysis", type="primary"):
  with st.spinner("Analyzing market data..."):
    result, error = analyze_stock(symbol_input)

    if error:
      st.error(error)
    else:
      st.subheader(f"Analysis for NSE: {result['symbol']}")

      m1, m2, m3, m4 = st.columns(4)
      m1.metric("Current Market Price (CMP)", f"₹{result['cmp']}")
      m2.metric("Signal", result["action"])
      m3.metric("Stop Loss (SL)", f"₹{result['stop_loss']}")
      m4.metric("Targets (T1 / T2)", f"₹{result['target_1']} / ₹{result['target_2']}")

      st.markdown("---")

      col_a, col_b = st.columns(2)
      with col_a:
        st.write("### 📊 Technical Indicators")
        st.write(f"• **14-day ATR (Volatility):** ₹{result['atr']}")
        st.write(f"• **20-day SMA:** ₹{result['sma_20']}")
        st.write(f"• **50-day SMA:** ₹{result['sma_50']}")
        st.write(f"• **14-day RSI:** {result['rsi']}")

      with col_b:
        st.write("### 🎯 Risk-Management Levels")
        st.write(f"• **Recommended Buy Price:** ₹{result['cmp']}")
        st.write(f"• **Stop-Loss Level:** ₹{result['stop_loss']}")
        st.write(f"• **Target 1 (1:1.5 Risk-Reward):** ₹{result['target_1']}")
        st.write(f"• **Target 2 (1:2.5 Risk-Reward):** ₹{result['target_2']}")

      st.write("### 📈 Technical Price Chart")
      df = result["df"]
      fig = go.Figure()
      fig.add_trace(
          go.Candlestick(
              x=df.index,
              open=df["Open"],
              high=df["High"],
              low=df["Low"],
              close=df["Close"],
              name="Price",
          )
      )
      fig.add_hline(
          y=result["stop_loss"],
          line_dash="dash",
          line_color="red",
          annotation_text="Stop Loss",
      )
      fig.add_hline(
          y=result["target_1"],
          line_dash="dash",
          line_color="green",
          annotation_text="Target 1",
      )
      fig.update_layout(
          template="plotly_dark",
          height=450,
          margin=dict(l=20, r=20, t=20, b=20),
      )
      st.plotly_chart(fig, use_container_width=True)

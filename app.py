import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# 1. Page Configuration
st.set_page_config(page_title="Stock Data Extraction App", layout='wide')
st.title("📈 Stock Data Extraction App")
st.write("Extract stock market prices and analyze trends using a ticker symbol.")

# 2. Sidebar Inputs
st.sidebar.header("User Input")
ticker = st.sidebar.text_input("Enter Ticker", "AAPL").upper()
start_date = st.sidebar.date_input("Start Date", pd.to_datetime("today") - pd.DateOffset(months=6))
end_date = st.sidebar.date_input("End Date", pd.to_datetime("today"))

# 3. Data Fetching (Optimized with Caching)
@st.cache_data
def load_data(t, start, end):
    """Fetches historical data and caches it to prevent unnecessary API calls."""
    stock = yf.Ticker(t)
    return stock.history(start=start, end=end)

df = load_data(ticker, start_date, end_date)

# 4. Main App Logic
if df.empty:
    st.error("No data found. Please check the ticker symbol or date range.")
else:
    st.success(f"Data successfully extracted for {ticker}")

    # --- Calculations ---
    # Moving Averages
    df["ma_5"] = df["Close"].rolling(window=5).mean()
    df["ma_20"] = df["Close"].rolling(window=20).mean()
    df["ma_50"] = df["Close"].rolling(window=50).mean()

    # RSI (Rolling calculation over the whole dataset)
    delta = df["Close"].diff()
    gains = delta.clip(lower=0).rolling(window=14).mean()
    losses = -delta.clip(upper=0).rolling(window=14).mean()
    rs = gains / losses
    df["RSI"] = 100 - (100 / (1 + rs))

    # Volatility
    daily_returns = df["Close"].pct_change()
    vol_20 = daily_returns.rolling(window=20).std()
    df["Volatility"] = vol_20 * np.sqrt(252)

    # Get latest values for display
    current_price = df["Close"].iloc[-1]
    ma_20_current = df["ma_20"].iloc[-1]
    ma_50_current = df["ma_50"].iloc[-1]
    current_rsi = df["RSI"].iloc[-1]
    current_vol = df["Volatility"].iloc[-1]

    # Determine Trend
    if current_price > ma_20_current and current_price > ma_50_current:
        trend = "Upward Trend"
    elif current_price < ma_20_current and current_price < ma_50_current:
        trend = "Downward Trend"
    else:
        trend = "Mixed Trend"

    # Determine Volatility Category
    if pd.isna(current_vol): # Handle cases where there isn't enough data yet
        vol_category = "Unknown"
    elif current_vol > 0.40:
        vol_category = "High"
    elif current_vol >= 0.25:
        vol_category = "Medium"
    else:
        vol_category = "Low"

    # --- Dashboard Display ---
    st.header("Market Overview")
    
    # Use columns to create a neat top-level dashboard
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Current Price", f"${current_price:.2f}")
    with col2:
        st.metric("Current Trend", trend)
    with col3:
        st.metric("14-Day RSI", f"{current_rsi:.2f}")
    with col4:
        st.metric("Annualized Volatility", f"{current_vol:.2%}" if not pd.isna(current_vol) else "N/A")

    st.divider()

    # --- Interactive Chart ---
    st.subheader(f"Closing Price & Moving Averages for {ticker}")
    # Prepare data for Streamlit's native interactive chart
    chart_data = df[["Close", "ma_5", "ma_20", "ma_50"]].rename(
        columns={"Close": "Price", "ma_5": "5-Day MA", "ma_20": "20-Day MA", "ma_50": "50-Day MA"}
    )
    st.line_chart(chart_data)

    # --- RSI Context ---
    if current_rsi > 70:
        st.error("RSI Status: Overbought (Possible Sell Signal)")
    elif current_rsi < 30:
        st.success("RSI Status: Oversold (Possible Buy Signal)")
    else:
        st.info("RSI Status: Neutral")

    st.divider()

    # --- Trading Recommendation ---
    st.subheader("Final Trading Recommendation")

    recommendation = "HOLD"  # Default fallback
    reason = "Awaiting clear signals."

    # Branch A: RSI < 30 (Oversold)
    if current_rsi < 30:
        if trend == "Upward Trend":
            recommendation = "STRONG BUY"
            reason = "Dip in a bullish trend. Excellent risk/reward."
        elif trend in ["Mixed Trend", "Downward Trend"]:
            if vol_category in ["Low", "Medium"]:
                recommendation = "BUY"
                reason = "Oversold bounce expected, but trade with caution against the trend."
            else:  
                recommendation = "HOLD"
                reason = "Oversold, but high volatility in a downtrend indicates a falling knife. Wait for stabilization."

    # Branch B: RSI > 70 (Overbought)
    elif current_rsi > 70:
        if trend == "Downward Trend":
            recommendation = "STRONG SELL"
            reason = "Overbought in a macro bear trend. High probability of rejection."
        elif trend in ["Upward Trend", "Mixed Trend"]:
            if vol_category == "High":
                recommendation = "SELL"
                reason = "Erratic and overextended. Good time to lock in profits."
            else:  
                recommendation = "HOLD"
                reason = "Overbought, but strong uptrends can remain overbought. Tighten stop-losses and let it run."

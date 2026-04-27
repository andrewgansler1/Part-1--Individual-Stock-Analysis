import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Set page title and layout
st.set_page_config(page_title="Stock Data Extraction App", layout='wide')

# Main title of the app
st.title("Stock Data Extraction App")

# Short description under the title
st.write("Extract stock market prices from Yahoo Finance using a ticker symbol.")

# Sidebar header
st.sidebar.header("User Input")

# Input box for ticker
ticker = st.sidebar.text_input("Enter Ticker", "AAPL")

# Input for start data
start_date = st.sidebar.date_input("Start Date", pd.to_datetime("today") - pd.DateOffset(months=6))
# Input for end date
end_date = st.sidebar.date_input("End Date", pd.to_datetime("today"))

if st.sidebar.button("Get Data"):
    # Create ticker object
    stock = yf.Ticker(ticker)

    # Get historical price data
    df = stock.history(start=start_date, end=end_date)

    # Check if data exists
    if df.empty:
        st.error("No data found. Please check the ticker symbol or date range.")
    else:
        # Show success message
        st.success(f"Data successfully extracted for {ticker}")

        # Trend Analysis
        st.subheader("Trend Analysis")

        # 1. Get current price and moving averages
        close = df["Close"].squeeze()
        current_price = close.iloc[-1]
        ma_20 = close.iloc[-20:].mean()
        ma_50 = close.iloc[-50:].mean()

        # 2. Determine the Trend
        if current_price > ma_20 and current_price > ma_50:
            trend = "Upward Trend"
        elif current_price < ma_20 and current_price < ma_50:
            trend = "Downward Trend"
        else:
            trend = "Mixed Trend"

        # 3. Calculate RSI
        delta = close.diff()
        gains = delta.clip(lower=0)
        losses = -delta.clip(upper=0)

        avg_gain = gains.iloc[-14:].mean()
        avg_loss = losses.iloc[-14:].mean()

        if avg_loss == 0:
            rsi = 100.0  # Fixed: explicitly define rsi here
        else:
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))

        # 4. Display the results beautifully formatted to 2 decimal places
        st.write(f"**Current Price:** ${current_price:.2f}")
        st.write(f"**20 Day Moving Average:** ${ma_20:.2f}")
        st.write(f"**50 Day Moving Average:** ${ma_50:.2f}")
        st.write(f"**Trend:** {trend}")
        
        # Momentum
        st.subheader("Momentum Analysis")
        st.write(f"**Relative Strength Index (RSI):** {rsi:.2f}")
        
        if rsi > 70:
            st.error("Overbought (Possible Sell Signal)")
        elif rsi < 30:
            st.success("Oversold (Possible Buy Signal)")
        else:
            st.info("Neutral")

        # Display Stock Data
        st.subheader("Historical Price Data")
        st.dataframe(df)

        # Plot the closing price
        st.subheader("Closing Price")
        fig, ax = plt.subplots()
        ax.plot(df.index, df["Close"])
        ax.set_xlabel("Date")
        ax.set_ylabel("Closing Price")
        ax.set_title(f"{ticker} Closing Price")
        st.pyplot(fig)
        
        st.subheader("Closing Price")
        fig, ax = plt.subplots()
        # Plot all three lines
        ax.plot(df.index, df["Close"], label="Closing Price", color="blue")
        ax.plot(df.index, df["MA_5"], label="5-Day MA", color="orange", linestyle="--")
        ax.plot(df.index, df["MA_20"], label="20-Day MA", color="green", linestyle="--")

        # Format the chart
        ax.set_xlabel("Date")
        ax.set_ylabel("Price")
        ax.set_title(f"{ticker} Closing Price")
        ax.set_title(f"{ticker} Closing Price")
        st.pyplot(fig)
        
        plt.plot(df["MA_5"], label="MA_5")
        plt.plot(df["MA_20"], label="MA_20")

        # Calculate daily returns
        daily_returns = close.pct_change()

        # 20-day rolling standard deviation of returns
        vol_20 = daily_returns.rolling(window=20).std()

        # Annualize volatility (multiply by sqrt(252 trading days))
        annual_vol_20 = vol_20 * (np.sqrt(252))

        # Get latest volatility value
        current_vol = float(annual_vol_20.iloc[-1])

        if current_vol > 0.40:
            vol_category = "High"
        elif current_vol >= 0.25:
            vol_category = "Medium"
        else:
            vol_category = "Low"

        # Convert the dataframe to CSV for download
        csv = df.to_csv().encode("utf-8")

        # Download button for CSV
        st.download_button(
            label="Download Data as CSV",
            data=csv,
            file_name=f"{ticker}_stock_data.csv",
            mime="text/csv"
        )
        # ------------------------------------------------
        # Step 5: Final Trading Recommendation
        # ------------------------------------------------
        st.subheader("Final Trading Recommendation")

        recommendation = "HOLD"  # Default fallback
        reason = ""

        # Branch A: RSI < 30 (Oversold)
        if rsi < 30:
            if trend == "Upward Trend":
                recommendation = "STRONG BUY"
                reason = "Dip in a bullish trend. Excellent risk/reward."
            elif trend in ["Mixed Trend", "Downward Trend"]:
                if vol_category in ["Low", "Medium"]:
                    recommendation = "BUY"
                    reason = "Oversold bounce expected, but trade with caution against the trend."
                else:  # High volatility
                    recommendation = "HOLD"
                    reason = "Oversold, but high volatility in a downtrend indicates a falling knife. Wait for stabilization."

        # Branch B: RSI > 70 (Overbought)
        elif rsi > 70:
            if trend == "Downward Trend":
                recommendation = "STRONG SELL"
                reason = "Overbought in a macro bear trend. High probability of rejection."
            elif trend in ["Upward Trend", "Mixed Trend"]:
                if vol_category == "High":
                    recommendation = "SELL"
                    reason = "Erratic and overextended. Good time to lock in profits."
                else:  # Low or Medium volatility
                    recommendation = "HOLD"
                    reason = "Overbought, but strong uptrends can remain overbought. Tighten stop-losses and let it run."

        # Branch C: RSI between 30 and 70 (Neutral)
        else:
            if trend == "Upward Trend":
                recommendation = "HOLD"
                reason = "Healthy uptrend with neutral momentum. Stay the course."
            elif trend == "Downward Trend":
                recommendation = "SELL"
                reason = "Bleeding out in a downtrend with no signs of a reversal."
            else:  # Mixed Trend
                recommendation = "HOLD"
                reason = "No clear directional edge. Keep capital safe and wait for a better setup."

        # Display the recommendation visually using Streamlit's colored message boxes
        if "BUY" in recommendation:
            st.success(f"**Recommendation: {recommendation}** \n*Reason:* {reason}")
        elif "SELL" in recommendation:
            st.error(f"**Recommendation: {recommendation}** \n*Reason:* {reason}")
        else:
            st.warning(f"**Recommendation: {recommendation}** \n*Reason:* {reason}")

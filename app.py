import yfinance as yf
import pandas as pd
import numpy as np
import streamlit as st

# 1. Page Configuration
st.set_page_config(page_title="Portfolio Analysis", layout='wide')
st.title("📈 Portfolio Data and Interpretation")
st.write("Compare your custom portfolio against the S&P 500 benchmark.")

# 2. Construct the portfolio
Portfolio = {
    'TSLA': 0.25,
    'NFLX': 0.20,
    'BABA': 0.20,
    'GME': 0.15,
    'PLTR': 0.20 
}

# 3. Define Date Range
end_date = pd.Timestamp.now().normalize()
start_date = end_date - pd.DateOffset(years=1)

# 4. Fetch Stock Data (Optimized with Caching)
@st.cache_data
def fetch_data(portfolio_dict, start, end):
    """Fetches stock and benchmark data, caches the result to speed up the app."""
    prices = pd.DataFrame()
    for symbol in portfolio_dict:
        data = yf.download(symbol, start=start, end=end, progress=False, auto_adjust=False, multi_level_index=False)
        prices[symbol] = data['Adj Close']
        
    benchmark_data = yf.download('^GSPC', start=start, end=end, progress=False, auto_adjust=False, multi_level_index=False)
    benchmark = benchmark_data['Adj Close']
    
    return prices, benchmark

prices, benchmark = fetch_data(Portfolio, start_date, end_date)

# 5. Calculate Daily Returns
daily_returns = prices.pct_change().dropna()
benchmark_returns = benchmark.pct_change().dropna()

# Align the index dates so both datasets match perfectly
common_index = daily_returns.index.intersection(benchmark_returns.index)
daily_returns = daily_returns.loc[common_index]
benchmark_returns = benchmark_returns.loc[common_index]

# Calculate weighted portfolio returns
portfolio_returns = pd.Series(0.0, index=common_index)
for symbol, weight in Portfolio.items():
    portfolio_returns += weight * daily_returns[symbol]

# 6. Calculate Metrics
# Cumulative Totals
portfolio_total = (1 + portfolio_returns).prod() - 1
benchmark_total = (1 + benchmark_returns).prod() - 1

# Volatility (Risk)
portfolio_vol = portfolio_returns.std() * np.sqrt(252)
benchmark_vol = benchmark_returns.std() * np.sqrt(252)

# Sharpe Ratio (Efficiency)
risk_free_rate = 0.03
portfolio_sharpe = (portfolio_total - risk_free_rate) / portfolio_vol
benchmark_sharpe = (benchmark_total - risk_free_rate) / benchmark_vol

# 7. Visualizations (New Feature)
st.header("Performance Dashboard")
st.divider()

st.subheader("Cumulative Growth Over Time")
# Calculate the running cumulative return over time for the chart
cum_portfolio = (1 + portfolio_returns).cumprod() - 1
cum_benchmark = (1 + benchmark_returns).cumprod() - 1

# Combine into one DataFrame for Streamlit to plot easily
chart_data = pd.DataFrame({
    'Portfolio': cum_portfolio,
    'S&P 500 (Benchmark)': cum_benchmark
})
st.line_chart(chart_data)

# 8. Dashboard Display
st.subheader("Key Metrics")
perf_diff = portfolio_total - benchmark_total

# Row 1: Return Metrics
col1, col2, col3 = st.columns(3)
with col1:
    st.metric(label="Portfolio Return", value=f"{portfolio_total:.2%}", delta=f"{perf_diff:.2%}")
with col2:
    st.metric(label="Benchmark Return", value=f"{benchmark_total:.2%}")
with col3:
    st.metric(label="Relative Performance", value=f"{perf_diff:.2%}")

st.write("") 

# Row 2: Risk Metrics
col4, col5, col6, col7 = st.columns(4)
with col4:
    st.metric(label="Portfolio Volatility", value=f"{portfolio_vol:.2%}")
with col5:
    st.metric(label="Benchmark Volatility", value=f"{benchmark_vol:.2%}")
with col6:
    st.metric(label="Portfolio Sharpe", value=f"{portfolio_sharpe:.2f}")
with col7:
    st.metric(label="Benchmark Sharpe", value=f"{benchmark_sharpe:.2f}")

# 9. Dynamic Portfolio Interpretation Summary
st.divider()
st.subheader("Analysis Summary")

# Determine dynamic text based on metrics
perf_text = "outperformed" if portfolio_total > benchmark_total else "underperformed"
risk_text = "more" if portfolio_vol > benchmark_vol else "less"
eff_text = "more" if portfolio_sharpe > benchmark_sharpe else "less"

st.info(f"""
**Based on the metrics above:**
* **Performance:** The portfolio **{perf_text}** the benchmark.
* **Risk:** The portfolio was **{risk_text}** risky (exhibiting {risk_text} volatility) compared to the broader market.
* **Efficiency:** The portfolio was **{eff_text}** efficient, generating a {eff_text} risk-adjusted return according to the Sharpe ratio.
""")

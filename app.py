import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np
from datetime import datetime, timedelta

# Configure page
st.set_page_config(
    page_title="FinSight – Institutional Portfolio Analytics",
    layout="wide",
    page_icon="📊"
)
st.title("📊 FinSight – Institutional Portfolio Analytics")

# --- Data Loading ---
@st.cache_data
def load_data():
    try:
        df = pd.read_csv("fundamentals.csv.csv", index_col=0)
        # Clean ticker column
        df['Ticker Symbol'] = df['Ticker Symbol'].str.strip()
        return df
    except Exception as e:
        st.error(f"❌ Error loading dataset: {str(e)}")
        st.stop()

df = load_data()
st.success(f"✅ Loaded {len(df)} assets from fundamentals dataset")

# --- Portfolio Simulation ---
st.sidebar.header("Portfolio Configuration")
num_assets = st.sidebar.slider("Number of assets", 5, 50, 20)

if 'Ticker Symbol' not in df.columns:
    st.error("Column 'Ticker Symbol' not found. Available columns:")
    st.write(df.columns.tolist())
    st.stop()

# Create realistic institutional portfolio
np.random.seed(42)
portfolio = pd.DataFrame({
    'Ticker': df['Ticker Symbol'].sample(num_assets).values,
    'Shares': np.random.randint(100, 10000, size=num_assets),
    'Entry Price': np.random.uniform(5, 300, size=num_assets).round(2)
})

# --- Risk Analytics Functions ---
def calculate_sharpe(returns, risk_free_rate=0.02):
    excess_returns = returns - risk_free_rate/252
    return np.sqrt(252) * excess_returns.mean() / returns.std()

def calculate_var(returns, confidence_level=0.95):
    return np.percentile(returns, 100 * (1 - confidence_level))

# --- Fetch Market Data ---
st.header("📈 Live Portfolio Analytics")
with st.spinner("Fetching live market data..."):
    try:
        # Get 3 months of data for more stable metrics
        data = yf.download(
            portfolio['Ticker'].tolist(),
            start=datetime.now() - timedelta(days=90),
            end=datetime.now(),
            group_by='ticker'
        )
        
        # Calculate daily returns
        returns = pd.DataFrame()
        for ticker in portfolio['Ticker']:
            if ticker in data.columns.levels[0]:
                close_prices = data[ticker]['Close']
                returns[ticker] = close_prices.pct_change()
        
        if returns.empty:
            st.error("No valid price data found for any tickers")
            st.stop()
            
    except Exception as e:
        st.error(f"Failed to fetch market data: {str(e)}")
        st.stop()

# --- Portfolio Performance ---
col1, col2 = st.columns(2)
with col1:
    st.subheader("Portfolio Composition")
    st.dataframe(portfolio.style.format({
        'Shares': '{:,}',
        'Entry Price': '${:.2f}'
    }))

with col2:
    st.subheader("Key Metrics")
    
    # Calculate metrics
    portfolio_return = returns.mean(axis=1).mean() * 252
    portfolio_volatility = returns.mean(axis=1).std() * np.sqrt(252)
    sharpe = calculate_sharpe(returns.mean(axis=1))
    
    metric_col1, metric_col2 = st.columns(2)
    metric_col1.metric("Annualized Return", f"{portfolio_return:.1%}")
    metric_col1.metric("Volatility", f"{portfolio_volatility:.1%}")
    metric_col2.metric("Sharpe Ratio", f"{sharpe:.2f}")
    metric_col2.metric("95% VaR", f"{calculate_var(returns.mean(axis=1)):.2%}")

# --- Fundamental Metrics Analysis ---
st.subheader("📊 Fundamental Metrics Analysis")
selected_metric = st.selectbox("Select fundamental metric", 
                             ['Total Revenue', 'Net Income', 'Total Assets', 'Long-Term Debt'])

# Merge portfolio with fundamental data
portfolio_fundamentals = portfolio.merge(
    df[['Ticker Symbol', 'Total Revenue', 'Net Income', 'Total Assets', 'Long-Term Debt']],
    left_on='Ticker',
    right_on='Ticker Symbol',
    how='left'
)

if not portfolio_fundamentals.empty:
    # Calculate portfolio-weighted metrics
    portfolio_fundamentals['Weight'] = portfolio_fundamentals['Shares'] / portfolio_fundamentals['Shares'].sum()
    
    # Display metrics
    col1, col2 = st.columns(2)
    
    with col1:
        st.write(f"### Portfolio {selected_metric} Distribution")
        st.bar_chart(portfolio_fundamentals.set_index('Ticker')[selected_metric])
    
    with col2:
        st.write("### Portfolio Fundamentals")
        avg_metric = (portfolio_fundamentals[selected_metric] * portfolio_fundamentals['Weight']).sum()
        st.metric(f"Portfolio Weighted {selected_metric}", f"${avg_metric/1e6:,.1f}M")
        
        # Show top 5 holdings by selected metric
        st.write(f"Top 5 by {selected_metric}:")
        st.dataframe(portfolio_fundamentals[['Ticker', selected_metric]].sort_values(
            selected_metric, ascending=False).head(5).style.format({
                selected_metric: '${:,.0f}'
            }))
else:
    st.warning("Could not merge portfolio with fundamental data")

# --- Individual Asset Analysis ---
st.subheader("🔍 Individual Asset Performance")
selected_ticker = st.selectbox("Select asset", portfolio['Ticker'])

if selected_ticker in data.columns.levels[0]:
    col1, col2 = st.columns(2)
    
    with col1:
        st.write(f"### {selected_ticker} Price History")
        st.line_chart(data[selected_ticker]['Close'])
    
    with col2:
        st.write("### Risk Metrics")
        ticker_returns = returns[selected_ticker].dropna()
        
        st.metric("Daily Sharpe", f"{calculate_sharpe(ticker_returns):.2f}")
        st.metric("95% VaR", f"{calculate_var(ticker_returns):.2%}")
        st.metric("Max Drawdown", 
                 f"{(ticker_returns.cumsum().min()):.2%}")
        
        # Show fundamental metrics for selected ticker
        ticker_fundamentals = df[df['Ticker Symbol'] == selected_ticker]
        if not ticker_fundamentals.empty:
            st.write("### Fundamental Metrics")
            st.metric("Total Revenue", f"${ticker_fundamentals['Total Revenue'].values[0]/1e6:,.1f}M")
            st.metric("Net Income", f"${ticker_fundamentals['Net Income'].values[0]/1e6:,.1f}M")
            st.metric("Total Assets", f"${ticker_fundamentals['Total Assets'].values[0]/1e6:,.1f}M")
else:
    st.warning(f"No data available for {selected_ticker}")

# --- PM-Style Documentation ---
st.sidebar.header("Product Documentation")
with st.sidebar.expander("Product Spec"):
    st.write("""
    **FinSight v1.0**  
    *For Institutional Portfolio Managers*
    
    **Key Features**:
    - Real-time risk metrics (Sharpe, VaR)
    - Fundamental metrics analysis
    - Benchmarking against market indices
    
    **Data Sources**:
    - Company fundamentals (CSV)
    - Live market data (Yahoo Finance)
    
    **Success Metrics**:
    - 50% faster than Excel workflows
    - Sub-3-second load time
    """)

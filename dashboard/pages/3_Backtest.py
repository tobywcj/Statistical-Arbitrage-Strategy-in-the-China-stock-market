import streamlit as st
import pandas as pd
import plotly.express as px
import asyncio
from datetime import datetime, timedelta
import sys
import os

# Add root directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from app.db.mongo import db
from app.analytics.clustering import calculate_log_returns, get_correlation_matrix, cluster_hierarchical, cluster_spectral
from app.analytics.strategy import calculate_cluster_returns, calculate_residuals, calculate_z_scores, generate_signals
from app.analytics.backtest import run_backtest

from app.providers.fallback import check_mongo_connection, fetch_bars_direct, get_fallback_instruments, get_db_overall_range

st.set_page_config(page_title="Backtest", page_icon="🧪", layout="wide")
st.title("🧪 Strategy Backtest")

# --- Fallback Check ---
if "db_connected" not in st.session_state:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    st.session_state["db_connected"] = loop.run_until_complete(check_mongo_connection())

if not st.session_state["db_connected"]:
    st.warning("⚠️ **Direct-Fetch Mode Active**: Data is being fetched directly from Yahoo Finance. **Note: Backtest will be limited to a sample of 30 stocks for speed.**")
else:
    st.success("✅ **Local Database Mode Active**: Data is being served from MongoDB.")

# --- Helper ---
@st.cache_data(ttl=300)
def load_data_for_backtest(exchange, start, end):
    if not st.session_state["db_connected"]:
        # Demo Mode: Sample 30 stocks
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        instruments = loop.run_until_complete(get_fallback_instruments())
        tickers = [i.ticker for i in instruments][:30]
        
        all_bars = []
        progress_bar = st.progress(0, text="Fetching backtest data from Yahoo...")
        for i, t in enumerate(tickers):
            progress_bar.progress((i + 1) / len(tickers), text=f"Fetching {t} ({i+1}/{len(tickers)})")
            bars = fetch_bars_direct(t, start, end)
            all_bars.extend([b.model_dump(by_alias=True) for b in bars])
        progress_bar.empty()
        return all_bars

    async def _fetch():
        from motor.motor_asyncio import AsyncIOMotorClient
        from app.db.mongo import settings

        client = AsyncIOMotorClient(settings.MONGO_URI)
        db = client[settings.MONGO_DB_NAME]
        
        bars_coll = db["bars_daily"]
        query = {
            "exchange": exchange, 
            "date": {"$gte": start, "$lte": end}
        }
        cursor = bars_coll.find(query)
        data = await cursor.to_list(length=None)
        client.close()
        return data
        
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    return loop.run_until_complete(_fetch())

# --- Parameters ---
with st.sidebar:
    st.header("Settings")
    
    st.subheader("Data")
    lookback_years = st.selectbox(
        "Lookback Years",
        options=list(range(1, 9)),
        index=1, # Default to 2 years
        help="Select the number of years of historical data to load for backtesting."
    )
    
    if st.session_state["db_connected"]:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        db_range = loop.run_until_complete(get_db_overall_range())
        if db_range:
            st.sidebar.caption(f"📦 **DB Coverage**: {db_range['min_date'].date()} to {db_range['max_date'].date()}")
        else:
            st.sidebar.caption("📦 **DB Coverage**: No data found.")

    start_date = st.date_input("Start Date", datetime.utcnow() - timedelta(days=365*lookback_years))
    end_date = st.date_input("End Date", datetime.utcnow())
    
    st.subheader("Clustering")
    method = st.selectbox("Method", ["Hierarchical", "Spectral"])
    num_clusters = st.slider("Num Clusters", 2, 20, 5)
    
    st.subheader("Strategy")
    lookback = st.slider("Z-Score Lookback", 5, 252, 60)
    entry_threshold = st.slider("Entry Threshold (Z)", 0.5, 3.0, 2.0)
    st.info("💡 **Why 2.0?** A Z-score of 2.0 represents a 95% statistical outlier. This ensures you trade significant divergences, reducing noise and transaction costs.")

if st.button("Run Backtest"):
    # 1. Load Data
    start_dt = datetime.combine(start_date, datetime.min.time())
    end_dt = datetime.combine(end_date, datetime.max.time())
    
    with st.spinner("Loading data..."):
        data = load_data_for_backtest("SSE", start_dt, end_dt)
        if not data:
            st.error("No data found.")
            st.stop()
            
        df_raw = pd.DataFrame(data)
        prices = df_raw.pivot(index="date", columns="ticker", values="close").sort_index().ffill().dropna(axis=1)
        
        if prices.empty:
            st.error("Not enough valid data.")
            st.stop()
            
    # 2. Train Clustering (Rolling? Or Static?)
    # MVP: Static clustering based on first half or whole period? 
    # Spec implies: "Given the cluster... devise strategy". 
    # Usually clustering is recomputed. For MVP, let's compute on entire dataset (lookahead bias warning, but simpler)
    # OR better: Compute clustering on first N days? 
    # Let's Stick to "Compute on Whole" for MVP simplicity, noting the bias.
    
    with st.spinner("Clustering..."):
        returns = calculate_log_returns(prices)
        corr_matrix = get_correlation_matrix(returns)
        
        if method == "Hierarchical":
            clusters = cluster_hierarchical(corr_matrix, num_clusters)
        else:
            clusters = cluster_spectral(corr_matrix, num_clusters)
            
    # 3. Strategy
    with st.spinner("Simulating Strategy..."):
        cluster_rets = calculate_cluster_returns(returns, clusters)
        residuals = calculate_residuals(returns, cluster_rets, clusters)
        z_scores = calculate_z_scores(residuals, lookback)
        signals = generate_signals(z_scores, entry_threshold)
        
        results = run_backtest(returns, signals, clusters)
        
    # 4. Results
    st.success("Backtest Complete")
    
    # Equity Curve
    cumulative = results['cumulative_returns']
    
    fig = px.line(cumulative, title="Portfolio Equity Curve")
    fig.update_layout(
        xaxis_title="Date",
        yaxis_title="Cumulative Return (1.0 = Initial Capital)"
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Metrics
    metrics = results['metrics']
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Return", f"{metrics['Total Return']:.2%}")
    col2.metric("Sharpe Ratio", f"{metrics['Sharpe Ratio']:.2f}")
    col3.metric("Max Drawdown", f"{metrics['Max Drawdown']:.2%}")
    col4.metric("Avg Daily Turnover", f"{metrics['Daily Turnover']:.4f}")
    
    with st.expander("Clustering Details"):
        for c_id, members in clusters.items():
            st.write(f"Cluster {c_id}: {members}")

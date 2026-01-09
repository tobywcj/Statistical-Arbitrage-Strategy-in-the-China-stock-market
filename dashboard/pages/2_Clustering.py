import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import asyncio
from datetime import datetime, timedelta
import sys
import os

# Add root directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from app.db.mongo import db
from app.analytics.clustering import calculate_log_returns, get_correlation_matrix, cluster_hierarchical, cluster_spectral

st.set_page_config(page_title="Clustering Analysis", page_icon="🧬", layout="wide")
st.title("🧬 Clustering Analysis")

# --- Helper ---
@st.cache_resource
def get_db():
    return db

@st.cache_data(ttl=300)
def load_all_prices(exchange, start, end):
    async def _fetch():
        from motor.motor_asyncio import AsyncIOMotorClient
        from app.db.mongo import settings

        client = AsyncIOMotorClient(settings.MONGO_URI)
        db = client[settings.MONGO_DB_NAME]

        # Find all tickers first
        instruments = db["instruments"]
        tickers_cursor = instruments.find({"exchange": exchange, "is_active": True})
        tickers = [i["ticker"] for i in await tickers_cursor.to_list(length=None)]
        
        # Load bars
        bars_coll = db["bars_daily"]
        query = {
            "exchange": exchange, 
            "date": {"$gte": start, "$lte": end}
        }
        # Optimize: can be heavy
        cursor = bars_coll.find(query)
        data = await cursor.to_list(length=None)
        client.close()
        return tickers, data
        
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    return loop.run_until_complete(_fetch())

# --- UI ---
exchange = "SSE"
col1, col2, col3 = st.columns(3)
with col1:
    start_date = st.date_input("Start Date", datetime.utcnow() - timedelta(days=365))
with col2:
    end_date = st.date_input("End Date", datetime.utcnow())
with col3:
    method = st.selectbox("Clustering Method", ["Hierarchical", "Spectral"])
    
    if method == "Hierarchical":
        st.info("Builds a tree of clusters by merging similar stocks. Good for finding nested relationships (e.g., Sector -> Industry).")
    else:
        st.info("Uses graph theory (eigenvalues) to cut the correlation network. Good for finding distinct, non-overlapping groups.")

num_clusters = st.slider("Number of Clusters", 2, 20, 5)

if st.button("Run Clustering"):
    with st.spinner("Loading data..."):
        start_dt = datetime.combine(start_date, datetime.min.time())
        end_dt = datetime.combine(end_date, datetime.max.time())
        tickers, data = load_all_prices(exchange, start_dt, end_dt)
        
        if not data:
            st.error("No data found.")
            st.stop()
        
        st.warning("Note: Clustering is performed on ALL available stocks. The Heatmap below shows only the Top 50 by volume for readability.")
            
        df_raw = pd.DataFrame(data)
        # Pivot to Price Matrix (Date x Ticker)
        prices = df_raw.pivot(index="date", columns="ticker", values="close")
        prices = prices.sort_index()
        
        # Handle missing data: ffill then clean drop
        prices = prices.ffill().dropna(axis=1, how='any') 
        
        if prices.empty:
            st.error("Not enough overlapping data.")
            st.stop()
            
    with st.spinner("Calculating correlations..."):
        returns = calculate_log_returns(prices)
        corr_matrix = get_correlation_matrix(returns)
        
        st.write(f"Analyzed {len(corr_matrix)} assets.")
        
        # Plot Correlation Heatmap (Top 50 by Volume)
        st.subheader("Correlation Heatmap (Top 50 Active Stocks)")
        
        # Calculate volume just for ranking display
        volumes = df_raw.pivot(index="date", columns="ticker", values="volume")
        avg_vol = volumes.mean().sort_values(ascending=False)
        # Intersection of valid prices and volume data
        valid_tickers = [t for t in avg_vol.index if t in corr_matrix.index]
        top_50 = valid_tickers[:50]
        
        display_corr = corr_matrix.loc[top_50, top_50]
        
        fig_corr, ax = plt.subplots(figsize=(10, 8))
        sns.heatmap(display_corr, cmap="coolwarm", center=0, ax=ax)
        st.pyplot(fig_corr)
        
    with st.spinner(f"Running {method} Clustering..."):
        if method == "Hierarchical":
            clusters = cluster_hierarchical(corr_matrix, num_clusters)
        else:
            clusters = cluster_spectral(corr_matrix, num_clusters)
            
        st.subheader("Clusters")
        
        # Display clusters
        for c_id, members in clusters.items():
            st.markdown(f"**Cluster {c_id}** ({len(members)} assets)")
            st.code(", ".join(members))

import streamlit as st
import sys
import os
import asyncio

# Add root directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.providers.fallback import check_mongo_connection

st.set_page_config(
    page_title="SSE Stat Arb",
    page_icon="📈",
    layout="wide"
)

st.title("📈 SSE Statistical Arbitrage MVP")

st.markdown("""
Welcome to the Shanghai Stock Exchange Statistical Arbitrage Platform. This system identifies statistical co-movements between stocks and executes a mean-reversion strategy based on cluster residuals.

### 🧩 Modules

- **📊 Data Explorer**: View historical OHLCV data for SSE stocks.
- **🧬 Clustering**: Analyze correlations and group stocks using Hierarchical or Spectral clustering.
- **🧪 Backtest**: Run Mean-Reversion strategies on generated clusters.

### 🛠 System Status
""")

# Quick connectivity check
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
db_available = loop.run_until_complete(check_mongo_connection())

# Sidebar Data Source Selection
st.sidebar.markdown("### 🔌 Data Source")
if db_available:
    source = st.sidebar.radio(
        "Select Source",
        ["Local MongoDB", "Real-time Yahoo"],
        index=0,
        help="Local MongoDB is faster (cached). Real-time Yahoo fetches data on-the-fly."
    )
    st.session_state["db_connected"] = (source == "Local MongoDB")
else:
    st.sidebar.warning("❌ Local MongoDB not detected.")
    st.sidebar.radio(
        "Select Source",
        ["Real-time Yahoo"],
        index=0,
        disabled=True
    )
    st.session_state["db_connected"] = False

if st.session_state["db_connected"]:
    st.success("✅ **Database Mode Active**: Using local MongoDB for high performance.")
else:
    st.warning("⚠️ **Direct-Fetch Mode Active**: Fetching directly from Yahoo Finance. **Note: Loading will be slower.**")

st.sidebar.divider()
st.sidebar.info("Select a page from the sidebar to get started.")
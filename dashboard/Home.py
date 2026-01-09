import streamlit as st
import sys
import os

# Add root directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.db.mongo import db

st.set_page_config(
    page_title="SSE Stat Arb",
    page_icon="📈",
    layout="wide"
)

st.title("🇨🇳 SSE Statistical Arbitrage MVP")

st.markdown("""
Welcome to the Shanghai Stock Exchange Statistical Arbitrage Platform.

### Modules

- **Data Explorer**: View historical OHLCV data for SSE stocks.
- **Clustering**: Analyze correlations and group stocks using Hierarchical or Spectral clustering.
- **Backtest**: Run Mean-Reversion strategies on generated clusters.

### System Status

Checking database connection...
""")

try:
    # Quick connectivity check
    import asyncio
    
    async def check_db():
        await db.get_collection("instruments")
        return "Connected"
        
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    status = loop.run_until_complete(check_db())
    st.success(f"MongoDB: {status}")
except Exception as e:
    st.error(f"MongoDB Connection Failed: {e}")

st.sidebar.info("Select a page from the sidebar to get started.")
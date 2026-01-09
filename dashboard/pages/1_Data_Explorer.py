import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import asyncio
from datetime import datetime, timedelta
import sys
import os

# Add root directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from app.providers.fallback import check_mongo_connection, fetch_bars_direct, get_fallback_instruments, get_db_overall_range

st.set_page_config(page_title="Data Explorer", page_icon="🔍", layout="wide")

st.title("🔍 Data Explorer")

# --- Fallback Check ---
if "db_connected" not in st.session_state:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    st.session_state["db_connected"] = loop.run_until_complete(check_mongo_connection())

if not st.session_state["db_connected"]:
    st.warning("⚠️ **Direct-Fetch Mode Active**: Data is being fetched directly from Yahoo Finance. No local database is being used.")
else:
    st.success("✅ **Local Database Mode Active**: Data is being served from MongoDB.")

# --- Data Loading ---
@st.cache_data(ttl=300)
def load_instruments():
    if not st.session_state["db_connected"]:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(get_fallback_instruments())
        
    async def _fetch():
        from motor.motor_asyncio import AsyncIOMotorClient
        from app.db.mongo import settings
        
        client = AsyncIOMotorClient(settings.MONGO_URI)
        db = client[settings.MONGO_DB_NAME]
        
        coll = db["instruments"]
        await coll.create_index("ticker", unique=True)
        cursor = coll.find({"exchange": "SSE", "is_active": True})
        
        result = await cursor.to_list(length=None)
        client.close()
        return result
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    return loop.run_until_complete(_fetch())

@st.cache_data(ttl=60)
def load_bars(ticker, start, end):
    if not st.session_state["db_connected"]:
        # Direct fetch from Yahoo
        data = fetch_bars_direct(ticker, start, end)
        if data:
            return pd.DataFrame([b.model_dump(by_alias=True) for b in data])
        return pd.DataFrame()

    async def _fetch():
        from motor.motor_asyncio import AsyncIOMotorClient
        from app.db.mongo import settings
        
        client = AsyncIOMotorClient(settings.MONGO_URI)
        db = client[settings.MONGO_DB_NAME]
        
        coll = db["bars_daily"]
        cursor = coll.find({
            "ticker": ticker, 
            "date": {"$gte": start, "$lte": end}
        }).sort("date", 1)
        
        result = await cursor.to_list(length=None)
        client.close()
        return result
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    data = loop.run_until_complete(_fetch())
    if data:
        return pd.DataFrame([d for d in data])
    return pd.DataFrame()

# --- UI Controls ---
st.sidebar.markdown("### 📅 Time Range")
lookback_years = st.sidebar.selectbox(
    "Lookback Years",
    options=list(range(1, 9)),
    index=1, # Default to 2 years
    help="Select the number of years of historical data to load."
)

if st.session_state["db_connected"]:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    db_range = loop.run_until_complete(get_db_overall_range())
    if db_range:
        st.sidebar.caption(f"📦 **DB Coverage**: {db_range['min_date'].date()} to {db_range['max_date'].date()}")
    else:
        st.sidebar.caption("📦 **DB Coverage**: No data found.")

instruments = load_instruments()
if not instruments:
    st.warning("No instruments found.")
    st.stop()

ticker_list = sorted([i['ticker'] for i in (instruments if isinstance(instruments[0], dict) else [i.model_dump() for i in instruments])])
ticker = st.selectbox("Select Ticker", ticker_list)

@st.cache_data(ttl=300)
def get_date_range(ticker, years):
    if not st.session_state["db_connected"]:
        # For fallback, use the selected years
        return {
            "min_date": datetime.utcnow() - timedelta(days=365*years),
            "max_date": datetime.utcnow()
        }

    async def _fetch():
        from motor.motor_asyncio import AsyncIOMotorClient
        from app.db.mongo import settings
        
        client = AsyncIOMotorClient(settings.MONGO_URI)
        db = client[settings.MONGO_DB_NAME]
        coll = db["bars_daily"]
        
        # Get min and max date
        pipeline = [
            {"$match": {"ticker": ticker}},
            {"$group": {
                "_id": None,
                "min_date": {"$min": "$date"},
                "max_date": {"$max": "$date"}
            }}
        ]
        result = await coll.aggregate(pipeline).to_list(length=1)
        client.close()
        return result[0] if result else None

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    return loop.run_until_complete(_fetch())

col1, col2 = st.columns(2)

date_range = get_date_range(ticker, lookback_years)
if date_range:
    min_dt = date_range["min_date"]
    max_dt = date_range["max_date"]
    
    if st.session_state["db_connected"]:
        st.caption(f"Available Data: {min_dt.date()} to {max_dt.date()}")
    else:
        st.caption("Mode: Real-time fetch (Direct from Yahoo Finance)")
    
    with col1:
        start_date = st.date_input(
            "Start Date", 
            value=max(min_dt, datetime.utcnow() - timedelta(days=365)),
            min_value=min_dt,
            max_value=max_dt
        )
    with col2:
        end_date = st.date_input(
            "End Date", 
            value=max_dt,
            min_value=min_dt,
            max_value=max_dt
        )
else:
    st.warning("No data found for this ticker. Please run backfill.")
    with col1:
        start_date = st.date_input("Start Date", datetime.utcnow() - timedelta(days=365))
    with col2:
        end_date = st.date_input("End Date", datetime.utcnow())

# --- Visualization ---

if st.button("Load Data"):
    # Convert date to datetime
    start_dt = datetime.combine(start_date, datetime.min.time())
    end_dt = datetime.combine(end_date, datetime.max.time())
    
    df = load_bars(ticker, start_dt, end_dt)
    
    if not df.empty:
        st.write(f"Loaded {len(df)} bars.")
        
        # Candle Chart
        fig = go.Figure(data=[go.Candlestick(
            x=df['date'],
            open=df['open'],
            high=df['high'],
            low=df['low'],
            close=df['close']
        )])
        fig.update_layout(title=f"{ticker} OHLC", xaxis_title="Date", yaxis_title="Price")
        st.plotly_chart(fig, use_container_width=True)
        
        # Volume
        st.subheader("Volume")
        st.bar_chart(df.set_index("date")["volume"])
        
        with st.expander("Raw Data"):
            st.dataframe(df)
            
    else:
        st.info("No data found for the selected range.")

import asyncio
import pandas as pd
from datetime import datetime
from typing import List, Optional
import yfinance as yf
from motor.motor_asyncio import AsyncIOMotorClient
from app.db.mongo import settings
from app.db.schema import Instrument, Bar

async def check_mongo_connection() -> bool:
    """Check if MongoDB is reachable."""
    try:
        client = AsyncIOMotorClient(settings.MONGO_URI, serverSelectionTimeoutMS=2000)
        await client.admin.command('ping')
        client.close()
        return True
    except Exception:
        return False

def fetch_bars_direct(ticker: str, start: datetime, end: datetime) -> List[Bar]:
    """Fetch bars directly from Yahoo Finance without DB."""
    # Convert ticker format (SH -> SS for Yahoo)
    y_ticker = ticker.replace(".SH", ".SS") if ticker.endswith(".SH") else ticker
    
    df = yf.download(y_ticker, start=start.strftime("%Y-%m-%d"), end=end.strftime("%Y-%m-%d"), progress=False)
    
    if df.empty:
        return []
    
    # yfinance often returns MultiIndex columns even for single tickers
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
        
    df = df.reset_index()
    bars = []
    for _, row in df.iterrows():
        try:
            # Handle potential MultiIndex/Series from yfinance
            def get_val(col, default_col=None):
                if col not in row and default_col in row:
                    col = default_col
                if col not in row:
                    return 0.0
                val = row[col]
                return float(val.iloc[0]) if isinstance(val, pd.Series) else float(val)

            d = row['Date'].iloc[0] if isinstance(row['Date'], pd.Series) else row['Date']
            d = d.to_pydatetime()
            
            bars.append(Bar(
                _id=f"{ticker}:{d.strftime('%Y-%m-%d')}",
                ticker=ticker,
                exchange="SSE",
                date=d,
                open=get_val('Open'),
                high=get_val('High'),
                low=get_val('Low'),
                close=get_val('Close'),
                adj_close=get_val('Adj Close', 'Close'),
                volume=get_val('Volume'),
                source="yahoo_direct"
            ))
        except Exception:
            continue
    return bars

async def get_fallback_instruments() -> List[Instrument]:
    """Return a hardcoded sample universe if DB is down."""
    from scripts.load_instruments import STOCK_CONNECT_SSE_SAMPLE
    return [
        Instrument(ticker=t, exchange="SSE", is_active=True, source="hardcoded_fallback")
        for t in STOCK_CONNECT_SSE_SAMPLE[:100] # Use top 100 for demo
    ]
async def get_db_overall_range() -> dict:
    """Get the min and max date available in the entire database."""
    try:
        client = AsyncIOMotorClient(settings.MONGO_URI, serverSelectionTimeoutMS=2000)
        db = client[settings.MONGO_DB_NAME]
        coll = db["bars_daily"]
        
        pipeline = [
            {"$group": {
                "_id": None,
                "min_date": {"$min": "$date"},
                "max_date": {"$max": "$date"}
            }}
        ]
        result = await coll.aggregate(pipeline).to_list(length=1)
        client.close()
        
        if result and result[0]["min_date"]:
            return result[0]
        return None
    except Exception:
        return None

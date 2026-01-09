from fastapi import FastAPI, Query, HTTPException
from typing import List, Optional
from datetime import datetime
from app.db.mongo import db
from app.db.schema import Bar, Instrument


app = FastAPI(title="SSE Statistical Arbitrage API")

@app.on_event("startup")
async def startup_db_client():
    db.connect()

@app.on_event("shutdown")
async def shutdown_db_client():
    db.close()

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.get("/v1/instruments", response_model=List[Instrument])
async def get_instruments(exchange: str = "SSE"):
    collection = await db.get_collection("instruments")
    cursor = collection.find({"exchange": exchange})
    instruments = await cursor.to_list(length=None)
    return instruments

@app.get("/v1/bars", response_model=List[Bar])
async def get_bars(
    ticker: str,
    start: datetime,
    end: datetime,
    fields: Optional[List[str]] = Query(None)
):
    collection = await db.get_collection("bars_daily")
    
    query = {
        "ticker": ticker,
        "date": {
            "$gte": start,
            "$lte": end
        }
    }
    
    cursor = collection.find(query).sort("date", 1)
    bars = await cursor.to_list(length=None)
    
    if not bars:
        return []
        
    return bars
    
# Analytics endpoints could be added here or just imported in dashboard
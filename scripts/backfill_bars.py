import asyncio
import argparse
from datetime import datetime, timedelta, timezone

from app.db.mongo import db
from app.providers.yahoo import YahooProvider

async def backfill_bars(exchange: str, years: int):
    print(f"Backfilling {years} years for {exchange}...")
    # Initialize DB connection
    await db.create_indexes()
    
    # Get instruments
    inst_coll = await db.get_collection("instruments")
    cursor = inst_coll.find({"exchange": exchange, "is_active": True})
    instruments = await cursor.to_list(length=None)
    
    if not instruments:
        print("No instruments found. Run load_instruments.py first.")
        return

    provider = YahooProvider()
    bars_coll = await db.get_collection("bars_daily")
    
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=years*365)
    
    print(f"Processing {len(instruments)} instruments...")
    
    for inst in instruments:
        ticker = inst["ticker"]
        # optimization: check latest date in DB to avoid refetching? 
        # For MVP we just fetch all requested range to be safe or overwrite.
        
        try:
            bars = provider.fetch_bars(ticker, start_date, end_date)
            if not bars:
                continue
                
            # Batch upsert is tricky with standard update_many for upserts with different IDs
            # Simple approach: one by one or bulk_write
            # For MVP speed, let's use bulk_write with ReplaceOne
            from pymongo import ReplaceOne
            
            ops = []
            for bar in bars:
                ops.append(
                    ReplaceOne(
                        {"_id": bar.id},
                        bar.model_dump(by_alias=True),
                        upsert=True
                    )
                )
            
            if ops:
                result = await bars_coll.bulk_write(ops)
                print(f"Upserted {len(ops)} bars for {ticker}")
                
        except Exception as e:
            print(f"Error processing {ticker}: {e}")
            
    print("Backfill complete.")
    db.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--exchange", type=str, default="SSE")
    parser.add_argument("--years", type=int, default=2)
    args = parser.parse_args()
    
    asyncio.run(backfill_bars(args.exchange, args.years))

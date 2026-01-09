import asyncio
import argparse
from app.db.mongo import db
from app.db.schema import Instrument

STOCK_CONNECT_SSE_SAMPLE = [
    "600000.SH", "600009.SH", "600010.SH", "600011.SH", "600015.SH",
    "600016.SH", "600018.SH", "600019.SH", "600025.SH", "600028.SH",
    "600029.SH", "600030.SH", "600031.SH", "600036.SH", "600048.SH",
    "600050.SH", "600061.SH", "600085.SH", "600089.SH", "600104.SH",
    "600109.SH", "600111.SH", "600115.SH", "600150.SH", "600161.SH",
    "600176.SH", "600183.SH", "600188.SH", "600196.SH", "600276.SH",
    "600309.SH", "600346.SH", "600362.SH", "600383.SH", "600406.SH",
    "600436.SH", "600438.SH", "600489.SH", "600519.SH", "600547.SH",
    "600570.SH", "600585.SH", "600588.SH", "600600.SH", "600606.SH",
    "600660.SH", "600690.SH", "600703.SH", "600741.SH", "600745.SH",
    "600760.SH", "600809.SH", "600845.SH", "600887.SH",
    "600893.SH", "600900.SH", "600918.SH", "600919.SH", "600926.SH",
    "600958.SH", "600999.SH", "601006.SH", "601009.SH", "601012.SH",
    "601021.SH", "601066.SH", "601088.SH", "601100.SH", "601111.SH",
    "601138.SH", "601155.SH", "601166.SH", "601169.SH", "601186.SH",
    "601211.SH", "601225.SH", "601229.SH", "601288.SH", "601318.SH",
    "601319.SH", "601328.SH", "601336.SH", "601360.SH", "601377.SH",
    "601390.SH", "601398.SH", "601601.SH", "601618.SH", "601628.SH",
    "601633.SH", "601658.SH", "601668.SH", "601669.SH", "601688.SH",
    "601698.SH", "601727.SH", "601766.SH", "601788.SH", "601799.SH",
    "601800.SH", "601808.SH", "601816.SH", "601818.SH", "601838.SH",
    "601857.SH", "601877.SH", "601878.SH", "601881.SH", "601888.SH",
    "601898.SH", "601899.SH", "601901.SH", "601919.SH", "601933.SH",
    "601939.SH", "601985.SH", "601988.SH", "601995.SH",
    "601998.SH"
]

async def load_instruments(source: str):
    print(f"Loading instruments from {source}...")
    await db.create_indexes()
    
    collection = await db.get_collection("instruments")
    
    if source == "hkex_stock_connect":
        tickers = STOCK_CONNECT_SSE_SAMPLE
    else:
        print("Unknown source. Using sample.")
        tickers = ["600000.SH", "600519.SH"]

    count = 0
    for ticker in tickers:
        inst = Instrument(
            ticker=ticker,
            exchange="SSE",
            is_active=True,
            source=source
        )
        try:
            await collection.replace_one(
                {"ticker": ticker},
                inst.model_dump(),
                upsert=True
            )
            count += 1
        except Exception as e:
            print(f"Failed to upsert {ticker}: {e}")
            
    print(f"Loaded {count} instruments.")
    db.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=str, default="hkex_stock_connect")
    args = parser.parse_args()
    
    asyncio.run(load_instruments(args.source))

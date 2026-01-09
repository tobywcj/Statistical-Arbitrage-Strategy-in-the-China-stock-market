import yfinance as yf
from datetime import datetime, timedelta
from typing import List, Optional
import pandas as pd
from app.providers.base import DataProvider
from app.db.schema import Instrument, Bar

class YahooProvider(DataProvider):
    
    def get_instruments(self) -> List[Instrument]:
        # Yahoo doesn't have an API to list all tickers for an exchange easily.
        # This usually relies on an external list or the Stock Connect list provided in the MVP scaffold logic via scripts.
        # We will return common SSE indices/stocks as a fallback or this might not be fully implemented here 
        # but the load_instruments script handles the source.
        # For strict interface compliance, we return an empty list or a hardcoded example.
        # In reality, the script provided by the user (stub) loads from HKEX or manual list.
        return []

    def fetch_bars(self, ticker: str, start: datetime, end: datetime) -> List[Bar]:
        
        # Yahoo expects YYYY-MM-DD
        start_str = start.strftime("%Y-%m-%d")
        end_str = end.strftime("%Y-%m-%d")
        
        # yfinance download
        # Ticker format: 600000.SS for Shanghai in Yahoo.
        # User input might be 600000.SH (Tushare convention).
        # We need to convert.
        if ticker.endswith(".SH"):
            y_ticker = ticker.replace(".SH", ".SS")
        elif ticker.endswith(".SZ"):
            y_ticker = ticker.replace(".SZ", ".SZ") # Yahoo uses .SZ for Shenzhen
        else:
            y_ticker = ticker
            
        print(f"Fetching {y_ticker} from {start_str} to {end_str} via Yahoo...")
        df = yf.download(y_ticker, start=start_str, end=end_str, progress=False, auto_adjust=False)
        
        if df.empty:
            print(f"No data found for {ticker}")
            return []
        
        bars = []
        # yfinance returns MultiIndex columns if multiple tickers, but here we ask for one.
        # If the columns are tuples like ('Close', '600000.SS'), flatten or access properly.
        # Recent yf versions might just be simple columns if single ticker.
        
        # Reset index to get Date as column
        df = df.reset_index()
        
        for _, row in df.iterrows():
            # Handle possible MultiIndex columns issue by checking simple access or .iloc
            # With one ticker, it should be simple.
            
            # yfinance often returns numpy types, convert to python native
            try:
                # Basic normalization
                if isinstance(row['Date'], pd.Series):
                     d = row['Date'].iloc[0].to_pydatetime()
                else:
                     d = row['Date'].to_pydatetime()
                # Some yf versions return rows with NaN if no trading.
                # If 'Open' is a Series, check if all/any are NaN or just take the scalar.
                val_to_check = row['Open'].iloc[0] if isinstance(row['Open'], pd.Series) else row['Open']
                if pd.isna(val_to_check):
                    continue
                
                # Handling multi-level if necessary, usually with one ticker it's fine.
                # Just to be safe with yf versioning:
                op = float(row['Open'].iloc[0]) if isinstance(row['Open'], pd.Series) else float(row['Open'])
                hi = float(row['High'].iloc[0]) if isinstance(row['High'], pd.Series) else float(row['High'])
                lo = float(row['Low'].iloc[0]) if isinstance(row['Low'], pd.Series) else float(row['Low'])
                cl = float(row['Close'].iloc[0]) if isinstance(row['Close'], pd.Series) else float(row['Close'])
                ac = float(row['Adj Close'].iloc[0]) if isinstance(row['Adj Close'], pd.Series) else float(row['Adj Close'])
                vo = float(row['Volume'].iloc[0]) if isinstance(row['Volume'], pd.Series) else float(row['Volume'])
                
                bar = Bar(
                    _id=f"{ticker}:{d.strftime('%Y-%m-%d')}",
                    ticker=ticker,
                    exchange="SSE",
                    date=d,
                    open=op,
                    high=hi,
                    low=lo,
                    close=cl,
                    adj_close=ac,
                    volume=vo,
                    source="yahoo"
                )
                bars.append(bar)
            except Exception as e:
                print(f"Error parsing row: {e}")
                continue
                
        return bars

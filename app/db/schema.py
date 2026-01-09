from datetime import datetime
from typing import Optional, List, Literal
from pydantic import BaseModel, Field



class Instrument(BaseModel):
    ticker: str
    exchange: str = "SSE"
    name: Optional[str] = None
    is_active: bool = True
    source: str = "manual"
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class Bar(BaseModel):
    id: str = Field(alias="_id")
    ticker: str
    exchange: str = "SSE"
    date: datetime
    open: float
    high: float
    low: float
    close: float
    adj_close: Optional[float] = None
    volume: float
    source: str = "yahoo"
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    class Config:
        populate_by_name = True

class BarRequest(BaseModel):
    ticker: str
    start_date: datetime
    end_date: datetime
    fields: List[str] = ["open", "high", "low", "close", "volume"]
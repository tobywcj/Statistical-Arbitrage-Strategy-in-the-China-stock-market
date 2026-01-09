from abc import ABC, abstractmethod
from datetime import datetime
from typing import List
from app.db.schema import Instrument, Bar

class DataProvider(ABC):
    
    @abstractmethod
    def get_instruments(self) -> List[Instrument]:
        """Fetch list of available instruments."""
        pass
    
    @abstractmethod
    def fetch_bars(self, ticker: str, start: datetime, end: datetime) -> List[Bar]:
        """Fetch historical bars for a given ticker."""
        pass

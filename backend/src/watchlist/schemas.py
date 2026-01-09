from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


VALID_TIMEFRAMES = ["1m", "3m", "5m", "15m", "30m", "1h", "2h", "4h", "6h", "8h", "12h", "1d", "3d", "1w", "1M"]


class WatchlistItemCreate(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=20, pattern=r"^[A-Z0-9]+$")
    timeframes: List[str] = Field(default=["1h", "4h"])

    def validate_timeframes(self):
        for tf in self.timeframes:
            if tf not in VALID_TIMEFRAMES:
                raise ValueError(f"Invalid timeframe: {tf}")
        return self


class WatchlistItemUpdate(BaseModel):
    timeframes: Optional[List[str]] = None
    is_active: Optional[bool] = None


class WatchlistItemResponse(BaseModel):
    id: int
    symbol: str
    timeframes: List[str]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class WatchlistResponse(BaseModel):
    items: List[WatchlistItemResponse]
    total: int

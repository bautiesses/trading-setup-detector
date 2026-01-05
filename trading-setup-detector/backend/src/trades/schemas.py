from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class TradeCreate(BaseModel):
    symbol: str
    side: str  # long or short
    entry_price: float
    size: float
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    notes: Optional[str] = None
    image_url: Optional[str] = None
    timeframe: Optional[str] = None
    strategy: Optional[str] = None
    entry_date: Optional[datetime] = None


class TradeUpdate(BaseModel):
    symbol: Optional[str] = None
    side: Optional[str] = None
    status: Optional[str] = None
    entry_price: Optional[float] = None
    exit_price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    size: Optional[float] = None
    pnl: Optional[float] = None
    pnl_percent: Optional[float] = None
    fees: Optional[float] = None
    notes: Optional[str] = None
    image_url: Optional[str] = None
    exit_notes: Optional[str] = None
    exit_image_url: Optional[str] = None
    timeframe: Optional[str] = None
    strategy: Optional[str] = None
    exit_date: Optional[datetime] = None


class TradeClose(BaseModel):
    exit_price: float
    fees: Optional[float] = 0
    exit_notes: Optional[str] = None
    exit_image_url: Optional[str] = None


class TradeResponse(BaseModel):
    id: int
    symbol: str
    side: str
    status: str
    entry_price: float
    exit_price: Optional[float]
    stop_loss: Optional[float]
    take_profit: Optional[float]
    size: float
    pnl: Optional[float]
    pnl_percent: Optional[float]
    fees: float
    notes: Optional[str]
    image_url: Optional[str]
    exit_notes: Optional[str]
    exit_image_url: Optional[str]
    timeframe: Optional[str]
    strategy: Optional[str]
    entry_date: datetime
    exit_date: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class TradesListResponse(BaseModel):
    trades: List[TradeResponse]
    total: int


class TradeStatsResponse(BaseModel):
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    total_pnl: float
    average_pnl: float
    best_trade: float
    worst_trade: float

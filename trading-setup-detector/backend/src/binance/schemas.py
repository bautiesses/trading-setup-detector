from pydantic import BaseModel
from typing import List


class Kline(BaseModel):
    open_time: int
    open: float
    high: float
    low: float
    close: float
    volume: float
    close_time: int
    quote_volume: float
    trades: int


class SymbolInfo(BaseModel):
    symbol: str
    base_asset: str
    quote_asset: str
    status: str


class SymbolsResponse(BaseModel):
    symbols: List[SymbolInfo]
    total: int


class KlinesResponse(BaseModel):
    symbol: str
    interval: str
    klines: List[Kline]


class PriceResponse(BaseModel):
    symbol: str
    price: float

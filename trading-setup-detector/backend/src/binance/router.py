from fastapi import APIRouter, Depends, Query
from src.binance.client import get_binance_client, BinanceClient
from src.binance.schemas import SymbolsResponse, KlinesResponse, PriceResponse
from src.auth.dependencies import get_current_active_user

router = APIRouter(prefix="/binance", tags=["Binance"])


@router.get("/symbols", response_model=SymbolsResponse)
async def get_symbols(
    _: None = Depends(get_current_active_user),
    client: BinanceClient = Depends(get_binance_client)
):
    symbols = await client.get_all_usdt_symbols()
    return SymbolsResponse(symbols=symbols, total=len(symbols))


@router.get("/klines/{symbol}", response_model=KlinesResponse)
async def get_klines(
    symbol: str,
    interval: str = Query(default="1h", regex=r"^(1m|3m|5m|15m|30m|1h|2h|4h|6h|8h|12h|1d|3d|1w|1M)$"),
    limit: int = Query(default=200, ge=1, le=1000),
    _: None = Depends(get_current_active_user),
    client: BinanceClient = Depends(get_binance_client)
):
    klines = await client.get_klines(symbol.upper(), interval, limit)
    return KlinesResponse(symbol=symbol.upper(), interval=interval, klines=klines)


@router.get("/price/{symbol}", response_model=PriceResponse)
async def get_price(
    symbol: str,
    _: None = Depends(get_current_active_user),
    client: BinanceClient = Depends(get_binance_client)
):
    price = await client.get_symbol_price(symbol.upper())
    return PriceResponse(symbol=symbol.upper(), price=price)

import httpx
from typing import List, Optional
import pandas as pd
from src.binance.schemas import Kline, SymbolInfo

# Public Binance API - no authentication needed
BINANCE_BASE_URL = "https://api.binance.com/api/v3"


class BinanceClient:
    def __init__(self):
        self.client: Optional[httpx.AsyncClient] = None

    async def connect(self):
        self.client = httpx.AsyncClient(timeout=30.0)

    async def close(self):
        if self.client:
            await self.client.aclose()

    async def get_klines(
        self,
        symbol: str,
        interval: str,
        limit: int = 200
    ) -> List[Kline]:
        if not self.client:
            await self.connect()

        response = await self.client.get(
            f"{BINANCE_BASE_URL}/klines",
            params={
                "symbol": symbol,
                "interval": interval,
                "limit": limit
            }
        )
        response.raise_for_status()
        klines = response.json()
        return [self._parse_kline(k) for k in klines]

    async def get_klines_df(
        self,
        symbol: str,
        interval: str,
        limit: int = 200
    ) -> pd.DataFrame:
        klines = await self.get_klines(symbol, interval, limit)
        df = pd.DataFrame([k.model_dump() for k in klines])
        df['timestamp'] = pd.to_datetime(df['open_time'], unit='ms')
        df.set_index('timestamp', inplace=True)
        return df

    async def get_all_usdt_symbols(self) -> List[SymbolInfo]:
        if not self.client:
            await self.connect()

        response = await self.client.get(f"{BINANCE_BASE_URL}/exchangeInfo")
        response.raise_for_status()
        info = response.json()

        symbols = []
        for s in info['symbols']:
            if s['status'] == 'TRADING' and s['quoteAsset'] == 'USDT':
                symbols.append(SymbolInfo(
                    symbol=s['symbol'],
                    base_asset=s['baseAsset'],
                    quote_asset=s['quoteAsset'],
                    status=s['status']
                ))
        return symbols

    async def get_symbol_price(self, symbol: str) -> float:
        if not self.client:
            await self.connect()

        response = await self.client.get(
            f"{BINANCE_BASE_URL}/ticker/price",
            params={"symbol": symbol}
        )
        response.raise_for_status()
        ticker = response.json()
        return float(ticker['price'])

    def _parse_kline(self, raw: list) -> Kline:
        return Kline(
            open_time=raw[0],
            open=float(raw[1]),
            high=float(raw[2]),
            low=float(raw[3]),
            close=float(raw[4]),
            volume=float(raw[5]),
            close_time=raw[6],
            quote_volume=float(raw[7]),
            trades=raw[8]
        )


# Singleton instance
binance_client = BinanceClient()


async def get_binance_client() -> BinanceClient:
    if binance_client.client is None:
        await binance_client.connect()
    return binance_client

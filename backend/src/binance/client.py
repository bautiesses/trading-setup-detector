import httpx
from typing import List, Optional
import pandas as pd
from src.binance.schemas import Kline, SymbolInfo

# Public Binance API endpoints to try (some may be blocked by region)
BINANCE_ENDPOINTS = [
    "https://data-api.binance.vision/api/v3",  # Data API - less restricted
    "https://api.binance.com/api/v3",
    "https://api1.binance.com/api/v3",
    "https://api2.binance.com/api/v3",
    "https://api3.binance.com/api/v3",
]
BINANCE_BASE_URL = BINANCE_ENDPOINTS[0]


class BinanceClient:
    def __init__(self):
        self.client: Optional[httpx.AsyncClient] = None
        self.working_endpoint: str = BINANCE_BASE_URL

    async def connect(self):
        self.client = httpx.AsyncClient(timeout=30.0)

    async def close(self):
        if self.client:
            await self.client.aclose()

    async def _request_with_fallback(self, path: str, params: dict = None) -> dict:
        """Try multiple Binance endpoints until one works"""
        if not self.client:
            await self.connect()

        last_error = None
        endpoints_to_try = [self.working_endpoint] + [e for e in BINANCE_ENDPOINTS if e != self.working_endpoint]

        for endpoint in endpoints_to_try:
            try:
                response = await self.client.get(f"{endpoint}{path}", params=params)
                response.raise_for_status()
                self.working_endpoint = endpoint  # Remember working endpoint
                return response.json()
            except httpx.HTTPStatusError as e:
                last_error = e
                if e.response.status_code == 451:  # Region blocked, try next
                    continue
                raise  # Other errors, don't retry
            except Exception as e:
                last_error = e
                continue

        raise last_error or Exception("All Binance endpoints failed")

    async def get_klines(
        self,
        symbol: str,
        interval: str,
        limit: int = 200
    ) -> List[Kline]:
        klines = await self._request_with_fallback(
            "/klines",
            params={"symbol": symbol, "interval": interval, "limit": limit}
        )
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
        info = await self._request_with_fallback("/exchangeInfo")

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
        ticker = await self._request_with_fallback("/ticker/price", params={"symbol": symbol})
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

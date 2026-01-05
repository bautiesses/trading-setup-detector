"""
Cliente de Binance para obtener datos de mercado
100% gratis - solo usa endpoints públicos
"""

import pandas as pd
import aiohttp
import asyncio
from typing import List, Optional
from datetime import datetime


class BinanceClient:
    """Cliente asíncrono para la API pública de Binance"""
    
    BASE_URL = "https://api.binance.com/api/v3"
    
    TIMEFRAME_MAP = {
        "1m": "1m", "3m": "3m", "5m": "5m", "15m": "15m", "30m": "30m",
        "1h": "1h", "2h": "2h", "4h": "4h", "6h": "6h", "8h": "8h", "12h": "12h",
        "1d": "1d", "3d": "3d", "1w": "1w", "1M": "1M"
    }
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def close(self):
        if self.session and not self.session.closed:
            await self.session.close()
    
    async def get_klines(
        self,
        symbol: str,
        interval: str,
        limit: int = 500
    ) -> pd.DataFrame:
        """
        Obtiene datos de velas (klines) de Binance
        
        Args:
            symbol: Par de trading (ej: BTCUSDT)
            interval: Timeframe (ej: 1h, 4h, 1d)
            limit: Número de velas (máx 1000)
        
        Returns:
            DataFrame con columnas: open, high, low, close, volume
        """
        session = await self._get_session()
        
        params = {
            "symbol": symbol.upper(),
            "interval": self.TIMEFRAME_MAP.get(interval, interval),
            "limit": min(limit, 1000)
        }
        
        async with session.get(f"{self.BASE_URL}/klines", params=params) as response:
            if response.status != 200:
                raise Exception(f"Error fetching klines: {await response.text()}")
            
            data = await response.json()
        
        df = pd.DataFrame(data, columns=[
            'open_time', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_volume', 'trades', 'taker_buy_base',
            'taker_buy_quote', 'ignore'
        ])
        
        df['open_time'] = pd.to_datetime(df['open_time'], unit='ms')
        df.set_index('open_time', inplace=True)
        
        for col in ['open', 'high', 'low', 'close', 'volume']:
            df[col] = df[col].astype(float)
        
        return df[['open', 'high', 'low', 'close', 'volume']]
    
    async def get_all_symbols(self) -> List[str]:
        """Obtiene todos los símbolos USDT disponibles"""
        session = await self._get_session()
        
        async with session.get(f"{self.BASE_URL}/exchangeInfo") as response:
            if response.status != 200:
                raise Exception(f"Error fetching symbols: {await response.text()}")
            
            data = await response.json()
        
        symbols = [
            s['symbol'] for s in data['symbols']
            if s['symbol'].endswith('USDT') and s['status'] == 'TRADING'
        ]
        
        return sorted(symbols)
    
    async def get_price(self, symbol: str) -> float:
        """Obtiene el precio actual de un símbolo"""
        session = await self._get_session()
        
        params = {"symbol": symbol.upper()}
        
        async with session.get(f"{self.BASE_URL}/ticker/price", params=params) as response:
            if response.status != 200:
                raise Exception(f"Error fetching price: {await response.text()}")
            
            data = await response.json()
        
        return float(data['price'])


# Singleton
_client: Optional[BinanceClient] = None


def get_binance_client() -> BinanceClient:
    global _client
    if _client is None:
        _client = BinanceClient()
    return _client


async def close_client():
    global _client
    if _client:
        await _client.close()
        _client = None

import httpx
from typing import Optional
from datetime import datetime
from pathlib import Path
import pandas as pd
from src.config import get_settings

settings = get_settings()


class SolanaChartClient:
    """Client for fetching Solana token price data and generating charts.

    Uses FREE APIs only:
    - DexScreener (no API key needed)
    - Jupiter Price API (no API key needed)
    """

    DEXSCREENER_BASE = "https://api.dexscreener.com/latest"
    JUPITER_PRICE_API = "https://price.jup.ag/v6"

    def __init__(self):
        self.charts_dir = Path(settings.solana_charts_dir)
        self.charts_dir.mkdir(parents=True, exist_ok=True)

    async def get_token_price_history(
        self,
        token_address: str,
        timeframe: str = "15m",
        limit: int = 100
    ) -> Optional[pd.DataFrame]:
        """
        Fetch price data from DexScreener.
        Note: DexScreener doesn't provide full OHLCV history via API,
        so we return None and skip chart generation for now.
        """
        # DexScreener API doesn't expose OHLCV history publicly
        # Chart generation will be skipped but trades are still tracked
        return None

    async def _get_dexscreener_pairs(self, token_address: str) -> Optional[dict]:
        """Get token pairs info from DexScreener"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.DEXSCREENER_BASE}/dex/tokens/{token_address}",
                    timeout=30.0
                )

                if response.status_code == 200:
                    return response.json()
                return None

        except Exception as e:
            print(f"DexScreener request failed: {e}")
            return None

    async def generate_trade_chart(
        self,
        token_address: str,
        token_symbol: str,
        trade_time: datetime,
        trade_price: float,
        trade_side: str,
        timeframe: str = "15m"
    ) -> Optional[str]:
        """
        Generate a chart image with trade point marked.
        Currently disabled as free APIs don't provide OHLCV history.
        Charts can be viewed on DexScreener directly.
        """
        # Chart generation disabled - no free OHLCV API available
        # User can view charts on DexScreener: https://dexscreener.com/solana/{token_address}
        return None

    async def get_current_token_price(self, token_address: str) -> Optional[float]:
        """Get current USD price for a token using FREE APIs"""
        try:
            async with httpx.AsyncClient() as client:
                # Try Jupiter Price API first (FREE, official)
                response = await client.get(
                    f"{self.JUPITER_PRICE_API}/price",
                    params={"ids": token_address},
                    timeout=10.0
                )

                if response.status_code == 200:
                    data = response.json()
                    token_data = data.get("data", {}).get(token_address)
                    if token_data:
                        return float(token_data.get("price", 0))

                # Fallback to DexScreener (FREE, no API key)
                response = await client.get(
                    f"{self.DEXSCREENER_BASE}/dex/tokens/{token_address}",
                    timeout=10.0
                )

                if response.status_code == 200:
                    data = response.json()
                    pairs = data.get("pairs", [])
                    if pairs:
                        return float(pairs[0].get("priceUsd", 0))

                return None
        except Exception as e:
            print(f"Error getting token price: {e}")
            return None

    async def get_sol_price(self) -> Optional[float]:
        """Get current SOL price in USD"""
        sol_mint = "So11111111111111111111111111111111111111112"
        return await self.get_current_token_price(sol_mint)

    def get_dexscreener_chart_url(self, token_address: str) -> str:
        """Get DexScreener chart URL for a token"""
        return f"https://dexscreener.com/solana/{token_address}"


solana_chart_client = SolanaChartClient()

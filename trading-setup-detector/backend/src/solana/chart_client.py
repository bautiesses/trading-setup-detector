import httpx
from typing import Optional
from datetime import datetime
from pathlib import Path
import pandas as pd
from src.config import get_settings

settings = get_settings()


class SolanaChartClient:
    """Client for fetching Solana token price data and generating charts"""

    BIRDEYE_BASE = "https://public-api.birdeye.so"
    DEXSCREENER_BASE = "https://api.dexscreener.com/latest"

    def __init__(self):
        self.birdeye_api_key = settings.birdeye_api_key
        self.charts_dir = Path(settings.solana_charts_dir)
        self.charts_dir.mkdir(parents=True, exist_ok=True)

    async def get_token_price_history(
        self,
        token_address: str,
        timeframe: str = "15m",
        limit: int = 100
    ) -> Optional[pd.DataFrame]:
        """
        Fetch OHLCV data from Birdeye API.

        Args:
            token_address: Solana token mint address
            timeframe: Candle interval (1m, 5m, 15m, 1h, 4h, 1d)
            limit: Number of candles to fetch

        Returns:
            DataFrame with OHLCV data or None
        """
        try:
            async with httpx.AsyncClient() as client:
                # Map timeframe to Birdeye format
                tf_map = {
                    "1m": "1m", "5m": "5m", "15m": "15m", "30m": "30m",
                    "1h": "1H", "4h": "4H", "1d": "1D"
                }
                birdeye_tf = tf_map.get(timeframe, "15m")

                response = await client.get(
                    f"{self.BIRDEYE_BASE}/defi/ohlcv",
                    params={
                        "address": token_address,
                        "type": birdeye_tf,
                        "limit": limit
                    },
                    headers={
                        "X-API-KEY": self.birdeye_api_key,
                        "x-chain": "solana"
                    },
                    timeout=30.0
                )

                if response.status_code != 200:
                    return await self._get_dexscreener_data(token_address)

                data = response.json()
                items = data.get("data", {}).get("items", [])

                if not items:
                    return None

                df = pd.DataFrame(items)
                df["timestamp"] = pd.to_datetime(df["unixTime"], unit="s")
                df = df.rename(columns={
                    "o": "Open", "h": "High", "l": "Low", "c": "Close", "v": "Volume"
                })
                df.set_index("timestamp", inplace=True)

                return df[["Open", "High", "Low", "Close", "Volume"]]

        except Exception as e:
            print(f"Error fetching price history: {e}")
            return None

    async def _get_dexscreener_data(self, token_address: str) -> Optional[pd.DataFrame]:
        """Fallback to DexScreener (free, no API key needed)"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.DEXSCREENER_BASE}/dex/tokens/{token_address}",
                    timeout=30.0
                )

                if response.status_code != 200:
                    return None

                # DexScreener doesn't provide full OHLCV history
                # But we can get current price info
                return None

        except Exception as e:
            print(f"DexScreener fallback failed: {e}")
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

        Args:
            token_address: Token mint address
            token_symbol: Token symbol for title
            trade_time: Time of the trade
            trade_price: Price at trade time
            trade_side: "buy" or "sell"
            timeframe: Chart timeframe

        Returns:
            Path to saved image or None
        """
        df = await self.get_token_price_history(token_address, timeframe, limit=50)

        if df is None or df.empty:
            return None

        try:
            import mplfinance as mpf

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{token_symbol}_{timeframe}_{timestamp}.png"
            filepath = self.charts_dir / filename

            # Chart colors
            marker_color = "#26a69a" if trade_side == "buy" else "#ef5350"

            # Custom style
            style = mpf.make_mpf_style(
                base_mpf_style='charles',
                marketcolors=mpf.make_marketcolors(
                    up='#26a69a', down='#ef5350',
                    edge='inherit', wick='inherit', volume='in'
                ),
                gridstyle='-', gridcolor='#333333',
                facecolor='#1a1a2e', figcolor='#1a1a2e',
                rc={'axes.labelcolor': 'white', 'xtick.color': 'white',
                    'ytick.color': 'white', 'axes.edgecolor': '#333333'}
            )

            # Add horizontal line at trade price
            hlines = dict(hlines=[trade_price], colors=[marker_color], linestyle='--', linewidths=1.5)

            # Create title
            side_label = "BUY" if trade_side == "buy" else "SELL"
            title = f'{token_symbol}/USD - {timeframe} | {side_label} @ ${trade_price:.6f}'

            # Plot
            mpf.plot(
                df,
                type='candle',
                style=style,
                volume=True,
                title=title,
                hlines=hlines,
                figsize=(12, 8),
                savefig=dict(fname=str(filepath), dpi=100, bbox_inches='tight',
                           facecolor='#1a1a2e', edgecolor='none')
            )

            return str(filepath)

        except ImportError:
            print("mplfinance not installed, skipping chart generation")
            return None
        except Exception as e:
            print(f"Error generating chart: {e}")
            return None

    async def get_current_token_price(self, token_address: str) -> Optional[float]:
        """Get current USD price for a token"""
        try:
            async with httpx.AsyncClient() as client:
                # Try Birdeye first
                if self.birdeye_api_key:
                    response = await client.get(
                        f"{self.BIRDEYE_BASE}/defi/price",
                        params={"address": token_address},
                        headers={
                            "X-API-KEY": self.birdeye_api_key,
                            "x-chain": "solana"
                        },
                        timeout=10.0
                    )

                    if response.status_code == 200:
                        data = response.json()
                        return data.get("data", {}).get("value")

                # Fallback to DexScreener
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


solana_chart_client = SolanaChartClient()

import mplfinance as mpf
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Optional
from src.config import get_settings

settings = get_settings()


class ChartGenerator:
    def __init__(self, output_dir: Optional[str] = None):
        self.output_dir = Path(output_dir or settings.charts_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Custom style for charts
        self.style = mpf.make_mpf_style(
            base_mpf_style='charles',
            marketcolors=mpf.make_marketcolors(
                up='#26a69a',
                down='#ef5350',
                edge='inherit',
                wick='inherit',
                volume='in'
            ),
            gridstyle='-',
            gridcolor='#e0e0e0',
            facecolor='white',
            figcolor='white'
        )

    async def generate(
        self,
        symbol: str,
        timeframe: str,
        data: pd.DataFrame,
        show_volume: bool = True,
        figsize: tuple = (12, 8)
    ) -> str:
        # Prepare filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{symbol}_{timeframe}_{timestamp}.png"
        filepath = self.output_dir / filename

        # Ensure data has proper column names for mplfinance
        df = data.copy()
        if 'Open' not in df.columns:
            df = df.rename(columns={
                'open': 'Open',
                'high': 'High',
                'low': 'Low',
                'close': 'Close',
                'volume': 'Volume'
            })

        # Generate chart
        mpf.plot(
            df,
            type='candle',
            style=self.style,
            volume=show_volume,
            title=f'{symbol} - {timeframe}',
            figsize=figsize,
            savefig=dict(fname=str(filepath), dpi=100, bbox_inches='tight')
        )

        return str(filepath)

    async def generate_from_klines(
        self,
        symbol: str,
        timeframe: str,
        klines: list,
        show_volume: bool = True
    ) -> str:
        # Convert klines to DataFrame
        df = pd.DataFrame([{
            'timestamp': k.open_time,
            'Open': k.open,
            'High': k.high,
            'Low': k.low,
            'Close': k.close,
            'Volume': k.volume
        } for k in klines])

        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)

        return await self.generate(symbol, timeframe, df, show_volume)


# Singleton instance
chart_generator: Optional[ChartGenerator] = None


def get_chart_generator() -> ChartGenerator:
    global chart_generator
    if chart_generator is None:
        chart_generator = ChartGenerator()
    return chart_generator

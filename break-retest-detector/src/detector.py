"""
Break & Retest Pattern Detector
Detecta patrones de ruptura y retesteo en criptomonedas.
100% gratis - usa solo datos de Binance
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from datetime import datetime


class PatternType(Enum):
    BULLISH_RETEST = "bullish_retest"  # Rompe resistencia, retestea como soporte
    BEARISH_RETEST = "bearish_retest"  # Rompe soporte, retestea como resistencia


@dataclass
class Level:
    """Representa un nivel de soporte/resistencia"""
    price: float
    strength: int  # Número de toques
    first_touch: datetime
    last_touch: datetime
    is_broken: bool = False
    break_direction: Optional[str] = None  # 'up' or 'down'
    break_time: Optional[datetime] = None


@dataclass
class Signal:
    """Señal de trading detectada"""
    symbol: str
    timeframe: str
    pattern_type: PatternType
    level_price: float
    current_price: float
    distance_to_level_pct: float
    timestamp: datetime
    strength: int
    message: str


class BreakRetestDetector:
    """
    Detector de patrones Break & Retest
    
    Lógica:
    1. Identifica niveles de soporte/resistencia usando pivots
    2. Detecta cuando el precio rompe un nivel
    3. Monitorea si el precio vuelve a testear el nivel
    4. Genera señal cuando hay un retest válido
    """
    
    def __init__(
        self,
        pivot_lookback: int = 10,
        level_tolerance_pct: float = 0.3,
        min_touches: int = 2,
        retest_tolerance_pct: float = 0.5,
        min_breakout_pct: float = 0.5,
        max_retest_candles: int = 50
    ):
        """
        Args:
            pivot_lookback: Velas a cada lado para identificar pivots
            level_tolerance_pct: % de tolerancia para agrupar niveles similares
            min_touches: Mínimo de toques para considerar un nivel válido
            retest_tolerance_pct: % de distancia al nivel para considerar retest
            min_breakout_pct: % mínimo de movimiento para confirmar breakout
            max_retest_candles: Máximo de velas después del breakout para esperar retest
        """
        self.pivot_lookback = pivot_lookback
        self.level_tolerance_pct = level_tolerance_pct
        self.min_touches = min_touches
        self.retest_tolerance_pct = retest_tolerance_pct
        self.min_breakout_pct = min_breakout_pct
        self.max_retest_candles = max_retest_candles
    
    def find_pivot_highs(self, df: pd.DataFrame) -> pd.Series:
        """Encuentra pivot highs (máximos locales)"""
        highs = df['high'].values
        pivot_highs = pd.Series(index=df.index, dtype=float)
        
        for i in range(self.pivot_lookback, len(highs) - self.pivot_lookback):
            is_pivot = True
            for j in range(1, self.pivot_lookback + 1):
                if highs[i] <= highs[i - j] or highs[i] <= highs[i + j]:
                    is_pivot = False
                    break
            if is_pivot:
                pivot_highs.iloc[i] = highs[i]
        
        return pivot_highs
    
    def find_pivot_lows(self, df: pd.DataFrame) -> pd.Series:
        """Encuentra pivot lows (mínimos locales)"""
        lows = df['low'].values
        pivot_lows = pd.Series(index=df.index, dtype=float)
        
        for i in range(self.pivot_lookback, len(lows) - self.pivot_lookback):
            is_pivot = True
            for j in range(1, self.pivot_lookback + 1):
                if lows[i] >= lows[i - j] or lows[i] >= lows[i + j]:
                    is_pivot = False
                    break
            if is_pivot:
                pivot_lows.iloc[i] = lows[i]
        
        return pivot_lows
    
    def cluster_levels(self, prices: List[float], timestamps: List[datetime]) -> List[Level]:
        """Agrupa precios similares en niveles"""
        if not prices:
            return []
        
        levels = []
        used = [False] * len(prices)
        
        for i, price in enumerate(prices):
            if used[i]:
                continue
            
            # Encuentra precios similares
            cluster_prices = [price]
            cluster_times = [timestamps[i]]
            used[i] = True
            
            for j in range(i + 1, len(prices)):
                if used[j]:
                    continue
                
                diff_pct = abs(prices[j] - price) / price * 100
                if diff_pct <= self.level_tolerance_pct:
                    cluster_prices.append(prices[j])
                    cluster_times.append(timestamps[j])
                    used[j] = True
            
            # Crear nivel si tiene suficientes toques
            if len(cluster_prices) >= self.min_touches:
                avg_price = np.mean(cluster_prices)
                levels.append(Level(
                    price=avg_price,
                    strength=len(cluster_prices),
                    first_touch=min(cluster_times),
                    last_touch=max(cluster_times)
                ))
        
        return sorted(levels, key=lambda x: x.price)
    
    def identify_levels(self, df: pd.DataFrame) -> Tuple[List[Level], List[Level]]:
        """
        Identifica niveles de soporte y resistencia
        Returns: (resistances, supports)
        """
        pivot_highs = self.find_pivot_highs(df)
        pivot_lows = self.find_pivot_lows(df)
        
        # Extraer precios y timestamps de pivots
        high_prices = pivot_highs.dropna().values.tolist()
        high_times = pivot_highs.dropna().index.tolist()
        
        low_prices = pivot_lows.dropna().values.tolist()
        low_times = pivot_lows.dropna().index.tolist()
        
        # Agrupar en niveles
        resistances = self.cluster_levels(high_prices, high_times)
        supports = self.cluster_levels(low_prices, low_times)
        
        return resistances, supports
    
    def check_breakout(
        self, 
        df: pd.DataFrame, 
        level: Level, 
        is_resistance: bool
    ) -> Optional[int]:
        """
        Verifica si hubo un breakout del nivel
        Returns: índice de la vela del breakout, o None
        """
        current_price = df['close'].iloc[-1]
        
        for i in range(len(df) - 1, max(0, len(df) - self.max_retest_candles), -1):
            candle = df.iloc[i]
            prev_candles = df.iloc[max(0, i-5):i]
            
            if is_resistance:
                # Breakout alcista: precio cruza arriba de resistencia
                if candle['close'] > level.price * (1 + self.min_breakout_pct / 100):
                    # Verificar que antes estaba debajo
                    if len(prev_candles) > 0 and prev_candles['close'].mean() < level.price:
                        return i
            else:
                # Breakout bajista: precio cruza debajo de soporte
                if candle['close'] < level.price * (1 - self.min_breakout_pct / 100):
                    # Verificar que antes estaba arriba
                    if len(prev_candles) > 0 and prev_candles['close'].mean() > level.price:
                        return i
        
        return None
    
    def check_retest(
        self,
        df: pd.DataFrame,
        level: Level,
        breakout_idx: int,
        is_bullish: bool
    ) -> bool:
        """
        Verifica si el precio está haciendo un retest del nivel
        """
        if breakout_idx >= len(df) - 1:
            return False
        
        current_price = df['close'].iloc[-1]
        current_low = df['low'].iloc[-1]
        current_high = df['high'].iloc[-1]
        
        distance_pct = abs(current_price - level.price) / level.price * 100
        
        if is_bullish:
            # Retest alcista: precio baja a tocar el nivel (ahora soporte)
            # El precio debe estar cerca del nivel y venir desde arriba
            touching_level = (
                current_low <= level.price * (1 + self.retest_tolerance_pct / 100) and
                current_price >= level.price * (1 - self.retest_tolerance_pct / 100)
            )
            # Verificar que después del breakout el precio subió
            post_breakout = df.iloc[breakout_idx:]
            went_higher = post_breakout['high'].max() > level.price * (1 + self.min_breakout_pct / 100)
            
            return touching_level and went_higher
        else:
            # Retest bajista: precio sube a tocar el nivel (ahora resistencia)
            touching_level = (
                current_high >= level.price * (1 - self.retest_tolerance_pct / 100) and
                current_price <= level.price * (1 + self.retest_tolerance_pct / 100)
            )
            # Verificar que después del breakout el precio bajó
            post_breakout = df.iloc[breakout_idx:]
            went_lower = post_breakout['low'].min() < level.price * (1 - self.min_breakout_pct / 100)
            
            return touching_level and went_lower
    
    def detect(self, df: pd.DataFrame, symbol: str, timeframe: str) -> List[Signal]:
        """
        Detecta patrones de Break & Retest
        
        Args:
            df: DataFrame con columnas OHLCV (open, high, low, close, volume)
            symbol: Símbolo del par (ej: BTCUSDT)
            timeframe: Timeframe (ej: 1h, 4h)
        
        Returns:
            Lista de señales detectadas
        """
        signals = []
        
        if len(df) < self.pivot_lookback * 2 + self.max_retest_candles:
            return signals
        
        # Identificar niveles
        resistances, supports = self.identify_levels(df)
        
        current_price = df['close'].iloc[-1]
        current_time = df.index[-1]
        
        # Buscar retests alcistas (breakout de resistencia)
        for resistance in resistances:
            breakout_idx = self.check_breakout(df, resistance, is_resistance=True)
            if breakout_idx is not None:
                if self.check_retest(df, resistance, breakout_idx, is_bullish=True):
                    distance_pct = (current_price - resistance.price) / resistance.price * 100
                    signals.append(Signal(
                        symbol=symbol,
                        timeframe=timeframe,
                        pattern_type=PatternType.BULLISH_RETEST,
                        level_price=resistance.price,
                        current_price=current_price,
                        distance_to_level_pct=distance_pct,
                        timestamp=current_time,
                        strength=resistance.strength,
                        message=f"🟢 BULLISH RETEST en {symbol} ({timeframe})\n"
                               f"Nivel: {resistance.price:.4f}\n"
                               f"Precio actual: {current_price:.4f}\n"
                               f"Fuerza del nivel: {resistance.strength} toques\n"
                               f"Acción: COMPRA en retest de resistencia rota"
                    ))
        
        # Buscar retests bajistas (breakout de soporte)
        for support in supports:
            breakout_idx = self.check_breakout(df, support, is_resistance=False)
            if breakout_idx is not None:
                if self.check_retest(df, support, breakout_idx, is_bullish=False):
                    distance_pct = (current_price - support.price) / support.price * 100
                    signals.append(Signal(
                        symbol=symbol,
                        timeframe=timeframe,
                        pattern_type=PatternType.BEARISH_RETEST,
                        level_price=support.price,
                        current_price=current_price,
                        distance_to_level_pct=distance_pct,
                        timestamp=current_time,
                        strength=support.strength,
                        message=f"🔴 BEARISH RETEST en {symbol} ({timeframe})\n"
                               f"Nivel: {support.price:.4f}\n"
                               f"Precio actual: {current_price:.4f}\n"
                               f"Fuerza del nivel: {support.strength} toques\n"
                               f"Acción: VENTA en retest de soporte roto"
                    ))
        
        return signals


def create_detector(
    sensitivity: str = "medium"
) -> BreakRetestDetector:
    """
    Crea un detector con configuración predefinida
    
    Args:
        sensitivity: "low", "medium", "high"
            - low: menos señales, más confiables
            - medium: balance
            - high: más señales, pueden incluir falsas
    """
    configs = {
        "low": {
            "pivot_lookback": 15,
            "level_tolerance_pct": 0.2,
            "min_touches": 3,
            "retest_tolerance_pct": 0.3,
            "min_breakout_pct": 0.8,
            "max_retest_candles": 30
        },
        "medium": {
            "pivot_lookback": 10,
            "level_tolerance_pct": 0.3,
            "min_touches": 2,
            "retest_tolerance_pct": 0.5,
            "min_breakout_pct": 0.5,
            "max_retest_candles": 50
        },
        "high": {
            "pivot_lookback": 5,
            "level_tolerance_pct": 0.5,
            "min_touches": 2,
            "retest_tolerance_pct": 0.8,
            "min_breakout_pct": 0.3,
            "max_retest_candles": 80
        }
    }
    
    config = configs.get(sensitivity, configs["medium"])
    return BreakRetestDetector(**config)

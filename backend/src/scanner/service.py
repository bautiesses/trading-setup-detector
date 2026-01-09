"""
Scanner Service - Break & Retest Pattern Detection
100% gratis - no usa APIs de pago
"""

from typing import List, Optional
from datetime import datetime, date, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
import pandas as pd

from src.scanner.models import ScanResult, ScannerConfig, ScanExecution
from src.scanner.break_retest import BreakRetestDetector, create_detector, PatternType
from src.watchlist.models import WatchlistItem
from src.binance.client import get_binance_client


class ScannerService:
    # Hours to consider a signal as duplicate
    DUPLICATE_WINDOW_HOURS = 24
    # Price tolerance for duplicate detection (0.5% = same level)
    PRICE_TOLERANCE = 0.005

    def __init__(self, db: AsyncSession):
        self.db = db
        self.detector = create_detector("medium")

    async def _signal_exists(
        self,
        user_id: int,
        symbol: str,
        timeframe: str,
        pattern_type: str,
        level_price: float
    ) -> bool:
        """Check if a similar signal already exists within the duplicate window"""
        cutoff = datetime.now() - timedelta(hours=self.DUPLICATE_WINDOW_HOURS)

        # Price range for duplicate detection
        price_low = level_price * (1 - self.PRICE_TOLERANCE)
        price_high = level_price * (1 + self.PRICE_TOLERANCE)

        query = select(func.count()).select_from(ScanResult).where(
            and_(
                ScanResult.user_id == user_id,
                ScanResult.symbol == symbol,
                ScanResult.timeframe == timeframe,
                ScanResult.pattern_type == pattern_type,
                ScanResult.level_price >= price_low,
                ScanResult.level_price <= price_high,
                ScanResult.created_at >= cutoff
            )
        )

        result = await self.db.execute(query)
        count = result.scalar()
        return count > 0

    async def run_scan(
        self,
        user_id: int,
        symbols: Optional[List[str]] = None,
        timeframes: Optional[List[str]] = None,
        sensitivity: str = "medium"
    ) -> List[ScanResult]:
        """
        Ejecuta el scanner de Break & Retest
        """
        results = []
        
        # Crear detector con la sensibilidad especificada
        self.detector = create_detector(sensitivity)

        # Obtener watchlist
        watchlist_query = select(WatchlistItem).where(
            WatchlistItem.user_id == user_id,
            WatchlistItem.is_active == True
        )
        if symbols:
            watchlist_query = watchlist_query.where(
                WatchlistItem.symbol.in_([s.upper() for s in symbols])
            )
        watchlist_result = await self.db.execute(watchlist_query)
        watchlist = list(watchlist_result.scalars().all())

        if not watchlist:
            return results

        # Obtener cliente de Binance
        binance = await get_binance_client()

        # Escanear cada símbolo/timeframe
        for item in watchlist:
            tfs = timeframes if timeframes else item.timeframes

            for tf in tfs:
                try:
                    print(f"Scanning {item.symbol} {tf}...")
                    
                    # Obtener datos de Binance como DataFrame
                    df = await binance.get_klines_df(item.symbol, tf, limit=500)
                    
                    # Asegurar que tenemos las columnas necesarias
                    df = df[['open', 'high', 'low', 'close', 'volume']]
                    
                    print(f"  Got {len(df)} candles for {item.symbol} {tf}")

                    # Detectar patrones
                    signals = self.detector.detect(df, item.symbol, tf)
                    
                    print(f"  Found {len(signals)} signals for {item.symbol} {tf}")

                    # Guardar resultados (solo si no son duplicados)
                    for signal in signals:
                        # Check if similar signal already exists
                        is_duplicate = await self._signal_exists(
                            user_id=user_id,
                            symbol=signal.symbol,
                            timeframe=signal.timeframe,
                            pattern_type=signal.pattern_type.value,
                            level_price=signal.level_price
                        )

                        if is_duplicate:
                            print(f"  Skipping duplicate signal: {signal.symbol} {signal.timeframe} {signal.pattern_type.value}")
                            continue

                        result = ScanResult(
                            user_id=user_id,
                            symbol=signal.symbol,
                            timeframe=signal.timeframe,
                            pattern_type=signal.pattern_type.value,
                            level_price=signal.level_price,
                            current_price=signal.current_price,
                            confidence_score=signal.strength / 10.0,  # Normalizar fuerza
                            is_match=True,
                            message=signal.message
                        )
                        self.db.add(result)
                        results.append(result)

                except Exception as e:
                    print(f"Error scanning {item.symbol} {tf}: {e}")
                    continue

        # Registrar la ejecución del scan
        execution = ScanExecution(
            user_id=user_id,
            symbols_scanned=len(watchlist),
            signals_found=len(results),
            sensitivity=sensitivity
        )
        self.db.add(execution)

        await self.db.commit()

        # Refrescar resultados
        for result in results:
            await self.db.refresh(result)

        return results

    async def get_results(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 50,
        pattern_type: Optional[str] = None
    ) -> tuple[List[ScanResult], int]:
        """Obtiene resultados de scans anteriores"""
        query = select(ScanResult).where(ScanResult.user_id == user_id)
        
        if pattern_type:
            query = query.where(ScanResult.pattern_type == pattern_type)

        query = query.order_by(ScanResult.created_at.desc()).offset(skip).limit(limit)
        result = await self.db.execute(query)
        results = list(result.scalars().all())

        # Contar total
        count_query = select(func.count()).select_from(ScanResult).where(
            ScanResult.user_id == user_id
        )
        if pattern_type:
            count_query = count_query.where(ScanResult.pattern_type == pattern_type)
        
        count_result = await self.db.execute(count_query)
        total = count_result.scalar()

        return results, total

    async def get_status(self, user_id: int) -> dict:
        """Obtiene el estado del scanner"""
        # Contar símbolos monitoreados
        symbols_result = await self.db.execute(
            select(func.count()).select_from(WatchlistItem).where(
                WatchlistItem.user_id == user_id,
                WatchlistItem.is_active == True
            )
        )
        symbols_count = symbols_result.scalar()

        # Contar scans de hoy (ejecuciones)
        today = date.today()
        scans_result = await self.db.execute(
            select(func.count()).select_from(ScanExecution).where(
                ScanExecution.user_id == user_id,
                func.date(ScanExecution.created_at) == today
            )
        )
        scans_today = scans_result.scalar() or 0

        # Contar señales de hoy
        signals_result = await self.db.execute(
            select(func.count()).select_from(ScanResult).where(
                ScanResult.user_id == user_id,
                func.date(ScanResult.created_at) == today
            )
        )
        signals_today = signals_result.scalar() or 0

        # Último scan
        last_scan_result = await self.db.execute(
            select(ScanExecution.created_at)
            .where(ScanExecution.user_id == user_id)
            .order_by(ScanExecution.created_at.desc())
            .limit(1)
        )
        last_scan = last_scan_result.scalar()

        return {
            "symbols_monitored": symbols_count,
            "scans_today": scans_today,
            "signals_today": signals_today,
            "last_scan": last_scan.isoformat() if last_scan else None,
            "is_running": False,  # Por ahora solo manual
            "scan_interval_minutes": 5
        }

    async def clear_old_results(self, user_id: int, days: int = 7):
        """Limpia resultados antiguos. Si days=0, borra TODOS los resultados."""
        if days == 0:
            # Clear ALL results
            await self.db.execute(
                ScanResult.__table__.delete().where(
                    ScanResult.user_id == user_id
                )
            )
        else:
            cutoff = datetime.now() - timedelta(days=days)
            await self.db.execute(
                ScanResult.__table__.delete().where(
                    ScanResult.user_id == user_id,
                    ScanResult.created_at < cutoff
                )
            )
        await self.db.commit()

    async def clear_duplicate_signals(self, user_id: int) -> int:
        """Remove duplicate signals keeping only the oldest one for each unique signal"""
        # Get all signals grouped by unique key
        query = select(ScanResult).where(
            ScanResult.user_id == user_id
        ).order_by(ScanResult.created_at.asc())

        result = await self.db.execute(query)
        all_signals = list(result.scalars().all())

        # Track unique signals by (symbol, timeframe, pattern_type, rounded_level)
        seen = {}
        duplicates_to_delete = []

        for signal in all_signals:
            # Round level_price to avoid floating point issues
            rounded_level = round(signal.level_price, 2)
            key = (signal.symbol, signal.timeframe, signal.pattern_type, rounded_level)

            if key in seen:
                # This is a duplicate, mark for deletion
                duplicates_to_delete.append(signal.id)
            else:
                seen[key] = signal.id

        # Delete duplicates
        if duplicates_to_delete:
            from sqlalchemy import delete
            await self.db.execute(
                delete(ScanResult).where(ScanResult.id.in_(duplicates_to_delete))
            )
            await self.db.commit()

        return len(duplicates_to_delete)

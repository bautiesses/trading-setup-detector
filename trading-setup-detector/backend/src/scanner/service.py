"""
Scanner Service - Break & Retest Pattern Detection
100% gratis - no usa APIs de pago
"""

from typing import List, Optional
from datetime import datetime, date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
import pandas as pd

from src.scanner.models import ScanResult, ScannerConfig, ScanExecution
from src.scanner.break_retest import BreakRetestDetector, create_detector, PatternType
from src.watchlist.models import WatchlistItem
from src.binance.client import get_binance_client


class ScannerService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.detector = create_detector("medium")

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

                    # Guardar resultados
                    for signal in signals:
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
        """Limpia resultados antiguos"""
        from datetime import timedelta
        cutoff = datetime.now() - timedelta(days=days)
        
        await self.db.execute(
            ScanResult.__table__.delete().where(
                ScanResult.user_id == user_id,
                ScanResult.created_at < cutoff
            )
        )
        await self.db.commit()

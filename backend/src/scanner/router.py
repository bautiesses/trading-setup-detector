from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime

from src.database import get_db
from src.auth.dependencies import get_current_active_user
from src.auth.models import User
from src.scanner.service import ScannerService
from src.scanner.scheduler import scanner_scheduler

router = APIRouter(prefix="/scanner", tags=["Scanner"])


class ScanResultResponse(BaseModel):
    id: int
    symbol: str
    timeframe: str
    pattern_type: str
    level_price: float
    current_price: float
    confidence_score: float
    is_match: bool
    message: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class ScanResultsListResponse(BaseModel):
    results: List[ScanResultResponse]
    total: int


class ScannerStatusResponse(BaseModel):
    symbols_monitored: int
    scans_today: int
    signals_today: int
    last_scan: Optional[str]
    is_running: bool
    scan_interval_minutes: int


class ManualScanRequest(BaseModel):
    symbols: Optional[List[str]] = None
    timeframes: Optional[List[str]] = None
    sensitivity: str = "medium"


class ManualScanResponse(BaseModel):
    success: bool
    signals_found: int
    results: List[ScanResultResponse]


@router.get("/status", response_model=ScannerStatusResponse)
async def get_scanner_status(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Obtiene el estado actual del scanner"""
    service = ScannerService(db)
    return await service.get_status(current_user.id)


@router.post("/scan", response_model=ManualScanResponse)
async def run_manual_scan(
    request: ManualScanRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Ejecuta un scan manual de Break & Retest
    
    - **symbols**: Lista de símbolos a escanear (opcional, usa watchlist si no se especifica)
    - **timeframes**: Lista de timeframes (opcional, usa los de la watchlist)
    - **sensitivity**: low, medium, high
    """
    service = ScannerService(db)
    results = await service.run_scan(
        user_id=current_user.id,
        symbols=request.symbols,
        timeframes=request.timeframes,
        sensitivity=request.sensitivity
    )
    
    return ManualScanResponse(
        success=True,
        signals_found=len(results),
        results=[ScanResultResponse.model_validate(r) for r in results]
    )


@router.get("/results", response_model=ScanResultsListResponse)
async def get_scan_results(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    pattern_type: Optional[str] = Query(default=None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Obtiene los resultados de scans anteriores
    
    - **pattern_type**: Filtrar por tipo (bullish_retest, bearish_retest)
    """
    service = ScannerService(db)
    results, total = await service.get_results(
        user_id=current_user.id,
        skip=skip,
        limit=limit,
        pattern_type=pattern_type
    )
    
    return ScanResultsListResponse(
        results=[ScanResultResponse.model_validate(r) for r in results],
        total=total
    )


@router.delete("/results")
async def clear_old_results(
    days: int = Query(default=7, ge=0, le=30),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Limpia resultados antiguos. Si days=0, borra TODOS los resultados."""
    service = ScannerService(db)
    await service.clear_old_results(current_user.id, days)
    if days == 0:
        return {"success": True, "message": "Todos los resultados eliminados"}
    return {"success": True, "message": f"Resultados mayores a {days} días eliminados"}


@router.delete("/duplicates")
async def clear_duplicate_signals(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Elimina señales duplicadas, manteniendo solo la más antigua de cada tipo"""
    service = ScannerService(db)
    deleted_count = await service.clear_duplicate_signals(current_user.id)
    return {"success": True, "deleted": deleted_count, "message": f"{deleted_count} señales duplicadas eliminadas"}


# ============ Auto Scanner Endpoints ============

class AutoScannerRequest(BaseModel):
    interval_minutes: int = 5


class AutoScannerStatusResponse(BaseModel):
    is_running: bool
    interval_minutes: int
    last_scan: Optional[str]


class NewSignalsResponse(BaseModel):
    signals: List[dict]
    count: int


@router.post("/auto/start")
async def start_auto_scanner(
    request: AutoScannerRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    Inicia el scanner automático

    - **interval_minutes**: Intervalo entre scans (mínimo 1, default 5)
    """
    interval = max(1, min(60, request.interval_minutes))  # Clamp between 1-60
    scanner_scheduler.start(interval_minutes=interval)
    return {
        "success": True,
        "message": f"Scanner automático iniciado cada {interval} minutos"
    }


@router.post("/auto/stop")
async def stop_auto_scanner(
    current_user: User = Depends(get_current_active_user)
):
    """Detiene el scanner automático"""
    scanner_scheduler.stop()
    return {
        "success": True,
        "message": "Scanner automático detenido"
    }


@router.get("/auto/status", response_model=AutoScannerStatusResponse)
async def get_auto_scanner_status(
    current_user: User = Depends(get_current_active_user)
):
    """Obtiene el estado del scanner automático"""
    return scanner_scheduler.get_status()


@router.get("/auto/new-signals", response_model=NewSignalsResponse)
async def get_new_signals(
    current_user: User = Depends(get_current_active_user)
):
    """
    Obtiene las nuevas señales detectadas desde la última consulta.
    Las señales se eliminan después de ser consultadas.
    """
    signals = await scanner_scheduler.get_new_signals(current_user.id)
    return NewSignalsResponse(signals=signals, count=len(signals))

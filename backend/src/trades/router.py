from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import os

from src.database import get_db
from src.auth.dependencies import get_current_active_user
from src.auth.models import User
from src.trades.service import TradeService
from src.trades.schemas import (
    TradeCreate,
    TradeUpdate,
    TradeClose,
    TradeReview,
    TradeResponse,
    TradesListResponse,
    TradeStatsResponse,
    AnalyzeMonthRequest,
    AnalyzeMonthResponse,
    MonthlyAnalysisCreate,
    MonthlyAnalysisResponse,
    MonthlyAnalysisListResponse,
)
from src.trades.ai_analyzer import AITradeAnalyzer, TradeForAnalysis

router = APIRouter(prefix="/trades", tags=["Trades"])


@router.post("/", response_model=TradeResponse)
async def create_trade(
    data: TradeCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new trade"""
    service = TradeService(db)
    trade = await service.create_trade(current_user.id, data)
    return trade


@router.get("/", response_model=TradesListResponse)
async def get_trades(
    status: Optional[str] = Query(default=None, description="Filter by status: open, closed, cancelled"),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all trades"""
    service = TradeService(db)
    trades, total = await service.get_trades(current_user.id, status, skip, limit)
    return TradesListResponse(
        trades=[TradeResponse.model_validate(t) for t in trades],
        total=total
    )


@router.get("/stats", response_model=TradeStatsResponse)
async def get_trade_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get trading statistics"""
    service = TradeService(db)
    stats = await service.get_stats(current_user.id)
    return stats


@router.get("/{trade_id}", response_model=TradeResponse)
async def get_trade(
    trade_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get a single trade"""
    service = TradeService(db)
    trade = await service.get_trade(current_user.id, trade_id)
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")
    return trade


@router.put("/{trade_id}", response_model=TradeResponse)
async def update_trade(
    trade_id: int,
    data: TradeUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update a trade"""
    service = TradeService(db)
    trade = await service.update_trade(current_user.id, trade_id, data)
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")
    return trade


@router.post("/{trade_id}/close", response_model=TradeResponse)
async def close_trade(
    trade_id: int,
    data: TradeClose,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Close a trade and calculate PnL"""
    service = TradeService(db)
    trade = await service.close_trade(current_user.id, trade_id, data)
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")
    return trade


@router.post("/{trade_id}/review", response_model=TradeResponse)
async def add_trade_review(
    trade_id: int,
    data: TradeReview,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Add post-close review to a trade (notes and image)"""
    service = TradeService(db)
    trade = await service.add_review(current_user.id, trade_id, data)
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")
    return trade


@router.delete("/{trade_id}")
async def delete_trade(
    trade_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete a trade"""
    service = TradeService(db)
    deleted = await service.delete_trade(current_user.id, trade_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Trade not found")
    return {"success": True, "message": "Trade deleted"}


@router.post("/analyze-month", response_model=AnalyzeMonthResponse)
async def analyze_month(
    data: AnalyzeMonthRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Analyze trades for a specific month using AI"""
    # Check if API key is configured
    if not os.getenv("ANTHROPIC_API_KEY"):
        return AnalyzeMonthResponse(
            success=False,
            error="ANTHROPIC_API_KEY no está configurada en el servidor"
        )

    service = TradeService(db)
    trades = await service.get_trades_by_month(current_user.id, data.month, data.year)

    if not trades:
        return AnalyzeMonthResponse(
            success=False,
            error=f"No hay trades cerrados en {data.month}/{data.year}"
        )

    # Convert to TradeForAnalysis format
    trades_for_analysis = [
        TradeForAnalysis(
            id=t.id,
            symbol=t.symbol,
            side=t.side,
            entry_price=t.entry_price,
            exit_price=t.exit_price,
            pnl=t.pnl,
            pnl_percent=t.pnl_percent,
            strategy=t.strategy,
            timeframe=t.timeframe,
            confidence_level=t.confidence_level,
            image_url=t.image_url,
            exit_image_url=t.exit_image_url,
            notes=t.notes,
            exit_notes=t.exit_notes,
        )
        for t in trades
    ]

    # Analyze with AI
    try:
        analyzer = AITradeAnalyzer()
        result = await analyzer.analyze_trades(trades_for_analysis, data.month, data.year)
        return AnalyzeMonthResponse(**result)
    except ValueError as e:
        return AnalyzeMonthResponse(success=False, error=str(e))
    except Exception as e:
        return AnalyzeMonthResponse(success=False, error=f"Error al analizar: {str(e)}")


# Monthly Analysis endpoints (saved analyses)
@router.post("/analyses", response_model=MonthlyAnalysisResponse)
async def save_monthly_analysis(
    data: MonthlyAnalysisCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Save a monthly analysis"""
    service = TradeService(db)
    analysis = await service.save_monthly_analysis(current_user.id, data)
    return analysis


@router.get("/analyses", response_model=MonthlyAnalysisListResponse)
async def get_monthly_analyses(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all saved monthly analyses"""
    service = TradeService(db)
    analyses, total = await service.get_all_monthly_analyses(current_user.id)

    # Debug: print each analysis to see what's causing validation errors
    validated = []
    for a in analyses:
        try:
            print(f"Validating analysis: id={a.id}, month={a.month}, year={a.year}, analysis_text={type(a.analysis_text)}, created_at={a.created_at}")
            validated.append(MonthlyAnalysisResponse.model_validate(a))
        except Exception as e:
            print(f"Validation error for analysis {a.id}: {e}")
            raise

    return MonthlyAnalysisListResponse(
        analyses=validated,
        total=total
    )


@router.delete("/analyses/{analysis_id}")
async def delete_monthly_analysis(
    analysis_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete a monthly analysis"""
    service = TradeService(db)
    deleted = await service.delete_monthly_analysis(current_user.id, analysis_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return {"success": True, "message": "Analysis deleted"}

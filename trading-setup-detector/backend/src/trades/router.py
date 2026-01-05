from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from src.database import get_db
from src.auth.dependencies import get_current_active_user
from src.auth.models import User
from src.trades.service import TradeService
from src.trades.schemas import (
    TradeCreate,
    TradeUpdate,
    TradeClose,
    TradeResponse,
    TradesListResponse,
    TradeStatsResponse,
)

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

"""
Trade Service - CRUD operations for trades
"""

from typing import List, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc

from src.trades.models import Trade
from src.trades.schemas import TradeCreate, TradeUpdate, TradeClose


class TradeService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_trade(self, user_id: int, data: TradeCreate) -> Trade:
        """Create a new trade"""
        trade = Trade(
            user_id=user_id,
            symbol=data.symbol.upper(),
            side=data.side.lower(),
            status="open",
            entry_price=data.entry_price,
            size=data.size,
            stop_loss=data.stop_loss,
            take_profit=data.take_profit,
            notes=data.notes,
            image_url=data.image_url,
            timeframe=data.timeframe,
            strategy=data.strategy,
            entry_date=data.entry_date or datetime.now(),
        )
        self.db.add(trade)
        await self.db.commit()
        await self.db.refresh(trade)
        return trade

    async def get_trades(
        self,
        user_id: int,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 50
    ) -> tuple[List[Trade], int]:
        """Get all trades for a user"""
        query = select(Trade).where(Trade.user_id == user_id)

        if status:
            query = query.where(Trade.status == status)

        # Count total
        count_query = select(func.count()).select_from(Trade).where(Trade.user_id == user_id)
        if status:
            count_query = count_query.where(Trade.status == status)
        count_result = await self.db.execute(count_query)
        total = count_result.scalar()

        # Get trades
        query = query.order_by(desc(Trade.entry_date)).offset(skip).limit(limit)
        result = await self.db.execute(query)
        trades = list(result.scalars().all())

        return trades, total

    async def get_trade(self, user_id: int, trade_id: int) -> Optional[Trade]:
        """Get a single trade"""
        result = await self.db.execute(
            select(Trade).where(Trade.id == trade_id, Trade.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def update_trade(self, user_id: int, trade_id: int, data: TradeUpdate) -> Optional[Trade]:
        """Update a trade"""
        trade = await self.get_trade(user_id, trade_id)
        if not trade:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(trade, key, value)

        # Recalculate PnL if trade is closed and relevant fields changed
        if trade.status == "closed" and trade.exit_price and trade.entry_price:
            if trade.side == "long":
                price_diff = trade.exit_price - trade.entry_price
            else:
                price_diff = trade.entry_price - trade.exit_price

            trade.pnl_percent = (price_diff / trade.entry_price) * 100
            trade.pnl = (trade.size * trade.pnl_percent / 100) - (trade.fees or 0)

        await self.db.commit()
        await self.db.refresh(trade)
        return trade

    async def close_trade(self, user_id: int, trade_id: int, data: TradeClose) -> Optional[Trade]:
        """Close a trade and calculate PnL"""
        trade = await self.get_trade(user_id, trade_id)
        if not trade:
            return None

        trade.exit_price = data.exit_price
        trade.status = "closed"
        trade.exit_date = datetime.now()
        trade.fees = data.fees or 0

        # Save exit notes and image separately
        if data.exit_notes:
            trade.exit_notes = data.exit_notes
        if data.exit_image_url:
            trade.exit_image_url = data.exit_image_url

        # Calculate PnL (size is in USD)
        if trade.side == "long":
            price_diff = trade.exit_price - trade.entry_price
        else:
            price_diff = trade.entry_price - trade.exit_price

        # PnL% = (price_diff / entry_price) * 100
        trade.pnl_percent = (price_diff / trade.entry_price) * 100
        # PnL = size * (pnl% / 100) - fees
        trade.pnl = (trade.size * trade.pnl_percent / 100) - trade.fees

        await self.db.commit()
        await self.db.refresh(trade)
        return trade

    async def delete_trade(self, user_id: int, trade_id: int) -> bool:
        """Delete a trade"""
        trade = await self.get_trade(user_id, trade_id)
        if not trade:
            return False

        await self.db.delete(trade)
        await self.db.commit()
        return True

    async def get_stats(self, user_id: int) -> dict:
        """Get trading statistics"""
        result = await self.db.execute(
            select(Trade).where(
                Trade.user_id == user_id,
                Trade.status == "closed"
            )
        )
        trades = list(result.scalars().all())

        if not trades:
            return {
                "total_trades": 0,
                "winning_trades": 0,
                "losing_trades": 0,
                "win_rate": 0,
                "total_pnl": 0,
                "average_pnl": 0,
                "best_trade": 0,
                "worst_trade": 0,
            }

        winning = [t for t in trades if t.pnl and t.pnl > 0]
        losing = [t for t in trades if t.pnl and t.pnl < 0]
        pnls = [t.pnl for t in trades if t.pnl is not None]

        return {
            "total_trades": len(trades),
            "winning_trades": len(winning),
            "losing_trades": len(losing),
            "win_rate": (len(winning) / len(trades) * 100) if trades else 0,
            "total_pnl": sum(pnls),
            "average_pnl": sum(pnls) / len(pnls) if pnls else 0,
            "best_trade": max(pnls) if pnls else 0,
            "worst_trade": min(pnls) if pnls else 0,
        }

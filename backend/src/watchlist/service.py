from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from src.watchlist.models import WatchlistItem
from src.watchlist.schemas import WatchlistItemCreate, WatchlistItemUpdate


class WatchlistService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_items(
        self,
        user_id: int,
        active_only: bool = False
    ) -> tuple[List[WatchlistItem], int]:
        query = select(WatchlistItem).where(WatchlistItem.user_id == user_id)
        if active_only:
            query = query.where(WatchlistItem.is_active == True)

        result = await self.db.execute(query)
        items = list(result.scalars().all())

        count_query = select(func.count()).select_from(WatchlistItem).where(
            WatchlistItem.user_id == user_id
        )
        if active_only:
            count_query = count_query.where(WatchlistItem.is_active == True)
        count_result = await self.db.execute(count_query)
        total = count_result.scalar()

        return items, total

    async def get_item(self, item_id: int, user_id: int) -> Optional[WatchlistItem]:
        result = await self.db.execute(
            select(WatchlistItem).where(
                WatchlistItem.id == item_id,
                WatchlistItem.user_id == user_id
            )
        )
        return result.scalar_one_or_none()

    async def get_item_by_symbol(self, symbol: str, user_id: int) -> Optional[WatchlistItem]:
        result = await self.db.execute(
            select(WatchlistItem).where(
                WatchlistItem.symbol == symbol.upper(),
                WatchlistItem.user_id == user_id
            )
        )
        return result.scalar_one_or_none()

    async def create_item(
        self,
        user_id: int,
        item_data: WatchlistItemCreate
    ) -> WatchlistItem:
        item = WatchlistItem(
            user_id=user_id,
            symbol=item_data.symbol.upper(),
            timeframes=item_data.timeframes
        )
        self.db.add(item)
        await self.db.commit()
        await self.db.refresh(item)
        return item

    async def update_item(
        self,
        item_id: int,
        user_id: int,
        update_data: WatchlistItemUpdate
    ) -> Optional[WatchlistItem]:
        item = await self.get_item(item_id, user_id)
        if not item:
            return None

        update_dict = update_data.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            setattr(item, key, value)

        await self.db.commit()
        await self.db.refresh(item)
        return item

    async def delete_item(self, item_id: int, user_id: int) -> bool:
        item = await self.get_item(item_id, user_id)
        if not item:
            return False

        await self.db.delete(item)
        await self.db.commit()
        return True

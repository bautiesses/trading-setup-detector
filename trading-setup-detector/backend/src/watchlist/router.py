from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import get_db
from src.auth.dependencies import get_current_active_user
from src.auth.models import User
from src.watchlist.service import WatchlistService
from src.watchlist.schemas import (
    WatchlistItemCreate, WatchlistItemUpdate,
    WatchlistItemResponse, WatchlistResponse
)

router = APIRouter(prefix="/watchlist", tags=["Watchlist"])


@router.get("/", response_model=WatchlistResponse)
async def list_watchlist(
    active_only: bool = Query(False),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    service = WatchlistService(db)
    items, total = await service.get_items(current_user.id, active_only)
    return WatchlistResponse(
        items=[WatchlistItemResponse.model_validate(i) for i in items],
        total=total
    )


@router.post("/", response_model=WatchlistItemResponse, status_code=201)
async def add_to_watchlist(
    item_data: WatchlistItemCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    service = WatchlistService(db)

    # Check if already exists
    existing = await service.get_item_by_symbol(item_data.symbol, current_user.id)
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Symbol {item_data.symbol} is already in your watchlist"
        )

    item = await service.create_item(current_user.id, item_data)
    return WatchlistItemResponse.model_validate(item)


@router.get("/{item_id}", response_model=WatchlistItemResponse)
async def get_watchlist_item(
    item_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    service = WatchlistService(db)
    item = await service.get_item(item_id, current_user.id)
    if not item:
        raise HTTPException(status_code=404, detail="Watchlist item not found")
    return WatchlistItemResponse.model_validate(item)


@router.put("/{item_id}", response_model=WatchlistItemResponse)
async def update_watchlist_item(
    item_id: int,
    update_data: WatchlistItemUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    service = WatchlistService(db)
    item = await service.update_item(item_id, current_user.id, update_data)
    if not item:
        raise HTTPException(status_code=404, detail="Watchlist item not found")
    return WatchlistItemResponse.model_validate(item)


@router.delete("/{item_id}", status_code=204)
async def remove_from_watchlist(
    item_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    service = WatchlistService(db)
    deleted = await service.delete_item(item_id, current_user.id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Watchlist item not found")

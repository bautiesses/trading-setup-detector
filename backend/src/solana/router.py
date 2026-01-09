from fastapi import APIRouter, Depends, Request, HTTPException, Header, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
import httpx

from src.database import get_db
from src.auth.dependencies import get_current_active_user
from src.auth.models import User
from src.solana.service import SolanaTradeService
from src.solana.helius_client import helius_client
from src.solana.schemas import (
    SolanaWalletCreate,
    SolanaWalletResponse,
    SolanaTradeResponse,
    SolanaTradesListResponse,
    SolanaTradeStatsResponse,
    SolanaTradeNotesUpdate
)
from src.config import get_settings

settings = get_settings()

router = APIRouter(prefix="/solana", tags=["Solana"])


# ============ WEBHOOK ENDPOINT (No auth - verified by signature) ============

@router.post("/webhook/helius")
async def helius_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    helius_signature: Optional[str] = Header(None, alias="helius-webhook-secret")
):
    """
    Webhook endpoint for Helius notifications.
    Receives Jupiter swap transactions and creates trade records.
    """
    # Get raw body for signature verification
    body = await request.body()

    # Verify signature
    if not helius_client.verify_webhook_signature(body, helius_signature):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")

    # Parse payload
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    # Ensure payload is a list
    if not isinstance(payload, list):
        payload = [payload]

    # Process in background to respond quickly
    async def process_webhook():
        service = SolanaTradeService(db)
        await service.process_webhook_payload(payload)

    background_tasks.add_task(process_webhook)

    return {"status": "accepted", "transactions": len(payload)}


# ============ WALLET MANAGEMENT ============

@router.post("/wallets", response_model=SolanaWalletResponse)
async def add_wallet(
    data: SolanaWalletCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Add a Solana wallet to track Jupiter swaps"""
    service = SolanaTradeService(db)
    try:
        wallet = await service.add_wallet(current_user.id, data)
        return wallet
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/wallets", response_model=List[SolanaWalletResponse])
async def get_wallets(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all tracked Solana wallets"""
    service = SolanaTradeService(db)
    return await service.get_wallets(current_user.id)


@router.delete("/wallets/{wallet_id}")
async def remove_wallet(
    wallet_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Remove a tracked wallet and its Helius webhook"""
    service = SolanaTradeService(db)
    success = await service.remove_wallet(current_user.id, wallet_id)
    if not success:
        raise HTTPException(status_code=404, detail="Wallet not found")
    return {"success": True}


# ============ TRADES ============

@router.get("/trades", response_model=SolanaTradesListResponse)
async def get_solana_trades(
    wallet_id: Optional[int] = Query(None),
    side: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get Solana trades with optional filters"""
    service = SolanaTradeService(db)
    trades, total = await service.get_trades(
        user_id=current_user.id,
        wallet_id=wallet_id,
        side=side,
        skip=skip,
        limit=limit
    )
    return SolanaTradesListResponse(trades=trades, total=total)


@router.get("/trades/stats", response_model=SolanaTradeStatsResponse)
async def get_solana_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get Solana trading statistics"""
    service = SolanaTradeService(db)
    return await service.get_stats(current_user.id)


@router.get("/trades/{trade_id}", response_model=SolanaTradeResponse)
async def get_solana_trade(
    trade_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get a single Solana trade details"""
    service = SolanaTradeService(db)
    trade = await service.get_trade(current_user.id, trade_id)
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")
    return trade


@router.post("/trades/{trade_id}/link/{linked_trade_id}")
async def link_trades(
    trade_id: int,
    linked_trade_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Link an entry trade (buy) with an exit trade (sell) for PnL calculation.
    The first trade_id should be the buy, linked_trade_id should be the sell.
    """
    service = SolanaTradeService(db)
    success = await service.link_trades(current_user.id, trade_id, linked_trade_id)
    if not success:
        raise HTTPException(
            status_code=400,
            detail="Could not link trades. Ensure entry is a buy and exit is a sell."
        )
    return {"success": True}


@router.put("/trades/{trade_id}/notes", response_model=SolanaTradeResponse)
async def update_trade_notes(
    trade_id: int,
    data: SolanaTradeNotesUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update notes for a Solana trade"""
    service = SolanaTradeService(db)
    trade = await service.update_notes(current_user.id, trade_id, data.notes)
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")
    return trade


@router.post("/import/{tx_signature}")
async def import_transaction(
    tx_signature: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Import a transaction manually by its signature.
    Fetches the transaction from Helius and processes it.
    """
    # Fetch transaction from Helius
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"https://api.helius.xyz/v0/transactions/?api-key={settings.helius_api_key}",
            json={"transactions": [tx_signature]},
            timeout=30.0
        )

        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="Could not fetch transaction from Helius")

        data = response.json()
        if not data:
            raise HTTPException(status_code=404, detail="Transaction not found")

    # Process the transaction
    service = SolanaTradeService(db)

    # Force type to SWAP for Jupiter transactions
    tx_data = data[0]
    if tx_data.get("source") == "JUPITER":
        tx_data["type"] = "SWAP"

    trades = await service.process_webhook_payload([tx_data])

    if not trades:
        raise HTTPException(status_code=400, detail="Could not process transaction as a trade")

    return {"success": True, "trades_imported": len(trades)}

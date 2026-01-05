from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


# ========== WALLET SCHEMAS ==========

class SolanaWalletCreate(BaseModel):
    address: str
    label: Optional[str] = None


class SolanaWalletResponse(BaseModel):
    id: int
    address: str
    label: Optional[str]
    is_active: bool
    helius_webhook_id: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# ========== TRADE SCHEMAS ==========

class SolanaTradeResponse(BaseModel):
    id: int
    wallet_id: int
    tx_signature: str
    block_time: datetime
    side: str

    token_in_address: str
    token_in_symbol: Optional[str]
    token_in_name: Optional[str]
    token_in_amount: float
    token_in_usd_value: Optional[float]

    token_out_address: str
    token_out_symbol: Optional[str]
    token_out_name: Optional[str]
    token_out_amount: float
    token_out_usd_value: Optional[float]

    price_per_token: Optional[float]
    price_usd: Optional[float]

    fee_sol: Optional[float]
    fee_usd: Optional[float]

    linked_trade_id: Optional[int]
    pnl: Optional[float]
    pnl_percent: Optional[float]

    chart_image_url: Optional[str]
    notes: Optional[str]
    dex_name: str

    created_at: datetime

    class Config:
        from_attributes = True


class SolanaTradesListResponse(BaseModel):
    trades: List[SolanaTradeResponse]
    total: int


class SolanaTradeStatsResponse(BaseModel):
    total_trades: int
    buy_trades: int
    sell_trades: int
    total_volume_usd: float
    total_fees_sol: float
    linked_pnl: float
    winning_trades: int
    losing_trades: int


class SolanaTradeNotesUpdate(BaseModel):
    notes: str


# ========== WEBHOOK SCHEMAS ==========

class WebhookPayload(BaseModel):
    """Simplified Helius webhook payload structure"""
    class Config:
        extra = "allow"

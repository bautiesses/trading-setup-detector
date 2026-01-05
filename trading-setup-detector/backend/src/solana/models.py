from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.sql import func
from src.database import Base


class SolanaWallet(Base):
    """Solana wallet for tracking Jupiter swaps"""
    __tablename__ = "solana_wallets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    address = Column(String(44), nullable=False, unique=True)
    label = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True)
    helius_webhook_id = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class SolanaTrade(Base):
    """Solana trade from Jupiter swaps"""
    __tablename__ = "solana_trades"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    wallet_id = Column(Integer, ForeignKey("solana_wallets.id"), nullable=False)

    # Transaction info
    tx_signature = Column(String(88), unique=True, nullable=False)
    slot = Column(Integer, nullable=True)
    block_time = Column(DateTime(timezone=True), nullable=False)

    # Trade info
    side = Column(String(10), nullable=False)  # buy or sell
    status = Column(String(20), default="closed")

    # Token In (what user spent)
    token_in_address = Column(String(44), nullable=False)
    token_in_symbol = Column(String(20), nullable=True)
    token_in_name = Column(String(100), nullable=True)
    token_in_amount = Column(Float, nullable=False)
    token_in_decimals = Column(Integer, nullable=False)
    token_in_usd_value = Column(Float, nullable=True)

    # Token Out (what user received)
    token_out_address = Column(String(44), nullable=False)
    token_out_symbol = Column(String(20), nullable=True)
    token_out_name = Column(String(100), nullable=True)
    token_out_amount = Column(Float, nullable=False)
    token_out_decimals = Column(Integer, nullable=False)
    token_out_usd_value = Column(Float, nullable=True)

    # Prices
    price_per_token = Column(Float, nullable=True)
    price_usd = Column(Float, nullable=True)

    # Fees
    fee_sol = Column(Float, nullable=True)
    fee_usd = Column(Float, nullable=True)
    platform_fee = Column(Float, nullable=True)
    slippage_percent = Column(Float, nullable=True)

    # PnL (for linked trades)
    linked_trade_id = Column(Integer, ForeignKey("solana_trades.id"), nullable=True)
    pnl = Column(Float, nullable=True)
    pnl_percent = Column(Float, nullable=True)

    # Chart & Notes
    chart_image_url = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)

    # DEX info
    dex_name = Column(String(50), default="Jupiter")
    route_info = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class TokenCache(Base):
    """Cache for Solana token metadata"""
    __tablename__ = "token_cache"

    id = Column(Integer, primary_key=True, index=True)
    address = Column(String(44), unique=True, nullable=False)
    symbol = Column(String(20), nullable=True)
    name = Column(String(100), nullable=True)
    decimals = Column(Integer, nullable=False, default=9)
    logo_uri = Column(Text, nullable=True)
    coingecko_id = Column(String(100), nullable=True)
    last_updated = Column(DateTime(timezone=True), server_default=func.now())

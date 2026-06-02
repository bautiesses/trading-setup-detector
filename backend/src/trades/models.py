from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Enum
from sqlalchemy.sql import func
from src.database import Base
import enum


class TradeStatus(str, enum.Enum):
    OPEN = "open"
    CLOSED = "closed"
    CANCELLED = "cancelled"


class TradeSide(str, enum.Enum):
    LONG = "long"
    SHORT = "short"


class Trade(Base):
    __tablename__ = "trades"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Trade info
    symbol = Column(String(20), nullable=False)
    side = Column(String(10), nullable=False)  # long or short
    status = Column(String(20), default="open")  # open, closed, cancelled

    # Prices
    entry_price = Column(Float, nullable=False)
    exit_price = Column(Float, nullable=True)
    stop_loss = Column(Float, nullable=True)
    take_profit = Column(Float, nullable=True)

    # Size & PnL
    size = Column(Float, nullable=False)  # Position size in USD or quantity
    pnl = Column(Float, nullable=True)  # Profit/Loss in USD
    pnl_percent = Column(Float, nullable=True)  # Profit/Loss percentage
    fees = Column(Float, default=0)

    # Notes & Image (Entry)
    notes = Column(Text, nullable=True)  # Entry notes
    image_url = Column(Text, nullable=True)  # Entry image URL or base64

    # Notes & Image (Exit)
    exit_notes = Column(Text, nullable=True)  # Exit/close notes
    exit_image_url = Column(Text, nullable=True)  # Exit image URL or base64

    # Post-trade review (after close)
    review_notes = Column(Text, nullable=True)  # Post-close analysis notes
    review_image_url = Column(Text, nullable=True)  # Post-close analysis image

    # Timeframe & Strategy
    timeframe = Column(String(10), nullable=True)
    strategy = Column(String(100), nullable=True)  # e.g., "Break & Retest"
    confidence_level = Column(Integer, nullable=True)  # 1-5 trader confidence

    # Entry reasons (JSON array: VAH, POC, VAL, VWAP, ABSORPTION)
    entry_reasons = Column(Text, nullable=True)  # JSON array of entry reasons

    # Dates
    entry_date = Column(DateTime(timezone=True), server_default=func.now())
    exit_date = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class MonthlyAnalysis(Base):
    __tablename__ = "monthly_analyses"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Period
    month = Column(Integer, nullable=False)  # 1-12
    year = Column(Integer, nullable=False)

    # Stats snapshot
    total_trades = Column(Integer, default=0)
    winning_trades = Column(Integer, default=0)
    losing_trades = Column(Integer, default=0)
    win_rate = Column(Float, default=0)
    total_pnl = Column(Float, default=0)

    # AI Analysis
    analysis_text = Column(Text, nullable=True)  # The AI-generated analysis
    images_analyzed = Column(Integer, default=0)

    # Dates
    created_at = Column(DateTime(timezone=True), server_default=func.now())

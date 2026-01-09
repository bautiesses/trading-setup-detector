from sqlalchemy import Column, Integer, String, Boolean, Float, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from src.database import Base


class ScanResult(Base):
    """Resultado de un scan de Break & Retest"""
    __tablename__ = "scan_results"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    symbol = Column(String(20), nullable=False)
    timeframe = Column(String(10), nullable=False)
    pattern_type = Column(String(50), nullable=False)  # bullish_retest, bearish_retest
    level_price = Column(Float, nullable=False)
    current_price = Column(Float, nullable=False)
    confidence_score = Column(Float, default=0.0)
    is_match = Column(Boolean, default=True)
    message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class ScanExecution(Base):
    """Registro de cada ejecución de scan"""
    __tablename__ = "scan_executions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    symbols_scanned = Column(Integer, default=0)
    signals_found = Column(Integer, default=0)
    sensitivity = Column(String(20), default="medium")
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class ScannerConfig(Base):
    """Configuración del scanner por usuario"""
    __tablename__ = "scanner_configs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    is_enabled = Column(Boolean, default=False)
    scan_interval_minutes = Column(Integer, default=5)
    sensitivity = Column(String(20), default="medium")  # low, medium, high
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

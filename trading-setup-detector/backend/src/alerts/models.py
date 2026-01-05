from sqlalchemy import Column, Integer, String, Boolean, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.database import Base


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    scan_result_id = Column(Integer, ForeignKey("scan_results.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    channel = Column(String(20), nullable=False)  # 'telegram', 'email', 'dashboard'
    status = Column(String(20), default="pending")  # 'pending', 'sent', 'failed'
    sent_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    scan_result = relationship("ScanResult", back_populates="alerts")
    user = relationship("User", back_populates="alerts")


class AlertSettings(Base):
    __tablename__ = "alert_settings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    telegram_enabled = Column(Boolean, default=False)
    telegram_chat_id = Column(String(50), nullable=True)
    email_enabled = Column(Boolean, default=False)
    email_address = Column(String(255), nullable=True)
    dashboard_enabled = Column(Boolean, default=True)
    min_confidence_threshold = Column(Float, default=0.7)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="alert_settings")

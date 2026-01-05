from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime


class AlertResponse(BaseModel):
    id: int
    scan_result_id: int
    channel: str
    status: str
    sent_at: Optional[datetime]
    error_message: Optional[str]
    created_at: datetime
    # Related data
    symbol: Optional[str] = None
    pattern_name: Optional[str] = None
    confidence_score: Optional[float] = None

    class Config:
        from_attributes = True


class AlertsListResponse(BaseModel):
    alerts: List[AlertResponse]
    total: int


class AlertSettingsResponse(BaseModel):
    telegram_enabled: bool
    telegram_chat_id: Optional[str]
    email_enabled: bool
    email_address: Optional[str]
    dashboard_enabled: bool
    min_confidence_threshold: float

    class Config:
        from_attributes = True


class AlertSettingsUpdate(BaseModel):
    telegram_enabled: Optional[bool] = None
    telegram_chat_id: Optional[str] = None
    email_enabled: Optional[bool] = None
    email_address: Optional[EmailStr] = None
    dashboard_enabled: Optional[bool] = None
    min_confidence_threshold: Optional[float] = Field(None, ge=0.0, le=1.0)


class TestAlertRequest(BaseModel):
    channel: str = Field(..., pattern=r"^(telegram|email|all)$")

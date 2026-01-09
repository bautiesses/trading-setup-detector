from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class ScanResultResponse(BaseModel):
    id: int
    pattern_id: int
    pattern_name: Optional[str] = None
    symbol: str
    timeframe: str
    confidence_score: Optional[float]
    is_match: bool
    chart_image_path: Optional[str]
    claude_response: Optional[Dict[str, Any]]
    created_at: datetime

    class Config:
        from_attributes = True


class ScanResultsListResponse(BaseModel):
    results: List[ScanResultResponse]
    total: int


class ScannerStatus(BaseModel):
    is_running: bool
    last_scan_at: Optional[datetime]
    next_scan_at: Optional[datetime]
    scan_interval_minutes: int
    patterns_active: int
    symbols_monitored: int
    total_scans_today: int
    matches_today: int


class ScannerConfigUpdate(BaseModel):
    scan_interval_minutes: Optional[int] = Field(None, ge=1, le=60)


class ManualScanRequest(BaseModel):
    symbols: Optional[List[str]] = None
    timeframes: Optional[List[str]] = None
    pattern_ids: Optional[List[int]] = None


class ManualScanResponse(BaseModel):
    message: str
    results_count: int
    matches_count: int
    results: List[ScanResultResponse]

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class PatternType(str, Enum):
    TRIANGLE_ASCENDING = "triangle_ascending"
    TRIANGLE_DESCENDING = "triangle_descending"
    TRIANGLE_SYMMETRICAL = "triangle_symmetrical"
    DOUBLE_TOP = "double_top"
    DOUBLE_BOTTOM = "double_bottom"
    HEAD_AND_SHOULDERS = "head_and_shoulders"
    INVERSE_HEAD_AND_SHOULDERS = "inverse_head_and_shoulders"
    WEDGE_RISING = "wedge_rising"
    WEDGE_FALLING = "wedge_falling"
    FLAG = "flag"
    PENNANT = "pennant"
    CUP_AND_HANDLE = "cup_and_handle"
    CUSTOM = "custom"


class PatternCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    pattern_type: PatternType = PatternType.CUSTOM
    confidence_threshold: float = Field(default=0.7, ge=0.0, le=1.0)


class PatternUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    pattern_type: Optional[PatternType] = None
    confidence_threshold: Optional[float] = Field(None, ge=0.0, le=1.0)
    is_active: Optional[bool] = None


class ClaudeAnalysis(BaseModel):
    pattern_identified: str
    key_characteristics: List[str]
    entry_conditions: List[str]
    exit_conditions: List[str]
    risk_level: str
    typical_duration: str
    success_indicators: List[str]
    failure_indicators: List[str]
    additional_notes: Optional[str] = None


class PatternResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    image_path: str
    pattern_type: str
    claude_analysis: Optional[Dict[str, Any]]
    confidence_threshold: float
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PatternListResponse(BaseModel):
    patterns: List[PatternResponse]
    total: int


class PatternTypesResponse(BaseModel):
    types: List[Dict[str, str]]

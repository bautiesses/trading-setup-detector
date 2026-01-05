from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from src.database import get_db
from src.auth.dependencies import get_current_active_user
from src.auth.models import User
from src.patterns.service import PatternService
from src.patterns.schemas import (
    PatternCreate, PatternUpdate, PatternResponse,
    PatternListResponse, PatternTypesResponse, PatternType
)

router = APIRouter(prefix="/patterns", tags=["Patterns"])


@router.get("/", response_model=PatternListResponse)
async def list_patterns(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    active_only: bool = Query(False),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    service = PatternService(db)
    patterns, total = await service.get_patterns(
        current_user.id, skip, limit, active_only
    )
    return PatternListResponse(
        patterns=[PatternResponse.model_validate(p) for p in patterns],
        total=total
    )


@router.post("/", response_model=PatternResponse, status_code=201)
async def create_pattern(
    name: str = Form(...),
    description: Optional[str] = Form(None),
    pattern_type: PatternType = Form(PatternType.CUSTOM),
    confidence_threshold: float = Form(0.7),
    image: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    if not image.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image")

    pattern_data = PatternCreate(
        name=name,
        description=description,
        pattern_type=pattern_type,
        confidence_threshold=confidence_threshold
    )

    service = PatternService(db)
    pattern = await service.create_pattern(current_user.id, pattern_data, image)
    return PatternResponse.model_validate(pattern)


@router.get("/types", response_model=PatternTypesResponse)
async def get_pattern_types(
    _: User = Depends(get_current_active_user)
):
    types = [
        {"value": pt.value, "label": pt.value.replace('_', ' ').title()}
        for pt in PatternType
    ]
    return PatternTypesResponse(types=types)


@router.get("/{pattern_id}", response_model=PatternResponse)
async def get_pattern(
    pattern_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    service = PatternService(db)
    pattern = await service.get_pattern(pattern_id, current_user.id)
    if not pattern:
        raise HTTPException(status_code=404, detail="Pattern not found")
    return PatternResponse.model_validate(pattern)


@router.put("/{pattern_id}", response_model=PatternResponse)
async def update_pattern(
    pattern_id: int,
    update_data: PatternUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    service = PatternService(db)
    pattern = await service.update_pattern(pattern_id, current_user.id, update_data)
    if not pattern:
        raise HTTPException(status_code=404, detail="Pattern not found")
    return PatternResponse.model_validate(pattern)


@router.delete("/{pattern_id}", status_code=204)
async def delete_pattern(
    pattern_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    service = PatternService(db)
    deleted = await service.delete_pattern(pattern_id, current_user.id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Pattern not found")


@router.post("/{pattern_id}/analyze", response_model=PatternResponse)
async def analyze_pattern(
    pattern_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    service = PatternService(db)
    pattern = await service.analyze_pattern(pattern_id, current_user.id)
    if not pattern:
        raise HTTPException(status_code=404, detail="Pattern not found")
    return PatternResponse.model_validate(pattern)

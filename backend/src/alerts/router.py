from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import get_db
from src.auth.dependencies import get_current_active_user
from src.auth.models import User
from src.alerts.service import AlertService
from src.alerts.schemas import (
    AlertResponse, AlertsListResponse,
    AlertSettingsResponse, AlertSettingsUpdate, TestAlertRequest
)

router = APIRouter(prefix="/alerts", tags=["Alerts"])


@router.get("/", response_model=AlertsListResponse)
async def list_alerts(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    service = AlertService(db)
    alerts, total = await service.get_alerts(current_user.id, skip, limit)

    return AlertsListResponse(
        alerts=[AlertResponse.model_validate(a) for a in alerts],
        total=total
    )


@router.get("/settings", response_model=AlertSettingsResponse)
async def get_alert_settings(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    service = AlertService(db)
    settings = await service.get_settings(current_user.id)

    if not settings:
        # Create default settings
        settings = await service.update_settings(current_user.id)

    return AlertSettingsResponse.model_validate(settings)


@router.put("/settings", response_model=AlertSettingsResponse)
async def update_alert_settings(
    update_data: AlertSettingsUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    service = AlertService(db)
    settings = await service.update_settings(
        current_user.id,
        **update_data.model_dump(exclude_unset=True)
    )
    return AlertSettingsResponse.model_validate(settings)


@router.post("/test")
async def send_test_alert(
    request: TestAlertRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    service = AlertService(db)
    result = await service.send_test_alert(current_user.id, request.channel)
    return result

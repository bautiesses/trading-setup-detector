from typing import List, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from src.alerts.models import Alert, AlertSettings
from src.scanner.models import ScanResult
from src.patterns.models import Pattern
from src.config import get_settings

settings = get_settings()


class AlertService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def send_alerts(self, user_id: int, scan_result: ScanResult) -> List[Alert]:
        alerts_created = []
        alert_settings = await self.get_settings(user_id)

        if not alert_settings:
            return alerts_created

        # Check confidence threshold
        if scan_result.confidence_score < alert_settings.min_confidence_threshold:
            return alerts_created

        # Dashboard alert (always if enabled)
        if alert_settings.dashboard_enabled:
            alert = await self._create_alert(user_id, scan_result.id, 'dashboard')
            alert.status = 'sent'
            alert.sent_at = datetime.utcnow()
            alerts_created.append(alert)

        # Telegram alert
        if alert_settings.telegram_enabled and alert_settings.telegram_chat_id:
            alert = await self._create_alert(user_id, scan_result.id, 'telegram')
            try:
                await self._send_telegram_alert(
                    chat_id=alert_settings.telegram_chat_id,
                    scan_result=scan_result
                )
                alert.status = 'sent'
                alert.sent_at = datetime.utcnow()
            except Exception as e:
                alert.status = 'failed'
                alert.error_message = str(e)
            alerts_created.append(alert)

        # Email alert
        if alert_settings.email_enabled and alert_settings.email_address:
            alert = await self._create_alert(user_id, scan_result.id, 'email')
            try:
                await self._send_email_alert(
                    email=alert_settings.email_address,
                    scan_result=scan_result
                )
                alert.status = 'sent'
                alert.sent_at = datetime.utcnow()
            except Exception as e:
                alert.status = 'failed'
                alert.error_message = str(e)
            alerts_created.append(alert)

        await self.db.commit()
        return alerts_created

    async def get_alerts(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 50
    ) -> tuple[List[Alert], int]:
        query = (
            select(Alert)
            .where(Alert.user_id == user_id)
            .order_by(Alert.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(query)
        alerts = list(result.scalars().all())

        count_result = await self.db.execute(
            select(func.count()).select_from(Alert).where(Alert.user_id == user_id)
        )
        total = count_result.scalar()

        return alerts, total

    async def get_settings(self, user_id: int) -> Optional[AlertSettings]:
        result = await self.db.execute(
            select(AlertSettings).where(AlertSettings.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def update_settings(self, user_id: int, **kwargs) -> AlertSettings:
        alert_settings = await self.get_settings(user_id)

        if not alert_settings:
            alert_settings = AlertSettings(user_id=user_id)
            self.db.add(alert_settings)

        for key, value in kwargs.items():
            if value is not None and hasattr(alert_settings, key):
                setattr(alert_settings, key, value)

        await self.db.commit()
        await self.db.refresh(alert_settings)
        return alert_settings

    async def send_test_alert(self, user_id: int, channel: str) -> dict:
        alert_settings = await self.get_settings(user_id)

        if not alert_settings:
            return {"success": False, "error": "No alert settings configured"}

        if channel == 'telegram' or channel == 'all':
            if alert_settings.telegram_chat_id:
                try:
                    from src.alerts.telegram_bot import TelegramAlertBot
                    bot = TelegramAlertBot(settings.telegram_bot_token)
                    await bot.send_test_message(alert_settings.telegram_chat_id)
                    return {"success": True, "channel": "telegram", "message": "Test alert sent"}
                except Exception as e:
                    return {"success": False, "channel": "telegram", "error": str(e)}

        if channel == 'email' or channel == 'all':
            if alert_settings.email_address:
                try:
                    from src.alerts.email_sender import EmailAlertService
                    email_service = EmailAlertService(
                        smtp_host=settings.smtp_host,
                        smtp_port=settings.smtp_port,
                        username=settings.smtp_username,
                        password=settings.smtp_password,
                        from_email=settings.smtp_from_email
                    )
                    await email_service.send_test_email(alert_settings.email_address)
                    return {"success": True, "channel": "email", "message": "Test alert sent"}
                except Exception as e:
                    return {"success": False, "channel": "email", "error": str(e)}

        return {"success": False, "error": "No valid channel configured"}

    async def _create_alert(self, user_id: int, scan_result_id: int, channel: str) -> Alert:
        alert = Alert(
            user_id=user_id,
            scan_result_id=scan_result_id,
            channel=channel,
            status='pending'
        )
        self.db.add(alert)
        return alert

    async def _send_telegram_alert(self, chat_id: str, scan_result: ScanResult) -> None:
        if not settings.telegram_bot_token:
            raise ValueError("Telegram bot token not configured")

        from src.alerts.telegram_bot import TelegramAlertBot
        bot = TelegramAlertBot(settings.telegram_bot_token)

        # Get pattern info
        pattern = await self.db.execute(
            select(Pattern).where(Pattern.id == scan_result.pattern_id)
        )
        pattern = pattern.scalar_one_or_none()
        pattern_name = pattern.name if pattern else "Unknown"

        reasoning = scan_result.claude_response.get('reasoning', '') if scan_result.claude_response else ''

        await bot.send_alert(
            chat_id=chat_id,
            symbol=scan_result.symbol,
            timeframe=scan_result.timeframe,
            pattern_name=pattern_name,
            confidence=scan_result.confidence_score,
            chart_image_path=scan_result.chart_image_path,
            reasoning=reasoning
        )

    async def _send_email_alert(self, email: str, scan_result: ScanResult) -> None:
        from src.alerts.email_sender import EmailAlertService

        email_service = EmailAlertService(
            smtp_host=settings.smtp_host,
            smtp_port=settings.smtp_port,
            username=settings.smtp_username,
            password=settings.smtp_password,
            from_email=settings.smtp_from_email
        )

        # Get pattern info
        pattern = await self.db.execute(
            select(Pattern).where(Pattern.id == scan_result.pattern_id)
        )
        pattern = pattern.scalar_one_or_none()
        pattern_name = pattern.name if pattern else "Unknown"

        reasoning = scan_result.claude_response.get('reasoning', '') if scan_result.claude_response else ''

        await email_service.send_alert(
            to_email=email,
            symbol=scan_result.symbol,
            timeframe=scan_result.timeframe,
            pattern_name=pattern_name,
            confidence=scan_result.confidence_score,
            chart_image_path=scan_result.chart_image_path,
            reasoning=reasoning
        )

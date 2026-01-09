from telegram import Bot
from telegram.constants import ParseMode


class TelegramAlertBot:
    def __init__(self, bot_token: str):
        self.bot = Bot(token=bot_token)

    async def send_alert(
        self,
        chat_id: str,
        symbol: str,
        timeframe: str,
        pattern_name: str,
        confidence: float,
        chart_image_path: str,
        reasoning: str
    ) -> bool:
        try:
            message = self._format_alert_message(
                symbol=symbol,
                timeframe=timeframe,
                pattern_name=pattern_name,
                confidence=confidence,
                reasoning=reasoning
            )

            with open(chart_image_path, 'rb') as photo:
                await self.bot.send_photo(
                    chat_id=chat_id,
                    photo=photo,
                    caption=message,
                    parse_mode=ParseMode.HTML
                )

            return True
        except Exception as e:
            print(f"Telegram send error: {e}")
            raise

    async def send_test_message(self, chat_id: str) -> bool:
        try:
            message = """
<b>Test Alert from Trading Setup Detector</b>

This is a test message to verify your Telegram notifications are working correctly.

Your alerts are configured and ready to receive pattern matches!
"""
            await self.bot.send_message(
                chat_id=chat_id,
                text=message,
                parse_mode=ParseMode.HTML
            )
            return True
        except Exception as e:
            print(f"Telegram test message error: {e}")
            raise

    def _format_alert_message(
        self,
        symbol: str,
        timeframe: str,
        pattern_name: str,
        confidence: float,
        reasoning: str
    ) -> str:
        confidence_emoji = "🟢" if confidence >= 0.8 else "🟡" if confidence >= 0.6 else "🔴"

        return f"""
<b>PATTERN ALERT</b>

<b>Symbol:</b> {symbol}
<b>Timeframe:</b> {timeframe}
<b>Pattern:</b> {pattern_name}
<b>Confidence:</b> {confidence_emoji} {confidence:.1%}

<b>Analysis:</b>
{reasoning[:500]}{"..." if len(reasoning) > 500 else ""}

<i>Trading Setup Detector</i>
"""

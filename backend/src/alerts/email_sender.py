import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from pathlib import Path


class EmailAlertService:
    def __init__(
        self,
        smtp_host: str,
        smtp_port: int,
        username: str,
        password: str,
        from_email: str
    ):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.from_email = from_email

    async def send_alert(
        self,
        to_email: str,
        symbol: str,
        timeframe: str,
        pattern_name: str,
        confidence: float,
        chart_image_path: str,
        reasoning: str
    ) -> bool:
        try:
            msg = MIMEMultipart('related')
            msg['Subject'] = f"Pattern Alert: {pattern_name} on {symbol} ({timeframe})"
            msg['From'] = self.from_email
            msg['To'] = to_email

            html_body = self._format_html_email(
                symbol, timeframe, pattern_name,
                confidence, reasoning
            )
            msg.attach(MIMEText(html_body, 'html'))

            if chart_image_path and Path(chart_image_path).exists():
                with open(chart_image_path, 'rb') as img_file:
                    img = MIMEImage(img_file.read())
                    img.add_header('Content-ID', '<chart>')
                    msg.attach(img)

            await aiosmtplib.send(
                msg,
                hostname=self.smtp_host,
                port=self.smtp_port,
                username=self.username,
                password=self.password,
                use_tls=True
            )

            return True
        except Exception as e:
            print(f"Email send error: {e}")
            raise

    async def send_test_email(self, to_email: str) -> bool:
        try:
            msg = MIMEMultipart()
            msg['Subject'] = "Test Alert - Trading Setup Detector"
            msg['From'] = self.from_email
            msg['To'] = to_email

            html_body = """
            <html>
            <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <h2 style="color: #2563eb;">Test Alert from Trading Setup Detector</h2>
                <p>This is a test message to verify your email notifications are working correctly.</p>
                <p>Your alerts are configured and ready to receive pattern matches!</p>
                <hr>
                <p style="color: #6b7280; font-size: 12px;">Trading Setup Detector</p>
            </body>
            </html>
            """
            msg.attach(MIMEText(html_body, 'html'))

            await aiosmtplib.send(
                msg,
                hostname=self.smtp_host,
                port=self.smtp_port,
                username=self.username,
                password=self.password,
                use_tls=True
            )

            return True
        except Exception as e:
            print(f"Email test error: {e}")
            raise

    def _format_html_email(
        self,
        symbol: str,
        timeframe: str,
        pattern_name: str,
        confidence: float,
        reasoning: str
    ) -> str:
        confidence_color = "#22c55e" if confidence >= 0.8 else "#eab308" if confidence >= 0.6 else "#ef4444"

        return f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <h2 style="color: #2563eb; border-bottom: 2px solid #2563eb; padding-bottom: 10px;">
                Pattern Alert
            </h2>

            <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                <tr>
                    <td style="padding: 8px; border-bottom: 1px solid #e5e7eb; font-weight: bold;">Symbol</td>
                    <td style="padding: 8px; border-bottom: 1px solid #e5e7eb;">{symbol}</td>
                </tr>
                <tr>
                    <td style="padding: 8px; border-bottom: 1px solid #e5e7eb; font-weight: bold;">Timeframe</td>
                    <td style="padding: 8px; border-bottom: 1px solid #e5e7eb;">{timeframe}</td>
                </tr>
                <tr>
                    <td style="padding: 8px; border-bottom: 1px solid #e5e7eb; font-weight: bold;">Pattern</td>
                    <td style="padding: 8px; border-bottom: 1px solid #e5e7eb;">{pattern_name}</td>
                </tr>
                <tr>
                    <td style="padding: 8px; border-bottom: 1px solid #e5e7eb; font-weight: bold;">Confidence</td>
                    <td style="padding: 8px; border-bottom: 1px solid #e5e7eb;">
                        <span style="color: {confidence_color}; font-weight: bold;">{confidence:.1%}</span>
                    </td>
                </tr>
            </table>

            <h3 style="color: #374151;">Analysis</h3>
            <p style="color: #4b5563; line-height: 1.6;">{reasoning}</p>

            <div style="margin: 20px 0;">
                <img src="cid:chart" alt="Chart" style="max-width: 100%; border: 1px solid #e5e7eb; border-radius: 8px;">
            </div>

            <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 20px 0;">
            <p style="color: #9ca3af; font-size: 12px;">Trading Setup Detector</p>
        </body>
        </html>
        """

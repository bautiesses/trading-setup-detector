import httpx
import hmac
import hashlib
from typing import Optional
from src.config import get_settings

settings = get_settings()


class HeliusClient:
    """Client for Helius API and webhook management"""

    BASE_URL = "https://api.helius.xyz/v0"

    def __init__(self):
        self.api_key = settings.helius_api_key
        self.webhook_secret = settings.helius_webhook_secret

    async def create_webhook(
        self,
        wallet_address: str,
        callback_url: str,
        webhook_type: str = "enhanced"
    ) -> dict:
        """
        Register a webhook for a wallet address.

        Args:
            wallet_address: Solana wallet address to monitor
            callback_url: URL to receive webhook notifications
            webhook_type: "enhanced" includes parsed Jupiter data

        Returns:
            Webhook registration response with webhookID
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.BASE_URL}/webhooks?api-key={self.api_key}",
                json={
                    "webhookURL": callback_url,
                    "transactionTypes": ["SWAP"],
                    "accountAddresses": [wallet_address],
                    "webhookType": webhook_type
                },
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()

    async def delete_webhook(self, webhook_id: str) -> bool:
        """Delete a webhook by ID"""
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f"{self.BASE_URL}/webhooks/{webhook_id}?api-key={self.api_key}",
                timeout=30.0
            )
            return response.status_code == 200

    async def get_webhooks(self) -> list:
        """Get all registered webhooks"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/webhooks?api-key={self.api_key}",
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()

    def verify_webhook_signature(self, payload: bytes, signature: Optional[str]) -> bool:
        """
        Verify webhook signature from Helius.

        Args:
            payload: Raw request body bytes
            signature: Signature from helius-webhook-secret header

        Returns:
            True if signature is valid or no secret configured
        """
        if not self.webhook_secret:
            return True

        if not signature:
            return False

        expected = hmac.new(
            self.webhook_secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(expected, signature)

    async def get_parsed_transaction(self, signature: str) -> Optional[dict]:
        """
        Get parsed transaction data for a signature.
        Useful for fetching details of missed webhooks.
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/transactions/?api-key={self.api_key}",
                params={"transactions": [signature]},
                timeout=30.0
            )
            if response.status_code == 200:
                data = response.json()
                return data[0] if data else None
            return None


helius_client = HeliusClient()

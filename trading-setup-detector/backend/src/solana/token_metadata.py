import httpx
from typing import Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.config import get_settings

settings = get_settings()


# Known tokens to avoid API calls
KNOWN_TOKENS = {
    "So11111111111111111111111111111111111111112": {
        "symbol": "SOL",
        "name": "Wrapped SOL",
        "decimals": 9
    },
    "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v": {
        "symbol": "USDC",
        "name": "USD Coin",
        "decimals": 6
    },
    "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB": {
        "symbol": "USDT",
        "name": "Tether USD",
        "decimals": 6
    },
    "7vfCXTUXx5WJV5JADk17DUJ4ksgau7utNKj4b963voxs": {
        "symbol": "WETH",
        "name": "Wrapped Ether",
        "decimals": 8
    },
    "mSoLzYCxHdYgdzU16g5QSh3i5K3z3KZK7ytfqcJm7So": {
        "symbol": "mSOL",
        "name": "Marinade Staked SOL",
        "decimals": 9
    },
    "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263": {
        "symbol": "BONK",
        "name": "Bonk",
        "decimals": 5
    }
}


class TokenMetadata:
    """Token metadata info"""
    def __init__(self, address: str, symbol: str = None, name: str = None,
                 decimals: int = 9, logo_uri: str = None):
        self.address = address
        self.symbol = symbol
        self.name = name
        self.decimals = decimals
        self.logo_uri = logo_uri


class TokenMetadataService:
    """Service for resolving and caching Solana token metadata"""

    async def get_token_info(self, address: str, db: Optional[AsyncSession] = None) -> Optional[TokenMetadata]:
        """
        Get token info, using cache or fetching from API.

        Args:
            address: Token mint address
            db: Optional database session for caching

        Returns:
            TokenMetadata object or None
        """
        # Check known tokens first
        if address in KNOWN_TOKENS:
            known = KNOWN_TOKENS[address]
            return TokenMetadata(
                address=address,
                symbol=known["symbol"],
                name=known["name"],
                decimals=known["decimals"]
            )

        # Check database cache if session provided
        if db:
            from src.solana.models import TokenCache
            result = await db.execute(
                select(TokenCache).where(TokenCache.address == address)
            )
            cached = result.scalar_one_or_none()

            if cached:
                # Return if fresh (less than 24 hours old)
                if cached.last_updated and datetime.now() - cached.last_updated < timedelta(hours=24):
                    return TokenMetadata(
                        address=cached.address,
                        symbol=cached.symbol,
                        name=cached.name,
                        decimals=cached.decimals,
                        logo_uri=cached.logo_uri
                    )

        # Fetch from API
        token_info = await self._fetch_token_info(address)

        if token_info and db:
            await self._cache_token(db, address, token_info)

        if token_info:
            return TokenMetadata(
                address=address,
                symbol=token_info.get("symbol"),
                name=token_info.get("name"),
                decimals=token_info.get("decimals", 9),
                logo_uri=token_info.get("logoURI")
            )

        return None

    async def _fetch_token_info(self, address: str) -> Optional[dict]:
        """Fetch token info from Jupiter Token List API (FREE)"""
        try:
            async with httpx.AsyncClient() as client:
                # Jupiter's token API (FREE, official)
                response = await client.get(
                    f"https://tokens.jup.ag/token/{address}",
                    timeout=10.0
                )

                if response.status_code == 200:
                    return response.json()

                # Fallback: try Solana FM (FREE)
                response = await client.get(
                    f"https://api.solana.fm/v1/tokens/{address}",
                    timeout=10.0
                )

                if response.status_code == 200:
                    data = response.json()
                    if data.get("result"):
                        token_info = data["result"]
                        return {
                            "symbol": token_info.get("symbol"),
                            "name": token_info.get("name"),
                            "decimals": token_info.get("decimals", 9),
                            "logoURI": token_info.get("logo")
                        }

        except Exception as e:
            print(f"Error fetching token info for {address}: {e}")

        return None

    async def _cache_token(self, db: AsyncSession, address: str, token_info: dict) -> None:
        """Cache token info in database"""
        try:
            from src.solana.models import TokenCache

            result = await db.execute(
                select(TokenCache).where(TokenCache.address == address)
            )
            existing = result.scalar_one_or_none()

            if existing:
                existing.symbol = token_info.get("symbol")
                existing.name = token_info.get("name")
                existing.decimals = token_info.get("decimals", 9)
                existing.logo_uri = token_info.get("logoURI")
                existing.last_updated = datetime.now()
            else:
                new_cache = TokenCache(
                    address=address,
                    symbol=token_info.get("symbol"),
                    name=token_info.get("name"),
                    decimals=token_info.get("decimals", 9),
                    logo_uri=token_info.get("logoURI")
                )
                db.add(new_cache)

            await db.commit()
        except Exception as e:
            print(f"Error caching token {address}: {e}")


token_metadata_service = TokenMetadataService()

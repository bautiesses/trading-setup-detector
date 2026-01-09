from typing import List, Optional, Tuple
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, and_

from src.solana.models import SolanaWallet, SolanaTrade, TokenCache
from src.solana.schemas import SolanaWalletCreate
from src.solana.jupiter_parser import jupiter_parser, ParsedSwap
from src.solana.helius_client import helius_client
from src.solana.chart_client import solana_chart_client
from src.solana.token_metadata import token_metadata_service
from src.config import get_settings

settings = get_settings()

# Minimum USD value to track trades
MIN_TRADE_USD = 10000


class SolanaTradeService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ========== WEBHOOK PROCESSING ==========

    async def process_webhook_payload(self, payload: List[dict]) -> List[SolanaTrade]:
        """Process incoming Helius webhook payload"""
        created_trades = []

        # Parse Jupiter swaps
        swaps = jupiter_parser.parse_webhook_payload(payload)

        for swap in swaps:
            trade = await self._create_trade_from_swap(swap)
            if trade:
                created_trades.append(trade)

        return created_trades

    async def _create_trade_from_swap(self, swap: ParsedSwap) -> Optional[SolanaTrade]:
        """Create a trade record from a parsed swap"""
        # Check if already processed (idempotency)
        existing = await self.db.execute(
            select(SolanaTrade).where(SolanaTrade.tx_signature == swap.tx_signature)
        )
        if existing.scalar_one_or_none():
            return None

        # Find wallet by signer address
        wallet = await self._find_wallet_by_address(swap.signer)
        if not wallet:
            print(f"No wallet found for signer: {swap.signer}")
            return None

        # Get token metadata
        token_in_meta = await token_metadata_service.get_token_info(swap.token_in_address, self.db)
        token_out_meta = await token_metadata_service.get_token_info(swap.token_out_address, self.db)

        # Determine trade side
        side = jupiter_parser.determine_trade_side(
            swap.token_in_address,
            swap.token_out_address
        )

        # Stablecoin addresses (USDC, USDT) - amounts are already in USD
        STABLECOINS = {
            "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",  # USDC
            "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB",  # USDT
        }

        # Calculate USD values - use stablecoin amount directly if available
        if swap.token_in_address in STABLECOINS:
            token_in_usd = swap.token_in_amount  # Amount IS the USD value
            token_in_price = 1.0
        else:
            token_in_price = await solana_chart_client.get_current_token_price(swap.token_in_address)
            token_in_usd = swap.token_in_amount * (token_in_price or 0)

        if swap.token_out_address in STABLECOINS:
            token_out_usd = swap.token_out_amount  # Amount IS the USD value
            token_out_price = 1.0
        else:
            token_out_price = await solana_chart_client.get_current_token_price(swap.token_out_address)
            token_out_usd = swap.token_out_amount * (token_out_price or 0)

        # Use the higher USD value (whichever we can calculate)
        trade_usd_value = max(token_in_usd, token_out_usd)

        # Filter: only track trades >= MIN_TRADE_USD
        # Exception: always track SELLS if there's a matching open BUY (to calculate PnL)
        if trade_usd_value < MIN_TRADE_USD:
            if side == "sell":
                # Check if there's an unlinked BUY for this token
                sold_token = swap.token_in_address
                has_open_buy = await self._has_unlinked_buy(wallet.user_id, sold_token)
                if has_open_buy:
                    print(f"Trade below minimum but has matching buy, allowing sell")
                else:
                    print(f"Trade below minimum (${trade_usd_value:.2f} < ${MIN_TRADE_USD}), skipping")
                    return None
            else:
                print(f"Trade below minimum (${trade_usd_value:.2f} < ${MIN_TRADE_USD}), skipping")
                return None

        # Calculate price per token (price of the traded token in USD)
        # For BUY: we spend token_in to get token_out, so price = token_in_usd / token_out_amount
        # For SELL: we spend token_in to get token_out, so price = token_out_usd / token_in_amount
        if side == "buy" and swap.token_out_amount > 0:
            # Price per token bought = USD spent / tokens received
            price_per_token = token_in_usd / swap.token_out_amount if token_in_usd > 0 else (token_out_price or 0)
        elif side == "sell" and swap.token_in_amount > 0:
            # Price per token sold = USD received / tokens sold
            price_per_token = token_out_usd / swap.token_in_amount if token_out_usd > 0 else (token_in_price or 0)
        else:
            price_per_token = 0

        # Get SOL price for fee calculation
        sol_price = await solana_chart_client.get_sol_price()
        fee_usd = swap.fee_sol * (sol_price or 0)

        # Create trade
        trade = SolanaTrade(
            user_id=wallet.user_id,
            wallet_id=wallet.id,
            tx_signature=swap.tx_signature,
            slot=swap.slot,
            block_time=swap.block_time,
            side=side,
            token_in_address=swap.token_in_address,
            token_in_symbol=token_in_meta.symbol if token_in_meta else None,
            token_in_name=token_in_meta.name if token_in_meta else None,
            token_in_amount=swap.token_in_amount,
            token_in_decimals=swap.token_in_decimals,
            token_in_usd_value=token_in_usd,
            token_out_address=swap.token_out_address,
            token_out_symbol=token_out_meta.symbol if token_out_meta else None,
            token_out_name=token_out_meta.name if token_out_meta else None,
            token_out_amount=swap.token_out_amount,
            token_out_decimals=swap.token_out_decimals,
            token_out_usd_value=token_out_usd,
            price_per_token=price_per_token,
            price_usd=token_out_price if side == "buy" else token_in_price,
            fee_sol=swap.fee_sol,
            fee_usd=fee_usd,
            dex_name="Jupiter"
        )

        self.db.add(trade)
        await self.db.commit()
        await self.db.refresh(trade)

        # Generate chart in background
        traded_token = swap.token_out_address if side == "buy" else swap.token_in_address
        traded_symbol = (token_out_meta.symbol if side == "buy" and token_out_meta
                        else (token_in_meta.symbol if token_in_meta else "TOKEN"))

        try:
            chart_path = await solana_chart_client.generate_trade_chart(
                token_address=traded_token,
                token_symbol=traded_symbol,
                trade_time=swap.block_time,
                trade_price=trade.price_usd or 0,
                trade_side=side
            )

            if chart_path:
                trade.chart_image_url = chart_path
                await self.db.commit()
        except Exception as e:
            print(f"Error generating chart: {e}")

        # Try to auto-link trades (match sells with previous buys)
        if side == "sell":
            await self._try_auto_link_trade(trade)

        return trade

    async def _try_auto_link_trade(self, sell_trade: SolanaTrade) -> bool:
        """
        Try to automatically link a sell trade with a matching buy trade.
        Supports partial sells - multiple sells can link to the same buy.
        Matches by:
        - Same token (token sold = token bought)
        - Buy must be before sell
        - Buy must have remaining unsold quantity
        """
        # The token being sold is token_in for a sell trade
        sold_token = sell_trade.token_in_address
        sold_amount = sell_trade.token_in_amount

        # Find buy trades for the same token (before this sell)
        result = await self.db.execute(
            select(SolanaTrade).where(
                and_(
                    SolanaTrade.user_id == sell_trade.user_id,
                    SolanaTrade.side == "buy",
                    SolanaTrade.token_out_address == sold_token,  # Bought same token
                    SolanaTrade.block_time < sell_trade.block_time,  # Before this sell
                )
            ).order_by(SolanaTrade.block_time)  # Oldest first (FIFO)
        )
        potential_buys = list(result.scalars().all())

        if not potential_buys:
            return False

        # For each buy, calculate how much has already been sold
        for buy in potential_buys:
            bought_amount = buy.token_out_amount
            if bought_amount <= 0:
                continue

            # Get all sells already linked to this buy
            linked_sells_result = await self.db.execute(
                select(SolanaTrade).where(
                    SolanaTrade.linked_trade_id == buy.id
                )
            )
            linked_sells = list(linked_sells_result.scalars().all())

            # Calculate total already sold from this buy
            already_sold = sum(s.token_in_amount for s in linked_sells)
            remaining = bought_amount - already_sold

            # If there's remaining quantity, link this sell
            if remaining > 0.0001:  # Small tolerance for floating point
                # Calculate PnL based on proportion sold
                entry_usd = buy.token_in_usd_value or 0  # What we paid for the buy
                exit_usd = sell_trade.token_out_usd_value or 0  # What we received

                # Adjust entry cost for partial sell
                if bought_amount > 0:
                    ratio = min(sold_amount, remaining) / bought_amount
                    entry_usd = entry_usd * ratio

                pnl = exit_usd - entry_usd
                pnl_percent = (pnl / entry_usd * 100) if entry_usd > 0 else 0

                # Update sell trade with link and PnL
                sell_trade.linked_trade_id = buy.id
                sell_trade.pnl = pnl
                sell_trade.pnl_percent = pnl_percent

                await self.db.commit()
                print(f"Auto-linked: Buy #{buy.id} -> Sell #{sell_trade.id}, PnL: ${pnl:.2f} ({pnl_percent:.1f}%)")
                return True

        return False

    async def _has_unlinked_buy(self, user_id: int, token_address: str) -> bool:
        """Check if there's a BUY with remaining quantity for this token"""
        # Get all buys for this token
        result = await self.db.execute(
            select(SolanaTrade).where(
                and_(
                    SolanaTrade.user_id == user_id,
                    SolanaTrade.side == "buy",
                    SolanaTrade.token_out_address == token_address,
                )
            )
        )
        buys = list(result.scalars().all())

        for buy in buys:
            bought_amount = buy.token_out_amount
            if bought_amount <= 0:
                continue

            # Get all sells linked to this buy
            linked_result = await self.db.execute(
                select(SolanaTrade).where(SolanaTrade.linked_trade_id == buy.id)
            )
            linked_sells = list(linked_result.scalars().all())

            already_sold = sum(s.token_in_amount for s in linked_sells)
            remaining = bought_amount - already_sold

            if remaining > 0.0001:
                return True

        return False

    async def _find_wallet_by_address(self, address: Optional[str]) -> Optional[SolanaWallet]:
        """Find wallet by address"""
        if not address:
            # Return first active wallet as fallback
            result = await self.db.execute(
                select(SolanaWallet).where(SolanaWallet.is_active == True)
            )
            return result.scalars().first()

        result = await self.db.execute(
            select(SolanaWallet).where(
                SolanaWallet.address == address,
                SolanaWallet.is_active == True
            )
        )
        return result.scalar_one_or_none()

    # ========== WALLET MANAGEMENT ==========

    async def add_wallet(self, user_id: int, data: SolanaWalletCreate) -> SolanaWallet:
        """Add a new wallet and register Helius webhook"""
        # Check if wallet already exists
        existing = await self.db.execute(
            select(SolanaWallet).where(SolanaWallet.address == data.address)
        )
        if existing.scalar_one_or_none():
            raise ValueError("Wallet already registered")

        # Create wallet
        wallet = SolanaWallet(
            user_id=user_id,
            address=data.address,
            label=data.label
        )
        self.db.add(wallet)
        await self.db.commit()
        await self.db.refresh(wallet)

        # Register Helius webhook
        if settings.helius_api_key:
            callback_url = f"{settings.app_base_url}/api/v1/solana/webhook/helius"
            try:
                webhook_result = await helius_client.create_webhook(
                    wallet_address=data.address,
                    callback_url=callback_url
                )
                wallet.helius_webhook_id = webhook_result.get("webhookID")
                await self.db.commit()
            except Exception as e:
                print(f"Failed to create Helius webhook: {e}")

        return wallet

    async def get_wallets(self, user_id: int) -> List[SolanaWallet]:
        """Get all wallets for a user"""
        result = await self.db.execute(
            select(SolanaWallet).where(SolanaWallet.user_id == user_id)
        )
        return list(result.scalars().all())

    async def remove_wallet(self, user_id: int, wallet_id: int) -> bool:
        """Remove a wallet and delete Helius webhook"""
        result = await self.db.execute(
            select(SolanaWallet).where(
                SolanaWallet.id == wallet_id,
                SolanaWallet.user_id == user_id
            )
        )
        wallet = result.scalar_one_or_none()
        if not wallet:
            return False

        # Delete Helius webhook
        if wallet.helius_webhook_id:
            try:
                await helius_client.delete_webhook(wallet.helius_webhook_id)
            except Exception as e:
                print(f"Failed to delete Helius webhook: {e}")

        await self.db.delete(wallet)
        await self.db.commit()
        return True

    # ========== TRADES ==========

    async def get_trades(
        self,
        user_id: int,
        wallet_id: Optional[int] = None,
        side: Optional[str] = None,
        skip: int = 0,
        limit: int = 50
    ) -> Tuple[List[SolanaTrade], int]:
        """Get trades with filters"""
        query = select(SolanaTrade).where(SolanaTrade.user_id == user_id)

        if wallet_id:
            query = query.where(SolanaTrade.wallet_id == wallet_id)
        if side:
            query = query.where(SolanaTrade.side == side)

        # Count total
        count_query = select(func.count()).select_from(
            query.subquery()
        )
        count_result = await self.db.execute(count_query)
        total = count_result.scalar() or 0

        # Fetch trades
        query = query.order_by(desc(SolanaTrade.block_time)).offset(skip).limit(limit)
        result = await self.db.execute(query)
        trades = list(result.scalars().all())

        return trades, total

    async def get_trade(self, user_id: int, trade_id: int) -> Optional[SolanaTrade]:
        """Get a single trade"""
        result = await self.db.execute(
            select(SolanaTrade).where(
                SolanaTrade.id == trade_id,
                SolanaTrade.user_id == user_id
            )
        )
        return result.scalar_one_or_none()

    async def link_trades(
        self,
        user_id: int,
        entry_trade_id: int,
        exit_trade_id: int
    ) -> bool:
        """Link an entry trade with its exit for PnL calculation"""
        entry = await self.get_trade(user_id, entry_trade_id)
        exit_trade = await self.get_trade(user_id, exit_trade_id)

        if not entry or not exit_trade:
            return False

        # Validate: entry should be buy, exit should be sell
        if entry.side != "buy" or exit_trade.side != "sell":
            return False

        # Calculate PnL based on USD values
        if entry.token_in_usd_value and exit_trade.token_out_usd_value:
            pnl = exit_trade.token_out_usd_value - entry.token_in_usd_value
            pnl_percent = (pnl / entry.token_in_usd_value) * 100 if entry.token_in_usd_value > 0 else 0

            exit_trade.linked_trade_id = entry.id
            exit_trade.pnl = pnl
            exit_trade.pnl_percent = pnl_percent

            await self.db.commit()
            return True

        return False

    async def update_notes(
        self,
        user_id: int,
        trade_id: int,
        notes: str
    ) -> Optional[SolanaTrade]:
        """Update trade notes"""
        trade = await self.get_trade(user_id, trade_id)
        if not trade:
            return None

        trade.notes = notes
        await self.db.commit()
        await self.db.refresh(trade)
        return trade

    async def get_stats(self, user_id: int) -> dict:
        """Get trading statistics"""
        result = await self.db.execute(
            select(SolanaTrade).where(SolanaTrade.user_id == user_id)
        )
        trades = list(result.scalars().all())

        if not trades:
            return {
                "total_trades": 0,
                "buy_trades": 0,
                "sell_trades": 0,
                "total_volume_usd": 0,
                "total_fees_sol": 0,
                "linked_pnl": 0,
                "winning_trades": 0,
                "losing_trades": 0
            }

        buys = [t for t in trades if t.side == "buy"]
        sells = [t for t in trades if t.side == "sell"]
        linked = [t for t in trades if t.pnl is not None]
        winning = [t for t in linked if t.pnl > 0]
        losing = [t for t in linked if t.pnl < 0]

        total_volume = sum(t.token_in_usd_value or 0 for t in trades)
        total_fees = sum(t.fee_sol or 0 for t in trades)
        total_pnl = sum(t.pnl or 0 for t in linked)

        return {
            "total_trades": len(trades),
            "buy_trades": len(buys),
            "sell_trades": len(sells),
            "total_volume_usd": round(total_volume, 2),
            "total_fees_sol": round(total_fees, 6),
            "linked_pnl": round(total_pnl, 2),
            "winning_trades": len(winning),
            "losing_trades": len(losing)
        }

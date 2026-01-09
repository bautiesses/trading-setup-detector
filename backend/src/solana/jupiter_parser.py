from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime


@dataclass
class ParsedSwap:
    """Parsed Jupiter swap data"""
    tx_signature: str
    slot: int
    block_time: datetime

    # Swap details
    token_in_address: str
    token_in_amount: float
    token_in_decimals: int

    token_out_address: str
    token_out_amount: float
    token_out_decimals: int

    # Fees
    fee_sol: float
    platform_fee: Optional[float] = None

    # Route info
    route: Optional[List[str]] = None

    # Signer wallet
    signer: Optional[str] = None

    # Raw data for debugging
    raw_data: Optional[Dict[str, Any]] = None


class JupiterParser:
    """Parse Jupiter swap transactions from Helius webhook data"""

    # Known Jupiter program IDs
    JUPITER_V6_PROGRAM = "JUP6LkbZbjS1jKKwapdHNy74zcZ3tLUZoi5QNyVTaV4"
    JUPITER_AGGREGATOR_V6 = "JUP4Fb2cqiRUcaTHdrPC8h2gNsA2ETXiPDD33WcGuJB"

    # Common token addresses
    SOL_MINT = "So11111111111111111111111111111111111111112"
    USDC_MINT = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
    USDT_MINT = "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB"

    STABLECOINS = {USDC_MINT, USDT_MINT}
    QUOTE_TOKENS = {SOL_MINT, USDC_MINT, USDT_MINT}

    def parse_webhook_payload(self, payload: List[Dict[str, Any]]) -> List[ParsedSwap]:
        """Parse Helius webhook payload containing swap transactions"""
        swaps = []

        for tx in payload:
            if self._is_jupiter_swap(tx):
                parsed = self._parse_swap_transaction(tx)
                if parsed:
                    swaps.append(parsed)

        return swaps

    def _is_jupiter_swap(self, tx: Dict[str, Any]) -> bool:
        """Check if transaction is a Jupiter swap"""
        # Check transaction type from Helius enhanced data
        if tx.get("type") == "SWAP":
            return True

        # Check if source is Jupiter (even if type is UNKNOWN)
        if tx.get("source") == "JUPITER":
            return True

        # Check for Jupiter program in account keys or instructions
        account_keys = tx.get("accountData", [])
        for account in account_keys:
            if account.get("account") in [self.JUPITER_V6_PROGRAM, self.JUPITER_AGGREGATOR_V6]:
                return True

        return False

    def _parse_swap_transaction(self, tx: Dict[str, Any]) -> Optional[ParsedSwap]:
        """Parse a single swap transaction"""
        try:
            # Extract token transfers from Helius enhanced format
            token_transfers = tx.get("tokenTransfers", [])

            if len(token_transfers) < 2:
                # Try to extract from events if tokenTransfers is empty
                events = tx.get("events", {})
                swap_event = events.get("swap", {})
                if swap_event:
                    return self._parse_from_swap_event(tx, swap_event)
                return None

            # Find user's transfers (fromUserAccount or toUserAccount matching signer)
            signer = self._get_signer(tx)

            # Aggregate all transfers by mint for the user
            # Token IN: sum of all tokens the user sent (fromUserAccount == signer)
            # Token OUT: sum of all tokens the user received (toUserAccount == signer)
            tokens_sent: Dict[str, float] = {}
            tokens_received: Dict[str, float] = {}

            for transfer in token_transfers:
                mint = transfer.get("mint", "")
                amount = float(transfer.get("tokenAmount", 0))

                if transfer.get("fromUserAccount") == signer:
                    tokens_sent[mint] = tokens_sent.get(mint, 0) + amount
                if transfer.get("toUserAccount") == signer:
                    tokens_received[mint] = tokens_received.get(mint, 0) + amount

            # Determine token_in (what user spent most of, excluding what they also received)
            # and token_out (what user received most of, excluding what they also sent)
            net_sent = {}
            net_received = {}

            for mint, amt in tokens_sent.items():
                net = amt - tokens_received.get(mint, 0)
                if net > 0:
                    net_sent[mint] = net

            for mint, amt in tokens_received.items():
                net = amt - tokens_sent.get(mint, 0)
                if net > 0:
                    net_received[mint] = net

            if not net_sent or not net_received:
                # Fallback to first/last transfer
                token_in = token_transfers[0]
                token_out = token_transfers[-1]
                token_in_address = token_in.get("mint", "")
                token_in_amount = float(token_in.get("tokenAmount", 0))
                token_out_address = token_out.get("mint", "")
                token_out_amount = float(token_out.get("tokenAmount", 0))
            else:
                # Get the main tokens (highest amounts)
                token_in_address = max(net_sent, key=net_sent.get)
                token_in_amount = net_sent[token_in_address]
                token_out_address = max(net_received, key=net_received.get)
                token_out_amount = net_received[token_out_address]

            # Parse timestamp
            timestamp = tx.get("timestamp", 0)
            if isinstance(timestamp, int):
                block_time = datetime.fromtimestamp(timestamp)
            else:
                block_time = datetime.now()

            return ParsedSwap(
                tx_signature=tx.get("signature", ""),
                slot=tx.get("slot", 0),
                block_time=block_time,
                token_in_address=token_in_address,
                token_in_amount=token_in_amount,
                token_in_decimals=9,  # Default, will use metadata later
                token_out_address=token_out_address,
                token_out_amount=token_out_amount,
                token_out_decimals=9,
                fee_sol=tx.get("fee", 0) / 1e9,
                signer=signer,
                raw_data=tx
            )
        except Exception as e:
            print(f"Error parsing swap: {e}")
            return None

    def _parse_from_swap_event(self, tx: Dict[str, Any], swap_event: Dict[str, Any]) -> Optional[ParsedSwap]:
        """Parse swap from Helius swap event format"""
        try:
            timestamp = tx.get("timestamp", 0)
            if isinstance(timestamp, int):
                block_time = datetime.fromtimestamp(timestamp)
            else:
                block_time = datetime.now()

            return ParsedSwap(
                tx_signature=tx.get("signature", ""),
                slot=tx.get("slot", 0),
                block_time=block_time,
                token_in_address=swap_event.get("tokenInputs", [{}])[0].get("mint", ""),
                token_in_amount=float(swap_event.get("tokenInputs", [{}])[0].get("tokenAmount", 0)),
                token_in_decimals=swap_event.get("tokenInputs", [{}])[0].get("decimals", 9),
                token_out_address=swap_event.get("tokenOutputs", [{}])[0].get("mint", ""),
                token_out_amount=float(swap_event.get("tokenOutputs", [{}])[0].get("tokenAmount", 0)),
                token_out_decimals=swap_event.get("tokenOutputs", [{}])[0].get("decimals", 9),
                fee_sol=tx.get("fee", 0) / 1e9,
                signer=self._get_signer(tx),
                raw_data=tx
            )
        except Exception:
            return None

    def _get_signer(self, tx: Dict[str, Any]) -> Optional[str]:
        """Extract the signer wallet address from transaction"""
        # Try feePayer first
        fee_payer = tx.get("feePayer")
        if fee_payer:
            return fee_payer

        # Try from account data
        account_data = tx.get("accountData", [])
        for account in account_data:
            if account.get("nativeBalanceChange", 0) < 0:
                return account.get("account")

        return None

    def determine_trade_side(
        self,
        token_in_address: str,
        token_out_address: str
    ) -> str:
        """
        Determine if this is a BUY or SELL.

        Logic:
        - If token_in is a stablecoin and token_out is SOL or another token -> BUY
        - If token_in is SOL or another token and token_out is stablecoin -> SELL
        - SOL -> Stablecoin = SELL (you're selling SOL)
        - Stablecoin -> SOL = BUY (you're buying SOL)
        """
        # Stablecoins take priority - they represent USD
        token_in_is_stable = token_in_address in self.STABLECOINS
        token_out_is_stable = token_out_address in self.STABLECOINS

        if token_in_is_stable and not token_out_is_stable:
            # Spending stablecoin to get something = BUY
            return "buy"
        elif not token_in_is_stable and token_out_is_stable:
            # Getting stablecoin for something = SELL
            return "sell"
        elif token_in_address == self.SOL_MINT and token_out_address not in self.QUOTE_TOKENS:
            # SOL -> non-quote token = BUY (buying with SOL)
            return "buy"
        elif token_in_address not in self.QUOTE_TOKENS and token_out_address == self.SOL_MINT:
            # Non-quote token -> SOL = SELL (selling for SOL)
            return "sell"
        else:
            # Token to token swap - consider it a buy of token_out
            return "buy"


jupiter_parser = JupiterParser()

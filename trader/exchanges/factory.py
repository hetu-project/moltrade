"""
Exchange client factory.

Keeps the bot decoupled from a specific venue so we can add new
adapters (e.g., polymarket, other DEXes) without touching core logic.
"""

from typing import Any, Dict

from hyperliquid_api import HyperliquidClient


def get_exchange_client(config: Dict[str, Any], *, test_mode: bool = False):
    trading_cfg = config.get("trading", {})
    venue = trading_cfg.get("exchange", "hyperliquid").lower()

    if venue == "hyperliquid":
        return HyperliquidClient(
            wallet_address=config["wallet_address"],
            private_key=config["private_key"],
            testnet=test_mode,
        )

    raise ValueError(f"Unsupported exchange '{venue}'. Add an adapter in exchanges.factory.")

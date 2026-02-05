"""
Signal broadcasting helpers for the trading bot.

Responsibilities:
- Initialize the global Nostr publisher
- Encrypt payloads with the shared platform key
- Publish trade signals, copy-trade intents, and execution reports
"""

import logging
from typing import Any, Dict, Optional

from dataclasses import asdict
import requests

from nostr.crypto import Nip04Crypto
from nostr.events import (
    TradeSignalEvent,
    CopyTradeIntentEvent,
    ExecutionReportEvent,
    TradeSignalPayload,
    CopyTradeIntentPayload,
    ExecutionReportPayload,
)
from nostr.publisher import init_global_publisher, get_publisher

logger = logging.getLogger(__name__)


class SignalBroadcaster:
    """Encrypt and publish trading signals to Nostr."""

    def __init__(self, config: Dict[str, Any]):
        nostr_cfg = config.get("nostr", {})
        self.enabled = bool(nostr_cfg.get("nsec"))
        self.shared_key = nostr_cfg.get("platform_shared_key")
        self.sid = nostr_cfg.get("sid", "bot-main")
        self.role = nostr_cfg.get("role", "bot")
        self.relays = nostr_cfg.get("relays", [])
        self.relayer_api = nostr_cfg.get("relayer_api")
        self.settlement_token = nostr_cfg.get("settlement_token")

        if not self.enabled:
            logger.info("Nostr broadcasting disabled: missing nsec")
            self.publisher = None
            return

        if not self.shared_key:
            logger.info("Nostr broadcasting disabled: missing platform_shared_key")
            self.publisher = None
            self.enabled = False
            return

        init_global_publisher(
            nostr_cfg["nsec"],
            self.relays,
            sid=self.sid,
            role=self.role,
            listen_kinds=nostr_cfg.get("listen_kinds"),
        )
        self.publisher = get_publisher()
        if self.publisher is None:
            logger.warning("Nostr publisher not initialized; broadcasting disabled")
            self.enabled = False
        else:
            logger.info(
                "Nostr broadcaster ready (relays=%d, sid=%s, role=%s)",
                len(self.relays),
                self.sid,
                self.role,
            )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _publish(self, event) -> bool:
        if not self.enabled or self.publisher is None:
            return False
        try:
            self.publisher.publish_event(event)
            return True
        except Exception as exc:
            logger.warning("Failed to publish Nostr event: %s", exc)
            return False

    def _encrypt(self, payload: Dict[str, Any]) -> Optional[str]:
        try:
            return Nip04Crypto.encrypt(payload, self.shared_key)
        except Exception as exc:
            logger.warning("Failed to encrypt payload: %s", exc)
            return None

    # ------------------------------------------------------------------
    # Public APIs
    # ------------------------------------------------------------------
    def send_trade_signal(
        self,
        *,
        symbol: str,
        signal: Dict[str, Any],
        strategy: str,
        test_mode: bool,
        account: Optional[str],
    ) -> bool:
        if not self.enabled:
            return False

        payload = TradeSignalPayload(
            symbol=symbol,
            signal=signal.get("signal", "hold"),
            strength=float(signal.get("strength", 0)),
            price=float(signal.get("price", 0)),
            size=float(signal.get("size", 0)),
            strategy=strategy,
            test_mode=test_mode,
            account=account,
            indicators=signal.get("indicators"),
            note=signal.get("note"),
        )
        encrypted = self._encrypt(asdict(payload))
        if not encrypted:
            return False

        event = TradeSignalEvent.build(
            sid=self.sid,
            encrypted_content=encrypted,
            symbol=symbol,
            strategy=strategy,
            signal=payload.signal,
            test_mode=test_mode,
        )
        return self._publish(event)

    def send_copytrade_intent(
        self,
        *,
        follower_pubkey: str,
        symbol: Optional[str],
        max_slippage_pct: Optional[float],
        size_pct: Optional[float],
        note: Optional[str] = None,
    ) -> bool:
        if not self.enabled:
            return False

        payload = CopyTradeIntentPayload(
            follower_pubkey=follower_pubkey,
            symbol=symbol,
            max_slippage_pct=max_slippage_pct,
            size_pct=size_pct,
            note=note,
        )
        encrypted = self._encrypt(asdict(payload))
        if not encrypted:
            return False

        event = CopyTradeIntentEvent.build(
            sid=self.sid,
            encrypted_content=encrypted,
            follower_pubkey=follower_pubkey,
            symbol=symbol,
        )
        return self._publish(event)

    def send_execution_report(
        self,
        *,
        symbol: str,
        side: str,
        size: float,
        price: float,
        status: str,
        tx_hash: Optional[str],
        pnl: Optional[float],
        pnl_percent: Optional[float],
        test_mode: bool,
        note: Optional[str] = None,
    ) -> bool:
        if not self.enabled:
            return False

        payload = ExecutionReportPayload(
            symbol=symbol,
            side=side,
            size=size,
            price=price,
            status=status,
            tx_hash=tx_hash,
            pnl=pnl,
            pnl_percent=pnl_percent,
            test_mode=test_mode,
            note=note,
        )
        encrypted = self._encrypt(asdict(payload))
        if not encrypted:
            return False

        event = ExecutionReportEvent.build(
            sid=self.sid,
            encrypted_content=encrypted,
            symbol=symbol,
            side=side,
            status=status,
            test_mode=test_mode,
        )
        published = self._publish(event)

        if tx_hash and self.relayer_api and self.publisher is not None:
            self._report_trade_tx(
                tx_hash=tx_hash,
                symbol=symbol,
                side=side,
                size=size,
                price=price,
                role=self.role,
            )

        return published

    def _report_trade_tx(
        self,
        *,
        tx_hash: str,
        symbol: str,
        side: str,
        size: float,
        price: float,
        role: str,
        follower_pubkey: Optional[str] = None,
    ) -> None:
        url = f"{self.relayer_api.rstrip('/')}/api/trades/record"
        headers = {"Content-Type": "application/json"}
        if self.settlement_token:
            headers["X-Settlement-Token"] = self.settlement_token

        payload = {
            "bot_pubkey": getattr(self.publisher, "public_key", None),
            "follower_pubkey": follower_pubkey,
            "role": role,
            "symbol": symbol,
            "side": side,
            "size": size,
            "price": price,
            "tx_hash": tx_hash,
        }

        try:
            resp = requests.post(url, json=payload, headers=headers, timeout=5)
            if resp.status_code >= 300:
                logger.warning(
                    "Failed to report trade tx (status=%s): %s", resp.status_code, resp.text
                )
        except Exception as exc:
            logger.warning("Failed to report trade tx to relayer: %s", exc)


__all__ = ["SignalBroadcaster"]

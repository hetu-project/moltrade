"""
Copy-trade listener that subscribes to Nostr trade signals and forwards
accepted signals to a callback after decrypting.
"""

import threading
import logging
from typing import Any, Callable, Dict, List, Optional

from nostr import init_global_publisher, get_publisher
from nostr.events import TRADE_SIGNAL_KIND
from nostr.crypto import GroupV1Crypto

logger = logging.getLogger(__name__)


class CopyTradeListener:
    def __init__(
        self,
        *,
        nsec: str,
        relays: List[str],
        shared_key_hex: str,
        allowed_pubkeys: Optional[List[str]] = None,
        listen_kinds: Optional[List[int]] = None,
        on_signal: Optional[Callable[[Dict[str, Any], str], None]] = None,
    ) -> None:
        self._nsec = nsec
        self._relays = relays or []
        self._shared_key_hex = shared_key_hex
        self._allowed_pubkeys = set(allowed_pubkeys or [])
        self._listen_kinds = listen_kinds or [TRADE_SIGNAL_KIND]
        self._on_signal = on_signal
        self._thread: Optional[threading.Thread] = None
        self._stop = threading.Event()

    def start(self) -> None:
        if not self._nsec or not self._relays:
            logger.warning("CopyTradeListener disabled: missing nsec or relays")
            return

        init_global_publisher(self._nsec, relays=self._relays, listen_kinds=self._listen_kinds)
        pub = get_publisher()
        if pub is None:
            logger.warning("CopyTradeListener failed to init publisher")
            return

        self._thread = threading.Thread(target=self._loop, args=(pub,), name="copytrade-listener", daemon=True)
        self._thread.start()
        logger.info("CopyTradeListener started (kinds=%s relays=%d)", self._listen_kinds, len(self._relays))

    def stop(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=1.5)

    def _loop(self, pub) -> None:
        chan = pub.get_event_channel()
        while not self._stop.is_set():
            try:
                ev = chan.get(timeout=1.0)
            except Exception:
                continue

            if ev.kind not in self._listen_kinds:
                continue

            sender = getattr(ev, "pubkey", "")
            if self._allowed_pubkeys and sender not in self._allowed_pubkeys:
                logger.debug("Skip signal from %s (not allowed)", sender)
                continue

            try:
                payload = GroupV1Crypto.decrypt(ev.content, self._shared_key_hex)
            except Exception as exc:
                logger.debug("Failed to decrypt signal: %s", exc)
                continue

            if not isinstance(payload, dict):
                logger.debug("Ignoring non-dict payload")
                continue

            if self._on_signal:
                try:
                    self._on_signal(payload, sender)
                except Exception as exc:
                    logger.warning("Copy-trade callback error: %s", exc)


__all__ = ["CopyTradeListener"]

"""
Nostr integration.

Trader components should depend only on the small helper
APIs in `publisher.py` to avoid pulling Nostr details into hot paths.
"""

from .publisher import (  # noqa: F401
    init_global_publisher,
    get_publisher,
)



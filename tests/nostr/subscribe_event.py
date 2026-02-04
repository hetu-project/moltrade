import sys
from pathlib import Path
import queue
from datetime import datetime
import logging

# Add trader directory to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "trader"))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%H:%M:%S'
)

from nostr import init_global_publisher, get_publisher
from nostr.events import TRADE_SIGNAL_KIND, COPYTRADE_INTENT_KIND, EXECUTION_REPORT_KIND # type: ignore
from pynostr.key import PrivateKey

listen_kinds_list = [TRADE_SIGNAL_KIND, COPYTRADE_INTENT_KIND, EXECUTION_REPORT_KIND]

pk = PrivateKey()
privkey_nsec = pk.bech32()  # Random test key; replace with your own

relays = ["wss://nostr.parallel.hetu.org:8443"]
print(f"\nInitializing subscriber...")
print(f"Public key: {pk.public_key.hex()}")
print(f"Subscribe since: {int(__import__('time').time())} ({datetime.now().strftime('%H:%M:%S')})")
print()

init_global_publisher(privkey_nsec, relays=relays, listen_kinds=listen_kinds_list)
pub = get_publisher()
if pub is None:
    print("Failed to initialize Nostr publisher")
    sys.exit(1)

print(f"Listening for Nostr events with kinds: {listen_kinds_list}")
print(f"Relays: {relays}")
print("Press Ctrl+C to exit\n")
print("Waiting for events...")

event_channel = pub.get_event_channel()
heart_beat_counter = 0
while True:
    try:
        ev = event_channel.get(timeout=5)
        event_time = datetime.fromtimestamp(ev.created_at).strftime('%Y-%m-%d %H:%M:%S')
        print(f"\n{'='*60}")
        print(f"✓ RECEIVED EVENT")
        print(f"{'='*60}")
        print(f"Kind: {ev.kind}")
        print(f"ID: {ev.id}")
        print(f"From: {getattr(ev, 'pubkey', '')}")
        print(f"Created at: {event_time} (timestamp: {ev.created_at})")
        content_display = ev.content[:200] + "..." if len(ev.content) > 200 else ev.content
        print(f"Content: {content_display}")
        print(f"Tags: {ev.tags}")
        print(f"{'='*60}\n")
    except queue.Empty:
        heart_beat_counter += 1
        if heart_beat_counter % 6 == 0:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Still listening... (no events yet)")
        continue
    except KeyboardInterrupt:
        print("\nShutting down...")
        break
# Strategy Integration Guide

This bot loads strategies from `trader/strategies.py`. To plug in your own strategy, follow the steps below.

## 1) Create your strategy class

- Inherit from `BaseStrategy` and implement `analyze(self, df: pd.DataFrame) -> dict`.
- The returned dict **must** contain: `signal` (`buy` | `sell` | `hold`), `price` (float), `size` (0-1 allocation), and `strength` (0-1). Optional: `indicators`, `note`.
- Respect risk controls: call `should_trade()` before emitting a non-hold signal, or let the bot handle it.

```python
from strategies import BaseStrategy
import pandas as pd

class MyAwesomeStrategy(BaseStrategy):
    def __init__(self, config):
        super().__init__(config)
        self.name = "my_awesome"
        self.params = config.get("strategies", {}).get(self.name, {})

    def analyze(self, df: pd.DataFrame) -> dict:
        if len(df) < 50:
            return {"signal": "hold", "strength": 0}

        # Your logic here
        price = float(df["close"].iloc[-1])
        return {
            "signal": "buy",  # or "sell" / "hold"
            "strength": 0.5,
            "price": price,
            "size": self.params.get("position_size", 0.1),
            "indicators": {"note": "custom logic"},
        }
```

## 2) Register the strategy

Add it to the map in `get_strategy` inside `trader/strategies.py`:

```python
from .my_awesome_strategy import MyAwesomeStrategy

strategies = {
    # ...existing
    "my_awesome": MyAwesomeStrategy,
}
```

## 3) Wire config

- Add your params under `strategies.my_awesome` in `config.json`.
- Example:

```json
{
  "trading": {
    "default_strategy": "my_awesome"
  },
  "strategies": {
    "my_awesome": {
      "position_size": 0.2
    }
  }
}
```

## 4) Keep outputs compatible

- `signal` strings should stay lowercase (`buy`, `sell`, `hold`).
- `size` is a fraction of account balance; the bot converts it to quantity using current price and balance.
- Include `price` even if you intend to place market orders (the bot uses it for sizing and logging).

## 5) Optional extras

- Populate `indicators` to surface debugging info in notifications or Nostr payloads.
- Include `note` for free-form context; it will travel with the signal payload.

## 6) Testing tips

- Run the bot in `--test` mode first to verify sizing and risk controls.
- Use small `strength` and `size` while validating logic.
- Watch `trading_bot.log` for emitted signals and decisions.

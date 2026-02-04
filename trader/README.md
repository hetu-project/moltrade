# Hyperliquid Trading Bot

## Features

- Supports multiple trading strategies (mean reversion, momentum, grid)
- Risk management (stop-loss, position sizing)
- Real-time market data monitoring
- Trade logging
- Test mode support
- 📱 **Telegram Real-Time Notifications** (New!)

## Install Dependencies

```bash
cd strategy
pip install -r requirements.txt
```

## Configuration

Copy `config.example.json` to `config.json` and fill in your API keys:

```json
{
  "wallet_address": "your_wallet_address",
  "private_key": "your_private_key"
}
```

### Configure Telegram Notifications (Optional)

```bash
python3 telegram_setup.py
```

Follow the prompts to configure automatically. For detailed instructions, see [TELEGRAM_SETUP.md](TELEGRAM_SETUP.md).

## Run

```bash
# Test mode (no real trades)
python main.py --test

# Live trading
python main.py --strategy momentum --symbol HYPE
```

## Strategy Descriptions

### 1. Mean Reversion Strategy (mean_reversion)

- Based on Bollinger Bands
- Buy when the price touches the lower band, sell when it touches the upper band
- Suitable for range-bound markets

### 2. Momentum Strategy (momentum)

- Uses RSI and MACD indicators
- Buy when oversold, sell when overbought
- Suitable for trending markets

### 3. Grid Trading Strategy (grid)

- Sets multiple buy and sell levels within a price range
- Buy low, sell high, and earn the spread
- Suitable for sideways markets

## Risk Warning

⚠️ Cryptocurrency trading carries risks and may result in financial loss. Please use cautiously and test with small amounts first.

Quick Start Guide

1️⃣ Configure the Bot
cd strategy

# Copy the configuration file

cp config.example.json config.json

# Edit the configuration (fill in your Hyperliquid wallet address and private key)

nano config.json

Important Configuration Items:

• wallet_address: Your wallet address
• private_key: Your private key (⚠️ Keep it safe)
• position_size: The percentage of funds used per trade (default 10%)
• stop_loss_percent: Stop-loss percentage (default 2%)
• take_profit_percent: Take-profit percentage (default 5%)

2️⃣ Test the Strategy (Recommended First Step)

# Use the quick start script

./start.sh

# Choose option 1 (test mode) or 2 (backtest mode)

# Or run backtest directly

python3 backtest.py

3️⃣ Run Live Trading

# Test mode (no real trades, simulation only)

python3 main.py --test --strategy momentum --symbol HYPE

# Live trading (⚠️ Real funds)

python3 main.py --strategy momentum --symbol HYPE --interval 60

3. api_key and api_secret

• Hyperliquid does not actually use these! ❌
• Many centralized exchanges (e.g., Binance, OKX) use API Key/Secret
• Hyperliquid is decentralized and only requires a wallet address and private key

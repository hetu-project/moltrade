#!/usr/bin/env python3
"""
Testnet Trading Strategy - Relaxed Conditions for Testing
"""
import pandas as pd
import numpy as np
import time
from typing import Dict

class TestStrategy:
    """Test Strategy - Lower thresholds to trigger trades more easily"""

    def __init__(self, config: Dict):
        self.name = "test"
        self.config = config
        self.last_trade_time = 0
        self.trade_count = 0

        # Test parameters - More relaxed conditions
        self.rsi_oversold = 35      # Lowered to 35 for earlier bottom-fishing
        self.rsi_overbought = 65    # Originally 60
        self.adx_threshold = 20     # Increased to 20 to ensure a trend exists
        self.signal_threshold = 0.5  # Originally 0.5
        self.required_conditions = 2  # Lowered to 2/5 to allow trades!

    def should_trade(self) -> bool:
        """Check if trading is allowed (risk control)"""
        cooldown = self.config.get('risk_management', {}).get('cool_down_seconds', 300)
        if time.time() - self.last_trade_time < cooldown:
            return False

        max_trades = self.config.get('risk_management', {}).get('max_trades_per_day', 8)
        if self.trade_count >= max_trades:
            return False

        return True

    def calculate_rsi(self, prices: pd.Series, period: int = 14) -> float:
        """Calculate RSI"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi.iloc[-1]

    def calculate_macd(self, prices: pd.Series) -> tuple:
        """Calculate MACD"""
        exp1 = prices.ewm(span=12, adjust=False).mean()
        exp2 = prices.ewm(span=26, adjust=False).mean()
        macd = exp1 - exp2
        signal = macd.ewm(span=9, adjust=False).mean()
        return macd.iloc[-1], signal.iloc[-1], macd.iloc[-2], signal.iloc[-2]

    def calculate_adx(self, df: pd.DataFrame, period: int = 14) -> tuple:
        """Calculate ADX"""
        high = df['high']
        low = df['low']
        close = df['close']

        plus_dm = high.diff()
        minus_dm = -low.diff()
        plus_dm[plus_dm < 0] = 0
        minus_dm[minus_dm < 0] = 0

        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()

        plus_di = 100 * (plus_dm.rolling(window=period).mean() / atr)
        minus_di = 100 * (minus_dm.rolling(window=period).mean() / atr)

        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
        adx = dx.rolling(window=period).mean()

        return adx.iloc[-1], plus_di.iloc[-1], minus_di.iloc[-1]

    def calculate_ema(self, prices: pd.Series, period: int) -> float:
        """Calculate EMA"""
        return prices.ewm(span=period, adjust=False).mean().iloc[-1]

    def calculate_bollinger_bands(self, prices: pd.Series, period: int = 20) -> tuple:
        """Calculate Bollinger Bands"""
        sma = prices.rolling(window=period).mean()
        std = prices.rolling(window=period).std()
        upper = sma + (std * 2)
        middle = sma
        lower = sma - (std * 2)
        return upper.iloc[-1], middle.iloc[-1], lower.iloc[-1]

    def analyze(self, df: pd.DataFrame) -> Dict:
        """Analyze the market and generate trading signals"""
        if len(df) < 100:
            return {'signal': 'hold', 'strength': 0}

        close = df['close']
        current_price = close.iloc[-1]

        # Calculate indicators
        rsi = self.calculate_rsi(close)
        macd, signal, prev_macd, prev_signal = self.calculate_macd(close)
        adx, plus_di, minus_di = self.calculate_adx(df)

        ema_short = self.calculate_ema(close, 10)
        ema_long = self.calculate_ema(close, 50)

        bb_upper, bb_middle, bb_lower = self.calculate_bollinger_bands(close)
        bb_width = (bb_upper - bb_lower) / bb_middle

        # Buy conditions (adjusted: bottom-fishing during a downtrend)
        buy_conditions = {
            'rsi_oversold': rsi < self.rsi_oversold,          # RSI < 40
            'macd_golden_cross': macd > prev_macd,             # MACD trending up (no golden cross required)
            'trend_strong': adx > self.adx_threshold,          # ADX > 15
            'ema_trend': ema_short > ema_long * 0.98,          # MAs close (2% tolerance)
            'price_position': current_price < bb_lower * 1.02  # Price near lower band (+2% tolerance)
        }

        # Sell conditions (relaxed)
        sell_conditions = {
            'rsi_high': rsi > self.rsi_overbought,       # RSI > 60
            'macd_negative': macd < prev_macd,            # MACD trending down
            'trend_exists': adx > self.adx_threshold,     # ADX > 15
            'ema_trend': ema_short < ema_long,            # Bearish MAs
            'price_position': current_price > bb_middle   # Price > BB middle band
        }

        buy_score = sum(buy_conditions.values())
        sell_score = sum(sell_conditions.values())

        signal_type = 'hold'
        strength = 0

        # Determine signal (3/5 conditions suffice)
        if buy_score >= self.required_conditions:
            signal_type = 'buy'
            strength = buy_score / 5
        elif sell_score >= self.required_conditions:
            signal_type = 'sell'
            strength = sell_score / 5

        # Check signal strength and cooldown
        if signal_type != 'hold':
            if strength < self.signal_threshold:
                signal_type = 'hold'

            cooldown = self.config.get('risk_management', {}).get('cool_down_seconds', 3600)
            if time.time() - self.last_trade_time < cooldown:
                signal_type = 'hold'

        return {
            'signal': signal_type,
            'strength': strength,
            'price': current_price,
            'size': self.config['trading']['position_size'] if signal_type != 'hold' else 0,
            'indicators': {
                'rsi': rsi,
                'macd': macd,
                'signal': signal,
                'adx': adx,
                'plus_di': plus_di,
                'minus_di': minus_di,
                'ema_short': ema_short,
                'ema_long': ema_long,
                'bb_upper': bb_upper,
                'bb_middle': bb_middle,
                'bb_lower': bb_lower,
                'bb_width': bb_width
            },
            'conditions': {
                'buy': buy_conditions,
                'sell': sell_conditions
            }
        }

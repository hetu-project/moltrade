"""
Low-Frequency Trading Strategy - Optimized for Fees
"""
import pandas as pd
import numpy as np
import logging
from ta.trend import MACD, EMAIndicator, ADXIndicator
from ta.momentum import RSIIndicator
from ta.volatility import BollingerBands, AverageTrueRange
from typing import Dict
import time

logger = logging.getLogger(__name__)

class TrendFollowingStrategy:
    """
    Pure Trend-Following Strategy - Only trade in clear trends

    Features:
    - Only do trends, not choppy markets
    - Extremely low trading frequency
    - High single-trading targets
    - Suitable for long-term holding
    """

    def __init__(self, config: Dict):
        self.config = config
        self.name = "trend_following"
        self.params = config.get('strategies', {}).get('trend_following', {})
        self.positions = {}
        self.last_trade_time = 0
        self.daily_pnl = 0
        self.trade_count = 0

    def should_trade(self) -> bool:
        """More strict trade frequency control"""
        # At least 4 hours before trading again
        if time.time() - self.last_trade_time < 14400:
            return False

        max_trades = self.config.get('risk_management', {}).get('max_trades_per_day', 3)  # Maximum 3 trades per day
        if self.trade_count >= max_trades:
            return False

        return True

    def analyze(self, df: pd.DataFrame) -> Dict:
        """
        Only trade in strong trends
        """
        if len(df) < 200:
            return {'signal': 'hold', 'strength': 0}

        # Multi-period moving averages
        ema_fast = EMAIndicator(df['close'], window=20).ema_indicator()
        ema_mid = EMAIndicator(df['close'], window=50).ema_indicator()
        ema_slow = EMAIndicator(df['close'], window=200).ema_indicator()

        # ADX
        adx = ADXIndicator(df['high'], df['low'], df['close'], window=14)
        adx_value = adx.adx()
        adx_pos = adx.adx_pos()
        adx_neg = adx.adx_neg()

        # MACD
        macd = MACD(df['close'], window_slow=26, window_fast=12, window_sign=9)
        macd_line = macd.macd()

        current_price = df['close'].iloc[-1]
        current_ema_fast = ema_fast.iloc[-1]
        current_ema_mid = ema_mid.iloc[-1]
        current_ema_slow = ema_slow.iloc[-1]
        current_adx = adx_value.iloc[-1]
        current_adx_pos = adx_pos.iloc[-1]
        current_adx_neg = adx_neg.iloc[-1]
        current_macd = macd_line.iloc[-1]

        signal = 'hold'
        strength = 0

        # Strong upward trend: multiple EMA alignment + strong ADX + positive MACD
        if (current_ema_fast > current_ema_mid > current_ema_slow and
            current_adx > 30 and
            current_adx_pos > current_adx_neg and
            current_macd > 0 and
            current_price > current_ema_fast):
            signal = 'buy'
            strength = 0.9

        # Strong downward trend: multiple EMA alignment + strong ADX + negative MACD
        elif (current_ema_fast < current_ema_mid < current_ema_slow and
              current_adx > 30 and
              current_adx_neg > current_adx_pos and
              current_macd < 0 and
              current_price < current_ema_fast):
            signal = 'sell'
            strength = 0.9

        position_size = self.config.get('trading', {}).get('position_size', 0.15)

        return {
            'signal': signal,
            'strength': strength,
            'price': current_price,
            'size': position_size * strength,
            'indicators': {
                'ema_fast': current_ema_fast,
                'ema_mid': current_ema_mid,
                'ema_slow': current_ema_slow,
                'adx': current_adx,
                'macd': current_macd
            }
        }

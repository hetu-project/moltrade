"""
Trading Strategy Implementations
"""
import pandas as pd
import numpy as np
from ta.trend import MACD, EMAIndicator
from ta.momentum import RSIIndicator
from ta.volatility import BollingerBands
from typing import Dict, Optional, List
import time

class BaseStrategy:
    """Base class for strategies"""
    def __init__(self, config: Dict):
        self.config = config
        self.name = "base"
        self.positions = {}
        self.last_trade_time = 0
        self.daily_pnl = 0
        self.trade_count = 0
        
    def analyze(self, df: pd.DataFrame) -> Dict:
        """Analyze market data and return trading signals"""
        raise NotImplementedError

    def should_trade(self) -> bool:
        """Check if trading is allowed (risk management)"""
        cool_down = self.config.get('risk_management', {}).get('cool_down_seconds', 60)
        if time.time() - self.last_trade_time < cool_down:
            return False
        
        max_trades = self.config.get('risk_management', {}).get('max_trades_per_day', 20)
        if self.trade_count >= max_trades:
            return False
        
        max_loss = self.config.get('risk_management', {}).get('max_daily_loss', 0.05)
        if self.daily_pnl < -max_loss:
            return False
        
        return True


class MomentumStrategy(BaseStrategy):
    """Momentum Strategy: Based on RSI and MACD"""
    def __init__(self, config: Dict):
        super().__init__(config)
        self.name = "momentum"
        self.params = config.get('strategies', {}).get('momentum', {})
        
    def analyze(self, df: pd.DataFrame) -> Dict:
        """
        Returns:
        {
            'signal': 'buy' | 'sell' | 'hold',
            'strength': Signal strength (0-1),
            'price': Suggested price,
            'size': Suggested position size
        }
        """
        if len(df) < 50:
            return {'signal': 'hold', 'strength': 0}
        
        # Calculate indicators
        rsi_period = self.params.get('rsi_period', 14)
        rsi = RSIIndicator(df['close'], window=rsi_period).rsi()
        
        macd = MACD(df['close'],
                   window_slow=self.params.get('macd_slow', 26),
                   window_fast=self.params.get('macd_fast', 12),
                   window_sign=self.params.get('macd_signal', 9))
        
        macd_line = macd.macd()
        signal_line = macd.macd_signal()
        
        # Current values
        current_rsi = rsi.iloc[-1]
        current_macd = macd_line.iloc[-1]
        current_signal = signal_line.iloc[-1]
        current_price = df['close'].iloc[-1]
        
        # Generate signal
        signal = 'hold'
        strength = 0
        
        rsi_oversold = self.params.get('rsi_oversold', 30)
        rsi_overbought = self.params.get('rsi_overbought', 70)
        
        # Buy signal: RSI oversold or MACD golden cross
        if (current_rsi < rsi_oversold) or (current_macd > current_signal and current_rsi < 50):
            signal = 'buy'
            strength = min((rsi_oversold - current_rsi) / rsi_oversold, 0.8) if current_rsi < rsi_oversold else 0.6
        
        # Sell signal: RSI overbought or MACD death cross
        elif (current_rsi > rsi_overbought) or (current_macd < current_signal and current_rsi > 50):
            signal = 'sell'
            strength = min((current_rsi - rsi_overbought) / (100 - rsi_overbought), 0.8) if current_rsi > rsi_overbought else 0.6
        
        # Calculate position size
        position_size = self.config.get('trading', {}).get('position_size', 0.1)
        size = position_size * strength
        
        return {
            'signal': signal,
            'strength': strength,
            'price': current_price,
            'size': size,
            'indicators': {
                'rsi': current_rsi,
                'macd': current_macd,
                'signal': current_signal
            }
        }


class MeanReversionStrategy(BaseStrategy):
    """Mean Reversion Strategy: Based on Bollinger Bands"""
    def __init__(self, config: Dict):
        super().__init__(config)
        self.name = "mean_reversion"
        self.params = config.get('strategies', {}).get('mean_reversion', {})
        
    def analyze(self, df: pd.DataFrame) -> Dict:
        if len(df) < 30:
            return {'signal': 'hold', 'strength': 0}
        
        # Bollinger Bands
        bb_period = self.params.get('bollinger_period', 20)
        bb_std = self.params.get('bollinger_std', 2)
        
        bb = BollingerBands(df['close'], window=bb_period, window_dev=bb_std)
        upper_band = bb.bollinger_hband()
        lower_band = bb.bollinger_lband()
        middle_band = bb.bollinger_mavg()
        
        # RSI
        rsi = RSIIndicator(df['close'], window=self.params.get('rsi_period', 14)).rsi()
        
        current_price = df['close'].iloc[-1]
        current_upper = upper_band.iloc[-1]
        current_lower = lower_band.iloc[-1]
        current_middle = middle_band.iloc[-1]
        current_rsi = rsi.iloc[-1]
        
        signal = 'hold'
        strength = 0
        
        # Price close to lower band + oversold = buy
        if current_price <= current_lower and current_rsi < 40:
            signal = 'buy'
            strength = min((current_lower - current_price) / current_lower * 10, 1.0)
        
        # Price close to upper band + overbought = sell
        elif current_price >= current_upper and current_rsi > 60:
            signal = 'sell'
            strength = min((current_price - current_upper) / current_upper * 10, 1.0)
        
        position_size = self.config.get('trading', {}).get('position_size', 0.1)
        size = position_size * strength
        
        return {
            'signal': signal,
            'strength': strength,
            'price': current_price,
            'size': size,
            'indicators': {
                'upper_band': current_upper,
                'lower_band': current_lower,
                'middle_band': current_middle,
                'rsi': current_rsi
            }
        }


class GridStrategy(BaseStrategy):
    """Grid Trading Strategy"""
    def __init__(self, config: Dict):
        super().__init__(config)
        self.name = "grid"
        self.params = config.get('strategies', {}).get('grid', {})
        self.grid_orders = []
        
    def setup_grid(self, current_price: float):
        """Set up the grid"""
        levels = self.params.get('grid_levels', 10)
        range_percent = self.params.get('grid_range_percent', 0.1)
        order_size = self.params.get('order_size_percent', 0.05)
        
        upper_price = current_price * (1 + range_percent)
        lower_price = current_price * (1 - range_percent)
        
        step = (upper_price - lower_price) / levels
        
        self.grid_orders = []
        for i in range(levels + 1):
            price = lower_price + i * step
            self.grid_orders.append({
                'price': price,
                'size': order_size,
                'type': 'buy' if price < current_price else 'sell'
            })
        
        return self.grid_orders
    
    def analyze(self, df: pd.DataFrame) -> Dict:
        current_price = df['close'].iloc[-1]
        
        if not self.grid_orders:
            self.setup_grid(current_price)
        
        # Check if we need to re-set the grid
        prices = [order['price'] for order in self.grid_orders]
        if current_price > max(prices) or current_price < min(prices):
            self.setup_grid(current_price)
        
        # Find the closest grid line
        closest_order = min(self.grid_orders, key=lambda x: abs(x['price'] - current_price))
        
        return {
            'signal': 'grid',
            'grid_orders': self.grid_orders,
            'closest_order': closest_order,
            'current_price': current_price
        }


def get_strategy(strategy_name: str, config: Dict) -> BaseStrategy:
    """Get strategy instance"""
    try:
        from trader.strategies.trend_follow_strategies import TrendFollowingStrategy
    except ImportError:
        pass
    
    try:
        from trader.strategies.test_strategy import TestStrategy
    except ImportError:
        pass
    
    strategies = {
        'momentum': MomentumStrategy,
        'mean_reversion': MeanReversionStrategy,
        'grid': GridStrategy,
        'trend_following': TrendFollowingStrategy,
        'test': TestStrategy
    }
    
    strategy_class = strategies.get(strategy_name)
    if not strategy_class:
        raise ValueError(f"Unknown strategy: {strategy_name}")
    
    return strategy_class(config)

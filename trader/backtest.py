"""
Backtesting Tool - For Strategy Testing
"""
from datetime import datetime, timedelta
import json
from typing import Dict, List

import numpy as np
import pandas as pd
from trader.strategies.strategies import get_strategy

class Backtester:
    def __init__(self, config: Dict, initial_balance: float = 10000):
        self.config = config
        self.initial_balance = initial_balance
        self.balance = initial_balance
        self.positions = []
        self.trades = []
        self.equity_curve = []

    def load_historical_data(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """Load historical data (using simulated data here, actual data should be fetched from the exchange)"""
        # Generate simulated data
        dates = pd.date_range(start=start_date, end=end_date, freq='1h')

        # Simulate price movements - add volatility and trends
        price = 100
        prices = []
        trend = 0

        for i, _ in enumerate(dates):
            # Change trend every 100 periods
            if i % 100 == 0:
                trend = np.random.choice([-1, 1])
            price += trend * np.random.uniform(-1, 1)
            prices.append(price)

        df = pd.DataFrame({
            'timestamp': dates,
            'open': prices,
            'high': [p * 1.03 for p in prices],
            'low': [p * 0.97 for p in prices],
            'close': prices,
            'volume': np.random.uniform(1000, 10000, len(dates))
        })

        print(f"Generated {len(df)} data points, price range: ${df['close'].min():.2f} - ${df['close'].max():.2f}")

        return df

    def run_backtest(self, symbol: str, strategy_name: str, 
                    start_date: str, end_date: str) -> Dict:
        """Run backtest"""
        print(f"Starting backtest: {strategy_name} | {start_date} to {end_date}")

        # Load data
        df = self.load_historical_data(symbol, start_date, end_date)

        # Initialize strategy
        strategy = get_strategy(strategy_name, self.config)

        position = None

        # Iterate through data row by row
        for i in range(50, len(df)):
            signal = strategy.analyze(df.iloc[:i])
            # Process signals and manage positions

        # Calculate statistics
        return self.calculate_statistics()

    def calculate_statistics(self) -> Dict:
        """Calculate backtest statistics"""
        total_return = (self.balance - self.initial_balance) / self.initial_balance

        if not self.trades:
            return {}

        winning_trades = [t for t in self.trades if t['pnl'] > 0]
        win_rate = len(winning_trades) / len(self.trades)

        avg_win = np.mean([t['pnl'] for t in winning_trades]) if winning_trades else 0
        losing_trades = [t for t in self.trades if t['pnl'] <= 0]
        avg_loss = np.mean([t['pnl'] for t in losing_trades]) if losing_trades else 0

        # Maximum drawdown
        equity_series = pd.Series([e['equity'] for e in self.equity_curve])
        cummax = equity_series.cummax()
        drawdown = (equity_series - cummax) / cummax
        max_drawdown = drawdown.min()

        stats = {
            'initial_balance': self.initial_balance,
            'final_balance': self.balance,
            'total_return': total_return,
            'total_return_percent': f"{total_return:.2%}",
            'total_trades': len(self.trades),
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'win_rate': win_rate,
            'win_rate_percent': f"{win_rate:.2%}",
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_factor': abs(avg_win / avg_loss) if avg_loss != 0 else 0,
            'max_drawdown': max_drawdown,
            'max_drawdown_percent': f"{max_drawdown:.2%}"
        }

        return stats

    def print_report(self, stats: Dict):
        """Print backtest report"""
        print("\n" + "="*50)
        print("Backtest Report")
        print("="*50)
        print(f"Initial Balance: ${stats['initial_balance']:,.2f}")
        print(f"Final Balance: ${stats['final_balance']:,.2f}")
        print(f"Total Return: {stats['total_return_percent']}")
        print(f"\nTotal Trades: {stats['total_trades']}")
        print(f"Winning Trades: {stats['winning_trades']}")
        print(f"Losing Trades: {stats['losing_trades']}")
        print(f"Win Rate: {stats['win_rate_percent']}")
        print(f"\nAverage Win: ${stats['avg_win']:.2f}")
        print(f"Average Loss: ${stats['avg_loss']:.2f}")
        print(f"Profit Factor: {stats['profit_factor']:.2f}")
        print(f"\nMaximum Drawdown: {stats['max_drawdown_percent']}")
        print("="*50)

if __name__ == "__main__":
    # Load configuration
    with open('config.example.json', 'r') as f:
        config = json.load(f)

    # Run backtest
    backtester = Backtester(config, initial_balance=10000)

    # Test momentum strategy
    stats = backtester.run_backtest(
        symbol='HYPE',
        strategy_name='momentum',
        start_date='2024-01-01',
        end_date='2024-12-31'
    )

    backtester.print_report(stats)

    # Save detailed results
    with open('backtest_results.json', 'w') as f:
        json.dump({
            'statistics': stats,
            'trades': backtester.trades,
            'equity_curve': backtester.equity_curve
        }, f, indent=2, default=str)

    print("\nDetailed results saved to backtest_results.json")

"""
Hyperliquid API Client - Using the Official SDK
"""
import time
from typing import Dict, List, Optional
from hyperliquid.exchange import Exchange
from hyperliquid.info import Info
from eth_account import Account

class HyperliquidClient:
    def __init__(self, wallet_address: str, private_key: str, testnet: bool = False):
        """Initialize the client"""
        self.wallet_address = wallet_address
        self.private_key = private_key
        self.testnet = testnet

        # Create account object
        self.account = Account.from_key(private_key)

        # Use the official SDK
        base_url = "https://api.hyperliquid-testnet.xyz" if testnet else None

        self.exchange = Exchange(
            wallet=self.account,
            base_url=base_url
        )

        self.info = Info(base_url=base_url)

    def get_market_data(self, symbol: str) -> Dict:
        """Fetch market data"""
        try:
            meta = self.info.meta()
            universe = meta.get('universe', [])
            for asset in universe:
                if asset.get('name') == symbol:
                    return asset
            return {}
        except Exception as e:
            print(f"Failed to fetch market data: {e}")
            return {}

    def get_orderbook(self, symbol: str) -> Dict:
        """Fetch order book"""
        try:
            return self.info.l2_snapshot(symbol)
        except Exception as e:
            print(f"Failed to fetch order book: {e}")
            return {}

    def get_candles(self, symbol: str, interval: str = "1m", limit: int = 100) -> List:
        """Fetch candlestick data"""
        try:
            # Calculate seconds based on interval
            interval_seconds = {
                '1m': 60,
                '3m': 180,
                '5m': 300,
                '15m': 900,
                '30m': 1800,
                '1h': 3600,
                '2h': 7200,
                '4h': 14400,
                '1d': 86400
            }.get(interval, 60)

            start_time = int((time.time() - limit * interval_seconds) * 1000)
            end_time = int(time.time() * 1000)

            # Fetch candlestick data using SDK - parameter order: name, interval, startTime, endTime
            candles_data = self.info.candles_snapshot(
                name=symbol,
                interval=interval,
                startTime=start_time,
                endTime=end_time
            )

            # Convert to a unified format [timestamp, open, high, low, close, volume]
            candles = []
            for candle in candles_data:
                candles.append([
                    candle['t'],  # timestamp
                    float(candle['o']),  # open
                    float(candle['h']),  # high
                    float(candle['l']),  # low
                    float(candle['c']),  # close
                    float(candle.get('v', 0))   # volume
                ])

            return candles
        except Exception as e:
            print(f"Failed to fetch candlestick data: {e}")
            import traceback
            traceback.print_exc()
            return []

    def get_user_state(self) -> Dict:
        """Fetch user account information"""
        try:
            return self.info.user_state(self.wallet_address)
        except Exception as e:
            print(f"Failed to fetch account information: {e}")
            return {}

    def get_open_orders(self) -> List:
        """Fetch current open orders"""
        try:
            state = self.get_user_state()
            return state.get('assetPositions', [])
        except Exception as e:
            print(f"Failed to fetch open orders: {e}")
            return []

    def get_positions(self) -> List:
        """Fetch current positions"""
        try:
            state = self.get_user_state()
            return state.get('assetPositions', [])
        except Exception as e:
            print(f"Failed to fetch positions: {e}")
            return []

    def place_order(self, symbol: str, is_buy: bool, size: float, price: Optional[float] = None, 
                   order_type: str = "limit", reduce_only: bool = False) -> Dict:
        """Place an order - Using the official SDK"""
        try:
            from hyperliquid.utils.signing import OrderType

            # Fetch asset precision
            asset = self.get_market_data(symbol)
            sz_decimals = asset.get('szDecimals', 0)

            # Round to correct precision (DOGE is 0, i.e., integer)
            # Note: Round up to ensure minimum order value is met
            import math
            if sz_decimals == 0:
                size = math.ceil(size)  # Round up
            else:
                size = round(size, sz_decimals)

            # Minimum trade size check
            if size < (10 ** -sz_decimals):
                print(f"Trade size too small: {size}, minimum: {10 ** -sz_decimals}")
                return {"error": "size_too_small"}

            # Determine order type
            if order_type == "limit" and price is not None:
                ot = {"limit": {"tif": "Gtc"}}
                limit_px = price
            else:
                ot = {"market": {}}
                # Market orders require a price far from the market
                market_data = self.get_market_data(symbol)
                if is_buy:
                    limit_px = float(market_data.get('markPx', 0)) * 1.05  # Buy price +5%
                else:
                    limit_px = float(market_data.get('markPx', 0)) * 0.95  # Sell price -5%

            print(f"Order parameters: symbol={symbol}, is_buy={is_buy}, size={size}, limit_px={limit_px}, order_type={ot}")

            # Place order using SDK
            result = self.exchange.order(
                name=symbol,  # Parameter name is 'name', not 'coin'
                is_buy=is_buy,
                sz=size,
                limit_px=limit_px,
                order_type=ot,
                reduce_only=reduce_only
            )

            return result

        except Exception as e:
            print(f"Failed to place order: {e}")
            import traceback
            traceback.print_exc()
            raise

    def cancel_order(self, order_id: int, symbol: str) -> Dict:
        """Cancel an order"""
        try:
            return self.exchange.cancel(name=symbol, oid=order_id)
        except Exception as e:
            print(f"Failed to cancel order: {e}")
            return {}

    def cancel_all_orders(self, symbol: Optional[str] = None) -> Dict:
        """Cancel all orders"""
        try:
            if symbol:
                return self.exchange.cancel_all(name=symbol)
            else:
                # Cancel orders for all assets
                result = {}
                positions = self.get_open_orders()
                for pos in positions:
                    coin = pos.get('position', {}).get('coin')
                    if coin:
                        result[coin] = self.exchange.cancel_all(name=coin)
                return result
        except Exception as e:
            print(f"Failed to cancel all orders: {e}")
            return {}

    def get_balance(self, symbol: str = "USDC") -> float:
        """Fetch balance"""
        try:
            state = self.get_user_state()

            if 'marginSummary' in state:
                return float(state['marginSummary']['accountValue'])

            # Fallback: Fetch from withdrawable
            if 'withdrawable' in state:
                return float(state['withdrawable'])

            return 0.0

        except Exception as e:
            print(f"Failed to fetch balance: {e}")
            return 0.0

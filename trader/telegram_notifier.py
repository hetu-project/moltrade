"""
Telegram Notification Module
"""
import requests
import logging
from typing import Optional, Dict
from datetime import datetime

logger = logging.getLogger(__name__)


class TelegramNotifier:
    """Telegram Notifier"""

    def __init__(self, bot_token: str, chat_id: str, enabled: bool = True):
        """
        Initialize the Telegram Notifier

        Args:
            bot_token: Telegram Bot Token
            chat_id: Chat ID to receive messages
            enabled: Whether to enable notifications
        """
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.enabled = enabled
        self.base_url = f"https://api.telegram.org/bot{bot_token}"

        if enabled:
            logger.info(f"Telegram notifications enabled | Chat ID: {chat_id}")
        else:
            logger.info("Telegram notifications disabled")

    def _send_message(self, text: str, parse_mode: str = "HTML") -> bool:
        """
        Send a Telegram message

        Args:
            text: Message content
            parse_mode: Parsing mode (HTML/Markdown)

        Returns:
            Whether the message was sent successfully
        """
        if not self.enabled:
            return False

        try:
            url = f"{self.base_url}/sendMessage"
            payload = {
                "chat_id": self.chat_id,
                "text": text,
                "parse_mode": parse_mode
            }

            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()

            return True

        except Exception as e:
            logger.error(f"Failed to send Telegram message: {e}")
            return False

    def notify_startup(self, strategy: str, symbol: str, test_mode: bool = False):
        """Startup Notification"""
        mode = "🧪 Test Mode" if test_mode else "🚀 Live Mode"

        text = f"""
🤖 <b>Trading Bot Started</b>

📊 <b>Strategy:</b> {strategy}
💰 <b>Symbol:</b> {symbol}
⚙️ <b>Mode:</b> {mode}
🕐 <b>Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

The bot is now running...
"""
        return self._send_message(text)

    def notify_trade_signal(self, symbol: str, signal: Dict, current_price: float):
        """Trade Signal Notification"""
        signal_type = signal['signal'].upper()
        strength = signal['strength']

        # Choose emoji based on signal type
        emoji_map = {
            'BUY': '🟢',
            'SELL': '🔴',
            'HOLD': '⚪'
        }
        emoji = emoji_map.get(signal_type, '⚪')

        if signal_type == 'HOLD':
            return False  # Do not send HOLD signals

        indicators = signal.get('indicators', {})
        rsi = indicators.get('rsi', 0)
        macd = indicators.get('macd', 0)
        macd_signal = indicators.get('signal', 0)

        text = f"""
{emoji} <b>Trade Signal: {signal_type}</b>

💰 <b>Symbol:</b> {symbol}
💵 <b>Current Price:</b> ${current_price:,.2f}
📊 <b>Signal Strength:</b> {strength:.1%}

📈 <b>Technical Indicators:</b>
• RSI: {rsi:.1f}
• MACD: {macd:.2f}
• Signal: {macd_signal:.2f}

🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        return self._send_message(text)

    def notify_trade_executed(self, symbol: str, trade_type: str, size: float,
                             price: float, test_mode: bool = False):
        """Trade Execution Notification"""
        mode_tag = "[Test] " if test_mode else ""
        emoji = "🟢" if trade_type.upper() == 'BUY' else "🔴"

        text = f"""
{emoji} <b>{mode_tag}Trade Executed</b>

📝 <b>Type:</b> {trade_type.upper()}
💰 <b>Symbol:</b> {symbol}
📊 <b>Quantity:</b> {size:.4f}
💵 <b>Price:</b> ${price:,.2f}
💸 <b>Amount:</b> ${size * price:,.2f}

🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        return self._send_message(text)

    def notify_position_closed(self, symbol: str, entry_price: float, exit_price: float,
                              pnl: float, pnl_percent: float, reason: str, test_mode: bool = False):
        """Position Closure Notification"""
        mode_tag = "[Test] " if test_mode else ""

        # Choose emoji based on profit/loss
        if pnl > 0:
            emoji = "🎉"
            pnl_text = f"+${pnl:.2f}"
        else:
            emoji = "😔"
            pnl_text = f"-${abs(pnl):.2f}"

        text = f"""
{emoji} <b>{mode_tag}Position Closed</b>

💰 <b>Symbol:</b> {symbol}
📈 <b>Entry Price:</b> ${entry_price:,.2f}
📉 <b>Exit Price:</b> ${exit_price:,.2f}

💸 <b>Profit/Loss:</b> {pnl_text} ({pnl_percent:+.2%})
📝 <b>Reason:</b> {reason}

🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        return self._send_message(text)

    def notify_error(self, error_msg: str):
        """Error Notification"""
        text = f"""
⚠️ <b>Error Warning</b>

{error_msg}

🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        return self._send_message(text)

    def notify_daily_summary(self, stats: Dict):
        """Daily Summary Notification"""
        trades = stats.get('trades_today', 0)
        pnl = stats.get('pnl_today', 0)
        win_rate = stats.get('win_rate', 0)
        balance = stats.get('balance', 0)

        emoji = "📈" if pnl > 0 else "📉"

        text = f"""
{emoji} <b>Daily Trade Summary</b>

💼 <b>Today's Trades:</b> {trades} trades
💰 <b>Today's Profit/Loss:</b> ${pnl:+,.2f}
📊 <b>Win Rate:</b> {win_rate:.1%}
💵 <b>Current Balance:</b> ${balance:,.2f}

📅 {datetime.now().strftime('%Y-%m-%d')}
"""
        return self._send_message(text)

    def notify_risk_warning(self, warning_type: str, details: str):
        """Risk Warning"""
        text = f"""
🚨 <b>Risk Warning</b>

⚠️ <b>Type:</b> {warning_type}
📝 <b>Details:</b> {details}

Please manage your risk!

🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        return self._send_message(text)

    def notify_shutdown(self, stats: Dict):
        """Shutdown Notification"""
        text = f"""
🛑 <b>Trading Bot Stopped</b>

📊 <b>Run Statistics:</b>
• Total Trades: {stats.get('total_trades', 0)} trades
• Total Profit/Loss: ${stats.get('total_pnl', 0):+,.2f}
• Win Rate: {stats.get('win_rate', 0):.1%}

🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        return self._send_message(text)

def get_notifier(config: Dict) -> Optional[TelegramNotifier]:
    """
    Create a notifier from config

    Args:
        config: Config dictionary

    Returns:
        TelegramNotifier instance or None
    """
    telegram_config = config.get('telegram', {})
    
    if not telegram_config.get('enabled', False):
        return None
    
    bot_token = telegram_config.get('bot_token')
    chat_id = telegram_config.get('chat_id')
    
    if not bot_token or not chat_id:
        logger.warning("Telegram config incomplete, notifications disabled")
        return None
    
    return TelegramNotifier(bot_token, chat_id, enabled=True)

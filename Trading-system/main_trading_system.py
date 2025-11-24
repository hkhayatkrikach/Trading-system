import asyncio
import logging
import time
from datetime import datetime
from typing import Dict
import json
import sqlite3
from market_data.api_connector import MarketAPI
from market_data.data_fetcher import DataFetcher
from trading_engine.signal_generator import SignalGenerator
from trading_engine.risk_manager import RiskManager
from telegram_bot.bot import TradingSignalBot

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TradingSystem:
    def __init__(self, config: Dict):
        self.config = config
        self.api_connector = MarketAPI(config.get('exchange', 'binance'))
        self.data_fetcher = DataFetcher(self.api_connector)
        self.signal_generator = SignalGenerator(config)
        self.risk_manager = RiskManager(config)
        self.telegram_bot = TradingSignalBot()
        
        # Initialize database
        self.db_connection = sqlite3.connect('trading_system.db', check_same_thread=False)
        self.init_database()
        
        # Trading symbols to monitor
        self.symbols = config.get('symbols', ['BTC/USDT', 'ETH/USDT', 'SOL/USDT'])
    
    def init_database(self):
        """Initialize the database"""
        cursor = self.db_connection.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                symbol TEXT,
                signal_type TEXT,
                entry_price REAL,
                stop_loss REAL,
                take_profit REAL,
                position_size REAL,
                risk_amount REAL,
                profit_potential REAL,
                capital_before REAL,
                capital_after REAL,
                status TEXT DEFAULT 'OPEN'
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS signals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                symbol TEXT,
                signal_type TEXT,
                entry_price REAL,
                stop_loss REAL,
                take_profit REAL,
                position_size REAL,
                risk_percent REAL,
                rsi REAL,
                volume_ratio REAL,
                trend TEXT
            )
        ''')
        
        self.db_connection.commit()
    
    async def run_trading_cycle(self):
        """Main trading cycle"""
        logger.info("Starting trading system...")
        
        while True:
            try:
                for symbol in self.symbols:
                    await self.analyze_symbol(symbol)
                
                # Check if daily target is reached
                if self.risk_manager.should_stop_trading_today():
                    logger.info("Daily target reached. Stopping trading for today.")
                    await self.send_daily_report()
                    # Wait until next trading day
                    await asyncio.sleep(3600)  # Wait 1 hour before checking again
                
                # Wait before next cycle
                await asyncio.sleep(self.config.get('refresh_interval', 300))  # 5 minutes default
                
            except Exception as e:
                logger.error(f"Error in trading cycle: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retrying
    
    async def analyze_symbol(self, symbol: str):
        """Analyze a single symbol"""
        try:
            logger.info(f"Analyzing {symbol}")
            
            # Fetch market data
            market_data = self.data_fetcher.fetch_and_analyze(symbol, self.config.get('timeframe', '1h'))
            
            if not market_data:
                logger.warning(f"No data received for {symbol}")
                return
            
            # Generate signals
            signal = self.signal_generator.generate_signals(market_data)
            
            if not signal:
                return
            
            # Check if we have a valid signal
            if signal.get('long_signal') or signal.get('short_signal'):
                await self.execute_trade(signal)
        
        except Exception as e:
            logger.error(f"Error analyzing {symbol}: {e}")
    
    async def execute_trade(self, signal: Dict):
        """Execute a trade based on signal"""
        try:
            # Calculate position size
            position_info = self.risk_manager.calculate_position_size(
                signal['entry_price'], 
                signal['stop_loss'], 
                signal['symbol']
            )
            
            # Create trade signal data
            trade_signal = {
                'symbol': signal['symbol'],
                'signal_type': 'LONG' if signal['long_signal'] else 'SHORT',
                'entry_price': signal['entry_price'],
                'stop_loss': signal['stop_loss'],
                'take_profit': signal['take_profit'],
                'position_size': position_info['position_size'],
                'risk_amount': position_info['risk_amount'],
                'profit_potential': position_info['profit_potential'],
                'risk_percent': position_info['risk_percent'],
                'capital': self.risk_manager.current_capital
            }
            
            # Send signal to Telegram
            await self.telegram_bot.send_signal_message(trade_signal)
            
            # Save to database
            self.save_trade_to_db(trade_signal)
            
            logger.info(f"Trade executed for {signal['symbol']}: {trade_signal['signal_type']}")
            
        except Exception as e:
            logger.error(f"Error executing trade: {e}")
    
    def save_trade_to_db(self, trade_signal: Dict):
        """Save trade to database"""
        cursor = self.db_connection.cursor()
        
        cursor.execute('''
            INSERT INTO signals (
                symbol, signal_type, entry_price, stop_loss, take_profit,
                position_size, risk_percent, rsi, volume_ratio, trend
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            trade_signal['symbol'],
            trade_signal['signal_type'],
            trade_signal['entry_price'],
            trade_signal['stop_loss'],
            trade_signal['take_profit'],
            trade_signal['position_size'],
            trade_signal['risk_percent'],
            0,  # Placeholder - would need to get from market data
            0,  # Placeholder - would need to get from market data
            'N/A'  # Placeholder - would need to get from market data
        ))
        
        self.db_connection.commit()
    
    async def send_daily_report(self):
        """Send daily performance report"""
        performance = self.risk_manager.get_performance_metrics()
        
        report = f"""
📊 **DAILY TRADING REPORT**

💰 **Capital Actual**: ${performance['current_capital']:,.2f}
📈 **P&L Diario**: ${performance['daily_pnl']:,.2f}
📊 **Retorno Diario**: {performance['daily_return']:.2f}%
🎯 **Objetivo Diario**: {self.config['daily_target']}%
📈 **Retorno Total**: {performance['total_return']:.2f}%
        
✅ **Daily target reached!**
        """
        
        await self.telegram_bot.send_daily_report(report)
    
    def start(self):
        """Start the trading system"""
        try:
            asyncio.run(self.run_trading_cycle())
        except KeyboardInterrupt:
            logger.info("Trading system stopped by user")
        except Exception as e:
            logger.error(f"Fatal error in trading system: {e}")

# Configuration
CONFIG = {
    'exchange': 'binance',
    'symbols': ['BTC/USDT', 'ETH/USDT', 'SOL/USDT'],
    'timeframe': '1h',
    'refresh_interval': 300,  # 5 minutes
    'base_capital': 10000,
    'daily_target': 5.0,
    'max_risk_per_trade': 2.0,
    'telegram_bot_token': 'your_telegram_bot_token',
    'telegram_chat_id': 'your_telegram_chat_id'
}

if __name__ == "__main__":
    trading_system = TradingSystem(CONFIG)
    trading_system.start()
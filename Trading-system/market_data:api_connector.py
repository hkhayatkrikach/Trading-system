import ccxt
import pandas as pd
import time
from datetime import datetime, timedelta
import requests
import logging

class MarketAPI:
    def __init__(self, exchange_name='binance'):
        self.exchange = getattr(ccxt, exchange_name)({
            'enableRateLimit': True,
            'options': {
                'adjustForTimeDifference': True
            }
        })
        self.logger = logging.getLogger(__name__)
    
    def get_ohlcv(self, symbol, timeframe='1h', limit=1000):
        """Obtener datos OHLCV"""
        try:
            ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            return df
        except Exception as e:
            self.logger.error(f"Error fetching OHLCV data: {e}")
            return pd.DataFrame()
    
    def get_ticker(self, symbol):
        """Obtener ticker actual"""
        try:
            return self.exchange.fetch_ticker(symbol)
        except Exception as e:
            self.logger.error(f"Error fetching ticker: {e}")
            return {}
    
    def get_balance(self):
        """Obtener balance de la cuenta (si se tiene API key)"""
        try:
            return self.exchange.fetch_balance()
        except Exception as e:
            self.logger.error(f"Error fetching balance: {e}")
            return {}
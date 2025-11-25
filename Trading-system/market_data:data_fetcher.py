import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List
from .api_connector import MarketAPI
from .indicators import TechnicalIndicators

class DataFetcher:
    def __init__(self, api_connector: MarketAPI):
        self.api = api_connector
        self.indicators = TechnicalIndicators()
    
    def fetch_and_analyze(self, symbol: str, timeframe: str = '1h', lookback: int = 1000) -> Dict:
        """Fetch data and calculate all indicators"""
        # Get OHLCV data
        df = self.api.get_ohlcv(symbol, timeframe, lookback)

        if df.empty:
            return {}

        df['symbol'] = symbol
        df['timeframe'] = timeframe
        
        # Calculate technical indicators
        df['ema21'] = self.indicators.ema(df['close'], 21)
        df['ema50'] = self.indicators.ema(df['close'], 50)
        df['ema200'] = self.indicators.ema(df['close'], 200)
        df['rsi'] = self.indicators.rsi(df['close'], 14)
        df['atr'] = self.indicators.atr(df['high'], df['low'], df['close'], 14)
        df['sma_volume'] = self.indicators.sma(df['volume'], 20)
        
        # Calculate Bollinger Bands
        bb_upper, bb_middle, bb_lower = self.indicators.bollinger_bands(df['close'], 20, 2)
        df['bb_upper'] = bb_upper
        df['bb_middle'] = bb_middle
        df['bb_lower'] = bb_lower
        
        # Calculate MACD
        macd_line, signal_line, histogram = self.indicators.macd(df['close'])
        df['macd'] = macd_line
        df['macd_signal'] = signal_line
        df['macd_histogram'] = histogram
        
        # Calculate additional metrics
        df['volume_ratio'] = df['volume'] / df['sma_volume']
        df['price_change'] = df['close'].pct_change()
        df['volatility'] = df['close'].rolling(20).std()
        
        return df.to_dict('records')
    
    def detect_candlestick_patterns(self, df: pd.DataFrame) -> Dict:
        """Detect candlestick patterns"""
        patterns = {}
        
        # Calculate candle properties
        df['body'] = abs(df['close'] - df['open'])
        df['upper_shadow'] = df['high'] - df['close'].where(df['close'] > df['open'], df['open'])
        df['lower_shadow'] = df['close'].where(df['close'] < df['open'], df['open']) - df['low']
        df['total_range'] = df['high'] - df['low']
        
        # Hammer pattern
        patterns['hammer'] = (
            (df['lower_shadow'] >= 2 * df['body']) & 
            (df['upper_shadow'] <= df['body']) & 
            (df['close'] > df['open'])
        )
        
        # Shooting star pattern
        patterns['shooting_star'] = (
            (df['upper_shadow'] >= 2 * df['body']) & 
            (df['lower_shadow'] <= df['body']) & 
            (df['close'] < df['open'])
        )
        
        # Bullish engulfing
        patterns['bullish_engulfing'] = (
            (df['open'].shift(1) > df['close'].shift(1)) &  # Previous candle red
            (df['close'] > df['open']) &  # Current candle green
            (df['open'] < df['close'].shift(1)) &  # Current open below previous close
            (df['close'] > df['open'].shift(1))  # Current close above previous open
        )
        
        # Bearish engulfing
        patterns['bearish_engulfing'] = (
            (df['close'].shift(1) > df['open'].shift(1)) &  # Previous candle green
            (df['open'] > df['close']) &  # Current candle red
            (df['close'] < df['open'].shift(1)) &  # Current close below previous open
            (df['open'] > df['close'].shift(1))  # Current open above previous close
        )
        
        return patterns
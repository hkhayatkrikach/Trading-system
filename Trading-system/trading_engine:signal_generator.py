import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from datetime import datetime
from market_data.indicators import TechnicalIndicators

class SignalGenerator:
    def __init__(self, config: Dict):
        self.config = config
        self.indicators = TechnicalIndicators()
    
    def generate_signals(self, market_data: List[Dict]) -> Dict:
        """Generate trading signals based on market data"""
        if not market_data:
            return {}
        
        df = pd.DataFrame(market_data)
        
        if len(df) < 50:  # Need sufficient data
            return {}
        
        # Calculate conditions
        current_price = df['close'].iloc[-1]
        current_volume = df['volume'].iloc[-1]
        current_rsi = df['rsi'].iloc[-1]
        current_atr = df['atr'].iloc[-1]
        
        # Trend detection
        trend = self.detect_trend(df)
        volume_ok = current_volume > df['sma_volume'].iloc[-1] * 1.3
        rsi_ok = self.check_rsi_conditions(current_rsi, trend)
        
        # Smart Money Concepts
        liquidity_levels = self.detect_liquidity_levels(df)
        order_blocks = self.detect_order_blocks(df)
        fvg = self.detect_fvg(df)
        
        # Candlestick patterns
        patterns = self.detect_candlestick_patterns(df)
        
        # Generate signals
        long_signal = self.evaluate_long_signal(df, trend, volume_ok, rsi_ok, liquidity_levels, order_blocks, fvg, patterns)
        short_signal = self.evaluate_short_signal(df, trend, volume_ok, rsi_ok, liquidity_levels, order_blocks, fvg, patterns)
        
        return {
            'symbol': df['symbol'].iloc[-1] if 'symbol' in df.columns else 'N/A',
            'timestamp': datetime.now().isoformat(),
            'current_price': current_price,
            'trend': trend,
            'long_signal': long_signal,
            'short_signal': short_signal,
            'entry_price': self.calculate_entry_price(df, long_signal, short_signal),
            'stop_loss': self.calculate_stop_loss(df, long_signal, short_signal),
            'take_profit': self.calculate_take_profit(df, long_signal, short_signal)
        }
    
    def detect_trend(self, df: pd.DataFrame) -> str:
        """Detect market trend"""
        ema21 = df['ema21'].iloc[-1]
        ema50 = df['ema50'].iloc[-1]
        ema200 = df['ema200'].iloc[-1]
        current_price = df['close'].iloc[-1]
        
        if current_price > ema21 > ema50 > ema200:
            return 'bullish'
        elif current_price < ema21 < ema50 < ema200:
            return 'bearish'
        else:
            return 'sideways'
    
    def check_rsi_conditions(self, rsi: float, trend: str) -> bool:
        """Check RSI conditions based on trend"""
        if trend == 'bullish':
            return 30 < rsi < 70  # Not overbought
        elif trend == 'bearish':
            return 30 < rsi < 70  # Not oversold
        else:
            return 30 < rsi < 70
    
    def detect_liquidity_levels(self, df: pd.DataFrame) -> Dict:
        """Detect liquidity sweep levels"""
        recent_high = df['high'].tail(20).max()
        recent_low = df['low'].tail(20).min()
        
        current_high = df['high'].iloc[-1]
        current_low = df['low'].iloc[-1]
        
        return {
            'swept_up': current_low <= recent_low,
            'swept_down': current_high >= recent_high,
            'recent_high': recent_high,
            'recent_low': recent_low
        }
    
    def detect_order_blocks(self, df: pd.DataFrame) -> Dict:
        """Detect order blocks"""
        # Look for consolidation areas
        consolidation = df.tail(10)
        high_range = consolidation['high'].max() - consolidation['low'].min()
        atr = df['atr'].iloc[-1]
        
        return {
            'bullish_ob': len(df) > 1 and df['low'].iloc[-1] <= df['low'].iloc[-6:-1].min() and df['close'].iloc[-1] > df['low'].iloc[-6:-1].min(),
            'bearish_ob': len(df) > 1 and df['high'].iloc[-1] >= df['high'].iloc[-6:-1].max() and df['close'].iloc[-1] < df['high'].iloc[-6:-1].max(),
            'consolidation': high_range < atr * 0.5
        }
    
    def detect_fvg(self, df: pd.DataFrame) -> Dict:
        """Detect Fair Value Gaps"""
        if len(df) < 3:
            return {'bullish_fvg': False, 'bearish_fvg': False}
        
        # Bullish FVG: current low > previous high (2 bars ago)
        bullish_fvg = df['low'].iloc[-1] > df['high'].iloc[-3] and df['close'].iloc[-2] < df['open'].iloc[-2]
        
        # Bearish FVG: current high < previous low (2 bars ago)
        bearish_fvg = df['high'].iloc[-1] < df['low'].iloc[-3] and df['close'].iloc[-2] > df['open'].iloc[-2]
        
        return {
            'bullish_fvg': bullish_fvg,
            'bearish_fvg': bearish_fvg
        }
    
    def detect_candlestick_patterns(self, df: pd.DataFrame) -> Dict:
        """Detect candlestick patterns"""
        patterns = {}
        
        # Calculate candle properties
        body = abs(df['close'].iloc[-1] - df['open'].iloc[-1])
        upper_shadow = df['high'].iloc[-1] - max(df['close'].iloc[-1], df['open'].iloc[-1])
        lower_shadow = min(df['close'].iloc[-1], df['open'].iloc[-1]) - df['low'].iloc[-1]
        total_range = df['high'].iloc[-1] - df['low'].iloc[-1]
        
        # Hammer
        patterns['hammer'] = total_range > 0 and lower_shadow >= 0.6 * total_range and body >= 0.15 * total_range and df['close'].iloc[-1] > df['open'].iloc[-1]
        
        # Shooting star
        patterns['shooting_star'] = total_range > 0 and upper_shadow >= 0.6 * total_range and body >= 0.15 * total_range and df['close'].iloc[-1] < df['open'].iloc[-1]
        
        # Engulfing patterns
        patterns['bullish_engulfing'] = (
            len(df) > 1 and 
            df['open'].iloc[-2] > df['close'].iloc[-2] and  # Previous red
            df['close'].iloc[-1] > df['open'].iloc[-1] and  # Current green
            df['open'].iloc[-1] < df['close'].iloc[-2] and  # Current opens below previous close
            df['close'].iloc[-1] > df['open'].iloc[-2]      # Current closes above previous open
        )
        
        patterns['bearish_engulfing'] = (
            len(df) > 1 and 
            df['close'].iloc[-2] > df['open'].iloc[-2] and  # Previous green
            df['open'].iloc[-1] > df['close'].iloc[-1] and  # Current red
            df['close'].iloc[-1] < df['open'].iloc[-2] and  # Current closes below previous open
            df['open'].iloc[-1] > df['close'].iloc[-2]      # Current opens above previous close
        )
        
        return patterns
    
    def evaluate_long_signal(self, df: pd.DataFrame, trend: str, volume_ok: bool, rsi_ok: bool, liquidity: Dict, order_blocks: Dict, fvg: Dict, patterns: Dict) -> bool:
        """Evaluate long signal conditions"""
        if trend != 'bullish':
            return False
        
        conditions = [
            volume_ok,
            rsi_ok,
            liquidity['swept_down'] or fvg['bullish_fvg'],
            order_blocks['bullish_ob'] or patterns['hammer'] or patterns['bullish_engulfing']
        ]
        
        return all(conditions)
    
    def evaluate_short_signal(self, df: pd.DataFrame, trend: str, volume_ok: bool, rsi_ok: bool, liquidity: Dict, order_blocks: Dict, fvg: Dict, patterns: Dict) -> bool:
        """Evaluate short signal conditions"""
        if trend != 'bearish':
            return False
        
        conditions = [
            volume_ok,
            rsi_ok,
            liquidity['swept_up'] or fvg['bearish_fvg'],
            order_blocks['bearish_ob'] or patterns['shooting_star'] or patterns['bearish_engulfing']
        ]
        
        return all(conditions)
    
    def calculate_entry_price(self, df: pd.DataFrame, long_signal: bool, short_signal: bool) -> float:
        """Calculate entry price"""
        current_price = df['close'].iloc[-1]
        atr = df['atr'].iloc[-1]
        
        if long_signal:
            return current_price - (atr * 0.1)  # Entry slightly below
        elif short_signal:
            return current_price + (atr * 0.1)  # Entry slightly above
        else:
            return current_price
    
    def calculate_stop_loss(self, df: pd.DataFrame, long_signal: bool, short_signal: bool) -> float:
        """Calculate stop loss"""
        current_price = df['close'].iloc[-1]
        atr = df['atr'].iloc[-1]
        
        if long_signal:
            return current_price - (atr * 1.5)  # 1.5 ATR below for long
        elif short_signal:
            return current_price + (atr * 1.5)  # 1.5 ATR above for short
        else:
            return current_price
    
    def calculate_take_profit(self, df: pd.DataFrame, long_signal: bool, short_signal: bool) -> float:
        """Calculate take profit (3:1 risk-reward ratio)"""
        entry = self.calculate_entry_price(df, long_signal, short_signal)
        sl = self.calculate_stop_loss(df, long_signal, short_signal)
        
        if long_signal:
            risk = entry - sl
            return entry + (risk * 3)  # 3:1 R:R
        elif short_signal:
            risk = sl - entry
            return entry - (risk * 3)  # 3:1 R:R
        else:
            return entry
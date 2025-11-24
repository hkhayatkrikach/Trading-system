from typing import Dict
import math

class RiskManager:
    def __init__(self, config: Dict):
        self.config = config
        self.current_capital = config.get('base_capital', 10000)
        self.daily_target = config.get('daily_target', 5.0)
        self.max_risk_per_trade = config.get('max_risk_per_trade', 2.0)
        self.daily_pnl = 0.0
        self.total_pnl = 0.0
    
    def calculate_position_size(self, entry_price: float, stop_loss: float, symbol: str = 'N/A') -> Dict:
        """Calculate position size based on risk management"""
        risk_amount = self.current_capital * (self.max_risk_per_trade / 100)
        risk_per_unit = abs(entry_price - stop_loss)
        
        if risk_per_unit == 0:
            return {
                'position_size': 0,
                'risk_amount': 0,
                'profit_potential': 0
            }
        
        position_size = risk_amount / risk_per_unit
        
        # Calculate profit potential
        take_profit = self.calculate_take_profit(entry_price, stop_loss)
        profit_per_unit = abs(take_profit - entry_price)
        profit_potential = position_size * profit_per_unit
        
        return {
            'position_size': position_size,
            'risk_amount': risk_amount,
            'profit_potential': profit_potential,
            'risk_percent': self.max_risk_per_trade
        }
    
    def calculate_take_profit(self, entry_price: float, stop_loss: float) -> float:
        """Calculate take profit based on 3:1 risk-reward ratio"""
        risk = abs(entry_price - stop_loss)
        target_percent = self.config.get('daily_target', 5.0)
        
        if entry_price > stop_loss:  # Long trade
            return entry_price + (risk * 3)
        else:  # Short trade
            return entry_price - (risk * 3)
    
    def update_capital(self, trade_result: float):
        """Update capital after trade"""
        self.daily_pnl += trade_result
        self.total_pnl += trade_result
        self.current_capital += trade_result
    
    def should_stop_trading_today(self) -> bool:
        """Check if daily target is reached"""
        daily_return = (self.daily_pnl / self.config.get('base_capital', 10000)) * 100
        return daily_return >= self.daily_target
    
    def get_performance_metrics(self) -> Dict:
        """Get current performance metrics"""
        daily_return = (self.daily_pnl / self.config.get('base_capital', 10000)) * 100
        total_return = (self.total_pnl / self.config.get('base_capital', 10000)) * 100
        
        return {
            'current_capital': self.current_capital,
            'daily_pnl': self.daily_pnl,
            'total_pnl': self.total_pnl,
            'daily_return': daily_return,
            'total_return': total_return,
            'daily_target_reached': self.should_stop_trading_today()
        }
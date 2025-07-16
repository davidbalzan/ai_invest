import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum

class RiskProfile(Enum):
    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"
    CUSTOM = "custom"

@dataclass
class InvestmentStrategy:
    """Represents a complete investment strategy configuration"""
    
    # Strategy Identity
    name: str
    description: str
    risk_profile: RiskProfile
    created_date: str
    last_modified: str
    active: bool = True
    
    # Risk Management
    stop_loss_percent: float = -10.0
    take_profit_percent: float = 20.0
    max_position_size_percent: float = 15.0  # Max % of portfolio per position
    max_sector_allocation_percent: float = 30.0  # Max % per sector
    cash_reserve_percent: float = 5.0  # Min cash reserve
    
    # Technical Analysis Settings
    rsi_overbought_threshold: float = 70.0
    rsi_oversold_threshold: float = 30.0
    rsi_rebalance_trigger: bool = True
    moving_average_periods: List[int] = None  # [20, 50] default
    use_macd_signals: bool = True
    
    # Sentiment Analysis Settings
    sentiment_weight: float = 0.3  # Weight in decision making (0-1)
    min_sentiment_score_buy: float = 0.1  # Min sentiment for buy signals
    sentiment_rebalance_trigger: bool = True
    news_articles_threshold: int = 5  # Min articles for reliable sentiment
    
    # Portfolio Management
    rebalancing_frequency: str = "weekly"  # daily, weekly, monthly
    auto_rebalancing: bool = False
    diversification_target: int = 10  # Target number of positions
    sector_diversification: bool = True
    
    # AI Decision Making
    ai_recommendation_weight: float = 0.7  # Weight of AI vs technical analysis
    require_multiple_signals: bool = True  # Require multiple buy/sell signals
    override_human_decisions: bool = False
    
    # Reporting and Monitoring
    notification_frequency: str = "daily"  # never, daily, weekly, monthly
    detailed_reporting: bool = True
    include_charts: bool = True
    email_reports: bool = False
    
    # Performance Targets
    annual_return_target: float = 12.0  # Target annual return %
    max_drawdown_tolerance: float = -15.0  # Max acceptable drawdown
    sharpe_ratio_target: float = 1.0  # Target risk-adjusted return
    
    def __post_init__(self):
        if self.moving_average_periods is None:
            self.moving_average_periods = [20, 50]

class StrategyManager:
    """Manages multiple investment strategies with different risk profiles"""
    
    def __init__(self, strategies_dir: str = "strategies"):
        self.strategies_dir = strategies_dir
        self.ensure_strategies_dir()
        self.strategies: Dict[str, InvestmentStrategy] = {}
        self.load_strategies()
        
        # Create default strategies if none exist
        if not self.strategies:
            self.create_default_strategies()
    
    def ensure_strategies_dir(self):
        """Create strategies directory if it doesn't exist"""
        os.makedirs(self.strategies_dir, exist_ok=True)
    
    def create_default_strategies(self):
        """Create default investment strategies"""
        
        # Conservative Strategy
        conservative = InvestmentStrategy(
            name="Conservative Growth",
            description="Low-risk strategy focused on stable, dividend-paying stocks with minimal volatility",
            risk_profile=RiskProfile.CONSERVATIVE,
            created_date=datetime.now().isoformat(),
            last_modified=datetime.now().isoformat(),
            
            # Conservative risk management
            stop_loss_percent=-5.0,
            take_profit_percent=10.0,
            max_position_size_percent=10.0,
            max_sector_allocation_percent=25.0,
            cash_reserve_percent=15.0,
            
            # Conservative technical settings
            rsi_overbought_threshold=65.0,
            rsi_oversold_threshold=35.0,
            rsi_rebalance_trigger=True,
            moving_average_periods=[50, 200],
            use_macd_signals=False,
            
            # Conservative sentiment settings
            sentiment_weight=0.2,
            min_sentiment_score_buy=0.3,
            sentiment_rebalance_trigger=False,
            news_articles_threshold=10,
            
            # Conservative portfolio management
            rebalancing_frequency="monthly",
            auto_rebalancing=False,
            diversification_target=15,
            sector_diversification=True,
            
            # Conservative AI settings
            ai_recommendation_weight=0.5,
            require_multiple_signals=True,
            override_human_decisions=False,
            
            # Performance targets
            annual_return_target=8.0,
            max_drawdown_tolerance=-8.0,
            sharpe_ratio_target=0.8
        )
        
        # Moderate Strategy
        moderate = InvestmentStrategy(
            name="Balanced Growth",
            description="Moderate-risk strategy balancing growth and stability with diversified portfolio",
            risk_profile=RiskProfile.MODERATE,
            created_date=datetime.now().isoformat(),
            last_modified=datetime.now().isoformat(),
            
            # Moderate risk management
            stop_loss_percent=-10.0,
            take_profit_percent=20.0,
            max_position_size_percent=15.0,
            max_sector_allocation_percent=30.0,
            cash_reserve_percent=10.0,
            
            # Moderate technical settings
            rsi_overbought_threshold=70.0,
            rsi_oversold_threshold=30.0,
            rsi_rebalance_trigger=True,
            moving_average_periods=[20, 50],
            use_macd_signals=True,
            
            # Moderate sentiment settings
            sentiment_weight=0.3,
            min_sentiment_score_buy=0.1,
            sentiment_rebalance_trigger=True,
            news_articles_threshold=5,
            
            # Moderate portfolio management
            rebalancing_frequency="weekly",
            auto_rebalancing=False,
            diversification_target=10,
            sector_diversification=True,
            
            # Moderate AI settings
            ai_recommendation_weight=0.7,
            require_multiple_signals=True,
            override_human_decisions=False,
            
            # Performance targets
            annual_return_target=12.0,
            max_drawdown_tolerance=-15.0,
            sharpe_ratio_target=1.0
        )
        
        # Aggressive Strategy
        aggressive = InvestmentStrategy(
            name="Aggressive Growth",
            description="High-risk, high-reward strategy focused on growth stocks and momentum trading",
            risk_profile=RiskProfile.AGGRESSIVE,
            created_date=datetime.now().isoformat(),
            last_modified=datetime.now().isoformat(),
            
            # Aggressive risk management
            stop_loss_percent=-15.0,
            take_profit_percent=30.0,
            max_position_size_percent=25.0,
            max_sector_allocation_percent=40.0,
            cash_reserve_percent=5.0,
            
            # Aggressive technical settings
            rsi_overbought_threshold=80.0,
            rsi_oversold_threshold=20.0,
            rsi_rebalance_trigger=True,
            moving_average_periods=[10, 20],
            use_macd_signals=True,
            
            # Aggressive sentiment settings
            sentiment_weight=0.4,
            min_sentiment_score_buy=0.0,
            sentiment_rebalance_trigger=True,
            news_articles_threshold=3,
            
            # Aggressive portfolio management
            rebalancing_frequency="daily",
            auto_rebalancing=True,
            diversification_target=6,
            sector_diversification=False,
            
            # Aggressive AI settings
            ai_recommendation_weight=0.8,
            require_multiple_signals=False,
            override_human_decisions=True,
            
            # Performance targets
            annual_return_target=25.0,
            max_drawdown_tolerance=-25.0,
            sharpe_ratio_target=1.2
        )
        
        # Save default strategies
        self.save_strategy(conservative)
        self.save_strategy(moderate)
        self.save_strategy(aggressive)
        
        # Set moderate as default active strategy
        self.set_active_strategy("Balanced Growth")
    
    def save_strategy(self, strategy: InvestmentStrategy):
        """Save a strategy to disk and memory"""
        strategy.last_modified = datetime.now().isoformat()
        
        # Save to disk
        filename = f"{strategy.name.lower().replace(' ', '_')}.json"
        filepath = os.path.join(self.strategies_dir, filename)
        
        with open(filepath, 'w') as f:
            # Convert dataclass to dict, handling enum
            strategy_dict = asdict(strategy)
            strategy_dict['risk_profile'] = strategy.risk_profile.value
            json.dump(strategy_dict, f, indent=2)
        
        # Save to memory
        self.strategies[strategy.name] = strategy
    
    def load_strategies(self):
        """Load all strategies from disk"""
        if not os.path.exists(self.strategies_dir):
            return
        
        for filename in os.listdir(self.strategies_dir):
            if filename.endswith('.json'):
                filepath = os.path.join(self.strategies_dir, filename)
                
                try:
                    with open(filepath, 'r') as f:
                        strategy_dict = json.load(f)
                    
                    # Convert risk_profile back to enum
                    strategy_dict['risk_profile'] = RiskProfile(strategy_dict['risk_profile'])
                    
                    strategy = InvestmentStrategy(**strategy_dict)
                    self.strategies[strategy.name] = strategy
                    
                except Exception as e:
                    print(f"Error loading strategy from {filename}: {e}")
    
    def get_strategy(self, name: str) -> Optional[InvestmentStrategy]:
        """Get a strategy by name"""
        return self.strategies.get(name)
    
    def get_active_strategy(self) -> Optional[InvestmentStrategy]:
        """Get the currently active strategy"""
        for strategy in self.strategies.values():
            if strategy.active:
                return strategy
        return None
    
    def set_active_strategy(self, name: str) -> bool:
        """Set a strategy as active (deactivate others)"""
        if name not in self.strategies:
            return False
        
        # Deactivate all strategies
        for strategy in self.strategies.values():
            strategy.active = False
            self.save_strategy(strategy)
        
        # Activate the selected strategy
        self.strategies[name].active = True
        self.save_strategy(self.strategies[name])
        return True
    
    def list_strategies(self) -> List[str]:
        """List all available strategy names"""
        return list(self.strategies.keys())
    
    def delete_strategy(self, name: str) -> bool:
        """Delete a strategy"""
        if name not in self.strategies:
            return False
        
        # Don't delete if it's the only strategy
        if len(self.strategies) <= 1:
            return False
        
        # Remove from disk
        filename = f"{name.lower().replace(' ', '_')}.json"
        filepath = os.path.join(self.strategies_dir, filename)
        
        if os.path.exists(filepath):
            os.remove(filepath)
        
        # If deleting active strategy, activate another one
        if self.strategies[name].active and len(self.strategies) > 1:
            remaining_strategies = [s for s in self.strategies.keys() if s != name]
            self.set_active_strategy(remaining_strategies[0])
        
        # Remove from memory
        del self.strategies[name]
        return True
    
    def create_custom_strategy(self, name: str, description: str, **kwargs) -> InvestmentStrategy:
        """Create a custom strategy with specified parameters"""
        
        # Start with moderate defaults
        moderate_strategy = self.get_strategy("Balanced Growth")
        if moderate_strategy:
            defaults = asdict(moderate_strategy)
        else:
            defaults = {}
        
        # Override with custom parameters
        defaults.update({
            'name': name,
            'description': description,
            'risk_profile': RiskProfile.CUSTOM,
            'created_date': datetime.now().isoformat(),
            'last_modified': datetime.now().isoformat(),
            'active': False
        })
        defaults.update(kwargs)
        
        # Ensure risk_profile is enum
        if isinstance(defaults.get('risk_profile'), str):
            defaults['risk_profile'] = RiskProfile(defaults['risk_profile'])
        
        strategy = InvestmentStrategy(**defaults)
        self.save_strategy(strategy)
        return strategy
    
    def compare_strategies(self, strategy_names: List[str]) -> Dict[str, Any]:
        """Compare multiple strategies across key metrics"""
        comparison = {
            'strategies': strategy_names,
            'comparison_date': datetime.now().isoformat(),
            'metrics': {}
        }
        
        metrics_to_compare = [
            'risk_profile', 'stop_loss_percent', 'take_profit_percent',
            'max_position_size_percent', 'sentiment_weight', 'annual_return_target',
            'max_drawdown_tolerance', 'diversification_target'
        ]
        
        for metric in metrics_to_compare:
            comparison['metrics'][metric] = {}
            for name in strategy_names:
                strategy = self.get_strategy(name)
                if strategy:
                    value = getattr(strategy, metric)
                    if isinstance(value, RiskProfile):
                        value = value.value
                    comparison['metrics'][metric][name] = value
        
        return comparison
    
    def validate_strategy(self, strategy: InvestmentStrategy) -> Dict[str, List[str]]:
        """Validate strategy settings and return warnings/errors"""
        warnings = []
        errors = []
        
        # Risk management validation
        if strategy.stop_loss_percent >= 0:
            errors.append("Stop loss percent must be negative")
        
        if strategy.take_profit_percent <= 0:
            errors.append("Take profit percent must be positive")
        
        if strategy.max_position_size_percent > 50:
            warnings.append("Max position size > 50% creates concentration risk")
        
        if strategy.cash_reserve_percent < 0 or strategy.cash_reserve_percent > 50:
            warnings.append("Cash reserve should be between 0-50%")
        
        # Technical analysis validation
        if strategy.rsi_overbought_threshold <= strategy.rsi_oversold_threshold:
            errors.append("RSI overbought threshold must be higher than oversold")
        
        if not strategy.moving_average_periods or len(strategy.moving_average_periods) < 2:
            warnings.append("At least 2 moving average periods recommended")
        
        # Sentiment validation
        if strategy.sentiment_weight < 0 or strategy.sentiment_weight > 1:
            errors.append("Sentiment weight must be between 0 and 1")
        
        # Performance targets validation
        if strategy.annual_return_target < 0:
            warnings.append("Negative return target is unusual")
        
        if strategy.max_drawdown_tolerance > -5:
            warnings.append("Max drawdown tolerance should typically be < -5%")
        
        return {'warnings': warnings, 'errors': errors}
    
    def get_strategy_summary(self, name: str) -> Optional[Dict[str, Any]]:
        """Get a summary of a strategy for reporting"""
        strategy = self.get_strategy(name)
        if not strategy:
            return None
        
        return {
            'name': strategy.name,
            'description': strategy.description,
            'risk_profile': strategy.risk_profile.value.title(),
            'active': strategy.active,
            'created_date': strategy.created_date,
            'last_modified': strategy.last_modified,
            
            'risk_management': {
                'stop_loss': f"{strategy.stop_loss_percent:+.1f}%",
                'take_profit': f"{strategy.take_profit_percent:+.1f}%",
                'max_position_size': f"{strategy.max_position_size_percent:.1f}%",
                'cash_reserve': f"{strategy.cash_reserve_percent:.1f}%"
            },
            
            'technical_analysis': {
                'rsi_thresholds': f"{strategy.rsi_oversold_threshold}-{strategy.rsi_overbought_threshold}",
                'moving_averages': strategy.moving_average_periods,
                'use_macd': strategy.use_macd_signals
            },
            
            'sentiment_analysis': {
                'weight': f"{strategy.sentiment_weight:.1%}",
                'min_buy_score': strategy.min_sentiment_score_buy,
                'min_articles': strategy.news_articles_threshold
            },
            
            'portfolio_management': {
                'rebalancing': strategy.rebalancing_frequency,
                'auto_rebalancing': strategy.auto_rebalancing,
                'target_positions': strategy.diversification_target
            },
            
            'performance_targets': {
                'annual_return': f"{strategy.annual_return_target:.1f}%",
                'max_drawdown': f"{strategy.max_drawdown_tolerance:.1f}%",
                'sharpe_ratio': strategy.sharpe_ratio_target
            }
        } 
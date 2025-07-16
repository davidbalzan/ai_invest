-- Add strategy and risk management fields to portfolios table
-- Migration: add_portfolio_strategy_fields

ALTER TABLE portfolios 
ADD COLUMN IF NOT EXISTS strategy VARCHAR(50) DEFAULT 'balanced_growth',
ADD COLUMN IF NOT EXISTS risk_level VARCHAR(20) DEFAULT 'moderate',
ADD COLUMN IF NOT EXISTS max_position_percent DECIMAL(5,2),
ADD COLUMN IF NOT EXISTS stop_loss_percent DECIMAL(6,2),
ADD COLUMN IF NOT EXISTS take_profit_percent DECIMAL(6,2),
ADD COLUMN IF NOT EXISTS daily_loss_limit DECIMAL(15,2),
ADD COLUMN IF NOT EXISTS rebalance_frequency VARCHAR(20) DEFAULT 'monthly';

-- Add comments for documentation
COMMENT ON COLUMN portfolios.strategy IS 'Investment strategy: conservative_growth, balanced_growth, aggressive_growth';
COMMENT ON COLUMN portfolios.risk_level IS 'Risk tolerance level: low, moderate, high';
COMMENT ON COLUMN portfolios.max_position_percent IS 'Maximum position size as percentage of portfolio';
COMMENT ON COLUMN portfolios.stop_loss_percent IS 'Stop loss percentage (negative value)';
COMMENT ON COLUMN portfolios.take_profit_percent IS 'Take profit percentage (positive value)';
COMMENT ON COLUMN portfolios.daily_loss_limit IS 'Maximum daily loss limit in dollars';
COMMENT ON COLUMN portfolios.rebalance_frequency IS 'Portfolio rebalancing frequency: never, weekly, monthly, quarterly';

-- Update existing portfolios with default values if they have NULL values
UPDATE portfolios 
SET 
    strategy = COALESCE(strategy, 'balanced_growth'),
    risk_level = COALESCE(risk_level, 'moderate'),
    rebalance_frequency = COALESCE(rebalance_frequency, 'monthly')
WHERE strategy IS NULL OR risk_level IS NULL OR rebalance_frequency IS NULL; 
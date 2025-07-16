-- Add raw analysis data storage fields for backtesting
-- Migration: add_analysis_raw_data_storage

ALTER TABLE analysis_sessions 
ADD COLUMN IF NOT EXISTS market_data_snapshot JSONB,
ADD COLUMN IF NOT EXISTS portfolio_snapshot JSONB,
ADD COLUMN IF NOT EXISTS ai_recommendations JSONB,
ADD COLUMN IF NOT EXISTS sentiment_analysis JSONB,
ADD COLUMN IF NOT EXISTS technical_indicators JSONB,
ADD COLUMN IF NOT EXISTS risk_metrics JSONB,
ADD COLUMN IF NOT EXISTS trading_signals JSONB,
ADD COLUMN IF NOT EXISTS backtesting_context JSONB;

-- Add comments for documentation
COMMENT ON COLUMN analysis_sessions.market_data_snapshot IS 'Complete market data snapshot at analysis time - critical for backtesting';
COMMENT ON COLUMN analysis_sessions.portfolio_snapshot IS 'Portfolio state snapshot including holdings, cash, total value at analysis time';
COMMENT ON COLUMN analysis_sessions.ai_recommendations IS 'Raw AI recommendations with confidence scores, reasoning, and alternative scenarios';
COMMENT ON COLUMN analysis_sessions.sentiment_analysis IS 'News sentiment, market sentiment, social media sentiment data';
COMMENT ON COLUMN analysis_sessions.technical_indicators IS 'All calculated technical indicators (RSI, MACD, moving averages, etc.)';
COMMENT ON COLUMN analysis_sessions.risk_metrics IS 'Risk assessment metrics including VaR, beta, volatility, correlations';
COMMENT ON COLUMN analysis_sessions.trading_signals IS 'Generated buy/sell/hold signals with entry/exit points and position sizing';
COMMENT ON COLUMN analysis_sessions.backtesting_context IS 'Additional context for backtesting including market conditions, volatility regime, etc.';

-- Create indexes for efficient backtesting queries
CREATE INDEX IF NOT EXISTS idx_analysis_sessions_started_at_status ON analysis_sessions(started_at, status);
CREATE INDEX IF NOT EXISTS idx_analysis_sessions_portfolio_completed ON analysis_sessions(portfolio_id, completed_at) WHERE status = 'COMPLETED';

-- Create a function to validate and extract backtesting data
CREATE OR REPLACE FUNCTION get_backtesting_data(session_id UUID)
RETURNS JSON AS $$
DECLARE
    result JSON;
BEGIN
    SELECT json_build_object(
        'session_id', id,
        'portfolio_id', portfolio_id,
        'analysis_type', analysis_type,
        'timestamp', started_at,
        'market_data', market_data_snapshot,
        'portfolio_state', portfolio_snapshot,
        'recommendations', ai_recommendations,
        'sentiment', sentiment_analysis,
        'technical_indicators', technical_indicators,
        'risk_metrics', risk_metrics,
        'trading_signals', trading_signals,
        'context', backtesting_context
    ) INTO result
    FROM analysis_sessions
    WHERE id = session_id AND status = 'COMPLETED'
    AND market_data_snapshot IS NOT NULL;
    
    RETURN result;
END;
$$ LANGUAGE plpgsql; 
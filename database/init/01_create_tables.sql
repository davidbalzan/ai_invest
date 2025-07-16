-- AI Investment Tool Database Schema
-- Created: 2025-01-15

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Users table for multi-user support
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    timezone VARCHAR(50) DEFAULT 'UTC',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE
);

-- Portfolios table for multi-portfolio management
CREATE TABLE portfolios (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    total_value DECIMAL(15,2) DEFAULT 0.00,
    cash_balance DECIMAL(15,2) DEFAULT 0.00,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE,
    UNIQUE(user_id, name)
);

-- Holdings table for current portfolio positions
CREATE TABLE holdings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    portfolio_id UUID NOT NULL REFERENCES portfolios(id) ON DELETE CASCADE,
    symbol VARCHAR(20) NOT NULL,
    company_name VARCHAR(255),
    shares DECIMAL(15,6) NOT NULL DEFAULT 0,
    average_cost DECIMAL(15,4) DEFAULT 0.00,
    current_price DECIMAL(15,4),
    market_value DECIMAL(15,2),
    unrealized_gain_loss DECIMAL(15,2),
    unrealized_gain_loss_percent DECIMAL(8,4),
    sector VARCHAR(100),
    industry VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(portfolio_id, symbol)
);

-- Transactions table for complete transaction history
CREATE TABLE transactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    portfolio_id UUID NOT NULL REFERENCES portfolios(id) ON DELETE CASCADE,
    symbol VARCHAR(20) NOT NULL,
    transaction_type VARCHAR(20) NOT NULL CHECK (transaction_type IN ('BUY', 'SELL', 'DIVIDEND', 'SPLIT', 'DEPOSIT', 'WITHDRAWAL')),
    shares DECIMAL(15,6),
    price DECIMAL(15,4),
    total_amount DECIMAL(15,2) NOT NULL,
    fees DECIMAL(15,2) DEFAULT 0.00,
    transaction_date TIMESTAMP WITH TIME ZONE NOT NULL,
    settlement_date TIMESTAMP WITH TIME ZONE,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    external_reference VARCHAR(255)
);

-- Analysis sessions table for tracking analysis requests
CREATE TABLE analysis_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    portfolio_id UUID NOT NULL REFERENCES portfolios(id) ON DELETE CASCADE,
    analysis_type VARCHAR(50) NOT NULL,
    status VARCHAR(20) DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'RUNNING', 'COMPLETED', 'FAILED')),
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    execution_time_ms INTEGER,
    api_calls_made INTEGER DEFAULT 0,
    cache_hits INTEGER DEFAULT 0,
    cost_estimate DECIMAL(10,4),
    error_message TEXT,
    report_path VARCHAR(500)
);

-- Stock data cache table (replacing JSON file cache)
CREATE TABLE stock_data_cache (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    cache_key VARCHAR(255) UNIQUE NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    data_type VARCHAR(50) NOT NULL, -- 'price_data', 'technical_indicators', 'company_info'
    data JSONB NOT NULL,
    market_session VARCHAR(20),
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    accessed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    access_count INTEGER DEFAULT 1
);

-- News sentiment cache table
CREATE TABLE news_sentiment_cache (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    cache_key VARCHAR(255) UNIQUE NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    articles JSONB NOT NULL,
    sentiment_score DECIMAL(5,4),
    article_count INTEGER,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    accessed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    access_count INTEGER DEFAULT 1
);

-- AI analysis cache table
CREATE TABLE ai_analysis_cache (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    cache_key VARCHAR(255) UNIQUE NOT NULL,
    context_hash VARCHAR(64) NOT NULL,
    analysis_type VARCHAR(50) NOT NULL,
    prompt_tokens INTEGER,
    completion_tokens INTEGER,
    response JSONB NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    accessed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    access_count INTEGER DEFAULT 1
);

-- Market data table for tracking market sessions and holidays
CREATE TABLE market_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    date DATE NOT NULL UNIQUE,
    session_type VARCHAR(20) NOT NULL CHECK (session_type IN ('MARKET_OPEN', 'MARKET_CLOSE', 'PRE_MARKET', 'POST_MARKET', 'WEEKEND', 'HOLIDAY')),
    market_open_time TIME,
    market_close_time TIME,
    is_trading_day BOOLEAN DEFAULT TRUE,
    holiday_name VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_portfolios_user_id ON portfolios(user_id);
CREATE INDEX idx_portfolios_active ON portfolios(is_active);

CREATE INDEX idx_holdings_portfolio_id ON holdings(portfolio_id);
CREATE INDEX idx_holdings_symbol ON holdings(symbol);
CREATE INDEX idx_holdings_updated_at ON holdings(updated_at);

CREATE INDEX idx_transactions_portfolio_id ON transactions(portfolio_id);
CREATE INDEX idx_transactions_symbol ON transactions(symbol);
CREATE INDEX idx_transactions_type ON transactions(transaction_type);
CREATE INDEX idx_transactions_date ON transactions(transaction_date);

CREATE INDEX idx_analysis_sessions_portfolio_id ON analysis_sessions(portfolio_id);
CREATE INDEX idx_analysis_sessions_status ON analysis_sessions(status);
CREATE INDEX idx_analysis_sessions_started_at ON analysis_sessions(started_at);

CREATE INDEX idx_stock_data_cache_key ON stock_data_cache(cache_key);
CREATE INDEX idx_stock_data_cache_symbol ON stock_data_cache(symbol);
CREATE INDEX idx_stock_data_cache_expires ON stock_data_cache(expires_at);
CREATE INDEX idx_stock_data_cache_accessed ON stock_data_cache(accessed_at);

CREATE INDEX idx_news_sentiment_cache_key ON news_sentiment_cache(cache_key);
CREATE INDEX idx_news_sentiment_cache_symbol ON news_sentiment_cache(symbol);
CREATE INDEX idx_news_sentiment_cache_expires ON news_sentiment_cache(expires_at);

CREATE INDEX idx_ai_analysis_cache_key ON ai_analysis_cache(cache_key);
CREATE INDEX idx_ai_analysis_cache_context ON ai_analysis_cache(context_hash);
CREATE INDEX idx_ai_analysis_cache_expires ON ai_analysis_cache(expires_at);

CREATE INDEX idx_market_sessions_date ON market_sessions(date);
CREATE INDEX idx_market_sessions_type ON market_sessions(session_type);

-- Triggers for updated_at timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_portfolios_updated_at BEFORE UPDATE ON portfolios
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_holdings_updated_at BEFORE UPDATE ON holdings
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column(); 
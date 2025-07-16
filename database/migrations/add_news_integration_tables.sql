-- Add news integration tables and functionality
-- Migration: add_news_integration_tables

-- News Articles Table
CREATE TABLE IF NOT EXISTS news_articles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(500) NOT NULL,
    description TEXT,
    content TEXT,
    url VARCHAR(1000) NOT NULL,
    url_to_image VARCHAR(1000),
    source_name VARCHAR(100) NOT NULL,
    source_id VARCHAR(50),
    author VARCHAR(200),
    published_at TIMESTAMP WITH TIME ZONE NOT NULL,
    content_hash VARCHAR(64) UNIQUE, -- For deduplication
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- News Categories and Classification
CREATE TABLE IF NOT EXISTS news_categories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    article_id UUID REFERENCES news_articles(id) ON DELETE CASCADE,
    category_type VARCHAR(50) NOT NULL, -- 'primary', 'sector', 'custom'
    category_value VARCHAR(100) NOT NULL, -- 'earnings', 'technology', etc.
    confidence_score DECIMAL(3,2), -- 0.00 to 1.00
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- News Sentiment Analysis
CREATE TABLE IF NOT EXISTS news_sentiment (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    article_id UUID REFERENCES news_articles(id) ON DELETE CASCADE,
    sentiment VARCHAR(20) NOT NULL, -- 'positive', 'negative', 'neutral'
    sentiment_score DECIMAL(4,3), -- -1.000 to 1.000
    confidence_score DECIMAL(3,2), -- 0.00 to 1.00
    impact_level VARCHAR(20), -- 'high', 'medium', 'low'
    keywords JSONB, -- Extracted keywords and their weights
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Stock-News Relationships
CREATE TABLE IF NOT EXISTS stock_news_relevance (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    article_id UUID REFERENCES news_articles(id) ON DELETE CASCADE,
    symbol VARCHAR(20) NOT NULL,
    relevance_score DECIMAL(4,3) NOT NULL, -- 0.000 to 1.000
    mention_count INTEGER DEFAULT 1,
    context_type VARCHAR(50), -- 'direct_mention', 'sector_related', 'competitor'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(article_id, symbol)
);

-- News Sources Management
CREATE TABLE IF NOT EXISTS news_sources (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_id VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    url VARCHAR(500),
    category VARCHAR(50),
    language VARCHAR(10),
    country VARCHAR(10),
    quality_score DECIMAL(3,2) DEFAULT 0.50, -- 0.00 to 1.00
    is_active BOOLEAN DEFAULT TRUE,
    api_provider VARCHAR(50), -- 'newsapi', 'alpha_vantage', 'finnhub'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- User News Preferences
CREATE TABLE IF NOT EXISTS user_news_preferences (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    categories JSONB, -- Preferred categories and weights
    sources JSONB, -- Preferred/blocked sources
    sentiment_threshold DECIMAL(3,2) DEFAULT 0.30,
    impact_threshold VARCHAR(20) DEFAULT 'medium',
    notification_settings JSONB,
    refresh_frequency INTEGER DEFAULT 60, -- minutes
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id)
);

-- News Fetch Jobs and Scheduling
CREATE TABLE IF NOT EXISTS news_fetch_jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_type VARCHAR(50) NOT NULL, -- 'scheduled', 'manual', 'portfolio_triggered'
    user_id UUID REFERENCES users(id),
    portfolio_id UUID REFERENCES portfolios(id),
    symbols JSONB, -- Array of symbols to fetch news for
    status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'running', 'completed', 'failed'
    api_provider VARCHAR(50),
    articles_fetched INTEGER DEFAULT 0,
    api_calls_made INTEGER DEFAULT 0,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_news_articles_published_at ON news_articles(published_at DESC);
CREATE INDEX IF NOT EXISTS idx_news_articles_source ON news_articles(source_name);
CREATE INDEX IF NOT EXISTS idx_news_articles_content_hash ON news_articles(content_hash);
CREATE INDEX IF NOT EXISTS idx_news_articles_title_search ON news_articles USING gin(to_tsvector('english', title));
CREATE INDEX IF NOT EXISTS idx_news_articles_content_search ON news_articles USING gin(to_tsvector('english', coalesce(content, description)));

CREATE INDEX IF NOT EXISTS idx_stock_news_relevance_symbol ON stock_news_relevance(symbol);
CREATE INDEX IF NOT EXISTS idx_stock_news_relevance_score ON stock_news_relevance(relevance_score DESC);
CREATE INDEX IF NOT EXISTS idx_stock_news_relevance_article ON stock_news_relevance(article_id);

CREATE INDEX IF NOT EXISTS idx_news_sentiment_sentiment ON news_sentiment(sentiment);
CREATE INDEX IF NOT EXISTS idx_news_sentiment_impact ON news_sentiment(impact_level);
CREATE INDEX IF NOT EXISTS idx_news_sentiment_article ON news_sentiment(article_id);

CREATE INDEX IF NOT EXISTS idx_news_categories_category ON news_categories(category_type, category_value);
CREATE INDEX IF NOT EXISTS idx_news_categories_article ON news_categories(article_id);

CREATE INDEX IF NOT EXISTS idx_news_sources_provider ON news_sources(api_provider);
CREATE INDEX IF NOT EXISTS idx_news_sources_active ON news_sources(is_active);

CREATE INDEX IF NOT EXISTS idx_user_news_preferences_user ON user_news_preferences(user_id);

CREATE INDEX IF NOT EXISTS idx_news_fetch_jobs_status ON news_fetch_jobs(status);
CREATE INDEX IF NOT EXISTS idx_news_fetch_jobs_user ON news_fetch_jobs(user_id);
CREATE INDEX IF NOT EXISTS idx_news_fetch_jobs_portfolio ON news_fetch_jobs(portfolio_id);
CREATE INDEX IF NOT EXISTS idx_news_fetch_jobs_created ON news_fetch_jobs(created_at);

-- Add constraints and checks
ALTER TABLE news_sentiment 
ADD CONSTRAINT chk_sentiment_values CHECK (sentiment IN ('positive', 'negative', 'neutral'));

ALTER TABLE news_sentiment 
ADD CONSTRAINT chk_sentiment_score_range CHECK (sentiment_score >= -1.000 AND sentiment_score <= 1.000);

ALTER TABLE news_sentiment 
ADD CONSTRAINT chk_confidence_score_range CHECK (confidence_score >= 0.00 AND confidence_score <= 1.00);

ALTER TABLE news_sentiment 
ADD CONSTRAINT chk_impact_level_values CHECK (impact_level IN ('high', 'medium', 'low'));

ALTER TABLE stock_news_relevance 
ADD CONSTRAINT chk_relevance_score_range CHECK (relevance_score >= 0.000 AND relevance_score <= 1.000);

ALTER TABLE news_sources 
ADD CONSTRAINT chk_quality_score_range CHECK (quality_score >= 0.00 AND quality_score <= 1.00);

ALTER TABLE user_news_preferences 
ADD CONSTRAINT chk_sentiment_threshold_range CHECK (sentiment_threshold >= 0.00 AND sentiment_threshold <= 1.00);

ALTER TABLE user_news_preferences 
ADD CONSTRAINT chk_impact_threshold_values CHECK (impact_threshold IN ('high', 'medium', 'low'));

ALTER TABLE news_fetch_jobs 
ADD CONSTRAINT chk_job_status_values CHECK (status IN ('pending', 'running', 'completed', 'failed'));

-- Add comments for documentation
COMMENT ON TABLE news_articles IS 'Core news articles storage with deduplication support';
COMMENT ON COLUMN news_articles.content_hash IS 'SHA-256 hash of title+content for deduplication';
COMMENT ON COLUMN news_articles.published_at IS 'Original publication timestamp from news source';

COMMENT ON TABLE news_categories IS 'News article categorization with confidence scoring';
COMMENT ON COLUMN news_categories.category_type IS 'Type of categorization: primary (earnings, M&A), sector (tech, healthcare), custom';
COMMENT ON COLUMN news_categories.confidence_score IS 'AI confidence in categorization (0.00-1.00)';

COMMENT ON TABLE news_sentiment IS 'Sentiment analysis results for news articles';
COMMENT ON COLUMN news_sentiment.sentiment_score IS 'Numerical sentiment score (-1.000 to 1.000)';
COMMENT ON COLUMN news_sentiment.keywords IS 'Extracted keywords with sentiment weights';

COMMENT ON TABLE stock_news_relevance IS 'Mapping between news articles and stock symbols with relevance scoring';
COMMENT ON COLUMN stock_news_relevance.relevance_score IS 'How relevant the article is to the stock (0.000-1.000)';
COMMENT ON COLUMN stock_news_relevance.context_type IS 'Type of relevance: direct mention, sector related, competitor';

COMMENT ON TABLE news_sources IS 'News source management with quality scoring';
COMMENT ON COLUMN news_sources.quality_score IS 'Source reliability score based on accuracy and timeliness';

COMMENT ON TABLE user_news_preferences IS 'User-specific news preferences and notification settings';
COMMENT ON COLUMN user_news_preferences.categories IS 'JSON object with category preferences and weights';
COMMENT ON COLUMN user_news_preferences.sources IS 'JSON object with source preferences (enabled/disabled)';

COMMENT ON TABLE news_fetch_jobs IS 'Background job tracking for news fetching operations';
COMMENT ON COLUMN news_fetch_jobs.symbols IS 'JSON array of stock symbols to fetch news for';

-- Triggers for updated_at timestamps
CREATE TRIGGER update_news_sources_updated_at BEFORE UPDATE ON news_sources
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_news_preferences_updated_at BEFORE UPDATE ON user_news_preferences
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_news_articles_updated_at BEFORE UPDATE ON news_articles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Helper functions for news operations
CREATE OR REPLACE FUNCTION get_portfolio_news(portfolio_uuid UUID, limit_count INTEGER DEFAULT 50)
RETURNS TABLE (
    article_id UUID,
    title VARCHAR(500),
    description TEXT,
    url VARCHAR(1000),
    source_name VARCHAR(100),
    published_at TIMESTAMP WITH TIME ZONE,
    sentiment VARCHAR(20),
    sentiment_score DECIMAL(4,3),
    impact_level VARCHAR(20),
    relevance_score DECIMAL(4,3),
    symbol VARCHAR(20)
) AS $
BEGIN
    RETURN QUERY
    SELECT 
        na.id,
        na.title,
        na.description,
        na.url,
        na.source_name,
        na.published_at,
        ns.sentiment,
        ns.sentiment_score,
        ns.impact_level,
        snr.relevance_score,
        snr.symbol
    FROM news_articles na
    JOIN stock_news_relevance snr ON na.id = snr.article_id
    JOIN holdings h ON snr.symbol = h.symbol
    LEFT JOIN news_sentiment ns ON na.id = ns.article_id
    WHERE h.portfolio_id = portfolio_uuid
    ORDER BY na.published_at DESC, snr.relevance_score DESC
    LIMIT limit_count;
END;
$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION get_news_summary_stats(user_uuid UUID)
RETURNS JSON AS $
DECLARE
    result JSON;
BEGIN
    SELECT json_build_object(
        'total_articles', COUNT(DISTINCT na.id),
        'positive_sentiment', COUNT(CASE WHEN ns.sentiment = 'positive' THEN 1 END),
        'negative_sentiment', COUNT(CASE WHEN ns.sentiment = 'negative' THEN 1 END),
        'neutral_sentiment', COUNT(CASE WHEN ns.sentiment = 'neutral' THEN 1 END),
        'high_impact', COUNT(CASE WHEN ns.impact_level = 'high' THEN 1 END),
        'sources_count', COUNT(DISTINCT na.source_name),
        'last_updated', MAX(na.created_at)
    ) INTO result
    FROM news_articles na
    JOIN stock_news_relevance snr ON na.id = snr.article_id
    JOIN holdings h ON snr.symbol = h.symbol
    JOIN portfolios p ON h.portfolio_id = p.id
    LEFT JOIN news_sentiment ns ON na.id = ns.article_id
    WHERE p.user_id = user_uuid
    AND na.created_at >= NOW() - INTERVAL '7 days';
    
    RETURN result;
END;
$ LANGUAGE plpgsql;
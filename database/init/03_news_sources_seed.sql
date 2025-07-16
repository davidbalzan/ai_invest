-- News Sources Seed Data
-- Initial configuration for news sources and providers

-- Insert default news sources for different providers
INSERT INTO news_sources (source_id, name, description, url, category, language, country, quality_score, api_provider) VALUES
-- NewsAPI.org sources
('bbc-news', 'BBC News', 'BBC News - World', 'https://www.bbc.co.uk/news', 'general', 'en', 'gb', 0.90, 'newsapi'),
('reuters', 'Reuters', 'Reuters - Business and Financial News', 'https://www.reuters.com', 'business', 'en', 'us', 0.95, 'newsapi'),
('bloomberg', 'Bloomberg', 'Bloomberg - Business and Markets', 'https://www.bloomberg.com', 'business', 'en', 'us', 0.95, 'newsapi'),
('cnbc', 'CNBC', 'CNBC - Business News and Analysis', 'https://www.cnbc.com', 'business', 'en', 'us', 0.85, 'newsapi'),
('financial-times', 'Financial Times', 'Financial Times - Global Business News', 'https://www.ft.com', 'business', 'en', 'gb', 0.90, 'newsapi'),
('wall-street-journal', 'Wall Street Journal', 'The Wall Street Journal', 'https://www.wsj.com', 'business', 'en', 'us', 0.95, 'newsapi'),
('techcrunch', 'TechCrunch', 'TechCrunch - Technology News', 'https://techcrunch.com', 'technology', 'en', 'us', 0.80, 'newsapi'),
('ars-technica', 'Ars Technica', 'Ars Technica - Technology News and Analysis', 'https://arstechnica.com', 'technology', 'en', 'us', 0.85, 'newsapi'),
('the-verge', 'The Verge', 'The Verge - Technology News', 'https://www.theverge.com', 'technology', 'en', 'us', 0.80, 'newsapi'),
('engadget', 'Engadget', 'Engadget - Technology News and Reviews', 'https://www.engadget.com', 'technology', 'en', 'us', 0.75, 'newsapi'),

-- Alpha Vantage sources (general categories)
('alpha-vantage-general', 'Alpha Vantage News', 'Alpha Vantage Market News', 'https://www.alphavantage.co', 'business', 'en', 'us', 0.80, 'alpha_vantage'),

-- Finnhub sources
('finnhub-general', 'Finnhub News', 'Finnhub Market News and Analysis', 'https://finnhub.io', 'business', 'en', 'us', 0.85, 'finnhub'),

-- Yahoo Finance (scraped)
('yahoo-finance', 'Yahoo Finance', 'Yahoo Finance - Stock Market News', 'https://finance.yahoo.com', 'business', 'en', 'us', 0.75, 'yahoo'),

-- Additional quality sources
('marketwatch', 'MarketWatch', 'MarketWatch - Stock Market News', 'https://www.marketwatch.com', 'business', 'en', 'us', 0.80, 'newsapi'),
('seeking-alpha', 'Seeking Alpha', 'Seeking Alpha - Stock Analysis', 'https://seekingalpha.com', 'business', 'en', 'us', 0.85, 'newsapi'),
('barrons', 'Barrons', 'Barrons - Investment News and Analysis', 'https://www.barrons.com', 'business', 'en', 'us', 0.90, 'newsapi'),
('fortune', 'Fortune', 'Fortune - Business News and Analysis', 'https://fortune.com', 'business', 'en', 'us', 0.85, 'newsapi'),
('business-insider', 'Business Insider', 'Business Insider - Business News', 'https://www.businessinsider.com', 'business', 'en', 'us', 0.75, 'newsapi')

ON CONFLICT (source_id) DO UPDATE SET
    name = EXCLUDED.name,
    description = EXCLUDED.description,
    url = EXCLUDED.url,
    category = EXCLUDED.category,
    language = EXCLUDED.language,
    country = EXCLUDED.country,
    quality_score = EXCLUDED.quality_score,
    api_provider = EXCLUDED.api_provider,
    updated_at = NOW();

-- Insert default user news preferences for existing users
INSERT INTO user_news_preferences (user_id, categories, sources, sentiment_threshold, impact_threshold, notification_settings, refresh_frequency)
SELECT 
    u.id,
    '{"earnings": 1.0, "technology": 0.8, "healthcare": 0.6, "finance": 0.9, "energy": 0.5, "consumer": 0.4}'::jsonb,
    '{"reuters": true, "bloomberg": true, "cnbc": true, "wall-street-journal": true, "financial-times": true, "techcrunch": true}'::jsonb,
    0.30,
    'medium',
    '{"email": true, "push": false, "in_app": true, "quiet_hours": {"start": "22:00", "end": "07:00"}}'::jsonb,
    60
FROM users u
WHERE NOT EXISTS (
    SELECT 1 FROM user_news_preferences unp WHERE unp.user_id = u.id
);

-- Create some sample news categories for reference
CREATE TEMP TABLE temp_news_categories AS VALUES
    ('primary', 'earnings', 'Company earnings reports and financial results'),
    ('primary', 'merger_acquisition', 'Mergers, acquisitions, and corporate deals'),
    ('primary', 'regulatory', 'Regulatory changes and government policy'),
    ('primary', 'product_launch', 'New product launches and announcements'),
    ('primary', 'management_change', 'Executive and management changes'),
    ('primary', 'market_analysis', 'Market analysis and expert opinions'),
    ('primary', 'analyst_rating', 'Analyst ratings and price target changes'),
    ('sector', 'technology', 'Technology sector news'),
    ('sector', 'healthcare', 'Healthcare and pharmaceutical sector'),
    ('sector', 'finance', 'Financial services and banking sector'),
    ('sector', 'energy', 'Energy and utilities sector'),
    ('sector', 'consumer', 'Consumer goods and retail sector'),
    ('sector', 'industrial', 'Industrial and manufacturing sector'),
    ('sector', 'real_estate', 'Real estate and construction sector'),
    ('sector', 'materials', 'Materials and commodities sector'),
    ('sector', 'telecommunications', 'Telecommunications sector'),
    ('sector', 'automotive', 'Automotive and transportation sector');

-- Add comments about the category system
COMMENT ON TABLE temp_news_categories IS 'Reference table showing available news categories for classification';

-- Create a view for easy access to news source statistics
CREATE OR REPLACE VIEW news_source_stats AS
SELECT 
    ns.source_id,
    ns.name,
    ns.api_provider,
    ns.quality_score,
    ns.is_active,
    COUNT(na.id) as article_count,
    MAX(na.created_at) as last_article_date,
    AVG(CASE 
        WHEN sent.sentiment = 'positive' THEN 1
        WHEN sent.sentiment = 'negative' THEN -1
        ELSE 0
    END) as avg_sentiment_score
FROM news_sources ns
LEFT JOIN news_articles na ON ns.source_id = na.source_id
LEFT JOIN news_sentiment sent ON na.id = sent.article_id
GROUP BY ns.source_id, ns.name, ns.api_provider, ns.quality_score, ns.is_active;

COMMENT ON VIEW news_source_stats IS 'Statistics view for news sources showing article counts and sentiment trends';

-- Create a function to initialize news preferences for new users
CREATE OR REPLACE FUNCTION initialize_user_news_preferences(user_uuid UUID)
RETURNS VOID AS $
BEGIN
    INSERT INTO user_news_preferences (
        user_id, 
        categories, 
        sources, 
        sentiment_threshold, 
        impact_threshold, 
        notification_settings, 
        refresh_frequency
    ) VALUES (
        user_uuid,
        '{"earnings": 1.0, "technology": 0.8, "healthcare": 0.6, "finance": 0.9, "energy": 0.5, "consumer": 0.4}'::jsonb,
        '{"reuters": true, "bloomberg": true, "cnbc": true, "wall-street-journal": true, "financial-times": true}'::jsonb,
        0.30,
        'medium',
        '{"email": true, "push": false, "in_app": true, "quiet_hours": {"start": "22:00", "end": "07:00"}}'::jsonb,
        60
    )
    ON CONFLICT (user_id) DO NOTHING;
END;
$ LANGUAGE plpgsql;

COMMENT ON FUNCTION initialize_user_news_preferences IS 'Initialize default news preferences for a new user';

-- Create trigger to automatically initialize news preferences for new users
CREATE OR REPLACE FUNCTION trigger_initialize_news_preferences()
RETURNS TRIGGER AS $
BEGIN
    PERFORM initialize_user_news_preferences(NEW.id);
    RETURN NEW;
END;
$ LANGUAGE plpgsql;

CREATE TRIGGER auto_initialize_news_preferences
    AFTER INSERT ON users
    FOR EACH ROW
    EXECUTE FUNCTION trigger_initialize_news_preferences();
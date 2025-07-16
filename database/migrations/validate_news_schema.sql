-- Validation script for news integration schema
-- Run this to verify all tables and constraints are properly created

-- Check if all required tables exist
DO $
DECLARE
    missing_tables TEXT[] := ARRAY[]::TEXT[];
    table_name TEXT;
    required_tables TEXT[] := ARRAY[
        'news_articles',
        'news_categories', 
        'news_sentiment',
        'stock_news_relevance',
        'news_sources',
        'user_news_preferences',
        'news_fetch_jobs'
    ];
BEGIN
    FOREACH table_name IN ARRAY required_tables
    LOOP
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name = table_name
        ) THEN
            missing_tables := array_append(missing_tables, table_name);
        END IF;
    END LOOP;
    
    IF array_length(missing_tables, 1) > 0 THEN
        RAISE EXCEPTION 'Missing required tables: %', array_to_string(missing_tables, ', ');
    ELSE
        RAISE NOTICE 'All required news tables exist ✓';
    END IF;
END;
$;

-- Check if all required indexes exist
DO $
DECLARE
    missing_indexes TEXT[] := ARRAY[]::TEXT[];
    index_name TEXT;
    required_indexes TEXT[] := ARRAY[
        'idx_news_articles_published_at',
        'idx_news_articles_source',
        'idx_news_articles_content_hash',
        'idx_stock_news_relevance_symbol',
        'idx_stock_news_relevance_score',
        'idx_news_sentiment_sentiment',
        'idx_news_categories_category',
        'idx_news_sources_provider',
        'idx_user_news_preferences_user',
        'idx_news_fetch_jobs_status'
    ];
BEGIN
    FOREACH index_name IN ARRAY required_indexes
    LOOP
        IF NOT EXISTS (
            SELECT 1 FROM pg_indexes 
            WHERE schemaname = 'public' AND indexname = index_name
        ) THEN
            missing_indexes := array_append(missing_indexes, index_name);
        END IF;
    END LOOP;
    
    IF array_length(missing_indexes, 1) > 0 THEN
        RAISE WARNING 'Missing recommended indexes: %', array_to_string(missing_indexes, ', ');
    ELSE
        RAISE NOTICE 'All recommended indexes exist ✓';
    END IF;
END;
$;

-- Check if all required functions exist
DO $
DECLARE
    missing_functions TEXT[] := ARRAY[]::TEXT[];
    function_name TEXT;
    required_functions TEXT[] := ARRAY[
        'get_portfolio_news',
        'get_news_summary_stats',
        'initialize_user_news_preferences'
    ];
BEGIN
    FOREACH function_name IN ARRAY required_functions
    LOOP
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.routines 
            WHERE routine_schema = 'public' AND routine_name = function_name
        ) THEN
            missing_functions := array_append(missing_functions, function_name);
        END IF;
    END LOOP;
    
    IF array_length(missing_functions, 1) > 0 THEN
        RAISE WARNING 'Missing helper functions: %', array_to_string(missing_functions, ', ');
    ELSE
        RAISE NOTICE 'All helper functions exist ✓';
    END IF;
END;
$;

-- Test basic functionality with sample data
DO $
DECLARE
    test_user_id UUID;
    test_article_id UUID;
    test_source_count INTEGER;
BEGIN
    -- Check if we have news sources
    SELECT COUNT(*) INTO test_source_count FROM news_sources WHERE is_active = true;
    
    IF test_source_count = 0 THEN
        RAISE WARNING 'No active news sources found. Run the seed script: 03_news_sources_seed.sql';
    ELSE
        RAISE NOTICE 'Found % active news sources ✓', test_source_count;
    END IF;
    
    -- Test user preferences initialization for existing users
    SELECT id INTO test_user_id FROM users LIMIT 1;
    
    IF test_user_id IS NOT NULL THEN
        PERFORM initialize_user_news_preferences(test_user_id);
        
        IF EXISTS (SELECT 1 FROM user_news_preferences WHERE user_id = test_user_id) THEN
            RAISE NOTICE 'User news preferences initialization working ✓';
        ELSE
            RAISE WARNING 'User news preferences initialization failed';
        END IF;
    ELSE
        RAISE NOTICE 'No users found to test preferences initialization';
    END IF;
    
END;
$;

-- Display schema summary
SELECT 
    'news_articles' as table_name,
    COUNT(*) as row_count,
    pg_size_pretty(pg_total_relation_size('news_articles')) as table_size
FROM news_articles
UNION ALL
SELECT 
    'news_sources' as table_name,
    COUNT(*) as row_count,
    pg_size_pretty(pg_total_relation_size('news_sources')) as table_size
FROM news_sources
UNION ALL
SELECT 
    'user_news_preferences' as table_name,
    COUNT(*) as row_count,
    pg_size_pretty(pg_total_relation_size('user_news_preferences')) as table_size
FROM user_news_preferences
ORDER BY table_name;

RAISE NOTICE 'News integration schema validation completed ✓';
-- Sample data for AI Investment Tool
-- This creates a default user and portfolio for backward compatibility

-- Create default user
INSERT INTO users (id, username, email, password_hash, first_name, last_name, timezone)
VALUES (
    'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11'::uuid,
    'default_user',
    'user@ai-investment.local',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/lewdBNiKL/jjIYkfG', -- password: 'password123'
    'Default',
    'User',
    'America/New_York'
);

-- Create default portfolio
INSERT INTO portfolios (id, user_id, name, description, cash_balance)
VALUES (
    'b1eebc99-9c0b-4ef8-bb6d-6bb9bd380a22'::uuid,
    'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11'::uuid,
    'Main Portfolio',
    'Default portfolio for AI investment analysis',
    10000.00
);

-- Sample holdings (matching the existing portfolio format)
INSERT INTO holdings (portfolio_id, symbol, company_name, shares, average_cost, sector, industry)
VALUES 
    ('b1eebc99-9c0b-4ef8-bb6d-6bb9bd380a22'::uuid, 'AAPL', 'Apple Inc.', 50.0, 150.00, 'Technology', 'Consumer Electronics'),
    ('b1eebc99-9c0b-4ef8-bb6d-6bb9bd380a22'::uuid, 'GOOGL', 'Alphabet Inc.', 20.0, 2500.00, 'Technology', 'Internet Content & Information'),
    ('b1eebc99-9c0b-4ef8-bb6d-6bb9bd380a22'::uuid, 'MSFT', 'Microsoft Corporation', 30.0, 300.00, 'Technology', 'Software'),
    ('b1eebc99-9c0b-4ef8-bb6d-6bb9bd380a22'::uuid, 'TSLA', 'Tesla, Inc.', 25.0, 800.00, 'Consumer Discretionary', 'Automobiles'),
    ('b1eebc99-9c0b-4ef8-bb6d-6bb9bd380a22'::uuid, 'NVDA', 'NVIDIA Corporation', 15.0, 400.00, 'Technology', 'Semiconductors');

-- Sample transactions for the holdings
INSERT INTO transactions (portfolio_id, symbol, transaction_type, shares, price, total_amount, transaction_date, notes)
VALUES 
    ('b1eebc99-9c0b-4ef8-bb6d-6bb9bd380a22'::uuid, 'AAPL', 'BUY', 50.0, 150.00, 7500.00, '2024-01-15 10:30:00-05', 'Initial Apple purchase'),
    ('b1eebc99-9c0b-4ef8-bb6d-6bb9bd380a22'::uuid, 'GOOGL', 'BUY', 20.0, 2500.00, 50000.00, '2024-02-01 11:15:00-05', 'Google investment'),
    ('b1eebc99-9c0b-4ef8-bb6d-6bb9bd380a22'::uuid, 'MSFT', 'BUY', 30.0, 300.00, 9000.00, '2024-02-15 14:20:00-05', 'Microsoft position'),
    ('b1eebc99-9c0b-4ef8-bb6d-6bb9bd380a22'::uuid, 'TSLA', 'BUY', 25.0, 800.00, 20000.00, '2024-03-01 09:45:00-05', 'Tesla investment'),
    ('b1eebc99-9c0b-4ef8-bb6d-6bb9bd380a22'::uuid, 'NVDA', 'BUY', 15.0, 400.00, 6000.00, '2024-03-10 13:30:00-05', 'NVIDIA AI play'),
    ('b1eebc99-9c0b-4ef8-bb6d-6bb9bd380a22'::uuid, 'CASH', 'DEPOSIT', NULL, NULL, 100000.00, '2024-01-01 09:00:00-05', 'Initial cash deposit');

-- Common market sessions for the current week
INSERT INTO market_sessions (date, session_type, market_open_time, market_close_time, is_trading_day)
VALUES 
    (CURRENT_DATE - INTERVAL '7 days', 'MARKET_OPEN', '09:30:00', '16:00:00', true),
    (CURRENT_DATE - INTERVAL '6 days', 'MARKET_OPEN', '09:30:00', '16:00:00', true),
    (CURRENT_DATE - INTERVAL '5 days', 'MARKET_OPEN', '09:30:00', '16:00:00', true),
    (CURRENT_DATE - INTERVAL '4 days', 'MARKET_OPEN', '09:30:00', '16:00:00', true),
    (CURRENT_DATE - INTERVAL '3 days', 'MARKET_OPEN', '09:30:00', '16:00:00', true),
    (CURRENT_DATE - INTERVAL '2 days', 'WEEKEND', NULL, NULL, false),
    (CURRENT_DATE - INTERVAL '1 day', 'WEEKEND', NULL, NULL, false),
    (CURRENT_DATE, 'MARKET_OPEN', '09:30:00', '16:00:00', true); 
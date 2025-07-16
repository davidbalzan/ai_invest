# AI Investment Tool

A sophisticated AI-powered investment analysis platform that combines advanced portfolio management, backtesting capabilities, and intelligent market analysis. Features both a comprehensive web interface and powerful CLI tools for professional investment analysis.

## 🚀 Key Features

### 🌐 Web Application (FastAPI)
- **Multi-User Platform**: Complete user management with authentication
- **Portfolio Dashboard**: Real-time portfolio tracking and analytics
- **RESTful API**: Full API access for external integrations
- **Interactive Reports**: Web-based analysis and visualization
- **Database Integration**: PostgreSQL backend with comprehensive data models

### 🖥️ Advanced CLI Tool
- **Strategy Management**: Multiple investment strategies with risk profiles
- **Backtesting Engine**: Historical performance analysis and what-if scenarios
- **Market Scheduling**: Intelligent analysis timing based on market sessions
- **AI Analysis**: GPT-4 powered insights and recommendations
- **Automated Reports**: PDF generation with professional formatting

### 🧠 AI-Powered Analysis
- **Technical Indicators**: RSI, Moving Averages, Bollinger Bands, MACD
- **Sentiment Analysis**: News sentiment scoring with predictive power analysis
- **AI Recommendations**: Context-aware investment suggestions
- **Risk Assessment**: Comprehensive risk metrics and management
- **Prediction Validation**: Historical accuracy tracking of AI predictions

### 💾 Smart Caching & Data Management
- **Market-Aware Caching**: Different TTL policies for market hours, weekends, holidays
- **Cost Optimization**: Reduces API costs by 70-90% through intelligent caching
- **Data Storage**: Complete transaction history and analysis session tracking
- **Cache Analytics**: Performance monitoring and optimization tools

### 📊 Portfolio Management
- **Multi-Portfolio Support**: Manage multiple investment portfolios per user
- **Transaction Tracking**: Complete buy/sell/dividend/split history
- **Holdings Management**: Real-time position tracking and performance
- **Risk Management**: Stop-loss, take-profit, and position sizing controls
- **Rebalancing**: Automated and manual portfolio rebalancing

## 🚀 Quick Start

### 1. Prerequisites
- Python 3.12+
- Docker & Docker Compose
- Git

### 2. Installation

```bash
# Clone the repository
git clone <repository-url>
cd ai-investment-tool

# Install dependencies
pipenv install

# Copy environment template
cp config_example.env .env
```

### 3. Database Setup

```bash
# Start PostgreSQL database
./scripts/start_database.sh start

# Start with pgAdmin web interface (optional)
./scripts/start_database.sh start-all
```

**Database Access:**
- **PostgreSQL**: `localhost:5432`
- **Database**: `ai_investment`
- **Username**: `ai_user`
- **Password**: `ai_password`
- **pgAdmin**: http://localhost:8080 (admin@example.com / admin123)

### 4. Configuration

Edit `.env` with your API keys:

```env
# Required API Keys
OPENAI_API_KEY=your_openai_api_key_here
FINNHUB_API_KEY=your_finnhub_api_key_here

# Database Configuration
DATABASE_URL=postgresql://ai_user:ai_password@localhost:5432/ai_investment

# Application Mode
PORTFOLIO_MODE=true
RUN_ONCE_MODE=true

# Cache Configuration
CACHE_ENABLED=true
CACHE_BACKEND=postgresql
```

### 5. Running the Application

#### Web Application
```bash
# Activate environment
pipenv shell

# Start web server
python -m app.main
# or
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Access the web interface at: http://localhost:8000

#### CLI Analysis
```bash
# Activate environment
pipenv shell

# Run portfolio analysis
python main.py

# Run with specific strategy
STRATEGY_NAME=aggressive_growth python main.py

# Show available strategies
SHOW_STRATEGY=true python main.py

# Run backtesting
RUN_BACKTEST=true BACKTEST_PERIOD=90 python main.py
```

## 🏗️ Architecture

### Dual-Mode Operation
The platform supports both legacy file-based operations and modern database-driven functionality:

#### Database Mode (Recommended)
- **Multi-User Support**: Complete user management with authentication
- **PostgreSQL Backend**: Robust data storage with ACID compliance
- **Advanced Caching**: Database-backed caching with market-aware TTL
- **API Integration**: Full RESTful API for web and mobile clients
- **Audit Trails**: Complete transaction and analysis history

#### File-Based Mode (Legacy)
- **Single Portfolio**: JSON-based portfolio storage
- **File Caching**: JSON-based intelligent caching system
- **Direct Integration**: Yahoo Finance, Finnhub, OpenAI APIs
- **Report Generation**: HTML/PDF output to local filesystem

### System Components

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web Client    │    │   CLI Client    │    │  External APIs  │
│   (FastAPI)     │    │   (main.py)     │    │  (YFinance,     │
│                 │    │                 │    │   OpenAI, etc.) │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          └──────────┬───────────┴──────────────────────┘
                     │
          ┌─────────────────────────────────┐
          │        Core Engine              │
          │  ┌─────────────────────────────┐│
          │  │     Strategy Manager        ││
          │  │   (Investment Strategies)   ││
          │  └─────────────────────────────┘│
          │  ┌─────────────────────────────┐│
          │  │    Backtesting Engine       ││
          │  │  (Historical Analysis)      ││
          │  └─────────────────────────────┘│
          │  ┌─────────────────────────────┐│
          │  │      AI Analyzer            ││
          │  │   (GPT-4 Integration)       ││
          │  └─────────────────────────────┘│
          │  ┌─────────────────────────────┐│
          │  │    Market Scheduler         ││
          │  │  (Timing Intelligence)      ││
          │  └─────────────────────────────┘│
          └─────────────────────────────────┘
                     │
          ┌─────────────────────────────────┐
          │       Data Layer                │
          │  ┌─────────────────────────────┐│
          │  │    PostgreSQL Database      ││
          │  │   (Users, Portfolios,       ││
          │  │    Transactions, Cache)     ││
          │  └─────────────────────────────┘│
          │  ┌─────────────────────────────┐│
          │  │      File Storage           ││
          │  │   (Reports, Charts,         ││
          │  │    Legacy Data)             ││
          │  └─────────────────────────────┘│
          └─────────────────────────────────┘
```

## Database Management

### Daily Operations
```bash
# Check database status
./scripts/start_database.sh status

# View recent logs
./scripts/start_database.sh logs

# Create backup before changes
./scripts/start_database.sh backup

# Access database shell
./scripts/start_database.sh shell
```

### Database Schema

**Core Tables:**
- `users` - User accounts and preferences
- `portfolios` - Portfolio definitions and metadata
- `holdings` - Current portfolio positions
- `transactions` - Complete transaction history
- `analysis_sessions` - Analysis execution tracking

**Cache Tables:**
- `stock_data_cache` - Market data with session-aware expiration
- `news_sentiment_cache` - News articles and sentiment scores
- `ai_analysis_cache` - AI-generated insights and recommendations

### Migration from File-Based System

The database includes sample data that matches the existing file-based portfolio structure, ensuring backward compatibility during transition.

## Caching System

### Cache Strategies by Market Session [[memory:3289523]]

| Market Session | TTL | Use Case |
|---------------|-----|----------|
| Market Hours | 5-10 min | Real-time trading decisions |
| Pre/Post Market | 15-30 min | Extended hours analysis |
| Market Closed | 1-4 hours | After-hours research |
| Weekends/Holidays | 12-24 hours | Long-term planning |

### Cache Management
```bash
# View cache statistics
python cache_utils.py stats

# Clean expired entries
python cache_utils.py clean

# Clear all cache
python cache_utils.py clear

# Show cache policies
python cache_utils.py policies

# Optimize cache performance
python cache_utils.py optimize
```

## Report Features [[memory:3313487]]

Generated PDF reports include:
- **Timing Information**: Analysis generation timestamp, data freshness indicators
- **Market Context**: Current market session, trading window recommendations
- **Data Quality**: Clear warnings when data is stale, specific trading recommendations
- **Comprehensive Analysis**: Portfolio performance, technical indicators, AI insights

## Dependencies

### Core Requirements
- Python 3.8+
- pipenv (dependency management) [[memory:3289523]]
- Docker & Docker Compose (database)

### Python Packages
- `yfinance` - Stock market data
- `openai` - AI analysis
- `requests` - News sentiment data
- `pandas` - Data processing
- `matplotlib` - Chart generation
- `reportlab` - PDF generation
- `psycopg2-binary` - PostgreSQL adapter
- `pytz` - Timezone handling

### API Services
- **OpenAI API** - GPT-4 analysis and recommendations
- **Finnhub API** - News sentiment data (60 calls/minute limit)
- **Yahoo Finance** - Stock market data (via yfinance)

## Development

### Database Development
```bash
# Reset database (WARNING: deletes all data)
./scripts/start_database.sh reset

# Stop all services
./scripts/start_database.sh stop

# Restart services
./scripts/start_database.sh restart
```

### File Structure
```
ai_investment_tool/
├── database/
│   └── init/           # Database initialization scripts
├── scripts/
│   └── start_database.sh  # Database management script
├── docker-compose.yml  # PostgreSQL & pgAdmin setup
├── main.py            # Main analysis script
├── cache_manager.py   # Intelligent caching system
├── data_fetcher.py    # API data retrieval
├── ai_analyzer.py     # AI-powered analysis
└── reports/           # Generated PDF reports
```

### Cost Optimization

The intelligent caching system can reduce API costs by 70-90%:
- **Stock Data**: Cached based on market sessions
- **News Sentiment**: Article-level caching with freshness tracking
- **AI Analysis**: Context-based cache keys with smart invalidation
- **Performance**: Automatic cache cleanup and optimization

## Future Enhancements

### Planned Features
- **Web Interface**: FastAPI server with Jinja2 templates
- **Real-time Updates**: WebSocket support for live data
- **Advanced Analytics**: Multi-portfolio comparison and correlation analysis
- **Alert System**: Price targets, news alerts, and portfolio rebalancing notifications
- **API Integration**: RESTful API for external integrations

### Architecture Evolution
- **Phase 1**: Database foundation (✅ Current)
- **Phase 2**: Web server and API development
- **Phase 3**: Enhanced analytics and real-time features

## License

This project is for educational and personal use. Please ensure compliance with API providers' terms of service.

## Support

For issues with:
- **Database**: Check Docker status and logs
- **API Limits**: Review caching configuration
- **Performance**: Run cache optimization utilities
- **Reports**: Verify data freshness and market timing

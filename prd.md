# Product Requirements Document (PRD): AI Investment Recommendation Tool

## 1. Product Overview
This is a passive Python-based tool that monitors stock markets, analyzes trends using AI agents, and provides buy/sell/hold recommendations. It leverages your tech skills for coding and starts with 500 EUR simulated capital. Designed for low-effort use (e.g., scheduled runs), it focuses on AI hardware stocks but is customizable.

**Goals:**
- Multiply small capital (500 EUR) via smart, data-driven insights.
- Passive operation: Run on-demand or scheduled without constant input.
- Legal/compliant: Uses public data; not financial advice.

**Target User:** Tech-savvy individual with a main job, seeking passive investment growth for AI hardware purchases.

## 2. Key Features
- **Data Fetching:** Pull historical/real-time stock data (e.g., prices, news) via yfinance/Finnhub.
- **AI Analysis:** Agents (via finrobot/autogen) predict trends (e.g., "up 2-3% next week") based on news/financials.
- **Recommendations:** Suggest investments from 500 EUR (e.g., simulated shares).
- **Visualization:** Basic charts (matplotlib) for price history.
- **Scheduling:** Passive daily/weekly runs (schedule library).
- **Extensibility:** Add email alerts, multi-stock portfolios, or free API swaps.

## 3. Technical Requirements
- **Stack:** Python 3.10+, yfinance (data), pyautogen/finrobot (AI agents), pandas/matplotlib (analysis/charts), schedule (timing).
- **APIs:** OpenAI (paid for AI), Finnhub (free/paid tiers), yfinance (free).
- **Setup:** requirements.txt for deps; config_api_keys.json for keys.
- **Environment:** Works on Linux (your OS); can be scheduled via cron.

## 4. Cost Considerations
- **Paid APIs:** OpenAI (~$0.05-0.20/query), Finnhub ($50+/month for premium). Light use: <$30/year.
- **Efficiency:** Cache results to minimize calls. Free alternatives (e.g., Alpha Vantage) for basics. Not cost-efficient for high-frequency monitoring with small capital unless returns offset fees.
- **Budget Impact:** Aim for <1% of 500 EUR annually; monitor via API dashboards.

## 5. Usage Flow
1. Install deps: pip install -r requirements.txt
2. Add API keys to config_api_keys.json
3. Run: python main.py (loops passively)
4. Output: Console recommendations/charts.

## 6. Risks/Disclaimer
- Market volatility: Tool simulates; real losses possible.
- Not advice: Educational only; consult professionals.
- Dependencies: API changes may break functionality.

## 7. Future Enhancements
- Email/SMS alerts.
- Portfolio tracking.
- More AI models (e.g., free alternatives).


## 8. AI Model & Data Source Options
- **OpenAI GPT-4**: Best for deep analysis, summarization, and reasoning. Integrates easily with Python and financial libraries. No real-time web access, but can analyze fetched data/news.
- **Grok (xAI)**: Accesses real-time X (Twitter) feeds for sentiment/news. Useful for rapid market feedback and event-driven strategies. API access is limited, but can be integrated via X API or future Grok endpoints.
- **Hybrid Approach**: Tool will support both: OpenAI for deep analysis, and X/Twitter (via API or Grok) for real-time sentiment/news. Modular design allows easy swapping of models/data sources.

## 9. Investment Platform Considerations
- **Goal**: Minimize fees, maximize flexibility for small capital (500 EUR).
- **Criteria**:
  - Low/no account minimums
  - Low trading commissions (ideally zero)
  - Low or no inactivity/custody fees
  - Access to fractional shares/ETFs
  - Regulated, reputable platform
- **Popular Options (EU/Global):**
  - **Trade Republic**: No commission, small custody fee, fractional shares, EU-regulated.
  - **Degiro**: Low fees, broad access, but some charges for inactivity/withdrawals.
  - **Revolut**: No commission for a few trades/month, easy for small sums, but limited advanced features.
  - **Interactive Brokers**: Very low fees, fractional shares, but more complex and may have inactivity fees for small accounts.
  - **eToro**: Zero commission stocks, social trading, but check for withdrawal/currency conversion fees.
- **Recommendation**: For 500 EUR, start with Trade Republic or Revolut for simplicity and low fees. Avoid platforms with high minimums or inactivity fees. Always check latest fee schedules and local regulations.

## 10. Future Enhancements
- Add support for more LLMs (Claude, Gemini, Llama-3, etc.)
- Integrate with brokerage APIs for automated execution (if/when capital grows and risk appetite increases).


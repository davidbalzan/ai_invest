#!/usr/bin/env python3

import sys
import os
import json
from datetime import datetime

# Add the current directory to path so we can import modules
sys.path.append('.')

from html_renderer import HTMLReportRenderer

def create_test_data():
    """Create test data that mimics the structure from database analysis"""
    return {
        "portfolio_snapshot": {
            "total_value": 570.82,
            "total_cost_basis": 516.93,
            "total_profit_loss": 53.89,
            "total_profit_loss_percent": 10.43
        },
        "individual_stocks": {
            "NVDA": {
                "symbol": "NVDA",
                "company_name": "NVIDIA Corporation",
                "current_price": 167.29,
                "current_value": 167.29,
                "cost_basis": 135.01,
                "profit_loss": 32.28,
                "profit_loss_percent": 23.91,
                "quantity": 1,
                "market_value": 167.29,
                "recommendation": "HOLD",
                "technical": {
                    "rsi": 72.5,
                    "ma_20": 155.30,
                    "ma_50": 145.80,
                    "bollinger_upper": 175.20,
                    "bollinger_lower": 140.50,
                },
                "sentiment": {
                    "score": 0.6,
                    "overall": "positive",
                    "article_count": 15
                },
                "ai_analysis": {
                    "recommendation": "HOLD",
                    "confidence": 0.78,
                    "reasoning": "NVDA is currently trading in overbought territory with an RSI of 72.5, suggesting potential consolidation ahead. However, the strong fundamentals in AI and data center markets, combined with positive sentiment (score: 0.6), support the current valuation. The stock remains above key moving averages, indicating underlying strength despite short-term overbought conditions.",
                    "raw_response": "RECOMMENDATION: HOLD - The technical indicators show that NVDA is currently overbought with a high RSI of 72.5, however, the positive news sentiment (score: 0.6) is supporting the stock. With the stock trading above both 20-day ($155.30) and 50-day ($145.80) moving averages, the underlying trend remains bullish. Given the strong fundamentals in AI and data center markets, holding is recommended until RSI normalizes below 70.\n[AI Analysis: 13:05:22 UTC]"
                },
                "risk": {
                    "risk_level": "medium"
                },
                "trading_signal": "HOLD",
                "chart_data": {
                    "dates": ["2025-01-01", "2025-01-02", "2025-01-03"],
                    "prices": [150.0, 160.0, 167.29],
                    "volumes": [1000000, 1200000, 1100000],
                    "ma_20": [148.0, 155.0, 155.30],
                    "ma_50": [140.0, 143.0, 145.80]
                }
            },
            "META": {
                "symbol": "META",
                "company_name": "Meta Platforms Inc",
                "current_price": 56.83,
                "current_value": 56.83,
                "cost_basis": 53.94,
                "profit_loss": 2.89,
                "profit_loss_percent": 5.36,
                "quantity": 1,
                "market_value": 56.83,
                "recommendation": "BUY",
                "technical": {
                    "rsi": 45.2,
                    "ma_20": 55.10,
                    "ma_50": 52.30,
                    "bollinger_upper": 62.50,
                    "bollinger_lower": 48.70,
                },
                "sentiment": {
                    "score": 0.4,
                    "overall": "positive",
                    "article_count": 12
                },
                "ai_analysis": {
                    "recommendation": "BUY",
                    "confidence": 0.85,
                    "reasoning": "META shows strong technical setup with RSI at healthy 45.2 levels, indicating room for upward movement without being overbought. The stock is trading above both 20-day and 50-day moving averages, confirming bullish momentum. Recent positive developments in AI initiatives and cost-cutting measures, combined with attractive valuation metrics, make this an opportune entry point.",
                    "raw_response": "RECOMMENDATION: BUY - The technical analysis shows META is in a strong position with RSI at 45.2, well below overbought levels, providing room for growth. The stock is trading above both moving averages ($55.10 and $52.30), indicating strong momentum. Recent AI developments and efficiency improvements, along with positive sentiment, support a BUY recommendation with high confidence.\n[AI Analysis: 13:05:25 UTC]"
                },
                "risk": {
                    "risk_level": "medium"
                },
                "trading_signal": "BUY",
                "chart_data": {
                    "dates": ["2025-01-01", "2025-01-02", "2025-01-03"],
                    "prices": [52.0, 54.5, 56.83],
                    "volumes": [800000, 900000, 850000],
                    "ma_20": [51.0, 53.0, 55.10],
                    "ma_50": [49.0, 50.5, 52.30]
                }
            },
            "INTC": {
                "symbol": "INTC",
                "company_name": "Intel Corporation",
                "current_price": 25.14,
                "current_value": 75.42,
                "cost_basis": 89.97,
                "profit_loss": -14.55,
                "profit_loss_percent": -16.17,
                "quantity": 3,
                "market_value": 75.42,
                "recommendation": "SELL",
                "technical": {
                    "rsi": 28.5,
                    "ma_20": 26.80,
                    "ma_50": 28.90,
                    "bollinger_upper": 30.20,
                    "bollinger_lower": 23.10,
                },
                "sentiment": {
                    "score": -0.3,
                    "overall": "negative",
                    "article_count": 18
                },
                "ai_analysis": {
                    "recommendation": "SELL",
                    "confidence": 0.92,
                    "reasoning": "INTC shows concerning technical weakness with RSI at oversold levels (28.5) and trading below both key moving averages, indicating continued downward pressure. Negative market sentiment (score: -0.3) reflects ongoing concerns about competitive position in AI chips and manufacturing delays. The fundamental headwinds and technical breakdown suggest further downside risk, warranting a SELL recommendation.",
                    "raw_response": "RECOMMENDATION: SELL - Intel faces significant headwinds with RSI at deeply oversold 28.5 levels and price below both 20-day ($26.80) and 50-day ($28.90) moving averages. Negative sentiment (-0.3) reflects market concerns about AI competitiveness and manufacturing challenges. Despite oversold conditions, fundamental weakness and competitive disadvantages suggest further downside, making SELL the prudent choice.\n[AI Analysis: 13:05:28 UTC]"
                },
                "risk": {
                    "risk_level": "high"
                },
                "trading_signal": "SELL",
                "chart_data": {
                    "dates": ["2025-01-01", "2025-01-02", "2025-01-03"],
                    "prices": [28.0, 26.5, 25.14],
                    "volumes": [1500000, 1800000, 1600000],
                    "ma_20": [29.0, 27.5, 26.80],
                    "ma_50": [30.0, 29.2, 28.90]
                }
            }
        },
        "market_analysis": {
            "portfolio_summary": {
                "total_value": 570.82,
                "total_cost_basis": 516.93,
                "total_profit_loss": 53.89,
                "total_profit_loss_percent": 10.43,
                "best_performer": {"symbol": "NVDA", "return_percent": 23.91},
                "worst_performer": {"symbol": "INTC", "return_percent": -16.17}
            },
            "recommendations": {
                "buy_signals": 1,
                "hold_signals": 1,
                "sell_signals": 1
            },
            "sector_allocation": {
                "Technology": 100.0
            },
            "risk_metrics": {
                "portfolio_risk": "medium",
                "concentration_risk": "high"
            }
        },
        "performance": {
            "total_return": 10.43,
            "risk_alerts": []
        },
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

def main():
    print("🔄 Generating enhanced HTML report with detailed AI explanations...")
    
    # Create test data
    test_data = create_test_data()
    
    # Initialize renderer
    renderer = HTMLReportRenderer()
    
    # Generate HTML report
    html_content = renderer.render_report(test_data)
    
    # Save to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"reports/enhanced_ai_analysis_{timestamp}.html"
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✅ Enhanced HTML report generated: {filename}")
    print(f"📂 File size: {len(html_content)} characters")
    print(f"🔍 Open the file in a browser to see the enhanced AI recommendations!")
    
    # Also print a sample of what the enhanced AI display should look like
    print("\n" + "="*60)
    print("ENHANCED AI RECOMMENDATION DISPLAY FEATURES:")
    print("="*60)
    print("✓ Color-coded recommendation badges (BUY=Green, HOLD=Orange, SELL=Red)")
    print("✓ Confidence percentage display")
    print("✓ Detailed reasoning in formatted boxes")
    print("✓ Expandable full AI response sections")
    print("✓ Professional styling with better readability")
    
    return filename

if __name__ == "__main__":
    main() 
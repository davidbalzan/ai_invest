from typing import Dict, List
import json
import os
from datetime import datetime

class HTMLReportRenderer:
    """Renders investment analysis reports as HTML from JSON data"""
    
    def __init__(self, template_dir: str = "templates"):
        self.template_dir = template_dir
        self.ensure_template_dir()
    
    def ensure_template_dir(self):
        """Create templates directory if it doesn't exist"""
        os.makedirs(self.template_dir, exist_ok=True)
    
    def render_report(self, report_data: Dict, output_path: str = None) -> str:
        """Render complete HTML report from JSON data"""
        
        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"reports/portfolio_analysis_{timestamp}.html"
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        html_content = self._generate_html(report_data)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return output_path
    
    def _generate_html(self, data: Dict) -> str:
        """Generate complete HTML document"""
        
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Portfolio Investment Analysis - {data.get('date', 'N/A')}</title>
    {self._get_styles()}
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body>
    <div class="container">
        {self._render_header(data)}
        {self._render_strategy_section(data)}
        {self._render_executive_summary(data)}
        {self._render_portfolio_overview(data)}
        {self._render_market_analysis(data)}
        {self._render_individual_stocks(data)}
        {self._render_performance_metrics(data)}
        {self._render_historical_trends(data)}
        {self._render_metrics_guide()}
        {self._render_footer(data)}
    </div>
    
    {self._get_javascript(data)}
</body>
</html>"""
    
    def _get_styles(self) -> str:
        """Generate CSS styles"""
        return """
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: white;
            margin-top: 20px;
            margin-bottom: 20px;
            border-radius: 15px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
        }
        
        .header {
            text-align: center;
            padding: 30px 0;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 15px;
            margin-bottom: 30px;
        }
        
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
            font-weight: 300;
        }
        
        .header .date {
            font-size: 1.2em;
            opacity: 0.9;
        }
        
        .section {
            margin-bottom: 40px;
            padding: 25px;
            background: #f8f9fa;
            border-radius: 10px;
            border-left: 5px solid #667eea;
        }
        
        .section h2 {
            color: #667eea;
            margin-bottom: 20px;
            font-size: 1.8em;
            border-bottom: 2px solid #e9ecef;
            padding-bottom: 10px;
        }
        
        .section h3 {
            color: #495057;
            margin-bottom: 15px;
            font-size: 1.3em;
        }
        
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 25px;
        }
        
        .metric-card {
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            text-align: center;
            transition: transform 0.3s ease;
        }
        
        .metric-card:hover {
            transform: translateY(-5px);
        }
        
        .metric-card .value {
            font-size: 2em;
            font-weight: bold;
            margin-bottom: 5px;
        }
        
        .metric-card .label {
            color: #6c757d;
            font-size: 0.9em;
        }
        
        .positive { color: #28a745; }
        .negative { color: #dc3545; }
        .neutral { color: #ffc107; }
        .warning { color: #fd7e14; }
        
        .stock-table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 25px;
            background: white;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        
        .stock-table th {
            background: #667eea;
            color: white;
            padding: 15px;
            text-align: left;
            font-weight: 600;
        }
        
        .stock-table td {
            padding: 12px 15px;
            border-bottom: 1px solid #e9ecef;
        }
        
        .stock-table tr:nth-child(even) {
            background: #f8f9fa;
        }
        
        .stock-table tr:hover {
            background: #e3f2fd;
        }
        
        .rsi-high { background: #ffebee !important; }
        .rsi-medium { background: #fff3e0 !important; }
        .rsi-good { background: #e8f5e8 !important; }
        
        .chart-container {
            position: relative;
            height: 400px;
            margin: 20px 0;
            background: white;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        
        .recommendation {
            background: #e3f2fd;
            padding: 15px;
            border-radius: 8px;
            border-left: 4px solid #2196f3;
            margin: 10px 0;
        }
        
        .risk-alert {
            background: #ffebee;
            padding: 15px;
            border-radius: 8px;
            border-left: 4px solid #f44336;
            margin: 10px 0;
        }
        
        .trend-indicator {
            display: inline-block;
            padding: 5px 10px;
            border-radius: 15px;
            font-size: 0.8em;
            font-weight: bold;
            text-transform: uppercase;
        }
        
        .trend-bullish {
            background: #d4edda;
            color: #155724;
        }
        
        .trend-bearish {
            background: #f8d7da;
            color: #721c24;
        }
        
        .trend-neutral {
            background: #fff3cd;
            color: #856404;
        }
        
        .footer {
            text-align: center;
            padding: 20px;
            color: #6c757d;
            font-size: 0.9em;
            border-top: 1px solid #e9ecef;
            margin-top: 40px;
        }
        
        .expandable {
            cursor: pointer;
            user-select: none;
        }
        
        .expandable:hover {
            background: #f0f0f0;
        }
        
        .collapsible-content {
            display: none;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 5px;
            margin-top: 10px;
        }
        
        .collapsible-content.active {
            display: block;
        }
        
        @media (max-width: 768px) {
            .container {
                margin: 10px;
                padding: 15px;
            }
            
            .metrics-grid {
                grid-template-columns: 1fr;
            }
            
            .header h1 {
                font-size: 2em;
            }
            
            .stock-table {
                font-size: 0.9em;
            }
        }
    </style>
        """
    
    def _render_header(self, data: Dict) -> str:
        """Render report header"""
        return f"""
        <div class="header">
            <h1>Portfolio Investment Analysis</h1>
            <div class="date">Report Generated: {data.get('date', 'N/A')} at {data.get('time', 'N/A')}</div>
            <div class="date">Report ID: {data.get('report_id', 'N/A')}</div>
        </div>
        """
    
    def _render_strategy_section(self, data: Dict) -> str:
        """Render investment strategy configuration section"""
        strategy = data.get('strategy', {})
        
        if not strategy:
            return ""
        
        risk_profile = strategy.get('risk_profile', 'Unknown')
        risk_class = {
            'Conservative': 'positive',
            'Moderate': 'neutral', 
            'Aggressive': 'warning',
            'Custom': 'neutral'
        }.get(risk_profile, 'neutral')
        
        return f"""
        <div class="section">
            <h2>🎯 Investment Strategy Configuration</h2>
            
            <div class="strategy-overview" style="background: #e3f2fd; padding: 20px; border-radius: 10px; margin-bottom: 25px;">
                <h3 style="margin-bottom: 15px; color: #1976d2;">Strategy: {strategy.get('name', 'N/A')}</h3>
                <p style="margin-bottom: 10px;"><strong>Description:</strong> {strategy.get('description', 'N/A')}</p>
                <p style="margin-bottom: 10px;"><strong>Risk Profile:</strong> 
                   <span class="trend-indicator trend-{risk_class.lower()}">{risk_profile}</span>
                </p>
                <p><strong>Active Since:</strong> {strategy.get('created_date', 'N/A')[:10] if strategy.get('created_date') else 'N/A'}</p>
            </div>
            
            <div class="metrics-grid">
                <div class="metric-card">
                    <h4 style="color: #dc3545; margin-bottom: 10px;">🛡️ Risk Management</h4>
                    <table style="width: 100%; font-size: 0.9em;">
                        <tr><td><strong>Stop Loss:</strong></td><td>{strategy.get('risk_management', {}).get('stop_loss', 'N/A')}</td></tr>
                        <tr><td><strong>Take Profit:</strong></td><td>{strategy.get('risk_management', {}).get('take_profit', 'N/A')}</td></tr>
                        <tr><td><strong>Max Position:</strong></td><td>{strategy.get('risk_management', {}).get('max_position_size', 'N/A')}</td></tr>
                        <tr><td><strong>Cash Reserve:</strong></td><td>{strategy.get('risk_management', {}).get('cash_reserve', 'N/A')}</td></tr>
                    </table>
                </div>
                
                <div class="metric-card">
                    <h4 style="color: #2196f3; margin-bottom: 10px;">📊 Technical Analysis</h4>
                    <table style="width: 100%; font-size: 0.9em;">
                        <tr><td><strong>RSI Thresholds:</strong></td><td>{strategy.get('technical_analysis', {}).get('rsi_thresholds', 'N/A')}</td></tr>
                        <tr><td><strong>Moving Averages:</strong></td><td>{strategy.get('technical_analysis', {}).get('moving_averages', 'N/A')}</td></tr>
                        <tr><td><strong>Use MACD:</strong></td><td>{'Yes' if strategy.get('technical_analysis', {}).get('use_macd') else 'No'}</td></tr>
                    </table>
                </div>
                
                <div class="metric-card">
                    <h4 style="color: #ff9800; margin-bottom: 10px;">📰 Sentiment Analysis</h4>
                    <table style="width: 100%; font-size: 0.9em;">
                        <tr><td><strong>Decision Weight:</strong></td><td>{strategy.get('sentiment_analysis', {}).get('weight', 'N/A')}</td></tr>
                        <tr><td><strong>Min Buy Score:</strong></td><td>{strategy.get('sentiment_analysis', {}).get('min_buy_score', 'N/A')}</td></tr>
                        <tr><td><strong>Min Articles:</strong></td><td>{strategy.get('sentiment_analysis', {}).get('min_articles', 'N/A')}</td></tr>
                    </table>
                </div>
                
                <div class="metric-card">
                    <h4 style="color: #4caf50; margin-bottom: 10px;">⚖️ Portfolio Management</h4>
                    <table style="width: 100%; font-size: 0.9em;">
                        <tr><td><strong>Rebalancing:</strong></td><td>{strategy.get('portfolio_management', {}).get('rebalancing', 'N/A').title()}</td></tr>
                        <tr><td><strong>Auto Rebalance:</strong></td><td>{'Enabled' if strategy.get('portfolio_management', {}).get('auto_rebalancing') else 'Disabled'}</td></tr>
                        <tr><td><strong>Target Positions:</strong></td><td>{strategy.get('portfolio_management', {}).get('target_positions', 'N/A')}</td></tr>
                    </table>
                </div>
                
                <div class="metric-card">
                    <h4 style="color: #9c27b0; margin-bottom: 10px;">🎯 Performance Targets</h4>
                    <table style="width: 100%; font-size: 0.9em;">
                        <tr><td><strong>Annual Return:</strong></td><td>{strategy.get('performance_targets', {}).get('annual_return', 'N/A')}</td></tr>
                        <tr><td><strong>Max Drawdown:</strong></td><td>{strategy.get('performance_targets', {}).get('max_drawdown', 'N/A')}</td></tr>
                        <tr><td><strong>Sharpe Ratio:</strong></td><td>{strategy.get('performance_targets', {}).get('sharpe_ratio', 'N/A')}</td></tr>
                    </table>
                </div>
            </div>
        </div>
        """
    
    def _render_executive_summary(self, data: Dict) -> str:
        """Render executive summary section"""
        portfolio = data.get('portfolio', {})
        performance = data.get('performance', {})
        
        total_return_class = 'positive' if portfolio.get('total_return_percent', 0) > 0 else 'negative'
        
        return f"""
        <div class="section">
            <h2>Executive Summary</h2>
            <div class="metrics-grid">
                <div class="metric-card">
                    <div class="value {total_return_class}">${portfolio.get('total_value', 0):,.2f}</div>
                    <div class="label">Total Portfolio Value</div>
                </div>
                <div class="metric-card">
                    <div class="value">${portfolio.get('total_invested', 0):,.2f}</div>
                    <div class="label">Total Invested</div>
                </div>
                <div class="metric-card">
                    <div class="value {total_return_class}">${portfolio.get('total_profit_loss', 0):+,.2f}</div>
                    <div class="label">Total P&L</div>
                </div>
                <div class="metric-card">
                    <div class="value {total_return_class}">{portfolio.get('total_return_percent', 0):+.2f}%</div>
                    <div class="label">Overall Return</div>
                </div>
                <div class="metric-card">
                    <div class="value">{portfolio.get('position_count', 0)}</div>
                    <div class="label">Total Positions</div>
                </div>
                <div class="metric-card">
                    <div class="value positive">{portfolio.get('profitable_positions', 0)}</div>
                    <div class="label">Profitable Positions</div>
                </div>
            </div>
            
            {self._render_best_worst_performers(performance)}
        </div>
        """
    
    def _render_best_worst_performers(self, performance: Dict) -> str:
        """Render best/worst performer cards"""
        best = performance.get('best_performer', {})
        worst = performance.get('worst_performer', {})
        
        if not best or not worst:
            return ""
        
        return f"""
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-top: 20px;">
            <div class="metric-card">
                <h4 style="color: #28a745; margin-bottom: 10px;">🏆 Best Performer</h4>
                <div class="value positive">{best.get('symbol', 'N/A')}</div>
                <div class="label">{best.get('return_percent', 0):+.2f}% return</div>
            </div>
            <div class="metric-card">
                <h4 style="color: #dc3545; margin-bottom: 10px;">📉 Needs Attention</h4>
                <div class="value negative">{worst.get('symbol', 'N/A')}</div>
                <div class="label">{worst.get('return_percent', 0):+.2f}% return</div>
            </div>
        </div>
        """
    
    def _render_portfolio_overview(self, data: Dict) -> str:
        """Render portfolio overview with charts"""
        return f"""
        <div class="section">
            <h2>Portfolio Overview</h2>
            <div class="chart-container">
                <canvas id="portfolioChart"></canvas>
            </div>
        </div>
        """
    
    def _render_market_analysis(self, data: Dict) -> str:
        """Render market analysis section"""
        market = data.get('market_analysis', {})
        sentiment_dist = market.get('sentiment_distribution', {})
        technical = market.get('technical_overview', {})
        recommendations = market.get('recommendations_summary', {})
        
        return f"""
        <div class="section">
            <h2>Market Analysis & Strategic Outlook</h2>
            
            <h3>Sentiment Distribution</h3>
            <div class="metrics-grid">
                <div class="metric-card">
                    <div class="value positive">{sentiment_dist.get('positive', 0)}</div>
                    <div class="label">Positive Sentiment</div>
                </div>
                <div class="metric-card">
                    <div class="value neutral">{sentiment_dist.get('neutral', 0)}</div>
                    <div class="label">Neutral Sentiment</div>
                </div>
                <div class="metric-card">
                    <div class="value negative">{sentiment_dist.get('negative', 0)}</div>
                    <div class="label">Negative Sentiment</div>
                </div>
            </div>
            
            <h3>Technical Overview</h3>
            <div class="metrics-grid">
                <div class="metric-card">
                    <div class="value">{technical.get('average_rsi', 50):.1f}</div>
                    <div class="label">Average RSI</div>
                </div>
                <div class="metric-card">
                    <div class="value warning">{technical.get('overbought_count', 0)}</div>
                    <div class="label">Overbought Positions</div>
                </div>
                <div class="metric-card">
                    <div class="value warning">{technical.get('oversold_count', 0)}</div>
                    <div class="label">Oversold Positions</div>
                </div>
            </div>
            
            <h3>AI Recommendations Summary</h3>
            <div class="metrics-grid">
                <div class="metric-card">
                    <div class="value positive">{recommendations.get('buy_signals', 0)}</div>
                    <div class="label">BUY Signals</div>
                </div>
                <div class="metric-card">
                    <div class="value neutral">{recommendations.get('hold_signals', 0)}</div>
                    <div class="label">HOLD Signals</div>
                </div>
                <div class="metric-card">
                    <div class="value negative">{recommendations.get('sell_signals', 0)}</div>
                    <div class="label">SELL Signals</div>
                </div>
            </div>
        </div>
        """
    
    def _render_individual_stocks(self, data: Dict) -> str:
        """Render individual stock analysis"""
        stocks = data.get('stocks', {})
        
        if not stocks:
            return ""
        
        stocks_html = """
        <div class="section">
            <h2>Individual Stock Analysis</h2>
        """
        
        for symbol, stock in stocks.items():
            stocks_html += self._render_stock_card(symbol, stock)
        
        stocks_html += "</div>"
        return stocks_html
    
    def _render_stock_card(self, symbol: str, stock: Dict) -> str:
        """Render individual stock card"""
        technical = stock.get('technical', {})
        sentiment = stock.get('sentiment', {})
        ai_analysis = stock.get('ai_analysis', {})
        risk = stock.get('risk', {})
        
        # Determine RSI class
        rsi = technical.get('rsi', 50)
        rsi_class = 'rsi-high' if rsi > 70 or rsi < 30 else 'rsi-medium' if rsi > 60 or rsi < 40 else 'rsi-good'
        
        profit_loss_class = 'positive' if stock.get('profit_loss', 0) > 0 else 'negative'
        sentiment_class = sentiment.get('overall', 'neutral').lower()
        
        # Check if chart data is available
        chart_data = stock.get('chart_data')
        chart_section = ""
        
        if chart_data and chart_data.get('dates') and chart_data.get('prices'):
            chart_section = f"""
            <div style="margin-top: 20px;">
                <h4 style="text-align: center; margin-bottom: 10px;">📈 Price Chart (90 Days)</h4>
                <div class="chart-container" style="height: 300px; margin-bottom: 10px;">
                    <canvas id="stockChart_{symbol}"></canvas>
                </div>
            </div>
            """
        
        return f"""
        <div class="metric-card" style="margin-bottom: 30px; text-align: left;">
            <h3 style="color: #667eea; margin-bottom: 15px; text-align: center;">{symbol} Analysis</h3>
            
            <table class="stock-table" style="margin-bottom: 15px;">
                <tr>
                    <td><strong>Current Price</strong></td>
                    <td>${stock.get('current_price', 0):.2f}</td>
                </tr>
                <tr class="{rsi_class}">
                    <td><strong>RSI</strong></td>
                    <td>{technical.get('rsi', 0):.2f}</td>
                </tr>
                <tr class="{sentiment_class}">
                    <td><strong>News Sentiment</strong></td>
                    <td>{sentiment.get('overall', 'neutral').title()}</td>
                </tr>
                <tr>
                    <td><strong>20-day MA</strong></td>
                    <td>${technical.get('ma_20', 0):.2f}</td>
                </tr>
                <tr>
                    <td><strong>50-day MA</strong></td>
                    <td>${technical.get('ma_50', 0):.2f}</td>
                </tr>
                <tr>
                    <td><strong>Holdings</strong></td>
                    <td>{stock.get('quantity', 0)} shares</td>
                </tr>
                <tr>
                    <td><strong>Cost Basis</strong></td>
                    <td>${stock.get('cost_basis', 0):.2f}</td>
                </tr>
                <tr>
                    <td><strong>Current Value</strong></td>
                    <td>${stock.get('current_value', 0):.2f}</td>
                </tr>
                <tr class="{profit_loss_class}">
                    <td><strong>P&L</strong></td>
                    <td>${stock.get('profit_loss', 0):+.2f}</td>
                </tr>
                <tr class="{profit_loss_class}">
                    <td><strong>Return %</strong></td>
                    <td>{stock.get('profit_loss_percent', 0):+.2f}%</td>
                </tr>
                <tr>
                    <td><strong>Risk Level</strong></td>
                    <td><span class="trend-indicator trend-{risk.get('risk_level', 'medium').lower()}">{risk.get('risk_level', 'MEDIUM')}</span></td>
                </tr>
            </table>
            
            {chart_section}
            
            <div class="recommendation">
                <strong>AI Recommendation:</strong> {ai_analysis.get('recommendation', 'N/A')}
            </div>
        </div>
        """
    
    def _render_performance_metrics(self, data: Dict) -> str:
        """Render performance metrics and risk alerts"""
        performance = data.get('performance', {})
        risk_alerts = performance.get('risk_alerts', [])
        
        alerts_html = ""
        if risk_alerts:
            alerts_html = "<h3>Risk Alerts</h3>"
            for alert in risk_alerts:
                alerts_html += f"""
                <div class="risk-alert">
                    <strong>{alert.get('symbol', 'N/A')}</strong>: {alert.get('reason', 'N/A')} 
                    (Value: {alert.get('value', 0):.2f})
                </div>
                """
        
        return f"""
        <div class="section">
            <h2>Performance Metrics & Risk Assessment</h2>
            {alerts_html}
        </div>
        """
    
    def _render_historical_trends(self, data: Dict) -> str:
        """Render historical trends section (placeholder for future implementation)"""
        return f"""
        <div class="section">
            <h2>Historical Trends</h2>
            <div class="chart-container">
                <canvas id="trendsChart"></canvas>
            </div>
            <p style="text-align: center; color: #6c757d; margin-top: 20px;">
                Historical trend analysis will be available after collecting more data points.
            </p>
        </div>
        """
    
    def _render_metrics_guide(self) -> str:
        """Render metrics explanation guide"""
        return """
        <div class="section">
            <h2>Investment Metrics Guide</h2>
            
            <div class="expandable" onclick="toggleContent('rsiGuide')">
                <h3>📊 Relative Strength Index (RSI) ▼</h3>
            </div>
            <div id="rsiGuide" class="collapsible-content">
                <p><strong>Definition:</strong> RSI measures momentum of price changes (0-100 scale)</p>
                <p><strong>Interpretation:</strong></p>
                <ul>
                    <li>🔴 RSI > 70: Potentially overbought (consider selling)</li>
                    <li>🟡 RSI 60-70 or 30-40: Caution zones</li>
                    <li>🟢 RSI 50-60: Healthy momentum</li>
                    <li>🔴 RSI < 30: Potentially oversold (consider buying)</li>
                </ul>
            </div>
            
            <div class="expandable" onclick="toggleContent('sentimentGuide')">
                <h3>📰 News Sentiment Analysis ▼</h3>
            </div>
            <div id="sentimentGuide" class="collapsible-content">
                <p><strong>Definition:</strong> Algorithmic analysis of recent news articles</p>
                <p><strong>Scale:</strong> Positive, Neutral, Negative</p>
                <p><strong>Methodology:</strong> VADER sentiment analysis on financial news</p>
            </div>
            
            <div class="expandable" onclick="toggleContent('aiGuide')">
                <h3>🤖 AI Recommendations ▼</h3>
            </div>
            <div id="aiGuide" class="collapsible-content">
                <p><strong>Types:</strong> BUY, HOLD, SELL</p>
                <p><strong>Factors:</strong> Technical indicators, sentiment, portfolio context, risk parameters</p>
                <p><strong>Note:</strong> Advisory only - combine with personal research</p>
            </div>
        </div>
        """
    
    def _render_footer(self, data: Dict) -> str:
        """Render report footer"""
        return f"""
        <div class="footer">
            <p><strong>Disclaimer:</strong> This report is for informational purposes only and does not constitute financial advice.</p>
            <p>Generated by AI Investment Tool - Report ID: {data.get('report_id', 'N/A')}</p>
        </div>
        """
    
    def _get_javascript(self, data: Dict) -> str:
        """Generate JavaScript for interactive features and charts"""
        stocks = data.get('stocks', {})
        portfolio_data = []
        
        for symbol, stock in stocks.items():
            portfolio_data.append({
                'symbol': symbol,
                'value': stock.get('current_value', 0),
                'return': stock.get('profit_loss_percent', 0)
            })
        
        # Generate individual stock chart configurations
        stock_charts_js = ""
        for symbol, stock in stocks.items():
            chart_data = stock.get('chart_data')
            if chart_data and chart_data.get('dates') and chart_data.get('prices'):
                cost_basis = stock.get('cost_basis', 0)
                current_price = stock.get('current_price', 0)
                
                # Determine profit/loss background color and zones
                is_profitable = current_price > cost_basis
                profit_loss_color = 'rgba(75, 192, 192, 0.1)' if is_profitable else 'rgba(255, 99, 132, 0.1)'
                
                # Create background data for profit/loss zone
                background_data = []
                for price in chart_data['prices']:
                    if price and cost_basis:
                        if is_profitable:
                            background_data.append(max(price, cost_basis))
                        else:
                            background_data.append(min(price, cost_basis))
                    else:
                        background_data.append(None)
                
                stock_charts_js += f"""
                // {symbol} stock chart
                const {symbol.lower()}Ctx = document.getElementById('stockChart_{symbol}');
                if ({symbol.lower()}Ctx) {{
                    new Chart({symbol.lower()}Ctx, {{
                        type: 'line',
                        data: {{
                            labels: {json.dumps(chart_data['dates'])},
                            datasets: [
                                // Price line
                                {{
                                    label: 'Price',
                                    data: {json.dumps(chart_data['prices'])},
                                    borderColor: '#2563eb',
                                    backgroundColor: 'rgba(37, 99, 235, 0.1)',
                                    borderWidth: 2,
                                    fill: false,
                                    tension: 0.1
                                }},
                                // 20-day MA
                                {{
                                    label: '20-day MA',
                                    data: {json.dumps(chart_data['ma_20'])},
                                    borderColor: '#f59e0b',
                                    backgroundColor: 'rgba(245, 158, 11, 0.1)',
                                    borderWidth: 1,
                                    fill: false,
                                    tension: 0.1,
                                    borderDash: [5, 5]
                                }},
                                // 50-day MA
                                {{
                                    label: '50-day MA',
                                    data: {json.dumps(chart_data['ma_50'])},
                                    borderColor: '#ef4444',
                                    backgroundColor: 'rgba(239, 68, 68, 0.1)',
                                    borderWidth: 1,
                                    fill: false,
                                    tension: 0.1,
                                    borderDash: [10, 5]
                                }},
                                // Profit/Loss zone (background fill)
                                {{
                                    label: '{'Profit Zone' if is_profitable else 'Loss Zone'}',
                                    data: {json.dumps(background_data)},
                                    backgroundColor: '{profit_loss_color}',
                                    borderColor: 'transparent',
                                    fill: {json.dumps(str(cost_basis))},
                                    tension: 0.1,
                                    pointRadius: 0,
                                    pointHoverRadius: 0,
                                    order: 10
                                }}
                            ]
                        }},
                        options: {{
                            responsive: true,
                            maintainAspectRatio: false,
                            plugins: {{
                                title: {{
                                    display: true,
                                    text: '{symbol} - Purchase: ${cost_basis:.2f} | Current: ${current_price:.2f} | P&L: {stock.get('profit_loss_percent', 0):+.1f}%',
                                    font: {{ size: 14, weight: 'bold' }},
                                    color: '{('#28a745' if is_profitable else '#dc3545')}'
                                }},
                                legend: {{
                                    position: 'bottom',
                                    labels: {{
                                        usePointStyle: true,
                                        padding: 15
                                    }}
                                }},
                                tooltip: {{
                                    mode: 'index',
                                    intersect: false,
                                    callbacks: {{
                                        label: function(context) {{
                                            let label = context.dataset.label || '';
                                            if (label) {{
                                                label += ': ';
                                            }}
                                            if (context.parsed.y !== null) {{
                                                label += '$' + context.parsed.y.toFixed(2);
                                            }}
                                            return label;
                                        }}
                                    }}
                                }}
                            }},
                            scales: {{
                                x: {{
                                    display: true,
                                    title: {{
                                        display: true,
                                        text: 'Date'
                                    }},
                                    ticks: {{
                                        maxTicksLimit: 8
                                    }}
                                }},
                                y: {{
                                    display: true,
                                    title: {{
                                        display: true,
                                        text: 'Price ($)'
                                    }},
                                    beginAtZero: false
                                }}
                            }},
                            elements: {{
                                point: {{
                                    radius: 1,
                                    hoverRadius: 6
                                }}
                            }},
                            interaction: {{
                                mode: 'nearest',
                                axis: 'x',
                                intersect: false
                            }}
                        }}
                    }});
                }}
                """
        
        return f"""
        <script>
            // Toggle collapsible content
            function toggleContent(id) {{
                const content = document.getElementById(id);
                content.classList.toggle('active');
                
                const parent = content.previousElementSibling;
                const arrow = parent.querySelector('h3');
                if (content.classList.contains('active')) {{
                    arrow.innerHTML = arrow.innerHTML.replace('▼', '▲');
                }} else {{
                    arrow.innerHTML = arrow.innerHTML.replace('▲', '▼');
                }}
            }}
            
            // Portfolio pie chart
            const portfolioCtx = document.getElementById('portfolioChart').getContext('2d');
            new Chart(portfolioCtx, {{
                type: 'doughnut',
                data: {{
                    labels: {json.dumps([item['symbol'] for item in portfolio_data])},
                    datasets: [{{
                        data: {json.dumps([item['value'] for item in portfolio_data])},
                        backgroundColor: [
                            '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0',
                            '#9966FF', '#FF9F40', '#FF6384', '#C9CBCF'
                        ],
                        borderWidth: 2,
                        borderColor: '#fff'
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {{
                        title: {{
                            display: true,
                            text: 'Portfolio Allocation by Value',
                            font: {{ size: 16 }}
                        }},
                        legend: {{
                            position: 'bottom'
                        }}
                    }}
                }}
            }});
            
            // Individual stock charts
            {stock_charts_js}
            
            // Trends chart (placeholder)
            const trendsCtx = document.getElementById('trendsChart').getContext('2d');
            new Chart(trendsCtx, {{
                type: 'line',
                data: {{
                    labels: ['Day 1', 'Day 2', 'Day 3', 'Day 4', 'Day 5'],
                    datasets: [{{
                        label: 'Portfolio Value',
                        data: [100, 102, 98, 105, 110],
                        borderColor: '#667eea',
                        backgroundColor: 'rgba(102, 126, 234, 0.1)',
                        tension: 0.4
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {{
                        title: {{
                            display: true,
                            text: 'Portfolio Performance Trend (Sample Data)',
                            font: {{ size: 16 }}
                        }}
                    }},
                    scales: {{
                        y: {{
                            beginAtZero: false
                        }}
                    }}
                }}
            }});
        </script>
        """ 
from typing import Dict, List, Tuple
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
            overflow: visible;
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
            overflow: visible;
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
        
        .recommendation-badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-weight: bold;
            font-size: 0.9em;
            margin-left: 8px;
        }
        
        .recommendation-buy {
            background: #c8e6c9;
            color: #2e7d32;
            border: 1px solid #4caf50;
        }
        
        .recommendation-sell {
            background: #ffcdd2;
            color: #c62828;
            border: 1px solid #f44336;
        }
        
        .recommendation-hold {
            background: #fff3e0;
            color: #ef6c00;
            border: 1px solid #ff9800;
        }
        
        .confidence-score {
            margin-top: 8px;
            font-size: 0.9em;
            color: #555;
        }
        
        .ai-reasoning {
            margin-top: 12px;
            padding: 10px;
            background: #f8f9fa;
            border-radius: 6px;
            border-left: 3px solid #007bff;
            font-style: italic;
            line-height: 1.4;
        }
        
        .raw-response {
            margin-top: 10px;
        }
        
        .raw-response details {
            cursor: pointer;
        }
        
        .raw-response summary {
            color: #007bff;
            font-size: 0.85em;
            margin-bottom: 5px;
        }
        
        .raw-response summary:hover {
            text-decoration: underline;
        }
        
        .ai-full-response {
            background: #f1f3f4;
            padding: 10px;
            border-radius: 4px;
            font-family: monospace;
            font-size: 0.85em;
            white-space: pre-wrap;
            margin-top: 5px;
            border: 1px solid #e0e0e0;
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
        
        /* Attention level badges */
        .attention-badge {
            display: inline-block;
            padding: 4px 8px;
            border-radius: 12px;
            font-size: 0.75em;
            font-weight: bold;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-left: 8px;
            white-space: nowrap;
        }
        
        .attention-badge.critical {
            background: linear-gradient(135deg, #dc3545, #b02a37);
            color: white;
            box-shadow: 0 2px 4px rgba(220, 53, 69, 0.3);
            animation: pulse-critical 2s infinite;
        }
        
        .attention-badge.high {
            background: linear-gradient(135deg, #fd7e14, #e8590c);
            color: white;
            box-shadow: 0 2px 4px rgba(253, 126, 20, 0.3);
        }
        
        .attention-badge.moderate {
            background: linear-gradient(135deg, #ffc107, #e0a800);
            color: #212529;
            box-shadow: 0 2px 4px rgba(255, 193, 7, 0.3);
        }
        
        .attention-badge.low {
            background: linear-gradient(135deg, #17a2b8, #138496);
            color: white;
            box-shadow: 0 2px 4px rgba(23, 162, 184, 0.3);
        }
        
        .attention-badge.minimal {
            background: linear-gradient(135deg, #28a745, #20c997);
            color: white;
            box-shadow: 0 2px 4px rgba(40, 167, 69, 0.3);
        }
        
        @keyframes pulse-critical {
            0% { box-shadow: 0 2px 4px rgba(220, 53, 69, 0.3); }
            50% { box-shadow: 0 4px 8px rgba(220, 53, 69, 0.6); }
            100% { box-shadow: 0 2px 4px rgba(220, 53, 69, 0.3); }
        }
        
        /* Clickable metrics dropdown styles */
        .metric-value-clickable {
            cursor: pointer;
            position: relative;
            transition: all 0.2s ease;
            border-radius: 6px;
        }
        
        .metric-value-clickable:hover {
            background-color: rgba(102, 126, 234, 0.1);
            transform: scale(1.02);
            box-shadow: 0 2px 8px rgba(102, 126, 234, 0.2);
        }
        
        .metric-card {
            position: relative;
            overflow: visible;
        }
        
        .symbol-dropdown {
            position: absolute;
            top: calc(100% + 12px);
            left: 50%;
            transform: translateX(-50%);
            background: white;
            border: 1px solid #e1e5e9;
            border-radius: 12px;
            box-shadow: 0 12px 40px rgba(0, 0, 0, 0.15), 0 4px 12px rgba(0, 0, 0, 0.1);
            min-width: 280px;
            max-width: 380px;
            width: max-content;
            z-index: 9999;
            display: none;
            backdrop-filter: blur(10px);
        }
        
        .symbol-dropdown::before {
            content: '';
            position: absolute;
            top: -8px;
            left: 50%;
            transform: translateX(-50%);
            width: 0;
            height: 0;
            border-left: 8px solid transparent;
            border-right: 8px solid transparent;
            border-bottom: 8px solid white;
            z-index: 10000;
        }
        
        .symbol-dropdown::after {
            content: '';
            position: absolute;
            top: -9px;
            left: 50%;
            transform: translateX(-50%);
            width: 0;
            height: 0;
            border-left: 9px solid transparent;
            border-right: 9px solid transparent;
            border-bottom: 9px solid #e1e5e9;
            z-index: 9999;
        }
        
        /* Bottom arrow variant */
        .symbol-dropdown.arrow-bottom::before {
            top: auto;
            bottom: -8px;
            border-bottom: none;
            border-top: 8px solid white;
        }
        
        .symbol-dropdown.arrow-bottom::after {
            top: auto;
            bottom: -9px;
            border-bottom: none;
            border-top: 9px solid #e1e5e9;
        }
        
        .symbol-dropdown.active {
            display: block;
            animation: dropdownFadeIn 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }
        
        @keyframes dropdownFadeIn {
            from { 
                opacity: 0; 
                transform: translateX(-50%) translateY(-15px) scale(0.95);
                filter: blur(2px);
            }
            to { 
                opacity: 1; 
                transform: translateX(-50%) translateY(0) scale(1);
                filter: blur(0px);
            }
        }
        
        .dropdown-header {
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            padding: 12px 16px;
            border-radius: 12px 12px 0 0;
            font-weight: 600;
            font-size: 0.85em;
            text-align: center;
            letter-spacing: 0.2px;
        }
        
        .dropdown-content {
            max-height: 250px;
            overflow-y: auto;
            padding: 6px 0;
        }
        
        .dropdown-content::-webkit-scrollbar {
            width: 6px;
        }
        
        .dropdown-content::-webkit-scrollbar-track {
            background: #f8f9fa;
            border-radius: 3px;
        }
        
        .dropdown-content::-webkit-scrollbar-thumb {
            background: #667eea;
            border-radius: 3px;
        }
        
        .symbol-item {
            padding: 10px 14px;
            margin: 0 6px;
            border-radius: 6px;
            transition: all 0.2s ease;
            cursor: pointer;
            position: relative;
        }
        
        .symbol-item:hover {
            background: linear-gradient(135deg, rgba(102, 126, 234, 0.08), rgba(118, 75, 162, 0.08));
            transform: translateX(4px);
            box-shadow: 0 2px 8px rgba(102, 126, 234, 0.15);
        }
        
        .symbol-name {
            font-weight: 600;
            color: #667eea;
            margin-bottom: 4px;
            font-size: 0.95em;
            letter-spacing: 0.3px;
        }
        
        .symbol-details {
            font-size: 0.78em;
            color: #6c757d;
            line-height: 1.3;
        }
        
        .dropdown-actions {
            padding: 8px 16px;
            background: #f8f9fa;
            border-top: 1px solid #e9ecef;
            border-radius: 0 0 8px 8px;
            text-align: center;
        }
        
        .dropdown-btn {
            background: #667eea;
            color: white;
            border: none;
            padding: 6px 12px;
            border-radius: 4px;
            font-size: 0.8em;
            cursor: pointer;
            margin: 0 4px;
            transition: background-color 0.2s ease;
        }
        
        .dropdown-btn:hover {
            background: #5a67d8;
        }
        
        .dropdown-btn.secondary {
            background: #6c757d;
        }
        
        .dropdown-btn.secondary:hover {
            background: #545b62;
        }
        
        .no-symbols {
            padding: 18px 14px;
            text-align: center;
            color: #8e9aaf;
            font-style: italic;
            font-size: 0.8em;
            border-radius: 0 0 12px 12px;
        }
        
        @media (max-width: 768px) {
            .container {
                margin: 10px;
                padding: 15px;
            }
            
            .metrics-grid {
                grid-template-columns: 1fr;
                gap: 16px;
            }
            
            .header h1 {
                font-size: 2em;
            }
            
            .stock-table {
                font-size: 0.9em;
            }
            
            .symbol-dropdown {
                position: fixed !important;
                top: 50% !important;
                left: 50% !important;
                transform: translate(-50%, -50%) !important;
                width: 85vw !important;
                max-width: 340px !important;
                min-width: 280px !important;
                z-index: 99999 !important;
                max-height: 70vh;
                overflow: hidden;
            }
            
            .symbol-dropdown::before {
                display: none;
            }
            
            .dropdown-content {
                max-height: calc(70vh - 140px);
                padding: 4px 0;
            }
            
            .symbol-item {
                padding: 12px 16px;
                margin: 0 4px;
            }
            
            .metric-value-clickable:hover {
                transform: scale(1.01);
            }
        }
        
        @media (max-width: 480px) {
            .symbol-dropdown {
                width: 90vw !important;
                max-width: none !important;
                min-width: 260px !important;
            }
            
            .dropdown-header {
                padding: 12px 16px;
                font-size: 0.9em;
            }
            
            .symbol-item {
                padding: 10px 14px;
            }
            
            .symbol-name {
                font-size: 1em;
            }
            
            .symbol-details {
                font-size: 0.85em;
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
        
        # Get portfolio ID for links
        portfolio_id = data.get('portfolio', {}).get('holdings_summary', {}).get('portfolio_id', 'unknown')
        
        # Prepare asset data for each metric
        stocks = data.get('stocks', {})
        
        # Sentiment distribution asset data
        positive_assets = []
        neutral_assets = []
        negative_assets = []
        
        for symbol, stock in stocks.items():
            sentiment = stock.get('sentiment', {}).get('overall', 'neutral')
            asset_data = {
                'symbol': symbol,
                'value': f"Sentiment: {sentiment.title()}, Score: {stock.get('sentiment', {}).get('score', 0):.3f}",
                'portfolioUrl': f'/portfolio/{portfolio_id}#{symbol}',
                'analysisUrl': f'/portfolio/{portfolio_id}/analysis?focus={symbol}'
            }
            
            if sentiment == 'positive':
                positive_assets.append(asset_data)
            elif sentiment == 'negative':
                negative_assets.append(asset_data)
            else:
                neutral_assets.append(asset_data)
        
        # Technical overview asset data
        overbought_assets = []
        oversold_assets = []
        
        for symbol, stock in stocks.items():
            rsi = stock.get('technical', {}).get('rsi', 50)
            asset_data = {
                'symbol': symbol,
                'value': f"RSI: {rsi:.2f}",
                'portfolioUrl': f'/portfolio/{portfolio_id}#{symbol}',
                'analysisUrl': f'/portfolio/{portfolio_id}/analysis?focus={symbol}'
            }
            
            if rsi > 70:
                overbought_assets.append(asset_data)
            elif rsi < 30:
                oversold_assets.append(asset_data)
        
        # AI recommendations asset data
        buy_assets = []
        hold_assets = []
        sell_assets = []
        
        for symbol, stock in stocks.items():
            recommendation = stock.get('ai_analysis', {}).get('recommendation_type', 'HOLD')
            confidence = stock.get('ai_analysis', {}).get('confidence', 0)
            asset_data = {
                'symbol': symbol,
                'value': f"Recommendation: {recommendation}, Confidence: {confidence:.1f}%",
                'portfolioUrl': f'/portfolio/{portfolio_id}#{symbol}',
                'analysisUrl': f'/portfolio/{portfolio_id}/analysis?focus={symbol}'
            }
            
            if recommendation == 'BUY':
                buy_assets.append(asset_data)
            elif recommendation == 'SELL':
                sell_assets.append(asset_data)
            else:
                hold_assets.append(asset_data)
        
        return f"""
        <div class="section">
            <h2>Market Analysis & Strategic Outlook</h2>
            
            <h3>Sentiment Distribution</h3>
            <div class="metrics-grid">
                <div class="metric-card">
                    <div class="value positive metric-value-clickable" data-assets='{json.dumps(positive_assets)}'>{sentiment_dist.get('positive', 0)}</div>
                    <div class="label">Positive Sentiment</div>
                </div>
                <div class="metric-card">
                    <div class="value neutral metric-value-clickable" data-assets='{json.dumps(neutral_assets)}'>{sentiment_dist.get('neutral', 0)}</div>
                    <div class="label">Neutral Sentiment</div>
                </div>
                <div class="metric-card">
                    <div class="value negative metric-value-clickable" data-assets='{json.dumps(negative_assets)}'>{sentiment_dist.get('negative', 0)}</div>
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
                    <div class="value warning metric-value-clickable" data-assets='{json.dumps(overbought_assets)}'>{technical.get('overbought_count', 0)}</div>
                    <div class="label">Overbought Positions</div>
                </div>
                <div class="metric-card">
                    <div class="value warning metric-value-clickable" data-assets='{json.dumps(oversold_assets)}'>{technical.get('oversold_count', 0)}</div>
                    <div class="label">Oversold Positions</div>
                </div>
            </div>
            
            <h3>AI Recommendations Summary</h3>
            <div class="metrics-grid">
                <div class="metric-card">
                    <div class="value positive metric-value-clickable" data-assets='{json.dumps(buy_assets)}'>{recommendations.get('buy_signals', 0)}</div>
                    <div class="label">BUY Signals</div>
                </div>
                <div class="metric-card">
                    <div class="value neutral metric-value-clickable" data-assets='{json.dumps(hold_assets)}'>{recommendations.get('hold_signals', 0)}</div>
                    <div class="label">HOLD Signals</div>
                </div>
                <div class="metric-card">
                    <div class="value negative metric-value-clickable" data-assets='{json.dumps(sell_assets)}'>{recommendations.get('sell_signals', 0)}</div>
                    <div class="label">SELL Signals</div>
                </div>
            </div>
        </div>
        """
    
    def _render_individual_stocks(self, data: Dict) -> str:
        """Render individual stock analysis ordered by attention urgency"""
        stocks = data.get('stocks', {})
        
        if not stocks:
            return ""
        
        # Sort stocks by attention priority (most urgent first)
        sorted_stocks = self._sort_stocks_by_attention(stocks)
        
        stocks_html = """
        <div class="section">
            <h2>Individual Stock Analysis</h2>
            <p style="color: #6c757d; font-style: italic; margin-bottom: 20px;">
                📊 Stocks are ordered by priority - those needing most attention appear first
            </p>
        """
        
        for symbol, stock in sorted_stocks:
            # Add attention indicator badge
            attention_score = self._calculate_attention_score(stock)
            attention_badge = self._get_attention_badge(attention_score)
            stocks_html += self._render_stock_card(symbol, stock, attention_badge)
        
        stocks_html += "</div>"
        return stocks_html
    
    def _sort_stocks_by_attention(self, stocks: Dict) -> List:
        """Sort stocks by attention urgency (highest priority first)"""
        stock_items = []
        
        for symbol, stock in stocks.items():
            attention_score = self._calculate_attention_score(stock)
            stock_items.append((symbol, stock, attention_score))
        
        # Sort by attention score (descending - highest attention first)
        stock_items.sort(key=lambda x: x[2], reverse=True)
        
        # Return as (symbol, stock) tuples
        return [(symbol, stock) for symbol, stock, score in stock_items]
    
    def _calculate_attention_score(self, stock: Dict) -> float:
        """Calculate urgency score for a stock (higher = needs more attention)"""
        score = 0.0
        
        # 1. Risk factors (high weight)
        technical = stock.get('technical', {})
        rsi = technical.get('rsi', 50)
        
        # Extreme RSI values need immediate attention
        if rsi > 80 or rsi < 20:
            score += 100  # Critical
        elif rsi > 70 or rsi < 30:
            score += 60   # High attention
        elif rsi > 65 or rsi < 35:
            score += 30   # Moderate attention
        
        # 2. Performance factors
        profit_loss_percent = stock.get('profit_loss_percent', 0)
        
        # Large losses need attention
        if profit_loss_percent < -15:
            score += 80   # Significant losses
        elif profit_loss_percent < -10:
            score += 50   # Notable losses
        elif profit_loss_percent < -5:
            score += 20   # Minor losses
        
        # Large gains may need profit-taking consideration
        if profit_loss_percent > 25:
            score += 40   # Consider profit-taking
        elif profit_loss_percent > 15:
            score += 20   # Monitor for profit-taking
        
        # 3. AI recommendation urgency
        ai_analysis = stock.get('ai_analysis', {})
        recommendation = ai_analysis.get('recommendation_type', 'HOLD')
        confidence = ai_analysis.get('confidence', 0)
        
        if recommendation == 'SELL':
            score += 70 + (confidence * 0.3)  # High urgency for sell signals
        elif recommendation == 'BUY':
            score += 50 + (confidence * 0.2)  # Moderate urgency for buy signals
        
        # 4. Sentiment factors
        sentiment = stock.get('sentiment', {})
        sentiment_overall = sentiment.get('overall', 'neutral')
        sentiment_score = sentiment.get('score', 0)
        
        if sentiment_overall == 'negative':
            score += 30 + abs(sentiment_score * 20)
        elif sentiment_overall == 'positive':
            score += 15 + (sentiment_score * 10)
        
        # 5. Risk level priority
        risk = stock.get('risk', {})
        risk_level = risk.get('risk_level', 'medium').lower()
        
        if risk_level == 'high':
            score += 40
        elif risk_level == 'medium':
            score += 15
        
        # 6. Moving average signals
        current_price = stock.get('current_price', 0)
        ma_20 = technical.get('ma_20', 0)
        ma_50 = technical.get('ma_50', 0)
        
        if current_price and ma_20 and ma_50:
            # Price below both MAs suggests attention needed
            if current_price < ma_20 and current_price < ma_50:
                score += 25
            # Death cross pattern (MA20 below MA50)
            elif ma_20 < ma_50:
                score += 20
        
        return score
    
    def _get_attention_badge(self, attention_score: float) -> str:
        """Generate attention level badge based on score"""
        if attention_score >= 200:
            return '<span class="attention-badge critical">🚨 CRITICAL</span>'
        elif attention_score >= 120:
            return '<span class="attention-badge high">⚠️ HIGH</span>'
        elif attention_score >= 60:
            return '<span class="attention-badge moderate">📊 MODERATE</span>'
        elif attention_score >= 20:
            return '<span class="attention-badge low">💡 LOW</span>'
        else:
            return '<span class="attention-badge minimal">✅ MINIMAL</span>'
    
    def _render_stock_card(self, symbol: str, stock: Dict, attention_badge: str = "") -> str:
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
                <h4 style="text-align: center; margin-bottom: 10px;">📈 Price & Volume Chart (90 Days)</h4>
                <div class="chart-container" style="height: 450px; margin-bottom: 10px;">
                    <canvas id="stockChart_{symbol}"></canvas>
                </div>
            </div>
            """
        
        return f"""
        <div class="metric-card" style="margin-bottom: 30px; text-align: left;">
            <h3 style="color: #667eea; margin-bottom: 15px; text-align: center;">
                {symbol} Analysis {attention_badge}
            </h3>
            
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
                <strong>AI Recommendation:</strong> 
                <span class="recommendation-badge recommendation-{ai_analysis.get('recommendation', 'HOLD').lower()}">
                    {ai_analysis.get('recommendation', 'N/A')}
                </span>
                
                {f'''<div class="confidence-score">
                    <strong>Confidence:</strong> {ai_analysis.get('confidence', 0):.0f}%
                </div>''' if ai_analysis.get('confidence', 0) > 0 else ''}
                
                {f'''<div class="ai-reasoning">
                    <strong>Analysis:</strong> {ai_analysis.get('reasoning', 'No detailed analysis available')}
                </div>''' if ai_analysis.get('reasoning') and ai_analysis.get('reasoning') != 'No analysis available' else ''}
                
                {f'''<div class="raw-response">
                    <details>
                        <summary>Full AI Response</summary>
                        <div class="ai-full-response">{ai_analysis.get('raw_response', '')}</div>
                    </details>
                </div>''' if ai_analysis.get('raw_response') and ai_analysis.get('raw_response') != ai_analysis.get('reasoning', '') else ''}
            </div>
        </div>
        """
    
    def _render_performance_metrics(self, data: Dict) -> str:
        """Render performance metrics and risk alerts"""
        portfolio = data.get('portfolio', {})
        stocks = data.get('stocks', {})
        performance = data.get('performance', {})
        risk_alerts = performance.get('risk_alerts', [])
        
        # Calculate additional performance metrics
        total_value = portfolio.get('total_value', 0)
        total_invested = portfolio.get('total_invested', 0)
        total_return_percent = portfolio.get('total_return_percent', 0)
        position_count = portfolio.get('position_count', 0)
        profitable_positions = portfolio.get('profitable_positions', 0)
        
        # Calculate risk metrics
        high_risk_count = 0
        volatile_stocks = []
        underperforming_stocks = []
        
        for symbol, stock in stocks.items():
            # Check for high-risk positions
            profit_loss_percent = stock.get('profit_loss_percent', 0)
            if profit_loss_percent < -10:
                high_risk_count += 1
                underperforming_stocks.append({
                    'symbol': symbol,
                    'return': profit_loss_percent
                })
            
            # Check for volatile positions (high RSI values)
            rsi = stock.get('technical', {}).get('rsi', 50)
            if rsi > 70 or rsi < 30:
                volatile_stocks.append({
                    'symbol': symbol,
                    'rsi': rsi
                })
        
        # Performance metrics grid
        metrics_html = f"""
        <h3>Portfolio Performance Metrics</h3>
        <div class="metrics-grid">
            <div class="metric-card">
                <div class="value {'positive' if total_return_percent > 0 else 'negative'}">{total_return_percent:+.2f}%</div>
                <div class="label">Total Return</div>
            </div>
            <div class="metric-card">
                <div class="value {'positive' if profitable_positions > position_count/2 else 'negative'}">{profitable_positions}/{position_count}</div>
                <div class="label">Profitable Positions</div>
            </div>
            <div class="metric-card">
                <div class="value {'warning' if high_risk_count > 0 else 'positive'}">{high_risk_count}</div>
                <div class="label">High Risk Positions</div>
            </div>
            <div class="metric-card">
                <div class="value {'warning' if len(volatile_stocks) > 0 else 'positive'}">{len(volatile_stocks)}</div>
                <div class="label">Volatile Positions</div>
            </div>
        </div>
        """
        
        # Risk alerts section
        alerts_html = ""
        if risk_alerts:
            alerts_html = "<h3>⚠️ Risk Alerts</h3>"
            for alert in risk_alerts:
                alerts_html += f"""
                <div class="risk-alert">
                    <strong>{alert.get('symbol', 'N/A')}</strong>: {alert.get('reason', 'N/A')} 
                    (Value: {alert.get('value', 0):.2f})
                </div>
                """
        elif underperforming_stocks:
            alerts_html = "<h3>⚠️ Underperforming Positions</h3>"
            for stock in underperforming_stocks[:3]:  # Show top 3
                alerts_html += f"""
                <div class="risk-alert">
                    <strong>{stock['symbol']}</strong>: Down {stock['return']:.1f}% - Consider reviewing position
                </div>
                """
        
        # Volatile positions section
        volatile_html = ""
        if volatile_stocks:
            volatile_html = "<h3>📊 Technical Attention Required</h3>"
            for stock in volatile_stocks[:3]:  # Show top 3
                status = "Overbought" if stock['rsi'] > 70 else "Oversold"
                volatile_html += f"""
                <div class="recommendation">
                    <strong>{stock['symbol']}</strong>: RSI {stock['rsi']:.1f} - {status} condition detected
                </div>
                """
        
        return f"""
        <div class="section">
            <h2>Performance Metrics & Risk Assessment</h2>
            {metrics_html}
            {alerts_html}
            {volatile_html}
        </div>
        """
    
    def _render_historical_trends(self, data: Dict) -> str:
        """Render historical trends and portfolio composition analysis"""
        stocks = data.get('stocks', {})
        portfolio = data.get('portfolio', {})
        
        # Calculate sector distribution
        sector_distribution = {}
        total_value = 0
        
        for symbol, stock in stocks.items():
            sector = stock.get('sector', 'Unknown')
            value = stock.get('current_value', 0)
            total_value += value
            
            if sector in sector_distribution:
                sector_distribution[sector] += value
            else:
                sector_distribution[sector] = value
        
        # Calculate percentages and sort
        sector_percentages = []
        if total_value > 0:
            for sector, value in sector_distribution.items():
                percentage = (value / total_value) * 100
                sector_percentages.append((sector, percentage, value))
            sector_percentages.sort(key=lambda x: x[1], reverse=True)
        
        # Portfolio composition table
        composition_html = """
        <h3>📊 Portfolio Composition by Sector</h3>
        <div class="stock-table" style="margin-bottom: 25px;">
            <table class="stock-table">
                <thead>
                    <tr>
                        <th>Sector</th>
                        <th>Allocation</th>
                        <th>Value</th>
                        <th>Risk Level</th>
                    </tr>
                </thead>
                <tbody>
        """
        
        for sector, percentage, value in sector_percentages:
            risk_class = "high" if percentage > 40 else "moderate" if percentage > 25 else "low"
            composition_html += f"""
                    <tr>
                        <td><strong>{sector}</strong></td>
                        <td>{percentage:.1f}%</td>
                        <td>${value:,.2f}</td>
                        <td><span class="trend-indicator trend-{risk_class}">{risk_class.upper()}</span></td>
                    </tr>
            """
        
        composition_html += """
                </tbody>
            </table>
        </div>
        """
        
        # Portfolio allocation insights
        insights_html = """
        <h3>💡 Portfolio Insights</h3>
        <div class="metrics-grid">
        """
        
        if sector_percentages:
            top_sector = sector_percentages[0]
            concentration_risk = "High" if top_sector[1] > 50 else "Moderate" if top_sector[1] > 30 else "Low"
            diversification = "Good" if len(sector_percentages) >= 4 else "Limited" if len(sector_percentages) >= 2 else "Poor"
            
            insights_html += f"""
            <div class="metric-card">
                <div class="value">{top_sector[0]}</div>
                <div class="label">Largest Sector ({top_sector[1]:.1f}%)</div>
            </div>
            <div class="metric-card">
                <div class="value {'warning' if concentration_risk == 'High' else 'positive' if concentration_risk == 'Low' else 'neutral'}">{concentration_risk}</div>
                <div class="label">Concentration Risk</div>
            </div>
            <div class="metric-card">
                <div class="value {'positive' if diversification == 'Good' else 'warning' if diversification == 'Limited' else 'negative'}">{diversification}</div>
                <div class="label">Diversification</div>
            </div>
            <div class="metric-card">
                <div class="value">{len(sector_percentages)}</div>
                <div class="label">Sectors Represented</div>
            </div>
            """
        
        insights_html += "</div>"
        
        # Historical trend chart (improved)
        chart_html = f"""
        <h3>📈 Portfolio Trend Analysis</h3>
        <div class="chart-container">
            <canvas id="trendsChart"></canvas>
        </div>
        <p style="text-align: center; color: #6c757d; margin-top: 20px; font-style: italic;">
            Chart shows portfolio composition by value. Historical performance tracking will improve with more data collection over time.
        </p>
        """
        
        return f"""
        <div class="section">
            <h2>Historical Trends & Portfolio Analysis</h2>
            {composition_html}
            {insights_html}
            {chart_html}
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
                volumes = chart_data.get('volumes', [])
                print(f"DEBUG {symbol} chart_data keys: {list(chart_data.keys())}")
                print(f"DEBUG {symbol} volume data: {len(volumes)} volumes, sample: {volumes[:3] if volumes else []}")
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
                
                # Get price range for smart y-axis scaling
                prices = [p for p in chart_data['prices'] if p is not None]
                if prices:
                    min_price = min(prices)
                    max_price = max(prices)
                    price_range = max_price - min_price
                    y_min = max(0, min_price - (price_range * 0.05))  # 5% padding below
                    y_max = max_price + (price_range * 0.05)  # 5% padding above
                else:
                    y_min = None
                    y_max = None
                
                # Get volume data and calculate scaling
                volumes = chart_data.get('volumes', [])[-90:]
                volume_max = max([v for v in volumes if v is not None]) if any(v is not None for v in volumes) else 1
                
                stock_charts_js += """
                // %s stock chart with volume
                const %sCtx = document.getElementById('stockChart_%s');
                if (%sCtx) {
                    new Chart(%sCtx, {
                        type: 'line',
                        data: {
                            labels: %s,
                            datasets: [
                                {
                                    label: 'Price ($)',
                                    data: %s,
                                    borderColor: '#667eea',
                                    backgroundColor: 'rgba(102, 126, 234, 0.1)',
                                    borderWidth: 2,
                                    tension: 0.1,
                                    yAxisID: 'y',
                                    pointRadius: 1,
                                    pointHoverRadius: 4
                                },
                                {
                                    label: '20-day MA',
                                    data: %s,
                                    borderColor: '#ffc107',
                                    backgroundColor: 'rgba(255, 193, 7, 0.1)',
                                    borderWidth: 1,
                                    tension: 0.1,
                                    yAxisID: 'y',
                                    pointRadius: 0
                                },
                                {
                                    label: '50-day MA',
                                    data: %s,
                                    borderColor: '#28a745',
                                    backgroundColor: 'rgba(40, 167, 69, 0.1)',
                                    borderWidth: 1,
                                    tension: 0.1,
                                    yAxisID: 'y',
                                    pointRadius: 0
                                },
                                {
                                    label: 'Cost Basis',
                                    data: Array(%d).fill(%f),
                                    borderColor: '#dc3545',
                                    backgroundColor: 'rgba(220, 53, 69, 0.1)',
                                    borderWidth: 2,
                                    borderDash: [5, 5],
                                    yAxisID: 'y',
                                    pointRadius: 0
                                },
                                {
                                    label: 'Volume',
                                    data: %s,
                                    type: 'bar',
                                    backgroundColor: 'rgba(255, 159, 64, 0.3)',
                                    borderColor: 'rgba(255, 159, 64, 0.8)',
                                    borderWidth: 1,
                                    yAxisID: 'y1',
                                    order: 2
                                }
                            ]
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false,
                            interaction: {
                                mode: 'index',
                                intersect: false
                            },
                            plugins: {
                                title: {
                                    display: true,
                                    text: '%s - Price & Volume Chart (90 Days)',
                                    font: { size: 14 }
                                },
                                legend: {
                                    position: 'top',
                                    labels: { usePointStyle: true }
                                }
                            },
                            scales: {
                                x: {
                                    display: true,
                                    title: { display: true, text: 'Date' }
                                },
                                y: {
                                    type: 'linear',
                                    display: true,
                                    position: 'left',
                                    title: { display: true, text: 'Price ($)' },
                                    min: %s,
                                    max: %s
                                },
                                y1: {
                                    type: 'linear',
                                    display: true,
                                    position: 'right',
                                    title: { display: true, text: 'Volume' },
                                    max: %d,
                                    grid: {
                                        drawOnChartArea: false
                                    }
                                }
                            }
                        }
                    });
                }
                """ % (
                    symbol, symbol.lower(), symbol, symbol.lower(), symbol.lower(),
                    json.dumps(chart_data['dates'][-90:]),
                    json.dumps(chart_data['prices'][-90:]),
                    json.dumps(chart_data.get('ma_20', [])[-90:]),
                    json.dumps(chart_data.get('ma_50', [])[-90:]),
                    len(chart_data['dates'][-90:]), cost_basis,
                    json.dumps(volumes),
                    symbol,
                    y_min if y_min is not None else "null",
                    y_max if y_max is not None else "null",
                    int(volume_max * 1.1) if volume_max else 1000000
                )

        # Return JavaScript content without f-strings
        javascript_content = """
        <script>
            // Toggle collapsible content
            function toggleContent(id) {
                const content = document.getElementById(id);
                content.classList.toggle('active');
                
                const parent = content.previousElementSibling;
                const arrow = parent.querySelector('h3');
                if (content.classList.contains('active')) {
                    arrow.textContent = arrow.textContent.replace('▼', '▲');
                } else {
                    arrow.textContent = arrow.textContent.replace('▲', '▼');
                }
            }
            
        document.addEventListener('DOMContentLoaded', function() {
            // Portfolio chart
            const ctx = document.getElementById('portfolioChart');
            if (ctx) {
                const ctxContext = ctx.getContext('2d');
                new Chart(ctxContext, {
                    type: 'doughnut',
                    data: {
                        labels: """ + json.dumps([stock['symbol'] for stock in portfolio_data]) + """,
                        datasets: [{
                            data: """ + json.dumps([stock['value'] for stock in portfolio_data]) + """,
                            backgroundColor: [
                                '#667eea', '#764ba2', '#f093fb', '#f5576c', 
                                '#4facfe', '#43e97b', '#fa709a', '#fee140',
                                '#a8edea', '#fed6e3', '#d299c2', '#fef9d7'
                            ],
                            borderWidth: 2,
                            borderColor: '#fff'
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            title: {
                                display: true,
                                text: 'Portfolio Allocation by Value',
                                font: { size: 16 }
                            },
                            legend: {
                                position: 'bottom'
                            }
                        }
                    }
                });
            }
            
            // Individual stock charts
            """ + stock_charts_js + """
            
            // Trends chart (placeholder)  
            const trendsCtx = document.getElementById('trendsChart');
            if (trendsCtx) {
                const trendsContext = trendsCtx.getContext('2d');
                new Chart(trendsContext, {
                    type: 'line',
                    data: {
                        labels: ['Day 1', 'Day 2', 'Day 3', 'Day 4', 'Day 5'],
                        datasets: [{
                            label: 'Portfolio Value',
                            data: [100, 102, 98, 105, 110],
                            borderColor: '#667eea',
                            backgroundColor: 'rgba(102, 126, 234, 0.1)',
                            tension: 0.4
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            title: {
                                display: true,
                                text: 'Portfolio Performance Trend (Sample Data)',
                                font: { size: 16 }
                            }
                        },
                        scales: {
                            y: {
                                beginAtZero: false
                            }
                        }
                    }
                });
            }
            
            // Clickable metrics dropdown functionality
            (function() {
                let currentDropdown = null;
                
                function closeAllDropdowns() {
                    document.querySelectorAll('.symbol-dropdown').forEach(function(dropdown) {
                        dropdown.remove();
                    });
                    
                    // Reset metric card styles
                    document.querySelectorAll('.metric-card').forEach(function(card) {
                        card.style.overflow = '';
                        card.style.zIndex = '';
                    });
                    
                    currentDropdown = null;
                }
                
                function createDropdown(assets, title) {
                    if (!assets || assets.length === 0) {
                        return '<div class="symbol-dropdown">' +
                               '<div class="dropdown-header">' + title + '</div>' +
                               '<div class="no-symbols">No assets in this category</div>' +
                               '</div>';
                    }
                    
                    let symbolsHtml = '';
                    assets.forEach(function(asset) {
                        symbolsHtml += '<div class="symbol-item" data-symbol="' + asset.symbol + '">' +
                                       '<div class="symbol-name">' + asset.symbol + '</div>' +
                                       '<div class="symbol-details">' + asset.value + '</div>' +
                                       '</div>';
                    });
                    
                    return '<div class="symbol-dropdown">' +
                           '<div class="dropdown-header">' + title + '</div>' +
                           '<div class="dropdown-content">' + symbolsHtml + '</div>' +
                           '</div>';
                }
                
                function scrollToSymbol(symbol) {
                    const headings = document.querySelectorAll('h3, h4');
                    let targetElement = null;
                    
                    for (let i = 0; i < headings.length; i++) {
                        if (headings[i].textContent.includes(symbol)) {
                            targetElement = headings[i];
                            break;
                        }
                    }
                    
                    if (targetElement) {
                        targetElement.scrollIntoView({
                            behavior: 'smooth',
                            block: 'start'
                        });
                        targetElement.style.background = 'rgba(102, 126, 234, 0.2)';
                        setTimeout(function() {
                            targetElement.style.background = '';
                        }, 2000);
                    } else {
                        const allElements = document.querySelectorAll('*');
                        for (let i = 0; i < allElements.length; i++) {
                            const element = allElements[i];
                            if (element.textContent.includes(symbol + ' Analysis') || 
                                element.textContent.includes(symbol + ':') ||
                                (element.tagName === 'STRONG' && element.textContent === symbol)) {
                                element.scrollIntoView({
                                    behavior: 'smooth',
                                    block: 'center'
                                });
                                element.style.background = 'rgba(102, 126, 234, 0.2)';
                                setTimeout(function() {
                                    element.style.background = '';
                                }, 2000);
                                break;
                            }
                        }
                    }
                }
                
                document.querySelectorAll('.metric-value-clickable').forEach(function(metric) {
                    metric.addEventListener('click', function(e) {
                        e.stopPropagation();
                        
                        if (currentDropdown === this) {
                            closeAllDropdowns();
                            return;
                        }
                        
                        closeAllDropdowns();
                        
                        const assetsData = this.getAttribute('data-assets');
                        if (!assetsData) return;
                        
                        let assets;
                        try {
                            assets = JSON.parse(assetsData);
                        } catch (err) {
                            console.error('Error parsing assets data:', err);
                            return;
                        }
                        
                        const label = this.nextElementSibling.textContent;
                        const title = label + ' (' + this.textContent + ')';
                        
                        const dropdown = document.createElement('div');
                        dropdown.innerHTML = createDropdown(assets, title);
                        const dropdownElement = dropdown.firstElementChild;
                        
                        this.style.position = 'relative';
                        
                        // Ensure parent metric card allows overflow
                        const metricCard = this.closest('.metric-card');
                        if (metricCard) {
                            metricCard.style.overflow = 'visible';
                            metricCard.style.zIndex = '10000';
                        }
                        
                        this.appendChild(dropdownElement);
                        
                        // Adjust position if dropdown would go off-screen
                        setTimeout(function() {
                            const rect = dropdownElement.getBoundingClientRect();
                            const viewportWidth = window.innerWidth;
                            const viewportHeight = window.innerHeight;
                            
                            // Check if dropdown goes off right edge
                            if (rect.right > viewportWidth - 20) {
                                dropdownElement.style.left = 'auto';
                                dropdownElement.style.right = '0';
                                dropdownElement.style.transform = 'translateX(0)';
                            }
                            // Check if dropdown goes off left edge  
                            else if (rect.left < 20) {
                                dropdownElement.style.left = '0';
                                dropdownElement.style.transform = 'translateX(0)';
                            }
                            
                            // Check if dropdown goes off bottom edge
                            if (rect.bottom > viewportHeight - 20) {
                                dropdownElement.style.top = 'auto';
                                dropdownElement.style.bottom = 'calc(100% + 12px)';
                                dropdownElement.classList.add('arrow-bottom');
                            }
                        }, 50);
                        
                        setTimeout(function() {
                            dropdownElement.classList.add('active');
                        }, 10);
                        
                        dropdownElement.querySelectorAll('.symbol-item').forEach(function(item) {
                            item.addEventListener('click', function(e) {
                                e.stopPropagation();
                                const symbol = this.getAttribute('data-symbol');
                                scrollToSymbol(symbol);
                                closeAllDropdowns();
                            });
                        });
                        
                        currentDropdown = this;
                    });
                });
                
                document.addEventListener('click', function(e) {
                    if (!e.target.closest('.metric-value-clickable') && !e.target.closest('.symbol-dropdown')) {
                        closeAllDropdowns();
                    }
                });
                
                window.addEventListener('scroll', function() {
                    closeAllDropdowns();
                });
                
                window.addEventListener('resize', function() {
                    closeAllDropdowns();
                });
                
                window.addEventListener('orientationchange', function() {
                    setTimeout(closeAllDropdowns, 100);
                });
                
                document.addEventListener('keydown', function(e) {
                    if (e.key === 'Escape') {
                        closeAllDropdowns();
                    }
                });
            })();
        });
        </script>
        """
        
        return javascript_content 
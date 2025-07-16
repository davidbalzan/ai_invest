import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER
import io
from datetime import datetime
import os

def get_metric_color(metric_name, value, result=None):
    """Determine color based on metric value using traffic light system"""
    
    if metric_name == 'RSI':
        rsi_val = float(value.replace('%', '')) if isinstance(value, str) else value
        if rsi_val > 70:
            return colors.red  # Overbought - Red
        elif rsi_val < 30:
            return colors.red  # Oversold - Red  
        elif 30 <= rsi_val <= 50 or 60 <= rsi_val <= 70:
            return colors.orange  # Caution zones - Amber
        else:  # 50-60 range
            return colors.green  # Good momentum - Green
    
    elif metric_name == 'News Sentiment':
        if value.lower() in ['positive']:
            return colors.green
        elif value.lower() in ['negative']:
            return colors.red
        else:  # neutral
            return colors.orange
    
    elif metric_name == 'P&L':
        # Extract numeric value from string like "+25.78" or "-10.50"
        try:
            if '+' in str(value):
                return colors.green  # Profit - Green
            elif '-' in str(value) and not str(value).startswith('$'):
                return colors.red  # Loss - Red
            else:
                return colors.black
        except:
            return colors.black
    
    elif metric_name == 'Return %':
        try:
            if '+' in str(value):
                return colors.green  # Positive return - Green
            elif '-' in str(value):
                return colors.red  # Negative return - Red
            else:
                return colors.black
        except:
            return colors.black
    
    elif metric_name in ['Current Price', '20-day MA', '50-day MA']:
        # Compare current price to moving averages
        if result and metric_name == 'Current Price':
            current_price = result.get('current_price', 0)
            ma_20 = result.get('ma_20', 0)
            ma_50 = result.get('ma_50', 0)
            
            if current_price > ma_20 and current_price > ma_50:
                return colors.green  # Above both MAs - Bullish
            elif current_price > ma_20 or current_price > ma_50:
                return colors.orange  # Above one MA - Neutral
            else:
                return colors.red  # Below both MAs - Bearish
        
        # For MA values themselves, use different logic
        elif metric_name in ['20-day MA', '50-day MA'] and result:
            current_price = result.get('current_price', 0)
            ma_value = result.get('ma_20' if '20-day' in metric_name else 'ma_50', 0)
            
            if current_price > ma_value:
                return colors.green  # Price above MA - Bullish
            elif abs(current_price - ma_value) / ma_value < 0.02:  # Within 2%
                return colors.orange  # Close to MA - Neutral
            else:
                return colors.red  # Price below MA - Bearish
    
    # Default color for other metrics
    return colors.black

def create_individual_stock_chart(symbol, data, portfolio_holdings):
    """Create an enhanced chart for individual stock with purchase points"""
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10), height_ratios=[3, 1])
    
    # Price chart
    ax1.plot(data.index, data['Close'], label='Close Price', linewidth=2, color='blue')
    
    # Moving averages
    ma_20 = data['Close'].rolling(window=20).mean()
    ma_50 = data['Close'].rolling(window=50).mean()
    ax1.plot(data.index, ma_20, label='20-day MA', alpha=0.7, color='orange')
    ax1.plot(data.index, ma_50, label='50-day MA', alpha=0.7, color='red')
    
    # Add purchase point and current price if in portfolio
    if symbol in portfolio_holdings:
        cost_basis = portfolio_holdings[symbol]['cost_basis']
        current_price = data['Close'].iloc[-1]
        
        # Purchase price line
        ax1.axhline(y=cost_basis, color='red', linestyle='--', alpha=0.8, 
                   label=f'Purchase: ${cost_basis:.2f}')
        
        # Current price line
        ax1.axhline(y=current_price, color='green', linestyle='-', alpha=0.8,
                   label=f'Current: ${current_price:.2f}')
        
        # Profit/Loss shading
        if current_price > cost_basis:
            ax1.fill_between(data.index, cost_basis, current_price, 
                           alpha=0.2, color='green', label='Profit Zone')
        else:
            ax1.fill_between(data.index, current_price, cost_basis, 
                           alpha=0.2, color='red', label='Loss Zone')
        
        # Performance metrics text box
        quantity = portfolio_holdings[symbol]['quantity']
        current_value = current_price * quantity
        total_cost = cost_basis * quantity
        profit_loss = current_value - total_cost
        profit_loss_percent = (profit_loss / total_cost) * 100
        
        textstr = f'''Holdings: {quantity} shares
Total Cost: ${total_cost:.2f}
Current Value: ${current_value:.2f}
P&L: ${profit_loss:+.2f} ({profit_loss_percent:+.1f}%)'''
        
        props = dict(boxstyle='round', facecolor='wheat', alpha=0.8)
        ax1.text(0.02, 0.98, textstr, transform=ax1.transAxes, fontsize=10,
                verticalalignment='top', bbox=props)
    
    ax1.set_title(f'{symbol} Stock Price Analysis', fontsize=16, fontweight='bold')
    ax1.set_ylabel('Price ($)', fontsize=12)
    ax1.legend(loc='upper left')
    ax1.grid(True, alpha=0.3)
    
    # Volume chart
    ax2.bar(data.index, data['Volume'], alpha=0.7, color='gray')
    ax2.set_title('Volume', fontsize=12)
    ax2.set_ylabel('Volume', fontsize=10)
    ax2.set_xlabel('Date', fontsize=12)
    
    # Format x-axis
    for ax in [ax1, ax2]:
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
    
    plt.tight_layout()
    
    # Save chart to bytes
    img_buffer = io.BytesIO()
    plt.savefig(img_buffer, format='png', dpi=300, bbox_inches='tight')
    img_buffer.seek(0)
    plt.close()
    
    return img_buffer

def create_portfolio_overview_chart(portfolio_holdings, get_stock_data):
    """Create portfolio overview chart"""
    if not portfolio_holdings:
        return None
    
    symbols = list(portfolio_holdings.keys())
    total_values = []
    total_costs = []
    labels = []
    
    for symbol in symbols:
        data = get_stock_data(symbol, period="1d")
        if data is not None:
            current_price = data['Close'].iloc[-1]
            holding = portfolio_holdings[symbol]
            cost_basis = holding['cost_basis']
            quantity = holding['quantity']
            
            current_value = current_price * quantity
            total_cost = cost_basis * quantity
            
            total_values.append(current_value)
            total_costs.append(total_cost)
            
            profit_loss = current_value - total_cost
            profit_loss_percent = (profit_loss / total_cost) * 100
            labels.append(f'{symbol}\n${current_value:.0f}\n({profit_loss_percent:+.1f}%)')
    
    if not total_values:
        return None
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
    
    # Portfolio composition pie chart
    ax1.pie(total_values, labels=labels, autopct='%1.1f%%', startangle=90)
    ax1.set_title('Portfolio Composition by Current Value', fontsize=14, fontweight='bold')
    
    # Performance comparison bar chart
    profit_losses = [cv - tc for cv, tc in zip(total_values, total_costs)]
    colors = ['green' if pl > 0 else 'red' for pl in profit_losses]
    
    bars = ax2.bar(symbols, profit_losses, color=colors, alpha=0.7)
    ax2.set_title('Profit/Loss by Stock', fontsize=14, fontweight='bold')
    ax2.set_ylabel('Profit/Loss ($)', fontsize=12)
    ax2.grid(True, alpha=0.3)
    
    # Add value labels on bars
    for bar, pl in zip(bars, profit_losses):
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height,
                f'${pl:.0f}', ha='center', va='bottom' if pl > 0 else 'top')
    
    plt.tight_layout()
    
    # Save chart to bytes
    img_buffer = io.BytesIO()
    plt.savefig(img_buffer, format='png', dpi=300, bbox_inches='tight')
    img_buffer.seek(0)
    plt.close()
    
    return img_buffer

def generate_pdf_report(analysis_results, portfolio_mode, include_individual_charts, report_output_dir, get_stock_data, create_individual_stock_chart, create_portfolio_overview_chart, portfolio_holdings):
    """Generate comprehensive PDF report with enhanced timing and trading window information"""
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from datetime import datetime, timezone
    from market_scheduler import MarketScheduler
    import tempfile
    import os
    
    # Initialize market scheduler for timing information
    market_scheduler = MarketScheduler()
    timing_warnings = market_scheduler.get_market_timing_warnings()
    
    # Create styles
    styles = getSampleStyleSheet()
    
    # Enhanced title styles for timing information
    timing_title_style = ParagraphStyle(
        'TimingTitle',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=colors.red,
        spaceAfter=12,
        spaceBefore=12,
        alignment=1  # Center alignment
    )
    
    urgency_style = ParagraphStyle(
        'UrgencyStyle',
        parent=styles['Normal'],
        fontSize=12,
        textColor=colors.darkred,
        spaceAfter=6,
        fontName='Helvetica-Bold'
    )
    
    data_freshness_style = ParagraphStyle(
        'DataFreshness',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.grey,
        spaceAfter=6,
        fontName='Helvetica-Oblique'
    )
    
    # Generate timestamp
    timestamp = datetime.now(timezone.utc)
    filename = f"portfolio_analysis_{timestamp.strftime('%Y%m%d_%H%M%S')}.pdf"
    filepath = os.path.join(report_output_dir, filename)
    
    # Create PDF document
    doc = SimpleDocTemplate(filepath, pagesize=letter)
    story = []
    temp_files = []  # Track temporary files for cleanup
    
    try:
        # Enhanced Header with Prominent Timing Information
        story.append(Paragraph("AI INVESTMENT PORTFOLIO ANALYSIS", styles['Title']))
        story.append(Spacer(1, 12))
        
        # PROMINENT TIMING AND TRADING WINDOW SECTION
        story.append(Paragraph("🚨 REPORT TIMING & TRADING WINDOW STATUS", timing_title_style))
        
        # Report timing context
        report_context = timing_warnings.get('report_timing_context', 'Unknown Context')
        story.append(Paragraph(f"<b>Report Type:</b> {report_context}", urgency_style))
        
        # Market session and urgency
        market_session = timing_warnings.get('market_session', 'unknown').replace('_', ' ').title()
        urgency_level = timing_warnings.get('urgency_level', 'unknown')
        story.append(Paragraph(f"<b>Market Session:</b> {market_session} | <b>Urgency Level:</b> {urgency_level}", urgency_style))
        
        # Report generation time
        market_time = timing_warnings.get('market_time', timestamp.strftime('%Y-%m-%d %H:%M:%S UTC'))
        story.append(Paragraph(f"<b>Generated:</b> {market_time}", data_freshness_style))
        
        # Next optimal trading time
        next_optimal = timing_warnings.get('next_optimal_trading_time', {})
        if next_optimal:
            story.append(Paragraph(f"<b>Next Optimal Trading:</b> {next_optimal.get('description', 'Unknown')}", data_freshness_style))
        
        story.append(Spacer(1, 12))
        
        # Timing warnings table
        warnings = timing_warnings.get('warnings', [])
        if warnings:
            story.append(Paragraph("⚠️ IMPORTANT TIMING CONSIDERATIONS", styles['Heading2']))
            
            warnings_data = [['Timing Warnings']]
            for warning in warnings:
                warnings_data.append([warning])
            
            warnings_table = Table(warnings_data, colWidths=[7*inch])
            warnings_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.orange),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]))
            story.append(warnings_table)
            story.append(Spacer(1, 12))
        
        # Action recommendations
        recommendations = timing_warnings.get('action_recommendations', [])
        if recommendations:
            story.append(Paragraph("💡 RECOMMENDED ACTIONS", styles['Heading2']))
            
            rec_data = [['Action Recommendations']]
            for rec in recommendations:
                rec_data.append([rec])
            
            rec_table = Table(rec_data, colWidths=[7*inch])
            rec_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.green),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.lightgreen),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]))
            story.append(rec_table)
            story.append(Spacer(1, 12))
        
        # Key Reminder Box
        story.append(Paragraph("🔔 CRITICAL REMINDER", styles['Heading2']))
        reminder_text = """
        <b>ALWAYS VERIFY CURRENT PRICES BEFORE EXECUTING TRADES</b><br/>
        This report is based on data available at the time of generation. 
        Market conditions, prices, and sentiment can change rapidly, especially during volatile periods.
        Double-check all information before making investment decisions.
        """
        story.append(Paragraph(reminder_text, urgency_style))
        story.append(Spacer(1, 20))
        
        # Regular portfolio analysis content
        story.append(Paragraph("📊 PORTFOLIO ANALYSIS DETAILS", styles['Heading1']))
        story.append(Spacer(1, 12))
        
        # Portfolio Summary with Enhanced Timing Context
        if portfolio_mode and analysis_results:
            total_value = sum(result.get('current_value', 0) for result in analysis_results.values())
            total_cost = sum(result.get('total_cost', 0) for result in analysis_results.values())
            total_profit_loss = total_value - total_cost
            total_profit_loss_percent = (total_profit_loss / total_cost * 100) if total_cost > 0 else 0
            
            summary_data = [
                ['Portfolio Summary', 'Value', 'Data Context'],
                ['Total Value', f"${total_value:.2f}", f"As of {market_time}"],
                ['Total Invested', f"${total_cost:.2f}", f"Report: {report_context}"],
                ['Total P&L', f"${total_profit_loss:+.2f}", f"Urgency: {urgency_level}"],
                ['Return %', f"{total_profit_loss_percent:+.2f}%", f"Session: {market_session}"],
                ['Positions', str(len(analysis_results)), f"Trading Window Status"]
            ]
            
            summary_table = Table(summary_data, colWidths=[2.5*inch, 2*inch, 2.5*inch])
            summary_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            story.append(summary_table)
            story.append(Spacer(1, 20))
            
        # Individual Stock Analysis with Enhanced Data Freshness
        if analysis_results:
            story.append(PageBreak())
            story.append(Paragraph("📈 INDIVIDUAL STOCK ANALYSIS", styles['Heading1']))
            story.append(Spacer(1, 12))
            
            for symbol, result in analysis_results.items():
                story.append(Paragraph(f"{symbol} - Detailed Analysis", styles['Heading2']))
                
                # Enhanced stock data table with timestamps
                current_price = result.get('current_price', 0)
                data_timestamp = result.get('data_timestamp')
                retrieval_timestamp = result.get('retrieval_timestamp')
                sentiment_retrieval = result.get('sentiment_retrieval_timestamp')
                news_age = result.get('news_age_minutes', 'unknown')
                
                # Format timestamps for display
                data_age = "unknown"
                retrieval_age = "unknown"
                sentiment_age = "unknown"
                
                try:
                    if data_timestamp:
                        data_age = _format_timestamp_for_pdf(data_timestamp)
                    if retrieval_timestamp:
                        retrieval_age = _format_timestamp_for_pdf(retrieval_timestamp)
                    if sentiment_retrieval:
                        sentiment_age = _format_timestamp_for_pdf(sentiment_retrieval)
                except:
                    pass
                
                # Trading window information for this stock
                stock_urgency = result.get('trading_window_urgency', 'unknown')
                action_window = result.get('action_window', 'unknown')
                data_confidence = result.get('data_confidence', 'unknown')
                
                stock_data = [
                    ['Metric', 'Value', 'Data Freshness'],
                    ['Current Price', f"${current_price:.2f}", f"Data from: {data_age}"],
                    ['RSI', f"{result.get('rsi', 0):.2f}", f"Retrieved: {retrieval_age}"],
                    ['20-day MA', f"${result.get('ma_20', 0):.2f}", f"News age: {_format_age_for_pdf(news_age)}"],
                    ['50-day MA', f"${result.get('ma_50', 0):.2f}", f"Sentiment: {sentiment_age}"],
                    ['News Sentiment', result.get('sentiment', 'neutral').title(), f"Articles: {result.get('articles_analyzed', 0)}"],
                    ['Trading Urgency', stock_urgency, f"Action Window: {action_window}"],
                    ['Data Confidence', data_confidence, f"Report Context: {report_context}"]
                ]
                
                if symbol in portfolio_holdings:
                    holding = portfolio_holdings[symbol]
                    stock_data.extend([
                        ['Holdings', f"{result.get('quantity', 0)} shares", f"Cost basis data"],
                        ['Cost Basis', f"${result.get('cost_basis', 0):.2f}", f"Portfolio tracking"],
                        ['Current Value', f"${result.get('current_value', 0):.2f}", f"Live calculation"],
                        ['P&L', f"${result.get('profit_loss', 0):+.2f}", f"Real-time P&L"],
                        ['Return %', f"{result.get('profit_loss_percent', 0):+.2f}%", f"Performance metric"]
                    ])
                
                stock_table = Table(stock_data, colWidths=[2*inch, 2.5*inch, 2.5*inch])
                
                # Enhanced table styling with urgency colors
                urgency_color = colors.lightgreen
                if stock_urgency == "IMMEDIATE":
                    urgency_color = colors.lightcoral
                elif stock_urgency == "HIGH":
                    urgency_color = colors.orange
                elif stock_urgency == "MEDIUM":
                    urgency_color = colors.yellow
                
                table_style = [
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (0, -1), 'LEFT'),  # Left align metrics
                    ('ALIGN', (1, 1), (-1, -1), 'LEFT'),  # Left align values
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    # Highlight urgency row
                    ('BACKGROUND', (0, 6), (-1, 6), urgency_color),
                    ('BACKGROUND', (0, 7), (-1, 7), colors.lightblue),
                ]
                
                stock_table.setStyle(TableStyle(table_style))
                story.append(stock_table)
                story.append(Spacer(1, 12))
                
                # AI Recommendation with timestamp
                recommendation = result.get('recommendation', 'No recommendation available')
                story.append(Paragraph("🤖 AI Recommendation", styles['Heading3']))
                story.append(Paragraph(recommendation, styles['Normal']))
                story.append(Spacer(1, 20))
                
                # Individual stock chart if requested
                if include_individual_charts:
                    chart = create_individual_stock_chart(symbol, get_stock_data(symbol), portfolio_holdings)
                    if chart:
                        chart.seek(0)
                        temp_chart_path = f"{report_output_dir}/temp_{symbol}_chart.png"
                        with open(temp_chart_path, 'wb') as f:
                            f.write(chart.read())
                        temp_files.append(temp_chart_path)  # Track for cleanup
                        
                        story.append(Paragraph(f"{symbol} Price Chart", styles['Heading3']))
                        story.append(Image(temp_chart_path, width=6*inch, height=3*inch))
                        story.append(Spacer(1, 20))
                
        # Final Trading Window Summary Page
        story.append(PageBreak())
        story.append(Paragraph("🎯 TRADING WINDOW SUMMARY", styles['Title']))
        story.append(Spacer(1, 20))
        
        # Comprehensive trading summary
        story.append(Paragraph("📊 Current Market Context", styles['Heading2']))
        
        context_data = [
            ['Market Information', 'Status'],
            ['Current Session', market_session],
            ['Report Type', report_context],
            ['Urgency Level', urgency_level],
            ['Generated At', market_time],
            ['Next Optimal Time', next_optimal.get('description', 'Unknown') if next_optimal else 'Unknown']
        ]
        
        context_table = Table(context_data, colWidths=[3.5*inch, 3.5*inch])
        context_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightblue),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        story.append(context_table)
        story.append(Spacer(1, 20))
        
        # Final disclaimer
        story.append(Paragraph("⚠️ IMPORTANT DISCLAIMER", styles['Heading2']))
        disclaimer_text = """
        <b>This report is for informational purposes only and should not be considered as financial advice.</b><br/><br/>
        
        <b>Data Freshness:</b> All data in this report reflects information available at the time of generation. 
        Market conditions can change rapidly, and prices may have moved since this analysis was conducted.<br/><br/>
        
        <b>Trading Windows:</b> The trading window recommendations are based on market hours and data freshness. 
        Always verify current market conditions and prices before executing any trades.<br/><br/>
        
        <b>Risk Warning:</b> Past performance does not guarantee future results. All investments carry risk, 
        and you may lose some or all of your invested capital. Consult with a qualified financial advisor 
        before making investment decisions.<br/><br/>
        
        <b>Generated:</b> {market_time} | <b>Market Session:</b> {market_session} | <b>Urgency:</b> {urgency_level}
        """.format(market_time=market_time, market_session=market_session, urgency_level=urgency_level)
        
        story.append(Paragraph(disclaimer_text, data_freshness_style))
        
        # Build PDF
        doc.build(story)
        print(f"📄 Enhanced PDF report generated: {filepath}")
        
        return filepath
        
    finally:
        # Clean up temporary files
        for temp_file in temp_files:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            except:
                pass  # Ignore cleanup errors

def _format_timestamp_for_pdf(timestamp):
    """Format timestamp for PDF display"""
    try:
        if hasattr(timestamp, 'strftime'):
            return timestamp.strftime('%H:%M:%S UTC')
        elif hasattr(timestamp, 'tz_localize'):
            # Handle pandas timestamp
            if timestamp.tz is None:
                timestamp = timestamp.tz_localize('UTC')
            else:
                timestamp = timestamp.tz_convert('UTC')
            return timestamp.strftime('%H:%M:%S UTC')
        else:
            return str(timestamp)
    except:
        return "timestamp unavailable"

def _format_age_for_pdf(age_minutes):
    """Format age for PDF display"""
    if age_minutes == "unknown" or age_minutes == "error" or age_minutes == "no_news":
        return str(age_minutes)
    
    try:
        age_minutes = int(age_minutes)
        if age_minutes < 1:
            return "just now"
        elif age_minutes < 60:
            return f"{age_minutes}m ago"
        elif age_minutes < 1440:  # Less than 24 hours
            hours = age_minutes // 60
            return f"{hours}h ago"
        else:
            days = age_minutes // 1440
            return f"{days}d ago"
    except:
        return str(age_minutes) 
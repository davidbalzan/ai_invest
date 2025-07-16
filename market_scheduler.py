import schedule
import time
import pytz
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Callable, Optional
import requests
import json
from dataclasses import dataclass

class MarketSession(Enum):
    """Different market sessions"""
    PRE_MARKET = "pre_market"
    MARKET_OPEN = "market_open"
    MARKET_CLOSE = "market_close"
    POST_MARKET = "post_market"
    MARKET_CLOSED = "market_closed"
    WEEKEND = "weekend"

class AnalysisType(Enum):
    """Types of analysis for different timings"""
    MORNING_PREP = "morning_prep"          # Before market opens
    OPENING_ANALYSIS = "opening_analysis"   # Market open + 30 min
    MIDDAY_CHECK = "midday_check"          # Midday analysis
    CLOSING_ANALYSIS = "closing_analysis"   # Market close + 30 min
    EVENING_SUMMARY = "evening_summary"     # End of day comprehensive
    WEEKEND_DEEP_DIVE = "weekend_deep_dive" # Weekend comprehensive analysis

@dataclass
class MarketHours:
    """Market hours configuration"""
    timezone: str
    pre_market_start: str  # "04:00"
    market_open: str       # "09:30"
    market_close: str      # "16:00"
    post_market_end: str   # "20:00"

@dataclass
class ScheduledTask:
    """Represents a scheduled analysis task"""
    task_id: str
    analysis_type: AnalysisType
    time: str
    frequency: str  # "daily", "weekdays", "monday", etc.
    market_session: MarketSession
    enabled: bool = True
    description: str = ""

class MarketScheduler:
    """Strategic scheduler aligned with market hours and optimal analysis times"""
    
    def __init__(self):
        # Default to US Eastern Time (NYSE/NASDAQ)
        self.market_hours = MarketHours(
            timezone="America/New_York",
            pre_market_start="04:00",
            market_open="09:30", 
            market_close="16:00",
            post_market_end="20:00"
        )
        
        self.scheduled_tasks: List[ScheduledTask] = []
        self.analysis_callback: Optional[Callable] = None
        self.market_holidays: List[datetime] = []
        
        # Load market holidays for current year
        self._load_market_holidays()
        
    def _load_market_holidays(self):
        """Load market holidays (can be extended to fetch from API)"""
        # 2024/2025 US Market Holidays
        current_year = datetime.now().year
        holidays_data = {
            2024: [
                "2024-01-01",  # New Year's Day
                "2024-01-15",  # Martin Luther King Jr. Day  
                "2024-02-19",  # Presidents Day
                "2024-03-29",  # Good Friday
                "2024-05-27",  # Memorial Day
                "2024-06-19",  # Juneteenth
                "2024-07-04",  # Independence Day
                "2024-09-02",  # Labor Day
                "2024-11-28",  # Thanksgiving
                "2024-12-25",  # Christmas
            ],
            2025: [
                "2025-01-01",  # New Year's Day
                "2025-01-20",  # Martin Luther King Jr. Day
                "2025-02-17",  # Presidents Day
                "2025-04-18",  # Good Friday
                "2025-05-26",  # Memorial Day
                "2025-06-19",  # Juneteenth
                "2025-07-04",  # Independence Day
                "2025-09-01",  # Labor Day
                "2025-11-27",  # Thanksgiving
                "2025-12-25",  # Christmas
            ]
        }
        
        try:
            year_holidays = holidays_data.get(current_year, [])
            self.market_holidays = [datetime.strptime(date, "%Y-%m-%d").date() 
                                  for date in year_holidays]
        except Exception as e:
            print(f"Warning: Could not load market holidays: {e}")
            self.market_holidays = []
    
    def get_market_session(self, dt: datetime = None) -> MarketSession:
        """Determine current market session"""
        if dt is None:
            dt = datetime.now()
            
        # Convert to market timezone
        market_tz = pytz.timezone(self.market_hours.timezone)
        if dt.tzinfo is None:
            dt = pytz.utc.localize(dt)
        market_time = dt.astimezone(market_tz)
        
        # Check if it's weekend
        if market_time.weekday() >= 5:  # Saturday = 5, Sunday = 6
            return MarketSession.WEEKEND
            
        # Check if it's a market holiday
        if market_time.date() in self.market_holidays:
            return MarketSession.MARKET_CLOSED
            
        # Get current time components
        current_time = market_time.time()
        pre_start = datetime.strptime(self.market_hours.pre_market_start, "%H:%M").time()
        market_open = datetime.strptime(self.market_hours.market_open, "%H:%M").time()
        market_close = datetime.strptime(self.market_hours.market_close, "%H:%M").time()
        post_end = datetime.strptime(self.market_hours.post_market_end, "%H:%M").time()
        
        # Determine session
        if current_time < pre_start:
            return MarketSession.MARKET_CLOSED
        elif pre_start <= current_time < market_open:
            return MarketSession.PRE_MARKET
        elif market_open <= current_time < market_close:
            return MarketSession.MARKET_OPEN
        elif market_close <= current_time <= post_end:
            return MarketSession.POST_MARKET
        else:
            return MarketSession.MARKET_CLOSED
    
    def is_market_day(self, dt: datetime = None) -> bool:
        """Check if given date is a trading day"""
        if dt is None:
            dt = datetime.now()
            
        # Weekend check
        if dt.weekday() >= 5:
            return False
            
        # Holiday check
        if dt.date() in self.market_holidays:
            return False
            
        return True
    
    def get_next_market_day(self, dt: datetime = None) -> datetime:
        """Get the next trading day"""
        if dt is None:
            dt = datetime.now()
            
        next_day = dt + timedelta(days=1)
        while not self.is_market_day(next_day):
            next_day += timedelta(days=1)
            
        return next_day
    
    def get_strategic_analysis_times(self) -> Dict[AnalysisType, str]:
        """Get recommended analysis times for different strategies"""
        return {
            AnalysisType.MORNING_PREP: "08:00",        # 1.5h before market opens
            AnalysisType.OPENING_ANALYSIS: "10:00",    # 30min after market opens
            AnalysisType.MIDDAY_CHECK: "13:00",        # Lunch time analysis
            AnalysisType.CLOSING_ANALYSIS: "16:30",    # 30min after market closes
            AnalysisType.EVENING_SUMMARY: "18:00",     # End of day comprehensive
            AnalysisType.WEEKEND_DEEP_DIVE: "10:00"    # Weekend morning analysis
        }
    
    def create_strategic_schedule(self, strategy_type: str = "balanced") -> List[ScheduledTask]:
        """Create a strategic schedule based on investment approach"""
        strategic_times = self.get_strategic_analysis_times()
        
        if strategy_type == "aggressive":
            # High-frequency monitoring for active trading
            tasks = [
                ScheduledTask("morning_prep", AnalysisType.MORNING_PREP, 
                            strategic_times[AnalysisType.MORNING_PREP], "weekdays",
                            MarketSession.PRE_MARKET, True,
                            "Pre-market analysis and preparation"),
                ScheduledTask("opening_analysis", AnalysisType.OPENING_ANALYSIS,
                            strategic_times[AnalysisType.OPENING_ANALYSIS], "weekdays", 
                            MarketSession.MARKET_OPEN, True,
                            "Market opening momentum analysis"),
                ScheduledTask("midday_check", AnalysisType.MIDDAY_CHECK,
                            strategic_times[AnalysisType.MIDDAY_CHECK], "weekdays",
                            MarketSession.MARKET_OPEN, True,
                            "Midday trend confirmation"),
                ScheduledTask("closing_analysis", AnalysisType.CLOSING_ANALYSIS,
                            strategic_times[AnalysisType.CLOSING_ANALYSIS], "weekdays",
                            MarketSession.POST_MARKET, True,
                            "Post-market analysis and next day prep"),
                ScheduledTask("weekend_deep_dive", AnalysisType.WEEKEND_DEEP_DIVE,
                            strategic_times[AnalysisType.WEEKEND_DEEP_DIVE], "saturday",
                            MarketSession.WEEKEND, True,
                            "Comprehensive weekend analysis")
            ]
            
        elif strategy_type == "conservative":
            # Minimal monitoring for long-term holding
            tasks = [
                ScheduledTask("evening_summary", AnalysisType.EVENING_SUMMARY,
                            strategic_times[AnalysisType.EVENING_SUMMARY], "weekdays",
                            MarketSession.POST_MARKET, True,
                            "Daily end-of-day summary"),
                ScheduledTask("weekend_deep_dive", AnalysisType.WEEKEND_DEEP_DIVE,
                            strategic_times[AnalysisType.WEEKEND_DEEP_DIVE], "sunday",
                            MarketSession.WEEKEND, True,
                            "Weekly comprehensive review")
            ]
            
        else:  # balanced (default)
            # Moderate monitoring with key timing
            tasks = [
                ScheduledTask("morning_prep", AnalysisType.MORNING_PREP,
                            strategic_times[AnalysisType.MORNING_PREP], "weekdays",
                            MarketSession.PRE_MARKET, True,
                            "Morning market preparation"),
                ScheduledTask("closing_analysis", AnalysisType.CLOSING_ANALYSIS,
                            strategic_times[AnalysisType.CLOSING_ANALYSIS], "weekdays",
                            MarketSession.POST_MARKET, True,
                            "End-of-day analysis"),
                ScheduledTask("weekend_deep_dive", AnalysisType.WEEKEND_DEEP_DIVE,
                            strategic_times[AnalysisType.WEEKEND_DEEP_DIVE], "saturday",
                            MarketSession.WEEKEND, True,
                            "Weekend portfolio review")
            ]
        
        return tasks
    
    def set_analysis_callback(self, callback: Callable):
        """Set the analysis function to be called"""
        self.analysis_callback = callback
    
    def add_custom_task(self, task: ScheduledTask):
        """Add a custom scheduled task"""
        self.scheduled_tasks.append(task)
        
    def remove_task(self, task_id: str):
        """Remove a scheduled task"""
        self.scheduled_tasks = [task for task in self.scheduled_tasks if task.task_id != task_id]
    
    def setup_schedule(self, tasks: List[ScheduledTask] = None):
        """Setup the schedule with given tasks"""
        if tasks is None:
            tasks = self.scheduled_tasks
            
        # Clear existing schedule
        schedule.clear()
        
        for task in tasks:
            if not task.enabled:
                continue
                
            # Create wrapped function that includes task context
            def create_task_wrapper(analysis_type: AnalysisType, market_session: MarketSession):
                def task_wrapper():
                    if not self.analysis_callback:
                        print(f"⚠️ No analysis callback set for {analysis_type.value}")
                        return
                        
                    # Check if market is open/closed as expected
                    current_session = self.get_market_session()
                    
                    print(f"🕐 Running {analysis_type.value} analysis...")
                    print(f"📊 Current market session: {current_session.value}")
                    print(f"🎯 Expected session: {market_session.value}")
                    
                    # Skip if not a market day and task expects market session
                    if (market_session in [MarketSession.PRE_MARKET, MarketSession.MARKET_OPEN, 
                                         MarketSession.POST_MARKET] and 
                        not self.is_market_day()):
                        print(f"⏭️ Skipping {analysis_type.value} - Market closed today")
                        return
                    
                    try:
                        # Call the analysis function with context
                        self.analysis_callback(analysis_type, current_session)
                    except Exception as e:
                        print(f"❌ Error in {analysis_type.value} analysis: {e}")
                        
                return task_wrapper
            
            # Schedule based on frequency
            job_func = create_task_wrapper(task.analysis_type, task.market_session)
            
            if task.frequency == "daily":
                schedule.every().day.at(task.time).do(job_func)
            elif task.frequency == "weekdays":
                schedule.every().monday.at(task.time).do(job_func)
                schedule.every().tuesday.at(task.time).do(job_func) 
                schedule.every().wednesday.at(task.time).do(job_func)
                schedule.every().thursday.at(task.time).do(job_func)
                schedule.every().friday.at(task.time).do(job_func)
            elif task.frequency == "monday":
                schedule.every().monday.at(task.time).do(job_func)
            elif task.frequency == "tuesday":
                schedule.every().tuesday.at(task.time).do(job_func)
            elif task.frequency == "wednesday":
                schedule.every().wednesday.at(task.time).do(job_func)
            elif task.frequency == "thursday":
                schedule.every().thursday.at(task.time).do(job_func)
            elif task.frequency == "friday":
                schedule.every().friday.at(task.time).do(job_func)
            elif task.frequency == "saturday":
                schedule.every().saturday.at(task.time).do(job_func)
            elif task.frequency == "sunday":
                schedule.every().sunday.at(task.time).do(job_func)
            elif task.frequency == "weekly":
                schedule.every().week.at(task.time).do(job_func)
                
        print(f"📅 Schedule configured with {len([t for t in tasks if t.enabled])} active tasks")
    
    def run_scheduler(self):
        """Run the scheduler (blocking)"""
        print("🚀 Market-aware scheduler starting...")
        print(f"🌍 Market timezone: {self.market_hours.timezone}")
        print(f"⏰ Market hours: {self.market_hours.market_open} - {self.market_hours.market_close}")
        
        # Show current market status
        current_session = self.get_market_session()
        is_trading_day = self.is_market_day()
        
        print(f"📊 Current market session: {current_session.value}")
        print(f"📈 Trading day: {'Yes' if is_trading_day else 'No'}")
        
        if self.market_holidays:
            next_holiday = next((h for h in self.market_holidays if h > datetime.now().date()), None)
            if next_holiday:
                print(f"🏖️ Next market holiday: {next_holiday}")
        
        print("\n🔄 Scheduled tasks:")
        for task in self.scheduled_tasks:
            status = "✅" if task.enabled else "❌"
            print(f"  {status} {task.task_id}: {task.time} ({task.frequency}) - {task.description}")
        
        print("\n⏳ Scheduler running... Press Ctrl+C to stop")
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(30)  # Check every 30 seconds
        except KeyboardInterrupt:
            print("\n👋 Scheduler stopped")
    
    def run_immediate_analysis(self, analysis_type: AnalysisType = None):
        """Run analysis immediately based on current market session"""
        if not self.analysis_callback:
            print("❌ No analysis callback set")
            return
            
        current_session = self.get_market_session()
        
        if analysis_type is None:
            # Auto-determine analysis type based on current market session
            if current_session == MarketSession.PRE_MARKET:
                analysis_type = AnalysisType.MORNING_PREP
            elif current_session == MarketSession.MARKET_OPEN:
                # Determine if closer to open or close
                market_tz = pytz.timezone(self.market_hours.timezone)
                now = datetime.now(market_tz).time()
                market_open = datetime.strptime(self.market_hours.market_open, "%H:%M").time()
                market_close = datetime.strptime(self.market_hours.market_close, "%H:%M").time()
                
                # Calculate minutes from open and to close
                now_minutes = now.hour * 60 + now.minute
                open_minutes = market_open.hour * 60 + market_open.minute
                close_minutes = market_close.hour * 60 + market_close.minute
                
                if (now_minutes - open_minutes) < (close_minutes - now_minutes):
                    analysis_type = AnalysisType.OPENING_ANALYSIS
                else:
                    analysis_type = AnalysisType.MIDDAY_CHECK
            elif current_session == MarketSession.POST_MARKET:
                analysis_type = AnalysisType.CLOSING_ANALYSIS
            elif current_session == MarketSession.WEEKEND:
                analysis_type = AnalysisType.WEEKEND_DEEP_DIVE
            else:
                analysis_type = AnalysisType.EVENING_SUMMARY
        
        print(f"🚀 Running immediate {analysis_type.value} analysis...")
        print(f"📊 Market session: {current_session.value}")
        
        try:
            self.analysis_callback(analysis_type, current_session)
        except Exception as e:
            print(f"❌ Error in immediate analysis: {e}")
    
    def get_next_scheduled_runs(self, limit: int = 5) -> List[Dict]:
        """Get the next scheduled analysis runs"""
        jobs = schedule.get_jobs()
        next_runs = []
        
        for job in jobs[:limit]:
            next_run = schedule.next_run()
            if next_run:
                next_runs.append({
                    'time': next_run.strftime('%Y-%m-%d %H:%M:%S'),
                    'job_func': str(job.job_func),
                    'interval': str(job.interval)
                })
        
        return next_runs
    
    def get_market_status_summary(self) -> Dict:
        """Get comprehensive market status information"""
        current_session = self.get_market_session()
        is_trading_day = self.is_market_day()
        
        # Calculate time to next market event
        market_tz = pytz.timezone(self.market_hours.timezone)
        now = datetime.now(market_tz)
        
        next_event = None
        next_event_time = None
        
        if current_session == MarketSession.MARKET_CLOSED and is_trading_day:
            # Next event is pre-market
            pre_market_time = now.replace(
                hour=int(self.market_hours.pre_market_start.split(':')[0]),
                minute=int(self.market_hours.pre_market_start.split(':')[1]),
                second=0, microsecond=0
            )
            if pre_market_time <= now:
                pre_market_time += timedelta(days=1)
            next_event = "Pre-market opens"
            next_event_time = pre_market_time
            
        elif current_session == MarketSession.PRE_MARKET:
            # Next event is market open
            market_open_time = now.replace(
                hour=int(self.market_hours.market_open.split(':')[0]),
                minute=int(self.market_hours.market_open.split(':')[1]),
                second=0, microsecond=0
            )
            next_event = "Market opens"
            next_event_time = market_open_time
            
        elif current_session == MarketSession.MARKET_OPEN:
            # Next event is market close
            market_close_time = now.replace(
                hour=int(self.market_hours.market_close.split(':')[0]),
                minute=int(self.market_hours.market_close.split(':')[1]),
                second=0, microsecond=0
            )
            next_event = "Market closes"
            next_event_time = market_close_time
            
        elif current_session == MarketSession.POST_MARKET:
            # Next event is post-market close
            post_close_time = now.replace(
                hour=int(self.market_hours.post_market_end.split(':')[0]),
                minute=int(self.market_hours.post_market_end.split(':')[1]),
                second=0, microsecond=0
            )
            next_event = "Post-market closes"
            next_event_time = post_close_time
        
        # Calculate next trading day if weekend/holiday
        if not is_trading_day:
            next_trading_day = self.get_next_market_day(now)
            next_event = "Next trading day"
            next_event_time = next_trading_day.replace(
                hour=int(self.market_hours.pre_market_start.split(':')[0]),
                minute=int(self.market_hours.pre_market_start.split(':')[1]),
                second=0, microsecond=0
            )
        
        time_to_next = None
        if next_event_time:
            time_diff = next_event_time - now
            hours, remainder = divmod(time_diff.total_seconds(), 3600)
            minutes, _ = divmod(remainder, 60)
            time_to_next = f"{int(hours)}h {int(minutes)}m"
        
        return {
            'current_session': current_session.value,
            'is_trading_day': is_trading_day,
            'market_timezone': self.market_hours.timezone,
            'current_time': now.strftime('%Y-%m-%d %H:%M:%S %Z'),
            'next_event': next_event,
            'time_to_next_event': time_to_next,
            'market_hours': {
                'pre_market': f"{self.market_hours.pre_market_start} - {self.market_hours.market_open}",
                'regular': f"{self.market_hours.market_open} - {self.market_hours.market_close}",
                'post_market': f"{self.market_hours.market_close} - {self.market_hours.post_market_end}"
            }
        } 

    def get_market_timing_warnings(self, analysis_timestamp: datetime = None) -> Dict:
        """Generate market timing warnings for reports"""
        if analysis_timestamp is None:
            analysis_timestamp = datetime.now(pytz.utc)
        
        # Convert to market timezone
        market_tz = pytz.timezone(self.market_hours.timezone)
        if analysis_timestamp.tzinfo is None:
            analysis_timestamp = pytz.utc.localize(analysis_timestamp)
        market_time = analysis_timestamp.astimezone(market_tz)
        
        current_session = self.get_market_session(analysis_timestamp)
        is_trading_day = self.is_market_day(analysis_timestamp)
        
        warnings = []
        report_timing_context = ""
        action_recommendations = []
        
        # Generate warnings based on when report was generated
        if current_session == MarketSession.MARKET_CLOSED and is_trading_day:
            warnings.append("⚠️ REPORT GENERATED BEFORE MARKET OPEN")
            warnings.append("• Stock prices reflect previous trading session")
            warnings.append("• Pre-market activity may have moved prices")
            report_timing_context = "Pre-market Report"
            action_recommendations.append("🔍 Check pre-market prices before acting")
            action_recommendations.append("⏰ Wait for market open for better liquidity")
            
        elif current_session == MarketSession.PRE_MARKET:
            warnings.append("ℹ️ REPORT GENERATED DURING PRE-MARKET")
            warnings.append("• Limited trading volume and liquidity")
            warnings.append("• Prices may gap at market open")
            report_timing_context = "Pre-market Report"
            action_recommendations.append("⚡ Pre-market trading available but risky")
            action_recommendations.append("💡 Consider waiting for market open")
            
        elif current_session == MarketSession.MARKET_OPEN:
            warnings.append("✅ REPORT GENERATED DURING MARKET HOURS")
            warnings.append("• Real-time pricing and full liquidity available")
            warnings.append("• Optimal time for trading execution")
            report_timing_context = "Live Market Report"
            action_recommendations.append("🚀 Optimal trading window - act quickly if needed")
            action_recommendations.append("📊 Monitor for intraday price movements")
            
        elif current_session == MarketSession.POST_MARKET:
            warnings.append("ℹ️ REPORT GENERATED DURING POST-MARKET")
            warnings.append("• Extended hours trading available")
            warnings.append("• Lower volume than regular hours")
            report_timing_context = "Post-market Report"
            action_recommendations.append("🌆 Extended hours trading available")
            action_recommendations.append("⏳ Consider waiting for next trading day")
            
        elif current_session == MarketSession.WEEKEND:
            warnings.append("🏖️ REPORT GENERATED DURING WEEKEND")
            warnings.append("• Markets are closed until next trading day")
            warnings.append("• Time to plan and research trades")
            report_timing_context = "Weekend Report"
            action_recommendations.append("📚 Use time for research and planning")
            action_recommendations.append("📅 Prepare for Monday market open")
            
        elif not is_trading_day:
            warnings.append("🏪 REPORT GENERATED ON MARKET HOLIDAY")
            warnings.append("• Markets are closed today")
            warnings.append("• Next trading day may show gaps")
            report_timing_context = "Holiday Report"
            action_recommendations.append("📅 Plan for next trading day")
            action_recommendations.append("🔍 Monitor overnight news and futures")
        
        else:
            warnings.append("🌙 REPORT GENERATED AFTER MARKET CLOSE")
            warnings.append("• Markets are closed for the day")
            warnings.append("• Overnight news may impact next session")
            report_timing_context = "After-hours Report"
            action_recommendations.append("📰 Monitor overnight news and earnings")
            action_recommendations.append("⏰ Plan for next trading session")
        
        # Add data freshness warnings
        time_since_market_close = self._calculate_time_since_last_market_close(analysis_timestamp)
        if time_since_market_close:
            hours_since_close = time_since_market_close.total_seconds() / 3600
            if hours_since_close > 72:  # More than 3 days
                warnings.append(f"⚠️ Last market close was {int(hours_since_close//24)} days ago")
                warnings.append("• Stock prices may be significantly stale")
                action_recommendations.append("🔍 Verify current market conditions before trading")
            elif hours_since_close > 24:  # More than 1 day
                warnings.append(f"ℹ️ Last market close was {int(hours_since_close)} hours ago")
                warnings.append("• Check for weekend/overnight news impact")
        
        # Calculate next optimal trading window
        next_optimal_time = self._get_next_optimal_trading_time(analysis_timestamp)
        
        return {
            'warnings': warnings,
            'report_timing_context': report_timing_context,
            'action_recommendations': action_recommendations,
            'market_session': current_session.value,
            'is_trading_day': is_trading_day,
            'analysis_timestamp': analysis_timestamp.isoformat(),
            'market_time': market_time.strftime('%Y-%m-%d %H:%M:%S %Z'),
            'next_optimal_trading_time': next_optimal_time,
            'urgency_level': self._assess_timing_urgency(current_session, is_trading_day)
        }
    
    def _calculate_time_since_last_market_close(self, current_time: datetime) -> timedelta:
        """Calculate time since last market close"""
        try:
            market_tz = pytz.timezone(self.market_hours.timezone)
            if current_time.tzinfo is None:
                current_time = pytz.utc.localize(current_time)
            market_time = current_time.astimezone(market_tz)
            
            # Find the last market close
            search_date = market_time.date()
            for days_back in range(7):  # Look back up to a week
                check_date = search_date - timedelta(days=days_back)
                if self.is_market_day(datetime.combine(check_date, market_time.time()).replace(tzinfo=market_tz)):
                    last_close = datetime.combine(
                        check_date,
                        datetime.strptime(self.market_hours.market_close, "%H:%M").time()
                    ).replace(tzinfo=market_tz)
                    if last_close < market_time:
                        return market_time - last_close
            
            return None
        except:
            return None
    
    def _get_next_optimal_trading_time(self, current_time: datetime) -> Dict:
        """Get the next optimal trading time"""
        try:
            market_tz = pytz.timezone(self.market_hours.timezone)
            if current_time.tzinfo is None:
                current_time = pytz.utc.localize(current_time)
            market_time = current_time.astimezone(market_tz)
            
            current_session = self.get_market_session(current_time)
            
            if current_session == MarketSession.MARKET_OPEN:
                return {
                    'time': 'NOW',
                    'description': 'Market is currently open',
                    'urgency': 'immediate'
                }
            
            # Find next market open
            next_market_day = self.get_next_market_day(current_time)
            next_open = datetime.combine(
                next_market_day.date(),
                datetime.strptime(self.market_hours.market_open, "%H:%M").time()
            ).replace(tzinfo=market_tz)
            
            time_to_open = next_open - market_time
            hours_to_open = time_to_open.total_seconds() / 3600
            
            return {
                'time': next_open.strftime('%Y-%m-%d %H:%M %Z'),
                'description': f"Next market open in {int(hours_to_open)}h {int((time_to_open.total_seconds() % 3600) / 60)}m",
                'urgency': 'planned'
            }
        except:
            return {
                'time': 'Unknown',
                'description': 'Unable to calculate next trading time',
                'urgency': 'unknown'
            }
    
    def _assess_timing_urgency(self, session: MarketSession, is_trading_day: bool) -> str:
        """Assess urgency level based on market timing"""
        if session == MarketSession.MARKET_OPEN:
            return "HIGH"
        elif session in [MarketSession.PRE_MARKET, MarketSession.POST_MARKET]:
            return "MEDIUM"
        elif session == MarketSession.MARKET_CLOSED and is_trading_day:
            return "MEDIUM"
        else:
            return "LOW" 
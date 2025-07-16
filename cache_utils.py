#!/usr/bin/env python3
"""
Cache Management Utility for AI Investment Tool
Provides commands to manage, inspect, and optimize the caching system
"""

import argparse
import sys
import os
from datetime import datetime, timezone
from cache_manager import CacheManager

def show_cache_stats():
    """Display comprehensive cache statistics"""
    cache_manager = CacheManager()
    stats = cache_manager.get_cache_stats()
    
    print("=" * 60)
    print("🗂️  AI INVESTMENT TOOL - CACHE STATISTICS")
    print("=" * 60)
    print(f"📊 Current Market Session: {stats['current_market_session'].replace('_', ' ').title()}")
    print(f"💾 Total Cache Entries: {stats['total_entries']}")
    print(f"📦 Total Cache Size: {stats['total_size_mb']:.2f} MB")
    print(f"⏰ Expired Entries: {stats['expired_entries']}")
    
    print("\n📂 Cache by Data Type:")
    print("-" * 40)
    for data_type, type_stats in stats['by_type'].items():
        status = "🟢" if type_stats['expired'] == 0 else "🟡" if type_stats['expired'] < type_stats['count'] else "🔴"
        print(f"{status} {data_type.replace('_', ' ').title():<20} {type_stats['count']:>3} entries ({type_stats['size_mb']:>6.2f} MB) - {type_stats['expired']} expired")
    
    if stats['expired_entries'] > 0:
        print(f"\n💡 Run 'python cache_utils.py clean' to remove {stats['expired_entries']} expired entries")
    
    print("=" * 60)

def clean_expired_cache():
    """Remove expired cache entries"""
    cache_manager = CacheManager()
    
    print("🧹 Cleaning expired cache entries...")
    removed_count = cache_manager.cleanup_expired_cache()
    
    if removed_count > 0:
        print(f"✅ Removed {removed_count} expired cache entries")
        # Show updated stats
        stats = cache_manager.get_cache_stats()
        print(f"💾 Cache now has {stats['total_entries']} entries ({stats['total_size_mb']:.2f} MB)")
    else:
        print("✨ No expired cache entries found")

def clear_all_cache():
    """Clear all cache entries"""
    cache_manager = CacheManager()
    
    print("🗑️  Clearing all cache entries...")
    removed_count = cache_manager.invalidate_cache()
    
    if removed_count > 0:
        print(f"✅ Cleared {removed_count} cache entries")
        print("💾 Cache is now empty")
    else:
        print("✨ Cache was already empty")

def clear_cache_by_type(data_type):
    """Clear cache entries for a specific data type"""
    cache_manager = CacheManager()
    
    valid_types = ['stock_data', 'sentiment_data', 'ai_recommendations', 'technical_indicators']
    if data_type not in valid_types:
        print(f"❌ Invalid data type. Valid types: {', '.join(valid_types)}")
        return
    
    print(f"🗑️  Clearing {data_type} cache entries...")
    removed_count = cache_manager.invalidate_cache(data_type=data_type)
    
    if removed_count > 0:
        print(f"✅ Cleared {removed_count} {data_type} cache entries")
    else:
        print(f"✨ No {data_type} cache entries found")

def force_refresh_symbol(symbol, data_types=None):
    """Force refresh cache for a specific symbol"""
    cache_manager = CacheManager()
    
    if data_types is None:
        data_types = ['stock_data', 'sentiment_data', 'ai_recommendations', 'technical_indicators']
    
    print(f"🔄 Marking {symbol} for force refresh...")
    
    for data_type in data_types:
        cache_manager.force_refresh_next_call(data_type, symbol)
        print(f"   ✓ {data_type} will be refreshed on next analysis")
    
    print(f"✅ {symbol} marked for refresh. Run analysis to fetch fresh data.")

def show_cache_policies():
    """Display current cache policies"""
    cache_manager = CacheManager()
    
    print("=" * 60)
    print("⚙️  CACHE EXPIRATION POLICIES")
    print("=" * 60)
    
    session_names = {
        'market_hours': '📈 Market Hours (9:30 AM - 4:00 PM ET)',
        'pre_post_market': '🕐 Pre/Post Market (4:00-9:30 AM, 4:00-8:00 PM ET)',
        'market_closed': '🌙 Market Closed (8:00 PM - 4:00 AM ET)',
        'weekend': '🏖️  Weekend',
        'holiday': '🎉 Holiday'
    }
    
    for data_type, policies in cache_manager.cache_policies.items():
        print(f"\n🗂️  {data_type.replace('_', ' ').title()}:")
        for session, minutes in policies.items():
            hours = minutes / 60
            if hours < 1:
                time_str = f"{minutes} minutes"
            elif hours == 24:
                time_str = "24 hours"
            elif hours >= 24:
                days = hours / 24
                time_str = f"{days:.0f} days"
            else:
                time_str = f"{hours:.1f} hours"
            
            print(f"   {session_names.get(session, session)}: {time_str}")
    
    print("\n💡 These policies can be customized in your .env file")
    print("=" * 60)

def optimize_cache():
    """Run cache optimization - cleanup and show recommendations"""
    cache_manager = CacheManager()
    
    print("🔧 Running cache optimization...")
    
    # Clean up expired entries
    removed_count = cache_manager.cleanup_expired_cache()
    if removed_count > 0:
        print(f"✅ Removed {removed_count} expired entries")
    
    # Get updated stats
    stats = cache_manager.get_cache_stats()
    
    print(f"💾 Cache optimized: {stats['total_entries']} entries ({stats['total_size_mb']:.2f} MB)")
    
    # Provide recommendations
    if stats['total_size_mb'] > 10:
        print("💡 Cache is large (>10MB). Consider periodic cleanup.")
    
    if stats['total_entries'] > 100:
        print("💡 Cache has many entries (>100). This is normal for active trading days.")
    
    print("✨ Cache optimization complete")

def main():
    parser = argparse.ArgumentParser(description="AI Investment Tool - Cache Management Utility")
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Stats command
    subparsers.add_parser('stats', help='Show cache statistics')
    
    # Clean command
    subparsers.add_parser('clean', help='Remove expired cache entries')
    
    # Clear commands
    clear_parser = subparsers.add_parser('clear', help='Clear cache entries')
    clear_parser.add_argument('--type', choices=['stock_data', 'sentiment_data', 'ai_recommendations', 'technical_indicators'], 
                            help='Clear specific data type (default: all)')
    
    # Force refresh command
    refresh_parser = subparsers.add_parser('refresh', help='Force refresh cache for a symbol')
    refresh_parser.add_argument('symbol', help='Stock symbol to refresh (e.g., AAPL)')
    refresh_parser.add_argument('--types', nargs='+', 
                              choices=['stock_data', 'sentiment_data', 'ai_recommendations', 'technical_indicators'],
                              help='Data types to refresh (default: all)')
    
    # Policies command
    subparsers.add_parser('policies', help='Show cache expiration policies')
    
    # Optimize command
    subparsers.add_parser('optimize', help='Run cache optimization')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        if args.command == 'stats':
            show_cache_stats()
        elif args.command == 'clean':
            clean_expired_cache()
        elif args.command == 'clear':
            if args.type:
                clear_cache_by_type(args.type)
            else:
                clear_all_cache()
        elif args.command == 'refresh':
            force_refresh_symbol(args.symbol, args.types)
        elif args.command == 'policies':
            show_cache_policies()
        elif args.command == 'optimize':
            optimize_cache()
    
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 
#!/usr/bin/env python3
"""
Import portfolio data from .env file into the database
"""
import os
import sys
from dotenv import load_dotenv
from decimal import Decimal
from uuid import UUID

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from app.models import User, Portfolio, Holding
from app.services.database_service import DatabaseService

def parse_portfolio_holdings(holdings_str: str):
    """Parse portfolio holdings from environment variable"""
    holdings = {}
    
    if holdings_str:
        for holding in holdings_str.split(','):
            parts = holding.strip().split(':')
            if len(parts) == 3:
                symbol, quantity, cost_basis = parts
                holdings[symbol.strip().upper()] = {
                    'quantity': float(quantity),
                    'cost_basis': float(cost_basis)
                }
    
    return holdings

def import_portfolio_from_env():
    """Import portfolio data from .env file"""
    # Load environment variables
    load_dotenv()
    
    # Get portfolio data from env
    holdings_str = os.getenv('PORTFOLIO_HOLDINGS', '')
    if not holdings_str:
        print("❌ No PORTFOLIO_HOLDINGS found in .env file")
        return False
    
    # Parse holdings
    holdings = parse_portfolio_holdings(holdings_str)
    if not holdings:
        print("❌ Failed to parse portfolio holdings")
        return False
    
    print(f"🔍 Found {len(holdings)} holdings in .env:")
    for symbol, data in holdings.items():
        print(f"   {symbol}: {data['quantity']} shares @ ${data['cost_basis']:.2f}")
    
    # Connect to database
    db = SessionLocal()
    db_service = DatabaseService(db)
    
    try:
        # Check if default user exists
        default_user_id = UUID("a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11")
        user = db_service.get_user(default_user_id)
        
        if not user:
            print("❌ Default user not found. Creating user...")
            # Create default user
            from app.schemas import UserCreate
            user_data = UserCreate(
                username="investor",
                email="investor@example.com",
                first_name="Portfolio",
                last_name="Investor",
                timezone="America/New_York"
            )
            user = db_service.create_user(user_data, "hashed_password_placeholder")
            print(f"✅ Created user: {user.username}")
        else:
            print(f"✅ Found existing user: {user.username}")
        
        # Check if portfolio already exists
        portfolios = db_service.get_user_portfolios(user.id)
        portfolio = None
        
        if portfolios:
            portfolio = portfolios[0]
            print(f"✅ Found existing portfolio: {portfolio.name}")
            
            # Ask user if they want to update or create new
            response = input("Portfolio exists. (U)pdate existing or (C)reate new? [U/C]: ").upper()
            if response == 'C':
                portfolio = None
        
        if not portfolio:
            # Create new portfolio
            from app.schemas import PortfolioCreate
            portfolio_data = PortfolioCreate(
                name="Main Investment Portfolio",
                description="Imported from .env configuration",
                cash_balance=Decimal('10000.00')  # Default cash balance
            )
            portfolio = db_service.create_portfolio(portfolio_data, user.id)
            print(f"✅ Created portfolio: {portfolio.name}")
        
        # Import holdings
        imported_count = 0
        updated_count = 0
        
        for symbol, data in holdings.items():
            # Check if holding already exists
            existing_holding = db_service.get_holding_by_symbol(portfolio.id, symbol)
            
            if existing_holding:
                # Update existing holding
                from app.schemas import HoldingUpdate
                holding_update = HoldingUpdate(
                    shares=Decimal(str(data['quantity'])),
                    average_cost=Decimal(str(data['cost_basis']))
                )
                updated_holding = db_service.update_holding(existing_holding.id, holding_update)
                print(f"🔄 Updated {symbol}: {data['quantity']} shares @ ${data['cost_basis']:.2f}")
                updated_count += 1
            else:
                # Create new holding
                from app.schemas import HoldingCreate
                holding_data = HoldingCreate(
                    portfolio_id=portfolio.id,
                    symbol=symbol,
                    company_name=f"{symbol} Holdings",  # Placeholder - could fetch from API
                    shares=Decimal(str(data['quantity'])),
                    average_cost=Decimal(str(data['cost_basis'])),
                    sector="Technology",  # Placeholder
                    industry="Software"   # Placeholder
                )
                new_holding = db_service.create_holding(holding_data)
                print(f"✅ Created {symbol}: {data['quantity']} shares @ ${data['cost_basis']:.2f}")
                imported_count += 1
        
        print(f"\n🎉 Portfolio import completed!")
        print(f"   Created: {imported_count} new holdings")
        print(f"   Updated: {updated_count} existing holdings")
        print(f"   Portfolio ID: {portfolio.id}")
        print(f"   User ID: {user.id}")
        
        # Display portfolio summary
        summary = db_service.get_portfolio_summary(portfolio.id)
        if summary:
            total_cost = sum(h.shares * h.average_cost for h in summary.portfolio.holdings if h.shares and h.average_cost)
            print(f"\n📊 Portfolio Summary:")
            print(f"   Total Holdings: {summary.total_holdings}")
            print(f"   Total Investment: ${total_cost:,.2f}")
            print(f"   Cash Balance: ${summary.portfolio.cash_balance:,.2f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error importing portfolio: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        db.close()

if __name__ == "__main__":
    print("🚀 AI Investment Tool - Portfolio Import")
    print("=" * 50)
    
    success = import_portfolio_from_env()
    
    if success:
        print("\n✅ Import completed successfully!")
        print("You can now access your portfolio at: http://localhost:8081/dashboard")
    else:
        print("\n❌ Import failed. Please check the error messages above.")
    
    print("=" * 50) 
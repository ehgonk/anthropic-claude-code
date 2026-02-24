"""
Database diagnostic script - check schema and fix if needed
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "data" / "broker.db"


def check_database():
    """Check database schema and provide diagnostics"""

    if not DB_PATH.exists():
        print(f"❌ Database not found: {DB_PATH}")
        print("   Run the backend first to create the database")
        return False

    print(f"✓ Database found: {DB_PATH}")
    print()

    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.cursor()

    # Check tables
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [row[0] for row in cur.fetchall()]

    print(f"📊 Tables ({len(tables)}):")
    for table in tables:
        cur.execute(f"SELECT COUNT(*) FROM {table}")
        count = cur.fetchone()[0]
        print(f"   - {table}: {count:,} rows")
    print()

    # Check stock_prices schema
    print("🔍 stock_prices schema:")
    cur.execute("PRAGMA table_info(stock_prices)")
    cols = cur.fetchall()

    has_stock_id = False
    for col in cols:
        print(f"   {col[1]:12} {col[2]:10} {'NOT NULL' if col[3] else ''}")
        if col[1] == 'stock_id':
            has_stock_id = True

    print()

    if not has_stock_id:
        print("❌ PROBLEM: 'stock_id' column is missing!")
        print()
        print("🔧 Possible solutions:")
        print("   1. Delete data/broker.db and restart backend to recreate")
        print("   2. Run migrations if available")
        return False

    print("✓ Schema looks correct")
    print()

    # Check stocks
    cur.execute("SELECT COUNT(*) FROM stocks")
    stock_count = cur.fetchone()[0]

    if stock_count == 0:
        print("⚠️  WARNING: No stocks in database")
        print("   Run: python -c 'from app.seed import seed_database; import asyncio; asyncio.run(seed_database())'")
        return False

    print(f"✓ {stock_count} stocks in database")
    print()

    # Sample stocks
    cur.execute("SELECT id, symbol, name, price FROM stocks LIMIT 5")
    print("📈 Sample stocks:")
    for row in cur.fetchall():
        print(f"   {row[0]:3} {row[1]:6} {row[2]:30} R$ {row[3]:.2f}")
    print()

    # Check date range
    cur.execute("SELECT MIN(date), MAX(date), COUNT(*) FROM stock_prices")
    min_date, max_date, price_count = cur.fetchone()

    if price_count > 0:
        print(f"📅 Price data:")
        print(f"   Range: {min_date} to {max_date}")
        print(f"   Records: {price_count:,}")
        print()
    else:
        print("⚠️  No price data yet - ready for download!")
        print()

    conn.close()
    return True


if __name__ == "__main__":
    print("=" * 60)
    print("Database Diagnostic Tool")
    print("=" * 60)
    print()

    success = check_database()

    print("=" * 60)
    if success:
        print("✅ Database is ready for download!")
        print()
        print("Next step:")
        print("   python download_yahoo_finance.py --symbol PETR4")
    else:
        print("❌ Database needs attention - see messages above")
    print("=" * 60)

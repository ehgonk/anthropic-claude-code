"""
Quick test of COTAHIST parser

Usage:
    python scripts/test_parser.py [file_path]
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.parsers import CotahistParser
from app.config import settings


def main():
    # Get file path from args or use first available
    if len(sys.argv) > 1:
        file_path = Path(sys.argv[1])
    else:
        cotahist_dir = settings.data_dir / "b3_cotahist"
        files = sorted(cotahist_dir.glob("COTAHIST_A*.txt"))
        if not files:
            print(f"❌ No COTAHIST files found in {cotahist_dir}")
            return
        file_path = files[0]

    print(f"📂 Testing parser with: {file_path.name}\n")

    parser = CotahistParser(file_path)

    # Count records
    print("Counting records...")
    total = parser.count_records()
    print(f"✓ Total Type-01 records: {total:,}\n")

    # Parse and show first 10 quotes
    print("First 10 quotes:")
    print("-" * 100)

    for i, quote in enumerate(parser.parse(), 1):
        print(f"{i:2d}. {quote.trading_code:12s} {quote.date} | "
              f"O:{quote.open_price:8.2f} H:{quote.high_price:8.2f} "
              f"L:{quote.low_price:8.2f} C:{quote.close_price:8.2f} "
              f"Vol:{quote.volume:12,d}")

        if i >= 10:
            break

    print("-" * 100)

    # Count unique stocks
    print("\nCounting unique stocks...")
    stocks = set()
    quote_count = 0

    for quote in parser.parse():
        stocks.add(quote.trading_code)
        quote_count += 1

    print(f"✓ Unique stocks: {len(stocks):,}")
    print(f"✓ Total quotes parsed: {quote_count:,}")

    # Show some popular stocks
    popular = ['PETR4', 'VALE3', 'ITUB4', 'BBDC4', 'ABEV3']
    print(f"\nChecking for popular stocks: {', '.join(popular)}")

    for code in popular:
        if code in stocks:
            print(f"  ✓ {code} found")
        else:
            print(f"  ✗ {code} not found")


if __name__ == "__main__":
    main()

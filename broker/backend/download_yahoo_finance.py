"""
Download real stock data from Yahoo Finance in batches

Features:
- Batch processing with rate limiting
- Resume capability (tracks progress)
- Graceful error handling per stock
- Incremental database updates
- Detailed logging

Usage:
    python download_yahoo_finance.py [--start-date YYYY-MM-DD] [--batch-size N] [--delay SECONDS]
"""

import sqlite3
import yfinance as yf
import time
import logging
import argparse
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Tuple

# Configuration
DB_PATH = Path(__file__).parent / "data" / "broker.db"
PROGRESS_FILE = Path(__file__).parent / "data" / ".download_progress.txt"
DEFAULT_START_DATE = "2000-01-01"
DEFAULT_BATCH_SIZE = 10
DEFAULT_DELAY = 2.0  # seconds between batches

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


def get_all_stocks_from_db() -> List[Tuple[int, str, str]]:
    """Get all stocks from database (id, symbol, name)"""
    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.cursor()
    cur.execute("SELECT id, symbol, name FROM stocks ORDER BY symbol")
    stocks = cur.fetchall()
    conn.close()
    return stocks


def get_last_date_for_stock(stock_id: int) -> Optional[date]:
    """Get the last date we have data for a stock"""
    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.cursor()
    cur.execute(
        "SELECT MAX(date) FROM stock_prices WHERE stock_id = ?",
        (stock_id,)
    )
    result = cur.fetchone()[0]
    conn.close()

    if result:
        return datetime.strptime(result, "%Y-%m-%d").date()
    return None


def get_completed_stocks() -> set:
    """Get list of completed stock symbols from progress file"""
    if not PROGRESS_FILE.exists():
        return set()

    with open(PROGRESS_FILE, 'r') as f:
        return set(line.strip() for line in f if line.strip())


def mark_stock_completed(symbol: str):
    """Mark a stock as completed in progress file"""
    with open(PROGRESS_FILE, 'a') as f:
        f.write(f"{symbol}\n")


def download_stock_data(
    symbol: str,
    start_date: str,
    end_date: str
) -> Optional[Dict]:
    """
    Download stock data from Yahoo Finance

    Returns dict with OHLCV data or None on error
    """
    try:
        ticker = yf.Ticker(f"{symbol}.SA")  # Brazilian stocks use .SA suffix

        # Download data
        df = ticker.history(start=start_date, end=end_date, auto_adjust=False)

        if df.empty:
            logger.warning(f"  {symbol}: No data returned from Yahoo Finance")
            return None

        # Convert to our format
        data = []
        for idx, row in df.iterrows():
            data.append({
                'date': idx.date(),
                'open': round(row['Open'], 2),
                'high': round(row['High'], 2),
                'low': round(row['Low'], 2),
                'close': round(row['Close'], 2),
                'volume': int(row['Volume'])
            })

        return {
            'symbol': symbol,
            'records': data,
            'count': len(data)
        }

    except Exception as e:
        logger.error(f"  {symbol}: Error downloading - {str(e)}")
        return None


def save_stock_data(stock_id: int, symbol: str, records: List[Dict]) -> int:
    """
    Save stock data to database

    Returns number of new records inserted
    """
    if not records:
        return 0

    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA journal_mode=WAL")
    cur = conn.cursor()

    try:
        # Get existing dates to avoid duplicates
        cur.execute(
            "SELECT date FROM stock_prices WHERE stock_id = ?",
            (stock_id,)
        )
        existing_dates = set(row[0] for row in cur.fetchall())

        # Insert only new records
        new_records = []
        for rec in records:
            date_str = rec['date'].strftime("%Y-%m-%d")
            if date_str not in existing_dates:
                new_records.append((
                    stock_id,
                    date_str,
                    rec['open'],
                    rec['high'],
                    rec['low'],
                    rec['close'],
                    rec['volume']
                ))

        if new_records:
            cur.executemany(
                "INSERT INTO stock_prices (stock_id, date, open, high, low, close, volume) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                new_records
            )

            # Update stock's latest price
            latest = records[-1]
            prev = records[-2] if len(records) >= 2 else records[-1]
            change_pct = ((latest['close'] - prev['close']) / prev['close']) * 100

            cur.execute(
                "UPDATE stocks SET price = ?, change_percent = ?, volume = ?, updated_at = ? "
                "WHERE id = ?",
                (
                    latest['close'],
                    round(change_pct, 4),
                    latest['volume'],
                    datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
                    stock_id
                )
            )

            conn.commit()

        conn.close()
        return len(new_records)

    except Exception as e:
        conn.rollback()
        conn.close()
        logger.error(f"  {symbol}: Database error - {str(e)}")
        return 0


def clear_progress():
    """Clear progress file to start fresh"""
    if PROGRESS_FILE.exists():
        PROGRESS_FILE.unlink()
    logger.info("Progress file cleared - starting fresh download")


def process_batch(
    batch: List[Tuple[int, str, str]],
    start_date: str,
    end_date: str,
    completed_stocks: set
) -> Dict:
    """
    Process a batch of stocks

    Returns stats dict
    """
    stats = {
        'attempted': 0,
        'succeeded': 0,
        'skipped': 0,
        'failed': 0,
        'new_records': 0
    }

    for stock_id, symbol, name in batch:
        stats['attempted'] += 1

        # Skip if already completed
        if symbol in completed_stocks:
            stats['skipped'] += 1
            logger.info(f"  {symbol}: Already completed (skipping)")
            continue

        # Check last date in DB
        last_date = get_last_date_for_stock(stock_id)
        download_start = start_date

        if last_date:
            # Download only missing data
            download_start = (last_date + timedelta(days=1)).strftime("%Y-%m-%d")
            logger.info(f"  {symbol}: Updating from {download_start} (last: {last_date})")
        else:
            logger.info(f"  {symbol}: Downloading full history from {start_date}")

        # Download data
        data = download_stock_data(symbol, download_start, end_date)

        if data is None:
            stats['failed'] += 1
            continue

        # Save to database
        new_records = save_stock_data(stock_id, symbol, data['records'])
        stats['new_records'] += new_records
        stats['succeeded'] += 1

        logger.info(f"  {symbol}: ✓ Downloaded {data['count']} records, {new_records} new")

        # Mark as completed
        mark_stock_completed(symbol)

        # Small delay between stocks in same batch
        time.sleep(0.5)

    return stats


def main():
    parser = argparse.ArgumentParser(description='Download Yahoo Finance data in batches')
    parser.add_argument('--start-date', default=DEFAULT_START_DATE, help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end-date', default=datetime.now().strftime("%Y-%m-%d"), help='End date (YYYY-MM-DD)')
    parser.add_argument('--batch-size', type=int, default=DEFAULT_BATCH_SIZE, help='Stocks per batch')
    parser.add_argument('--delay', type=float, default=DEFAULT_DELAY, help='Delay between batches (seconds)')
    parser.add_argument('--clear-progress', action='store_true', help='Clear progress and start fresh')
    parser.add_argument('--symbol', help='Download only specific symbol (e.g., PETR4)')
    args = parser.parse_args()

    # Clear progress if requested
    if args.clear_progress:
        clear_progress()

    # Get all stocks
    all_stocks = get_all_stocks_from_db()
    logger.info(f"Found {len(all_stocks)} stocks in database")

    # Filter by symbol if specified
    if args.symbol:
        all_stocks = [s for s in all_stocks if s[1] == args.symbol.upper()]
        if not all_stocks:
            logger.error(f"Symbol {args.symbol} not found in database")
            return
        logger.info(f"Downloading only {args.symbol}")

    # Get completed stocks
    completed = get_completed_stocks()
    if completed:
        logger.info(f"Resuming - {len(completed)} stocks already completed")

    # Calculate batches
    remaining_stocks = [s for s in all_stocks if s[1] not in completed]
    total_batches = (len(remaining_stocks) + args.batch_size - 1) // args.batch_size

    if not remaining_stocks:
        logger.info("All stocks already completed!")
        return

    logger.info(f"Starting download: {len(remaining_stocks)} stocks in {total_batches} batches")
    logger.info(f"Period: {args.start_date} to {args.end_date}")
    logger.info(f"Batch size: {args.batch_size}, Delay: {args.delay}s")
    logger.info("-" * 80)

    # Process batches
    total_stats = {
        'attempted': 0,
        'succeeded': 0,
        'skipped': 0,
        'failed': 0,
        'new_records': 0
    }

    start_time = time.time()

    for i in range(0, len(remaining_stocks), args.batch_size):
        batch = remaining_stocks[i:i + args.batch_size]
        batch_num = (i // args.batch_size) + 1

        logger.info(f"\n📦 Batch {batch_num}/{total_batches} ({len(batch)} stocks)")

        # Process batch
        batch_stats = process_batch(batch, args.start_date, args.end_date, completed)

        # Update totals
        for key in total_stats:
            total_stats[key] += batch_stats[key]

        # Log batch summary
        logger.info(
            f"  Batch summary: {batch_stats['succeeded']}/{batch_stats['attempted']} succeeded, "
            f"{batch_stats['new_records']} new records"
        )

        # Delay before next batch (but not after last batch)
        if i + args.batch_size < len(remaining_stocks):
            logger.info(f"  ⏳ Waiting {args.delay}s before next batch...")
            time.sleep(args.delay)

    # Final summary
    elapsed = time.time() - start_time
    logger.info("\n" + "=" * 80)
    logger.info("✅ Download complete!")
    logger.info(f"  Total stocks attempted: {total_stats['attempted']}")
    logger.info(f"  Succeeded: {total_stats['succeeded']}")
    logger.info(f"  Failed: {total_stats['failed']}")
    logger.info(f"  Skipped: {total_stats['skipped']}")
    logger.info(f"  New records inserted: {total_stats['new_records']:,}")
    logger.info(f"  Time elapsed: {elapsed:.1f}s ({elapsed/60:.1f} minutes)")

    # Verify database
    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM stock_prices")
    total_records = cur.fetchone()[0]
    cur.execute("SELECT MIN(date), MAX(date) FROM stock_prices")
    date_range = cur.fetchone()
    conn.close()

    logger.info(f"\n📊 Database summary:")
    logger.info(f"  Total price records: {total_records:,}")
    logger.info(f"  Date range: {date_range[0]} to {date_range[1]}")
    logger.info("=" * 80)


if __name__ == "__main__":
    main()

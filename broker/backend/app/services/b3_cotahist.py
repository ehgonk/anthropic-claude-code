"""
B3 COTAHIST Data Service

Downloads and parses official B3 historical stock data from COTAHIST files.
Data source: https://www.b3.com.br/pt_br/market-data-e-indices/servicos-de-dados/market-data/historico/mercado-a-vista/cotacoes-historicas/
"""

import httpx
import zipfile
import io
from pathlib import Path
from datetime import datetime
from typing import Optional


def parse_cotahist_line(line: str) -> dict | None:
    """Parse a single COTAHIST line (fixed-width format)"""
    if len(line) < 200:
        return None

    tipo_reg = line[0:2]
    if tipo_reg != "01":
        return None

    # Market type: 010 = spot market
    market_type = int(line[24:27].strip() or "0")

    ticker = line[12:24].strip()
    if not ticker or len(ticker) < 4:
        return None

    # Filter: only spot market (010)
    if market_type != 10:
        return None

    # Filter: only BRL (R$) quotes
    currency = line[52:56].strip()
    if currency != "R$":
        return None

    try:
        trade_date = datetime.strptime(line[2:10], "%Y%m%d")
    except ValueError:
        return None

    def _extract_decimal(raw: str, decimals: int = 2) -> float:
        try:
            val = int(raw.strip())
            return val / (10**decimals)
        except (ValueError, TypeError):
            return 0.0

    return {
        "ticker": ticker,
        "name": line[27:39].strip(),
        "trade_date": trade_date,
        "open_price": _extract_decimal(line[56:69]),
        "high_price": _extract_decimal(line[69:82]),
        "low_price": _extract_decimal(line[82:95]),
        "close_price": _extract_decimal(line[108:121]),
        "volume": _extract_decimal(line[152:170]),
    }


class B3CotahistService:
    """Service to download and parse B3 COTAHIST files"""

    # Direct download URL pattern for B3 COTAHIST files
    # Source: https://bvmf.bmfbovespa.com.br/InstDados/SerHist/
    BASE_URL = "https://bvmf.bmfbovespa.com.br/InstDados/SerHist/COTAHIST_A{year}.ZIP"

    def __init__(self, cache_dir: Optional[Path] = None):
        self.cache_dir = cache_dir or Path("data/cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    async def download_cotahist(self, year: int) -> bytes:
        """
        Download COTAHIST file for a specific year from B3

        Args:
            year: Year to download (e.g., 2025)

        Returns:
            ZIP file content as bytes
        """
        url = self.BASE_URL.format(year=year)
        print(f"Downloading COTAHIST from {url}...")

        # B3 requires proper headers to avoid 403 Forbidden
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }

        async with httpx.AsyncClient(timeout=60.0, follow_redirects=True, headers=headers) as client:
            response = await client.get(url)
            response.raise_for_status()

        print(f"Downloaded {len(response.content) / 1024 / 1024:.2f} MB")
        return response.content

    def extract_txt_from_zip(self, zip_content: bytes) -> str:
        """
        Extract TXT file from COTAHIST ZIP

        Args:
            zip_content: ZIP file content as bytes

        Returns:
            Content of the TXT file as string
        """
        with zipfile.ZipFile(io.BytesIO(zip_content)) as zf:
            # COTAHIST files typically have one TXT file inside
            txt_files = [f for f in zf.namelist() if f.upper().endswith('.TXT')]
            if not txt_files:
                raise ValueError("No TXT file found in ZIP")

            txt_filename = txt_files[0]
            print(f"Extracting {txt_filename}...")

            with zf.open(txt_filename) as f:
                # B3 files use latin-1 encoding
                content = f.read().decode('latin-1')

        return content

    def parse_cotahist(self, txt_content: str, symbols: Optional[list[str]] = None) -> dict[str, list[dict]]:
        """
        Parse COTAHIST TXT content

        Args:
            txt_content: Content of COTAHIST TXT file
            symbols: Optional list of symbols to filter

        Returns:
            Dictionary with symbol as key and list of daily records as value
        """
        print("Parsing COTAHIST file...")

        records = {}
        for line in txt_content.split('\n'):
            rec = parse_cotahist_line(line)
            if not rec:
                continue

            ticker = rec['ticker']

            # Filter by symbols if provided
            if symbols and ticker not in symbols:
                continue

            if ticker not in records:
                records[ticker] = []

            records[ticker].append(rec)

        print(f"Parsed {len(records)} symbols")
        return records

    async def get_stock_data(self, year: int, symbols: Optional[list[str]] = None) -> dict:
        """
        Get stock data for specific symbols and year

        Args:
            year: Year to get data for
            symbols: Optional list of stock symbols (e.g., ['PETR4', 'VALE3'])

        Returns:
            Dictionary with stock data
        """
        # Check cache
        cache_file = self.cache_dir / f"cotahist_{year}.txt"
        if cache_file.exists():
            print(f"Loading from cache: {cache_file}")
            txt_content = cache_file.read_text(encoding='latin-1')
        else:
            # Download and extract
            zip_content = await self.download_cotahist(year)
            txt_content = self.extract_txt_from_zip(zip_content)

            # Save to cache
            cache_file.write_text(txt_content, encoding='latin-1')
            print(f"Cached to {cache_file}")

        # Parse and filter
        records = self.parse_cotahist(txt_content, symbols=symbols)

        return records

    def df_to_stock_records(self, stock_data: dict) -> dict[str, dict]:
        """
        Convert parsed data to stock records grouped by symbol

        Args:
            stock_data: Dictionary from get_stock_data()

        Returns:
            Dictionary with symbol as key and stock info + prices as value
        """
        stocks = {}

        for symbol, daily_records in stock_data.items():
            if not daily_records:
                continue

            # Sort by date
            daily_records.sort(key=lambda x: x['trade_date'])

            # Get latest price for current quote
            latest = daily_records[-1]

            # Calculate change percent (comparing last two days)
            if len(daily_records) >= 2:
                prev_close = daily_records[-2]['close_price']
                curr_close = latest['close_price']
                if prev_close > 0:
                    change_percent = ((curr_close - prev_close) / prev_close) * 100
                else:
                    change_percent = 0.0
            else:
                change_percent = 0.0

            # Build stock record
            stocks[symbol] = {
                'symbol': symbol,
                'name': latest['name'],
                'price': latest['close_price'],
                'change_percent': change_percent,
                'volume': int(latest['volume']),
                'prices': [
                    {
                        'date': row['trade_date'].strftime('%Y-%m-%d'),
                        'open': row['open_price'],
                        'high': row['high_price'],
                        'low': row['low_price'],
                        'close': row['close_price'],
                        'volume': int(row['volume']),
                    }
                    for row in daily_records
                ]
            }

        return stocks


# Singleton instance
b3_service = B3CotahistService()

"""
Parser for B3 COTAHIST files (fixed-width format)

COTAHIST Format Specification:
- Record Type 00: Header
- Record Type 01: Daily quote data
- Record Type 99: Trailer

Type 01 (Quote) Fields (positions are 0-indexed):
- 002-009: Date (YYYYMMDD)
- 010-011: BDI Code
- 012-023: Trading code (CODNEG)
- 024-035: Short name (NOMRES)
- 056-068: Opening price (13 digits, last 2 are decimals)
- 069-081: High price
- 082-094: Low price
- 095-107: Average price
- 108-120: Close price
- 152-169: Total volume (18 digits)
- 170-182: Market type
"""

from datetime import datetime
from typing import Generator
from dataclasses import dataclass
from pathlib import Path


@dataclass
class CotahistQuote:
    """Represents a single quote from COTAHIST"""
    date: str  # YYYY-MM-DD format
    trading_code: str
    short_name: str
    open_price: float
    high_price: float
    low_price: float
    close_price: float
    volume: int


class CotahistParser:
    """Parser for B3 COTAHIST fixed-width files"""

    def __init__(self, file_path: Path):
        self.file_path = file_path

    @staticmethod
    def _parse_price(value: str) -> float:
        """Parse price field (13 digits, last 2 are decimals)"""
        try:
            # Remove leading/trailing spaces
            value = value.strip()
            if not value or value == '0' * len(value):
                return 0.0
            # Convert to float (last 2 digits are decimals)
            return float(value) / 100.0
        except (ValueError, AttributeError):
            return 0.0

    @staticmethod
    def _parse_volume(value: str) -> int:
        """Parse volume field (18 digits)"""
        try:
            value = value.strip()
            return int(value) if value else 0
        except (ValueError, AttributeError):
            return 0

    @staticmethod
    def _parse_date(value: str) -> str:
        """Parse date from YYYYMMDD to YYYY-MM-DD"""
        try:
            value = value.strip()
            if len(value) == 8:
                year = value[:4]
                month = value[4:6]
                day = value[6:8]
                return f"{year}-{month}-{day}"
            return value
        except (ValueError, AttributeError):
            return ""

    def parse_line(self, line: str) -> CotahistQuote | None:
        """
        Parse a single line from COTAHIST file

        Returns:
            CotahistQuote if line is a valid Type 01 record, None otherwise
        """
        # Check if it's a Type 01 record (quote data)
        if len(line) < 245 or line[0:2] != '01':
            return None

        try:
            # Extract fields (positions are 0-indexed)
            date_str = line[2:10]
            trading_code = line[12:24].strip()
            short_name = line[24:36].strip()

            # Parse prices (13 digits each, last 2 are decimals)
            open_price = self._parse_price(line[56:69])
            high_price = self._parse_price(line[69:82])
            low_price = self._parse_price(line[82:95])
            close_price = self._parse_price(line[108:121])

            # Parse volume (18 digits)
            volume = self._parse_volume(line[152:170])

            # Convert date to YYYY-MM-DD
            date = self._parse_date(date_str)

            # Skip invalid records
            if not trading_code or not date:
                return None

            # Filter: only stocks (ending with digits, usually spot market)
            # Common patterns: PETR4, VALE3, ITUB4, etc.
            if not any(c.isdigit() for c in trading_code):
                return None

            return CotahistQuote(
                date=date,
                trading_code=trading_code,
                short_name=short_name,
                open_price=open_price,
                high_price=high_price,
                low_price=low_price,
                close_price=close_price,
                volume=volume
            )
        except (IndexError, ValueError) as e:
            # Skip malformed lines
            return None

    def parse(self, filter_codes: set[str] | None = None) -> Generator[CotahistQuote, None, None]:
        """
        Parse COTAHIST file and yield quote records

        Args:
            filter_codes: Optional set of trading codes to filter (e.g., {'PETR4', 'VALE3'})

        Yields:
            CotahistQuote objects
        """
        with open(self.file_path, 'r', encoding='latin-1') as f:
            for line in f:
                quote = self.parse_line(line)
                if quote:
                    # Apply filter if provided
                    if filter_codes is None or quote.trading_code in filter_codes:
                        yield quote

    def count_records(self) -> int:
        """Count total number of quote records in file"""
        count = 0
        with open(self.file_path, 'r', encoding='latin-1') as f:
            for line in f:
                if len(line) >= 2 and line[0:2] == '01':
                    count += 1
        return count

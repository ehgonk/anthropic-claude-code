"""
Yahoo Finance Data Service - FONTE ÚNICA DE DADOS

Busca dados do mercado brasileiro usando Yahoo Finance.
Esta é a ÚNICA fonte de dados da aplicação.

Critérios:
- Data mínima: 1994-07-01 (início do Real - R$)
- Ibovespa: símbolo ^BVSP
- Ações brasileiras: sufixo .SA (ex: PETR4.SA)

Features:
- Download de dados históricos
- Cotações atuais
- Suporte para múltiplas ações
- Biblioteca yfinance estável e confiável
"""

import asyncio
import logging
from datetime import datetime, timedelta, date
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class YahooFinanceService:
    """Service to fetch stock data from Yahoo Finance"""

    # Data mínima: 1994-07-01 (início do Real)
    MIN_DATE = date(1994, 7, 1)

    # Ibovespa symbol on Yahoo Finance
    IBOVESPA_SYMBOL = "^BVSP"

    # Brazilian stock symbols on Yahoo Finance use .SA suffix
    SUFFIX = ".SA"

    # Popular Brazilian stocks
    POPULAR_STOCKS = [
        "PETR4", "VALE3", "ITUB4", "BBDC4", "ABEV3",
        "B3SA3", "RENT3", "MGLU3", "WEGE3", "SUZB3",
        "RAIL3", "VIVT3", "GGBR4", "EMBR3", "RADL3"
    ]

    def __init__(self):
        self.timeout = 30.0

    async def fetch_ibovespa_historical(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict]:
        """
        Busca dados históricos do Ibovespa do Yahoo Finance

        Args:
            start_date: Data inicial (padrão: 1994-07-01)
            end_date: Data final (padrão: hoje)

        Returns:
            Lista de registros diários:
            [
                {
                    'date': date(2024, 1, 1),
                    'open': 120000.0,
                    'high': 121000.0,
                    'low': 119000.0,
                    'close': 120500.0,
                    'volume': 15000000000
                }
            ]
        """
        # Datas padrão
        if end_date is None:
            end_date = datetime.now()
        if start_date is None:
            start_date = datetime(1994, 7, 1)

        # Garantir que não seja antes de 1994
        if start_date.date() < self.MIN_DATE:
            start_date = datetime.combine(self.MIN_DATE, datetime.min.time())

        logger.info(f"📊 Buscando Ibovespa do Yahoo Finance ({start_date.date()} a {end_date.date()})")

        # Run download in thread pool (yfinance is not async)
        loop = asyncio.get_event_loop()

        def download_ibov():
            try:
                import yfinance as yf
            except ImportError:
                raise Exception("yfinance library not installed")

            logger.info(f"📥 Downloading {self.IBOVESPA_SYMBOL}...")

            ticker = yf.Ticker(self.IBOVESPA_SYMBOL)

            # Get historical data
            df = ticker.history(
                start=start_date.strftime('%Y-%m-%d'),
                end=end_date.strftime('%Y-%m-%d'),
                interval='1d'
            )

            if df.empty:
                raise Exception("No data returned from Yahoo Finance")

            logger.info(f"✅ Downloaded {len(df)} records")

            # Convert DataFrame to records
            records = []
            for date_idx, row in df.iterrows():
                try:
                    record_date = date_idx.date()

                    # Filtrar por MIN_DATE (1994+)
                    if record_date < self.MIN_DATE:
                        continue

                    record = {
                        'date': record_date,
                        'open': float(row['Open']),
                        'high': float(row['High']),
                        'low': float(row['Low']),
                        'close': float(row['Close']),
                        'volume': int(row['Volume'])
                    }
                    records.append(record)

                except (ValueError, KeyError) as e:
                    logger.warning(f"Skipping invalid row: {e}")
                    continue

            # Sort by date (oldest first)
            records.sort(key=lambda x: x['date'])

            logger.info(f"✅ {len(records)} registros do Ibovespa processados")
            return records

        records = await loop.run_in_executor(None, download_ibov)
        return records

    def _add_suffix(self, symbol: str) -> str:
        """Add .SA suffix to Brazilian stock symbols if not present"""
        if not symbol.endswith(self.SUFFIX):
            return f"{symbol}{self.SUFFIX}"
        return symbol

    def _remove_suffix(self, symbol: str) -> str:
        """Remove .SA suffix from Yahoo Finance symbols"""
        if symbol.endswith(self.SUFFIX):
            return symbol[:-3]
        return symbol

    async def fetch_stock_data(
        self,
        symbols: List[str],
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Dict]:
        """
        Fetch historical data for multiple stocks

        Args:
            symbols: List of stock symbols (e.g., ['PETR4', 'VALE3'])
            start_date: Start date (default: 1 year ago)
            end_date: End date (default: today)

        Returns:
            Dictionary with symbol as key and stock data as value:
            {
                'symbol': 'PETR4',
                'name': 'Petrobras PN',
                'price': 38.50,
                'change_percent': 2.5,
                'volume': 123456789,
                'prices': [
                    {'date': '2024-01-01', 'open': 38.00, 'high': 39.00, 'low': 37.50, 'close': 38.50, 'volume': 123456}
                ]
            }
        """
        # Default date range
        if end_date is None:
            end_date = datetime.now()
        if start_date is None:
            start_date = end_date - timedelta(days=365)

        logger.info(f"📊 Fetching data for {len(symbols)} stocks from Yahoo Finance...")

        # Run download in thread pool (yfinance is not async)
        loop = asyncio.get_event_loop()

        def download_all():
            try:
                import yfinance as yf
            except ImportError:
                raise Exception("yfinance library not installed")

            results = {}

            for symbol in symbols:
                try:
                    yahoo_symbol = self._add_suffix(symbol)
                    logger.debug(f"Fetching {yahoo_symbol}...")

                    ticker = yf.Ticker(yahoo_symbol)

                    # Get historical data
                    df = ticker.history(
                        start=start_date.strftime('%Y-%m-%d'),
                        end=end_date.strftime('%Y-%m-%d'),
                        interval='1d'
                    )

                    if df.empty:
                        logger.warning(f"No data for {symbol}")
                        continue

                    # Get stock info
                    info = ticker.info
                    name = info.get('longName') or info.get('shortName') or symbol

                    # Convert DataFrame to price records
                    prices = []
                    for date_idx, row in df.iterrows():
                        try:
                            prices.append({
                                'date': date_idx.strftime('%Y-%m-%d'),
                                'open': float(row['Open']),
                                'high': float(row['High']),
                                'low': float(row['Low']),
                                'close': float(row['Close']),
                                'volume': int(row['Volume'])
                            })
                        except (ValueError, KeyError) as e:
                            logger.warning(f"Skipping invalid row for {symbol}: {e}")
                            continue

                    if not prices:
                        logger.warning(f"No valid price data for {symbol}")
                        continue

                    # Sort by date
                    prices.sort(key=lambda x: x['date'])

                    # Get latest price and calculate change
                    latest = prices[-1]
                    if len(prices) >= 2:
                        prev_close = prices[-2]['close']
                        change_pct = ((latest['close'] - prev_close) / prev_close) * 100
                    else:
                        change_pct = 0.0

                    results[symbol] = {
                        'symbol': symbol,
                        'name': name,
                        'price': latest['close'],
                        'change_percent': change_pct,
                        'volume': latest['volume'],
                        'prices': prices
                    }

                    logger.info(f"✅ {symbol}: {len(prices)} records")

                except Exception as e:
                    logger.error(f"❌ Failed to fetch {symbol}: {e}")
                    continue

            return results

        results = await loop.run_in_executor(None, download_all)
        logger.info(f"✅ Fetched {len(results)}/{len(symbols)} stocks successfully")

        return results

    async def fetch_single_stock(
        self,
        symbol: str,
        days: int = 365
    ) -> Optional[Dict]:
        """
        Fetch data for a single stock

        Args:
            symbol: Stock symbol (e.g., 'PETR4')
            days: Number of days of historical data

        Returns:
            Stock data dictionary or None if failed
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        results = await self.fetch_stock_data([symbol], start_date, end_date)
        return results.get(symbol)

    async def get_popular_stocks(self, days: int = 365) -> Dict[str, Dict]:
        """
        Fetch data for popular Brazilian stocks

        Args:
            days: Number of days of historical data

        Returns:
            Dictionary with stock data
        """
        logger.info(f"📊 Fetching {len(self.POPULAR_STOCKS)} popular stocks...")

        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        return await self.fetch_stock_data(self.POPULAR_STOCKS, start_date, end_date)

    async def search_stock(self, query: str) -> List[Dict]:
        """
        Search for stocks by symbol or name

        Args:
            query: Search query (symbol or company name)

        Returns:
            List of matching stocks
        """
        # Simple implementation: check if query matches any popular stock
        query_upper = query.upper()

        matching = []
        for symbol in self.POPULAR_STOCKS:
            if query_upper in symbol:
                stock_data = await self.fetch_single_stock(symbol, days=30)
                if stock_data:
                    matching.append(stock_data)

        return matching

    async def test_connection(self) -> Dict:
        """Test connection to Yahoo Finance"""
        try:
            import yfinance as yf

            # Test with a known stock
            test_symbol = "PETR4.SA"
            ticker = yf.Ticker(test_symbol)
            info = ticker.info

            if info and info.get('symbol'):
                return {
                    'status': 'ok',
                    'message': f'Successfully connected to Yahoo Finance (tested with {test_symbol})',
                    'test_symbol': test_symbol
                }
            else:
                return {
                    'status': 'warning',
                    'message': 'Connected but no data returned'
                }

        except Exception as e:
            return {
                'status': 'error',
                'message': str(e)
            }


# Global instance
yahoo_finance_service = YahooFinanceService()

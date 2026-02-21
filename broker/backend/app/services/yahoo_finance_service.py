"""
Yahoo Finance Data Service - FONTE ÚNICA DE DADOS

Busca dados do mercado brasileiro usando Yahoo Finance API diretamente.
Esta é a ÚNICA fonte de dados da aplicação.

Usa httpx para fazer requests HTTP diretamente à API do Yahoo Finance,
sem depender da biblioteca yfinance (que tem problemas com proxy/bloqueio).

Critérios:
- Data mínima: 1994-07-01 (início do Real - R$)
- Ibovespa: símbolo ^BVSP
- Ações brasileiras: sufixo .SA (ex: PETR4.SA)

Yahoo Finance Chart API:
- URL: https://query1.finance.yahoo.com/v8/finance/chart/{symbol}
- Params: period1, period2 (unix timestamps), interval (1d, 1wk, 1mo)
"""

import logging
import httpx
from datetime import datetime, timedelta, date
from typing import List, Dict, Optional
from urllib.parse import quote

logger = logging.getLogger(__name__)

# Import B3 stocks list
try:
    from ..config.b3_stocks import ALL_B3_STOCKS, IBOVESPA_STOCKS
except ImportError:
    # Fallback if config not available
    ALL_B3_STOCKS = []
    IBOVESPA_STOCKS = []

# Yahoo Finance API base URL
YAHOO_CHART_URL = "https://query1.finance.yahoo.com/v8/finance/chart"

# Headers to simulate browser request
YAHOO_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
}


class YahooFinanceService:
    """Service to fetch stock data from Yahoo Finance via direct HTTP"""

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

    def _to_unix(self, dt: datetime) -> int:
        """Convert datetime to Unix timestamp"""
        return int(dt.timestamp())

    def _get_client(self) -> httpx.AsyncClient:
        """Create httpx client without proxy"""
        return httpx.AsyncClient(
            headers=YAHOO_HEADERS,
            timeout=self.timeout,
            follow_redirects=True,
            proxy=None,
            trust_env=False,  # Ignore environment proxy settings
        )

    async def _fetch_chart_data(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        interval: str = "1d"
    ) -> List[Dict]:
        """
        Fetch chart data from Yahoo Finance API

        Args:
            symbol: Yahoo Finance symbol (e.g., ^BVSP, VALE3.SA)
            start_date: Start datetime
            end_date: End datetime
            interval: Data interval (1d, 1wk, 1mo)

        Returns:
            List of OHLCV records
        """
        # URL-encode symbol (important for ^BVSP)
        encoded_symbol = quote(symbol, safe='')
        url = f"{YAHOO_CHART_URL}/{encoded_symbol}"

        params = {
            "period1": self._to_unix(start_date),
            "period2": self._to_unix(end_date),
            "interval": interval,
            "includeAdjustedClose": "true",
            "events": "history",
        }

        logger.info(f"📥 Fetching {symbol} from Yahoo Finance API...")
        logger.info(f"   URL: {url}")
        logger.info(f"   Period: {start_date.date()} to {end_date.date()}")

        async with self._get_client() as client:
            response = await client.get(url, params=params)

            if response.status_code != 200:
                error_msg = f"Yahoo Finance API returned HTTP {response.status_code}"
                logger.error(f"❌ {error_msg}")
                logger.error(f"   Response: {response.text[:500]}")
                raise Exception(error_msg)

            data = response.json()

        # Parse the chart response
        chart = data.get("chart", {})
        result = chart.get("result")

        if not result or len(result) == 0:
            error = chart.get("error", {})
            error_msg = error.get("description", "No data returned")
            raise Exception(f"Yahoo Finance error: {error_msg}")

        result = result[0]
        timestamps = result.get("timestamp", [])
        indicators = result.get("indicators", {})
        quotes = indicators.get("quote", [{}])[0]

        if not timestamps:
            raise Exception("No timestamps in Yahoo Finance response")

        opens = quotes.get("open", [])
        highs = quotes.get("high", [])
        lows = quotes.get("low", [])
        closes = quotes.get("close", [])
        volumes = quotes.get("volume", [])

        records = []
        for i, ts in enumerate(timestamps):
            try:
                record_date = datetime.utcfromtimestamp(ts).date()

                # Filter by MIN_DATE (1994+)
                if record_date < self.MIN_DATE:
                    continue

                # Skip if any value is None
                if any(v is None for v in [opens[i], highs[i], lows[i], closes[i]]):
                    continue

                record = {
                    'date': record_date,
                    'open': float(opens[i]),
                    'high': float(highs[i]),
                    'low': float(lows[i]),
                    'close': float(closes[i]),
                    'volume': int(volumes[i]) if volumes[i] is not None else 0
                }
                records.append(record)

            except (ValueError, IndexError, TypeError) as e:
                logger.warning(f"Skipping invalid record at index {i}: {e}")
                continue

        logger.info(f"✅ Parsed {len(records)} records for {symbol}")
        return records

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
            Lista de registros diários com date, open, high, low, close, volume
        """
        if end_date is None:
            end_date = datetime.now()
        if start_date is None:
            start_date = datetime(1994, 7, 1)

        # Garantir que não seja antes de 1994
        if start_date.date() < self.MIN_DATE:
            start_date = datetime.combine(self.MIN_DATE, datetime.min.time())

        logger.info(f"📊 Buscando Ibovespa do Yahoo Finance ({start_date.date()} a {end_date.date()})")

        records = await self._fetch_chart_data(
            symbol=self.IBOVESPA_SYMBOL,
            start_date=start_date,
            end_date=end_date,
            interval="1d"
        )

        # Sort by date (oldest first)
        records.sort(key=lambda x: x['date'])

        logger.info(f"✅ {len(records)} registros do Ibovespa processados")
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
            Dictionary with symbol as key and stock data as value
        """
        if end_date is None:
            end_date = datetime.now()
        if start_date is None:
            start_date = end_date - timedelta(days=365)

        logger.info(f"📊 Fetching data for {len(symbols)} stocks from Yahoo Finance...")

        results = {}

        for symbol in symbols:
            try:
                yahoo_symbol = self._add_suffix(symbol)

                prices_raw = await self._fetch_chart_data(
                    symbol=yahoo_symbol,
                    start_date=start_date,
                    end_date=end_date,
                    interval="1d"
                )

                if not prices_raw:
                    logger.warning(f"No data for {symbol}")
                    continue

                # Convert to price records with string dates
                prices = []
                for r in prices_raw:
                    prices.append({
                        'date': r['date'].strftime('%Y-%m-%d'),
                        'open': r['open'],
                        'high': r['high'],
                        'low': r['low'],
                        'close': r['close'],
                        'volume': r['volume']
                    })

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
                    'name': symbol,  # Name will be set later if needed
                    'price': latest['close'],
                    'change_percent': change_pct,
                    'volume': latest['volume'],
                    'prices': prices
                }

                logger.info(f"✅ {symbol}: {len(prices)} records")

            except Exception as e:
                logger.error(f"❌ Failed to fetch {symbol}: {e}")
                continue

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

    async def get_all_b3_stocks(self, days: int = 365) -> Dict[str, Dict]:
        """
        Fetch data for ALL B3 stocks (~170 stocks)

        Args:
            days: Number of days of historical data

        Returns:
            Dictionary with stock data
        """
        if not ALL_B3_STOCKS:
            logger.warning("ALL_B3_STOCKS not available, falling back to POPULAR_STOCKS")
            return await self.get_popular_stocks(days)

        logger.info(f"📊 Fetching {len(ALL_B3_STOCKS)} B3 stocks...")

        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        return await self.fetch_stock_data(ALL_B3_STOCKS, start_date, end_date)

    async def get_ibovespa_stocks(self, days: int = 365) -> Dict[str, Dict]:
        """
        Fetch data for Ibovespa stocks (~85 stocks)

        Args:
            days: Number of days of historical data

        Returns:
            Dictionary with stock data
        """
        if not IBOVESPA_STOCKS:
            logger.warning("IBOVESPA_STOCKS not available, falling back to POPULAR_STOCKS")
            return await self.get_popular_stocks(days)

        logger.info(f"📊 Fetching {len(IBOVESPA_STOCKS)} Ibovespa stocks...")

        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        return await self.fetch_stock_data(IBOVESPA_STOCKS, start_date, end_date)

    async def search_stock(self, query: str) -> List[Dict]:
        """
        Search for stocks by symbol or name

        Args:
            query: Search query (symbol or company name)

        Returns:
            List of matching stocks
        """
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
            # Test with VALE3.SA - recent data (last 30 days)
            test_symbol = "VALE3.SA"
            logger.info(f"Testing Yahoo Finance connection with {test_symbol}...")

            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)

            records = await self._fetch_chart_data(
                symbol=test_symbol,
                start_date=start_date,
                end_date=end_date,
                interval="1d"
            )

            if records:
                latest = records[-1]
                return {
                    'status': 'ok',
                    'message': 'Successfully connected to Yahoo Finance',
                    'test_symbol': test_symbol,
                    'records_fetched': len(records),
                    'latest_date': str(latest['date']),
                    'latest_close': latest['close']
                }
            else:
                return {
                    'status': 'warning',
                    'message': 'Connected but no data returned',
                    'test_symbol': test_symbol
                }

        except Exception as e:
            logger.error(f"Yahoo Finance test failed: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }


# Global instance
yahoo_finance_service = YahooFinanceService()

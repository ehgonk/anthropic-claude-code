"""
Investing.com Data Service - ÚNICA FONTE DE DADOS

Busca dados históricos do Investing.com para o mercado brasileiro via WEB SCRAPING.

FEATURES:
- Sistema de batching inteligente (5-10 ações por batch)
- Rate limiting (10-12 requisições/minuto)
- Retry logic com exponential backoff
- Filtro de data mínima: 1994-07-01 (início do Real)
- Web scraping com cloudscraper (bypass Cloudflare)
- User-agent rotation para evitar bloqueios

MÉTODO: Web scraping direto das páginas de dados históricos
"""

import asyncio
import logging
import time
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional
from dataclasses import dataclass

# Web scraping
import cloudscraper
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


@dataclass
class RateLimiter:
    """Rate limiter para Investing.com"""
    max_requests_per_minute: int = 10  # Conservative: 10 req/min
    min_delay_seconds: float = 6.0     # Minimum 6s between requests

    def __post_init__(self):
        self.request_times: List[float] = []
        self._lock = asyncio.Lock()

    async def acquire(self):
        """Aguarda se necessário para respeitar rate limit"""
        async with self._lock:
            now = time.time()

            # Remove requests mais antigos que 1 minuto
            cutoff = now - 60
            self.request_times = [t for t in self.request_times if t > cutoff]

            # Se já atingiu o limite, aguarda
            if len(self.request_times) >= self.max_requests_per_minute:
                oldest = self.request_times[0]
                wait_time = 60 - (now - oldest) + 2  # +2 safety margin
                logger.info(f"⏳ Rate limit atingido. Aguardando {wait_time:.1f}s...")
                await asyncio.sleep(wait_time)
                # Limpa lista após wait
                self.request_times = []
                now = time.time()

            # Garante delay mínimo entre requests
            if self.request_times:
                last_request = self.request_times[-1]
                elapsed = now - last_request
                if elapsed < self.min_delay_seconds:
                    wait = self.min_delay_seconds - elapsed
                    logger.debug(f"⏱️  Aguardando {wait:.1f}s (delay mínimo)...")
                    await asyncio.sleep(wait)
                    now = time.time()

            self.request_times.append(now)
            logger.debug(f"📊 Rate limiter: {len(self.request_times)}/{self.max_requests_per_minute} requests no último minuto")


class InvestingService:
    """Serviço para buscar dados do Investing.com com batching e rate limiting"""

    # Data mínima: 1994-07-01 (início do Real)
    MIN_DATE = date(1994, 7, 1)

    # URLs dos ativos brasileiros no Investing.com - TOP 50 AÇÕES B3 2026
    INVESTING_URLS = {
        # === ÍNDICE ===
        '^BVSP': 'https://www.investing.com/indices/bovespa-historical-data',

        # === BANCOS (Top 5) ===
        'ITUB4': 'https://www.investing.com/equities/itau-unibanco-pn-historical-data',
        'BBDC4': 'https://www.investing.com/equities/bradesco-pn-historical-data',
        'BBAS3': 'https://www.investing.com/equities/bb-seguridade-on-nm-historical-data',
        'SANB11': 'https://www.investing.com/equities/santander-br-unit-historical-data',
        'BBSE3': 'https://www.investing.com/equities/bb-seguridade-on-nm-historical-data',

        # === PETRÓLEO & GÁS (Top 3) ===
        'PETR4': 'https://www.investing.com/equities/petrobras-historical-data',
        'PETR3': 'https://www.investing.com/equities/petrobras-on-nm-historical-data',
        'PRIO3': 'https://www.investing.com/equities/petrorio-on-nm-historical-data',

        # === MINERAÇÃO & SIDERURGIA (Top 6) ===
        'VALE3': 'https://www.investing.com/equities/vale-on-nm-historical-data',
        'GGBR4': 'https://www.investing.com/equities/gerdau-pn-historical-data',
        'CSNA3': 'https://www.investing.com/equities/cia-sider-nac-on-nm-historical-data',
        'USIM5': 'https://www.investing.com/equities/usiminas-pna-historical-data',
        'GOAU4': 'https://www.investing.com/equities/gerdau-met-pn-historical-data',
        'KLBN11': 'https://www.investing.com/equities/klabin-unit-historical-data',

        # === ENERGIA ELÉTRICA (Top 8) ===
        'ELET3': 'https://www.investing.com/equities/eletrobras-on-nm-historical-data',
        'ELET6': 'https://www.investing.com/equities/eletrobras-pnb-historical-data',
        'ENGI11': 'https://www.investing.com/equities/energisa-unit-historical-data',
        'CPLE6': 'https://www.investing.com/equities/copel-pnb-historical-data',
        'CMIG4': 'https://www.investing.com/equities/cemig-pn-historical-data',
        'EGIE3': 'https://www.investing.com/equities/engie-brasil-on-nm-historical-data',
        'TAEE11': 'https://www.investing.com/equities/taesa-unit-historical-data',
        'TRPL4': 'https://www.investing.com/equities/tran-paulist-pn-historical-data',

        # === VAREJO (Top 5) ===
        'MGLU3': 'https://www.investing.com/equities/magazine-luiza-on-nm-historical-data',
        'LREN3': 'https://www.investing.com/equities/lojas-renner-on-nm-historical-data',
        'ARZZ3': 'https://www.investing.com/equities/arezzo-on-nm-historical-data',
        'VVAR3': 'https://www.investing.com/equities/via-varejo-on-nm-historical-data',
        'PCAR3': 'https://www.investing.com/equities/grupo-pao-de-acucar-on-nm-historical-data',

        # === ALIMENTOS & BEBIDAS (Top 5) ===
        'ABEV3': 'https://www.investing.com/equities/ambev-on-nm-historical-data',
        'BRFS3': 'https://www.investing.com/equities/brf-sa-on-nm-historical-data',
        'JBSS3': 'https://www.investing.com/equities/jbs-on-nm-historical-data',
        'MRFG3': 'https://www.investing.com/equities/marfrig-on-nm-historical-data',
        'BEEF3': 'https://www.investing.com/equities/minerva-on-nm-historical-data',

        # === TELECOM (Top 2) ===
        'VIVT3': 'https://www.investing.com/equities/tef-brasil-pn-historical-data',
        'TIMS3': 'https://www.investing.com/equities/tim-participacoes-on-nm-historical-data',

        # === CONSTRUÇÃO CIVIL (Top 3) ===
        'CYRE3': 'https://www.investing.com/equities/cyrela-realt-on-nm-historical-data',
        'MRVE3': 'https://www.investing.com/equities/mrv-engenharia-on-nm-historical-data',
        'EZTC3': 'https://www.investing.com/equities/ez-tec-on-nm-historical-data',

        # === LOGÍSTICA & TRANSPORTE (Top 4) ===
        'RAIL3': 'https://www.investing.com/equities/rumo-on-nm-historical-data',
        'CCRO3': 'https://www.investing.com/equities/ccr-sa-on-nm-historical-data',
        'ECOR3': 'https://www.investing.com/equities/ecorodovias-on-nm-historical-data',
        'AZUL4': 'https://www.investing.com/equities/azul-pn-historical-data',

        # === SAÚDE (Top 3) ===
        'RADL3': 'https://www.investing.com/equities/rd-saude-on-nm-historical-data',
        'HAPV3': 'https://www.investing.com/equities/hapvida-on-nm-historical-data',
        'FLRY3': 'https://www.investing.com/equities/fleury-on-nm-historical-data',

        # === FINANCEIRAS & SERVIÇOS (Top 4) ===
        'B3SA3': 'https://www.investing.com/equities/b3-on-nm-historical-data',
        'RENT3': 'https://www.investing.com/equities/localiza-rent-a-car-on-nm-historical-data',
        'CIEL3': 'https://www.investing.com/equities/cielo-on-nm-historical-data',
        'PAGS34': 'https://www.investing.com/equities/pagseguro-bdr-historical-data',

        # === INDÚSTRIA & TECNOLOGIA (Top 4) ===
        'WEGE3': 'https://www.investing.com/equities/weg-on-nm-historical-data',
        'EMBR3': 'https://www.investing.com/equities/embraer-on-nm-historical-data',
        'SUZB3': 'https://www.investing.com/equities/suzano-on-nm-historical-data',
        'TOTS3': 'https://www.investing.com/equities/totvs-on-nm-historical-data',
    }

    # Alias para compatibilidade
    INVESTING_IDS = INVESTING_URLS

    def __init__(
        self,
        batch_size: int = 6,
        max_retries: int = 3,
        initial_backoff: float = 3.0
    ):
        """
        Args:
            batch_size: Número de ações por batch (padrão: 6)
            max_retries: Tentativas máximas por requisição (padrão: 3)
            initial_backoff: Backoff inicial em segundos (padrão: 3.0)
        """
        self.batch_size = batch_size
        self.max_retries = max_retries
        self.initial_backoff = initial_backoff

        # Rate limiter global
        self.rate_limiter = RateLimiter(
            max_requests_per_minute=10,
            min_delay_seconds=6.0
        )

        # Cloudscraper para bypass de Cloudflare
        self.scraper = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'windows',
                'mobile': False
            },
            delay=10  # Browser simulation delay
        )
        self.timeout = 30

    async def _retry_with_backoff(self, func, *args, **kwargs):
        """Executa função com retry e exponential backoff"""
        for attempt in range(self.max_retries):
            try:
                await self.rate_limiter.acquire()
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise

                backoff = self.initial_backoff * (2 ** attempt)
                logger.warning(
                    f"⚠️  Tentativa {attempt + 1}/{self.max_retries} falhou: {e}"
                )
                logger.info(f"   Aguardando {backoff:.1f}s antes de tentar novamente...")
                await asyncio.sleep(backoff)

    async def _fetch_with_scraping(
        self,
        url: str,
        start_date: datetime,
        end_date: datetime
    ) -> List[Dict]:
        """
        Busca dados via web scraping do Investing.com

        Args:
            url: URL do ativo no Investing.com
            start_date: Data inicial
            end_date: Data final

        Returns:
            Lista de registros OHLCV
        """
        loop = asyncio.get_event_loop()

        def scrape():
            logger.info(f"🌐 Scraping {url}...")

            response = self.scraper.get(url, timeout=self.timeout)

            if response.status_code != 200:
                raise Exception(f"HTTP {response.status_code}")

            html = response.text
            logger.debug(f"✅ Página carregada ({len(html)} bytes)")

            soup = BeautifulSoup(html, 'lxml')

            # Procurar tabela de dados históricos
            table = (
                soup.find('table', {'id': 'curr_table'}) or
                soup.find('table', {'data-test': 'historical-data-table'}) or
                soup.find('table', {'class': 'genTbl'}) or
                soup.find('table', {'class': 'historicalTbl'})
            )

            if not table:
                logger.warning("Tabela não encontrada, tentando estrutura alternativa...")
                # Tentar divs
                data_divs = soup.find_all('div', {'class': 'datatable_row'})
                if data_divs:
                    return self._parse_divs(data_divs, start_date, end_date)
                raise Exception("Dados históricos não encontrados na página")

            logger.info("📊 Tabela encontrada, parseando...")

            records = []
            rows = table.find_all('tr')[1:]  # Skip header

            for row in rows:
                try:
                    cols = row.find_all('td')
                    if len(cols) < 6:
                        continue

                    # Parse data
                    date_str = cols[0].get_text(strip=True)
                    date_obj = self._parse_date(date_str)

                    # Filtrar por intervalo
                    if date_obj < start_date.date() or date_obj > end_date.date():
                        continue

                    # Filtrar por MIN_DATE
                    if date_obj < self.MIN_DATE:
                        continue

                    # Parse valores (ordem: Data | Último | Abertura | Máxima | Mínima | Vol.)
                    record = {
                        'date': date_obj,
                        'close': self._parse_number(cols[1].get_text(strip=True)),
                        'open': self._parse_number(cols[2].get_text(strip=True)),
                        'high': self._parse_number(cols[3].get_text(strip=True)),
                        'low': self._parse_number(cols[4].get_text(strip=True)),
                        'volume': self._parse_volume(cols[5].get_text(strip=True))
                    }

                    records.append(record)

                except (ValueError, IndexError) as e:
                    logger.debug(f"Linha ignorada: {e}")
                    continue

            records.sort(key=lambda x: x['date'])
            logger.info(f"✅ {len(records)} registros parseados")
            return records

        result = await loop.run_in_executor(None, scrape)
        return result

    def _parse_divs(self, divs: list, start_date: datetime, end_date: datetime) -> List[Dict]:
        """Parse dados de estrutura alternativa (divs)"""
        records = []

        for div in divs:
            try:
                date_elem = div.find('div', {'class': 'datatable_cell__date'})
                if not date_elem:
                    continue

                date_obj = self._parse_date(date_elem.get_text(strip=True))

                if date_obj < start_date.date() or date_obj > end_date.date():
                    continue
                if date_obj < self.MIN_DATE:
                    continue

                cells = div.find_all('div', {'class': 'datatable_cell'})
                if len(cells) < 6:
                    continue

                record = {
                    'date': date_obj,
                    'close': self._parse_number(cells[1].get_text(strip=True)),
                    'open': self._parse_number(cells[2].get_text(strip=True)),
                    'high': self._parse_number(cells[3].get_text(strip=True)),
                    'low': self._parse_number(cells[4].get_text(strip=True)),
                    'volume': self._parse_volume(cells[5].get_text(strip=True))
                }

                records.append(record)

            except (ValueError, IndexError) as e:
                logger.debug(f"Div ignorado: {e}")
                continue

        records.sort(key=lambda x: x['date'])
        return records

    def _parse_date(self, date_str: str) -> date:
        """Parse data de vários formatos"""
        date_str = date_str.strip()

        months_pt = {
            'jan': '01', 'fev': '02', 'mar': '03', 'abr': '04',
            'mai': '05', 'jun': '06', 'jul': '07', 'ago': '08',
            'set': '09', 'out': '10', 'nov': '11', 'dez': '12'
        }

        date_lower = date_str.lower()
        for pt, num in months_pt.items():
            date_lower = date_lower.replace(pt, num)

        formats = [
            '%d/%m/%Y', '%m/%d/%Y', '%d-%m-%Y', '%Y-%m-%d',
            '%d 01 %Y', '%d.%m.%Y',
        ]

        for fmt in formats:
            try:
                return datetime.strptime(date_lower, fmt).date()
            except ValueError:
                continue

        try:
            return datetime.strptime(date_str, '%b %d, %Y').date()
        except ValueError:
            pass

        raise ValueError(f"Não foi possível parsear data: {date_str}")

    def _parse_number(self, value: str) -> float:
        """Parse número de string"""
        if not value or value.strip() in ['-', 'N/A', '', 'n/a']:
            return 0.0

        value = value.strip().replace('\xa0', '').replace(' ', '')
        value = value.replace('.', '').replace(',', '.')

        multipliers = {'K': 1_000, 'M': 1_000_000, 'B': 1_000_000_000, 'Mi': 1_000_000}
        for suffix, mult in multipliers.items():
            if value.upper().endswith(suffix.upper()):
                return float(value[:-len(suffix)]) * mult

        try:
            return float(value)
        except ValueError:
            return 0.0

    def _parse_volume(self, value: str) -> int:
        """Parse volume de string"""
        try:
            return int(self._parse_number(value))
        except (ValueError, TypeError):
            return 0

    async def fetch_ibovespa_historical(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict]:
        """
        Busca dados históricos do Ibovespa

        Args:
            start_date: Data inicial (padrão: 1994-07-01)
            end_date: Data final (padrão: hoje)

        Returns:
            Lista de registros diários
        """
        if end_date is None:
            end_date = datetime.now()
        if start_date is None:
            start_date = datetime(1994, 7, 1)

        if start_date.date() < self.MIN_DATE:
            start_date = datetime.combine(self.MIN_DATE, datetime.min.time())

        logger.info(f"📊 Buscando Ibovespa do Investing.com ({start_date.date()} a {end_date.date()})")

        try:
            records = await self._retry_with_backoff(
                self._fetch_with_scraping,
                self.INVESTING_URLS['^BVSP'],
                start_date,
                end_date
            )

            if records:
                logger.info(f"✅ {len(records)} registros do Ibovespa baixados")
                return records
            else:
                raise Exception("Nenhum dado retornado")

        except Exception as e:
            logger.error(f"❌ Falha ao buscar Ibovespa: {e}")
            raise

    async def fetch_stock_data(
        self,
        symbols: List[str],
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Dict]:
        """
        Busca dados de múltiplas ações em BATCHES

        Args:
            symbols: Lista de símbolos (e.g., ['PETR4', 'VALE3'])
            start_date: Data inicial (padrão: 1 ano atrás)
            end_date: Data final (padrão: hoje)

        Returns:
            Dict com símbolo como chave e dados como valor
        """
        if end_date is None:
            end_date = datetime.now()
        if start_date is None:
            start_date = end_date - timedelta(days=365)

        logger.info(f"📊 Buscando {len(symbols)} ações do Investing.com em batches...")
        logger.info(f"   Batch size: {self.batch_size}")
        logger.info(f"   Rate limit: {self.rate_limiter.max_requests_per_minute} req/min")

        results = {}
        total_batches = (len(symbols) + self.batch_size - 1) // self.batch_size

        # Dividir em batches
        for batch_idx in range(0, len(symbols), self.batch_size):
            batch = symbols[batch_idx:batch_idx + self.batch_size]
            current_batch = batch_idx // self.batch_size + 1

            logger.info(f"")
            logger.info(f"📦 BATCH {current_batch}/{total_batches}: {len(batch)} ações")
            logger.info(f"   Símbolos: {', '.join(batch)}")

            # Processar cada símbolo no batch
            for symbol in batch:
                try:
                    logger.info(f"   🔍 Processando {symbol}...")

                    # Verifica se tem URL no mapa
                    if symbol not in self.INVESTING_URLS:
                        logger.warning(f"   ⚠️  {symbol}: URL não encontrada no mapa, pulando")
                        continue

                    url = self.INVESTING_URLS[symbol]

                    # Tenta buscar com retry
                    prices_raw = await self._retry_with_backoff(
                        self._fetch_with_scraping,
                        url,
                        start_date,
                        end_date
                    )

                    if not prices_raw:
                        logger.warning(f"   ⚠️  {symbol}: Sem dados")
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
                        change_pct = ((latest['close'] - prev_close) / prev_close) * 100 if prev_close > 0 else 0.0
                    else:
                        change_pct = 0.0

                    results[symbol] = {
                        'symbol': symbol,
                        'name': symbol,
                        'price': latest['close'],
                        'change_percent': change_pct,
                        'volume': latest['volume'],
                        'prices': prices
                    }

                    logger.info(f"   ✅ {symbol}: {len(prices)} registros (último: R$ {latest['close']:.2f})")

                except Exception as e:
                    logger.error(f"   ❌ {symbol} falhou: {e}")
                    continue

            logger.info(f"📦 Batch {current_batch}/{total_batches} concluído ({len(results)}/{len(symbols)} sucessos até agora)")

        logger.info(f"")
        logger.info(f"✅ Download completo: {len(results)}/{len(symbols)} ações baixadas")
        return results

    async def fetch_single_stock(
        self,
        symbol: str,
        days: int = 365
    ) -> Optional[Dict]:
        """
        Busca dados de uma única ação

        Args:
            symbol: Símbolo da ação (e.g., 'PETR4')
            days: Número de dias de histórico

        Returns:
            Dict com dados da ação ou None se falhar
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        results = await self.fetch_stock_data([symbol], start_date, end_date)
        return results.get(symbol)

    async def test_connection(self) -> Dict:
        """Testa conexão com Investing.com"""
        try:
            # Testa com VALE3
            test_symbol = 'VALE3'
            logger.info(f"Testando conexão com Investing.com ({test_symbol})...")

            result = await self.fetch_single_stock(test_symbol, days=30)

            if result:
                return {
                    'status': 'ok',
                    'message': 'Conectado com sucesso ao Investing.com',
                    'method': 'web_scraping',
                    'test_symbol': test_symbol,
                    'records_fetched': len(result['prices']),
                    'latest_price': result['price']
                }
            else:
                return {
                    'status': 'warning',
                    'message': 'Conectado mas sem dados',
                    'test_symbol': test_symbol
                }

        except Exception as e:
            logger.error(f"Teste falhou: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }


# Instância global
investing_service = InvestingService(
    batch_size=6,          # 6 ações por batch
    max_retries=3,         # 3 tentativas
    initial_backoff=3.0    # 3s backoff inicial
)

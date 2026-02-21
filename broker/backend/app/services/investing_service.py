"""
Investing.com Data Service - ÚNICA FONTE DE DADOS

Busca dados históricos do Investing.com para o mercado brasileiro.
Critérios: dados a partir de 1994-07-01 (Real - R$)

Método: Web scraping com cloudscraper (bypass Cloudflare)
"""

import asyncio
import logging
from datetime import datetime, date
from typing import List, Dict, Optional
import cloudscraper
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class InvestingService:
    """Serviço para buscar dados do Investing.com"""

    # Data mínima: 1994-07-01 (início do Real)
    MIN_DATE = date(1994, 7, 1)

    # URL do Ibovespa
    IBOVESPA_URL = "https://www.investing.com/indices/bovespa-historical-data"

    def __init__(self):
        # Cloudscraper para bypass de Cloudflare
        self.scraper = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'windows',
                'mobile': False
            }
        )
        self.timeout = 30

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
        # Datas padrão
        if end_date is None:
            end_date = datetime.now()
        if start_date is None:
            start_date = datetime(1994, 7, 1)

        # Garantir que não seja antes de 1994
        if start_date.date() < self.MIN_DATE:
            start_date = datetime.combine(self.MIN_DATE, datetime.min.time())

        logger.info(f"📊 Buscando Ibovespa do Investing.com ({start_date.date()} a {end_date.date()})")

        try:
            records = await self._fetch_data(
                self.IBOVESPA_URL,
                start_date,
                end_date
            )

            if records:
                logger.info(f"✅ {len(records)} registros do Ibovespa baixados")
                return records
            else:
                raise Exception("Nenhum dado retornado")

        except Exception as e:
            logger.error(f"❌ Falha ao buscar dados: {e}")
            raise

    async def _fetch_data(
        self,
        url: str,
        start_date: datetime,
        end_date: datetime
    ) -> List[Dict]:
        """
        Busca dados de uma URL do Investing.com

        Usa cloudscraper para bypass de Cloudflare
        """
        loop = asyncio.get_event_loop()

        def scrape():
            logger.info(f"🌐 Acessando {url}...")

            # Requisição com cloudscraper
            response = self.scraper.get(url, timeout=self.timeout)

            if response.status_code != 200:
                raise Exception(f"HTTP {response.status_code}")

            html = response.text
            logger.info(f"✅ Página carregada ({len(html)} bytes)")

            # Parse HTML
            soup = BeautifulSoup(html, 'html.parser')

            # Procurar tabela de dados históricos
            # Investing.com usa diferentes estruturas dependendo da página
            table = (
                soup.find('table', {'id': 'curr_table'}) or
                soup.find('table', {'data-test': 'historical-data-table'}) or
                soup.find('table', {'class': 'genTbl'}) or
                soup.find('table', {'class': 'historicalTbl'})
            )

            if not table:
                logger.warning("Tabela não encontrada, tentando estrutura alternativa...")
                # Tentar encontrar divs com dados
                data_divs = soup.find_all('div', {'class': 'datatable_row'})
                if data_divs:
                    return self._parse_divs(data_divs, start_date, end_date)
                raise Exception("Não foi possível encontrar dados históricos na página")

            logger.info("📊 Tabela encontrada, parseando...")

            # Parse tabela
            records = []
            rows = table.find_all('tr')[1:]  # Pular cabeçalho

            for row in rows:
                try:
                    cols = row.find_all('td')
                    if len(cols) < 6:
                        continue

                    # Parse data
                    date_str = cols[0].get_text(strip=True)
                    date_obj = self._parse_date(date_str)

                    # Filtrar por intervalo de datas
                    if date_obj < start_date.date() or date_obj > end_date.date():
                        continue

                    # Filtrar por MIN_DATE (1994+)
                    if date_obj < self.MIN_DATE:
                        continue

                    # Parse valores (ordem pode variar)
                    # Formato comum: Data | Último | Abertura | Máxima | Mínima | Vol. | Var%
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

            # Ordenar por data (mais antiga primeiro)
            records.sort(key=lambda x: x['date'])

            logger.info(f"✅ {len(records)} registros parseados")
            return records

        records = await loop.run_in_executor(None, scrape)
        return records

    def _parse_divs(self, divs: list, start_date: datetime, end_date: datetime) -> List[Dict]:
        """Parse dados de estrutura alternativa (divs)"""
        records = []

        for div in divs:
            try:
                # Extrair informações dos divs
                date_elem = div.find('div', {'class': 'datatable_cell__date'})
                if not date_elem:
                    continue

                date_obj = self._parse_date(date_elem.get_text(strip=True))

                # Filtrar por datas
                if date_obj < start_date.date() or date_obj > end_date.date():
                    continue
                if date_obj < self.MIN_DATE:
                    continue

                # Outros campos
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

        # Mapeamento de meses em português
        months_pt = {
            'jan': '01', 'fev': '02', 'mar': '03', 'abr': '04',
            'mai': '05', 'jun': '06', 'jul': '07', 'ago': '08',
            'set': '09', 'out': '10', 'nov': '11', 'dez': '12'
        }

        # Substituir meses em português
        date_lower = date_str.lower()
        for pt, num in months_pt.items():
            date_lower = date_lower.replace(pt, num)

        formats = [
            '%d/%m/%Y',     # 15/01/2024
            '%m/%d/%Y',     # 01/15/2024
            '%d-%m-%Y',     # 15-01-2024
            '%Y-%m-%d',     # 2024-01-15
            '%d 01 %Y',     # 15 jan 2024 (após conversão)
            '%d.%m.%Y',     # 15.01.2024
        ]

        for fmt in formats:
            try:
                return datetime.strptime(date_lower, fmt).date()
            except ValueError:
                continue

        # Tentar formato "Jan 15, 2024"
        try:
            return datetime.strptime(date_str, '%b %d, %Y').date()
        except ValueError:
            pass

        raise ValueError(f"Não foi possível parsear data: {date_str}")

    def _parse_number(self, value: str) -> float:
        """Parse número de string"""
        if not value or value.strip() in ['-', 'N/A', '', 'n/a']:
            return 0.0

        # Remover espaços e símbolos
        value = value.strip().replace('\xa0', '').replace(' ', '')

        # Investing.com usa ponto para milhares e vírgula para decimais (formato europeu)
        # Exemplo: 123.456,78
        value = value.replace('.', '').replace(',', '.')

        # Handle K, M, B multipliers
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

    async def test_connection(self) -> Dict:
        """Testa conexão com Investing.com"""
        try:
            loop = asyncio.get_event_loop()

            def test():
                response = self.scraper.get(self.IBOVESPA_URL, timeout=10)

                if response.status_code == 200:
                    return {
                        'status': 'ok',
                        'message': 'Conectado com sucesso ao Investing.com',
                        'cloudflare_bypass': True,
                        'response_size': len(response.text)
                    }
                else:
                    return {
                        'status': 'error',
                        'message': f'HTTP {response.status_code}'
                    }

            result = await loop.run_in_executor(None, test)
            return result

        except Exception as e:
            return {
                'status': 'error',
                'message': str(e)
            }


# Instância global
investing_service = InvestingService()

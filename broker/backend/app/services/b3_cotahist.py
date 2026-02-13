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
import pandas as pd
from b3fileparser.b3parser import B3Parser


class B3CotahistService:
    """Service to download and parse B3 COTAHIST files"""

    # Direct download URL pattern for B3 COTAHIST files
    # Source: https://bvmf.bmfbovespa.com.br/InstDados/SerHist/
    BASE_URL = "https://bvmf.bmfbovespa.com.br/InstDados/SerHist/COTAHIST_A{year}.ZIP"

    def __init__(self, cache_dir: Optional[Path] = None):
        self.cache_dir = cache_dir or Path("data/cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.parser = B3Parser.create_parser(engine='pandas')

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

        async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
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

    def parse_cotahist(self, txt_content: str) -> pd.DataFrame:
        """
        Parse COTAHIST TXT content using b3fileparser

        Args:
            txt_content: Content of COTAHIST TXT file

        Returns:
            DataFrame with parsed stock data
        """
        # Save to temporary file (b3fileparser reads from file)
        temp_file = self.cache_dir / "temp_cotahist.txt"
        temp_file.write_text(txt_content, encoding='latin-1')

        print("Parsing COTAHIST file...")
        df = self.parser.read_b3_file(str(temp_file))

        # Clean up temp file
        temp_file.unlink()

        print(f"Parsed {len(df):,} records")
        return df

    def filter_vista_stocks(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Filter only spot market (VISTA) stocks from COTAHIST data

        TIPO_DE_MERCADO codes:
        - 10: VISTA (spot market)
        - 20: FRACIONARIO (fractional)
        - 70: OPCOES_DE_COMPRA (call options)
        - 80: OPCOES_DE_VENDA (put options)

        Args:
            df: Full COTAHIST DataFrame

        Returns:
            Filtered DataFrame with only VISTA stocks
        """
        # Filter spot market only
        vista_df = df[df['TIPO_DE_MERCADO'] == 10].copy()

        # Filter out options and other derivatives (keep only stocks ending in digits)
        # Example: PETR4, VALE3, ITUB4 (not PETRB, VALEPA, etc.)
        vista_df = vista_df[
            vista_df['CODIGO_DE_NEGOCIACAO'].str.match(r'^[A-Z]{4}\d{1,2}$')
        ]

        print(f"Filtered to {len(vista_df):,} VISTA stock records")
        return vista_df

    async def get_stock_data(self, year: int, symbols: Optional[list[str]] = None) -> pd.DataFrame:
        """
        Get stock data for specific symbols and year

        Args:
            year: Year to get data for
            symbols: Optional list of stock symbols (e.g., ['PETR4', 'VALE3'])
                    If None, returns all stocks

        Returns:
            DataFrame with filtered stock data
        """
        # Check cache
        cache_file = self.cache_dir / f"cotahist_{year}.parquet"
        if cache_file.exists():
            print(f"Loading from cache: {cache_file}")
            df = pd.read_parquet(cache_file)
        else:
            # Download and parse
            zip_content = await self.download_cotahist(year)
            txt_content = self.extract_txt_from_zip(zip_content)
            df = self.parse_cotahist(txt_content)
            df = self.filter_vista_stocks(df)

            # Save to cache
            df.to_parquet(cache_file)
            print(f"Cached to {cache_file}")

        # Filter by symbols if provided
        if symbols:
            df = df[df['CODIGO_DE_NEGOCIACAO'].isin(symbols)]
            print(f"Filtered to {len(symbols)} symbols: {len(df):,} records")

        return df

    def df_to_stock_records(self, df: pd.DataFrame) -> dict[str, dict]:
        """
        Convert B3 DataFrame to stock records grouped by symbol

        Args:
            df: COTAHIST DataFrame

        Returns:
            Dictionary with symbol as key and stock info + prices as value
        """
        stocks = {}

        for symbol in df['CODIGO_DE_NEGOCIACAO'].unique():
            symbol_df = df[df['CODIGO_DE_NEGOCIACAO'] == symbol].copy()

            # Sort by date
            symbol_df = symbol_df.sort_values('DATA_DO_PREGAO')

            # Get latest price for current quote
            latest = symbol_df.iloc[-1]

            # Calculate change percent (comparing last two days)
            if len(symbol_df) >= 2:
                prev_close = symbol_df.iloc[-2]['PRECO_ULTIMO_NEGOCIO'] / 100
                curr_close = latest['PRECO_ULTIMO_NEGOCIO'] / 100
                change_percent = ((curr_close - prev_close) / prev_close) * 100
            else:
                change_percent = 0.0

            # Build stock record
            stocks[symbol] = {
                'symbol': symbol,
                'name': latest['NOME_RESUMIDO_DA_EMPRESA_EMISSORA'].strip(),
                'price': latest['PRECO_ULTIMO_NEGOCIO'] / 100,  # B3 prices are in cents
                'change_percent': change_percent,
                'volume': int(latest['VOLUME_TOTAL_NEGOCIADO']),
                'prices': [
                    {
                        'date': row['DATA_DO_PREGAO'].strftime('%Y-%m-%d'),
                        'open': row['PRECO_DE_ABERTURA'] / 100,
                        'high': row['PRECO_MAXIMO'] / 100,
                        'low': row['PRECO_MINIMO'] / 100,
                        'close': row['PRECO_ULTIMO_NEGOCIO'] / 100,
                        'volume': int(row['VOLUME_TOTAL_NEGOCIADO']),
                    }
                    for _, row in symbol_df.iterrows()
                ]
            }

        return stocks


# Singleton instance
b3_service = B3CotahistService()

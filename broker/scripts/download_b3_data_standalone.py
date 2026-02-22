#!/usr/bin/env python3
"""
Script standalone para download de dados históricos da B3
Funciona independentemente, salvando dados em arquivos CSV

Uso: python download_b3_data_standalone.py
"""

import yfinance as yf
import pandas as pd
from datetime import datetime
import os
import sys

# Lista das principais ações do Ibovespa
IBOV_STOCKS = [
    'PETR4.SA', 'VALE3.SA', 'ITUB4.SA', 'BBDC4.SA', 'ABEV3.SA',
    'B3SA3.SA', 'WEGE3.SA', 'RENT3.SA', 'BBAS3.SA', 'SUZB3.SA',
    'ELET3.SA', 'VIVT3.SA', 'PRIO3.SA', 'COGN3.SA', 'MGLU3.SA',
    'JBSS3.SA', 'RAIL3.SA', 'RADL3.SA', 'EMBR3.SA', 'CSAN3.SA',
    'HAPV3.SA', 'GGBR4.SA', 'LREN3.SA', 'BEEF3.SA', 'BRAP4.SA',
    'SBSP3.SA', 'CYRE3.SA', 'ARZZ3.SA', 'MRFG3.SA', 'CRFB3.SA'
]


def download_stock_data(symbol, start_date='1994-01-01', end_date=None):
    """Baixa dados históricos de uma ação"""
    if end_date is None:
        end_date = datetime.now().strftime('%Y-%m-%d')

    try:
        print(f"📥 Baixando {symbol}...", end=' ')
        ticker = yf.Ticker(symbol)
        df = ticker.history(start=start_date, end=end_date)

        if df.empty:
            print("❌ Sem dados")
            return None

        # Adiciona coluna do símbolo
        df['Symbol'] = symbol.replace('.SA', '')

        # Renomeia colunas para português
        df = df.rename(columns={
            'Open': 'Abertura',
            'High': 'Maxima',
            'Low': 'Minima',
            'Close': 'Fechamento',
            'Volume': 'Volume'
        })

        # Mantém apenas as colunas necessárias
        df = df[['Symbol', 'Abertura', 'Maxima', 'Minima', 'Fechamento', 'Volume']]

        print(f"✅ {len(df)} registros")
        return df

    except Exception as e:
        print(f"❌ Erro: {e}")
        return None


def download_ibovespa(start_date='1994-01-01', end_date=None):
    """Baixa dados históricos do índice Ibovespa"""
    if end_date is None:
        end_date = datetime.now().strftime('%Y-%m-%d')

    try:
        print(f"📥 Baixando IBOVESPA...", end=' ')
        ticker = yf.Ticker('^BVSP')
        df = ticker.history(start=start_date, end=end_date)

        if df.empty:
            print("❌ Sem dados")
            return None

        # Renomeia colunas
        df = df.rename(columns={
            'Close': 'Fechamento'
        })

        df = df[['Fechamento']]
        print(f"✅ {len(df)} registros")
        return df

    except Exception as e:
        print(f"❌ Erro: {e}")
        return None


def main():
    print("=" * 70)
    print("🔥 DOWNLOAD DE DADOS HISTÓRICOS DA B3 🔥")
    print("=" * 70)

    # Cria pasta para os dados
    output_dir = 'dados_b3'
    os.makedirs(output_dir, exist_ok=True)

    # Solicita período
    print("\n📅 PERÍODO DE DOWNLOAD:")
    start_year = input("   Ano inicial (padrão: 1994): ").strip() or "1994"
    end_year = input("   Ano final (padrão: atual): ").strip() or str(datetime.now().year)

    start_date = f"{start_year}-01-01"
    end_date = f"{end_year}-12-31"

    print(f"\n✅ Período: {start_date} até {end_date}")
    print(f"✅ Total de ações: {len(IBOV_STOCKS)}")
    print(f"✅ Dados serão salvos em: {os.path.abspath(output_dir)}")

    confirm = input("\n👉 Confirmar download? (S/n): ").strip().lower()
    if confirm and confirm != 's':
        print("❌ Cancelado!")
        sys.exit(0)

    # Baixa Ibovespa
    print("\n📊 BAIXANDO ÍNDICE IBOVESPA:")
    ibov_df = download_ibovespa(start_date, end_date)
    if ibov_df is not None:
        ibov_file = os.path.join(output_dir, 'ibovespa.csv')
        ibov_df.to_csv(ibov_file)
        print(f"   Salvo em: {ibov_file}")

    # Baixa ações
    print(f"\n📈 BAIXANDO {len(IBOV_STOCKS)} AÇÕES:")
    all_data = []
    success_count = 0

    for i, symbol in enumerate(IBOV_STOCKS, 1):
        print(f"   [{i}/{len(IBOV_STOCKS)}] ", end='')
        df = download_stock_data(symbol, start_date, end_date)

        if df is not None:
            all_data.append(df)
            success_count += 1

    # Salva todos os dados
    if all_data:
        print(f"\n💾 SALVANDO DADOS...")
        combined_df = pd.concat(all_data, ignore_index=True)
        output_file = os.path.join(output_dir, 'acoes_b3.csv')
        combined_df.to_csv(output_file, index=False)

        print(f"\n✅ DOWNLOAD CONCLUÍDO!")
        print(f"   ✅ {success_count}/{len(IBOV_STOCKS)} ações baixadas com sucesso")
        print(f"   ✅ {len(combined_df):,} registros totais")
        print(f"   ✅ Arquivo: {os.path.abspath(output_file)}")
        print(f"\n📁 Dados salvos em: {os.path.abspath(output_dir)}")
        print(f"   - acoes_b3.csv (ações)")
        print(f"   - ibovespa.csv (índice)")

    else:
        print("\n❌ Nenhum dado foi baixado!")


if __name__ == "__main__":
    try:
        import yfinance
        import pandas
    except ImportError:
        print("❌ Pacotes necessários não instalados!")
        print("\n📦 Execute primeiro:")
        print("   pip install yfinance pandas")
        sys.exit(1)

    main()

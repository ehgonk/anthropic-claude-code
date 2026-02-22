#!/usr/bin/env python3
"""
Script STANDALONE para download de dados históricos via Yahoo Finance
NÃO PRECISA DO BACKEND RODANDO!

Uso: python scripts/download_data_standalone.py [opção]
"""

import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
import time

# Adicionar o diretório backend ao path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

try:
    import yfinance as yf
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import sessionmaker
    import requests
except ImportError:
    print("\n❌ ERRO: Dependências não instaladas!")
    print("\nExecute primeiro:")
    print("  cd backend")
    print("  pip install -r requirements.txt")
    print()
    sys.exit(1)

# Configurar sessão do yfinance com User-Agent
session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
})

# Configurações
DATABASE_PATH = backend_path / "data" / "broker.db"
HISTORICAL_START_YEAR = 2000  # Ano inicial (2000 = início do Real estável)
BATCH_SIZE_YEARS = 3
BATCH_DELAY_SECONDS = 5  # Aumentado para evitar rate limiting
STOCK_DELAY_SECONDS = 3  # Delay entre ações (aumentado para evitar rate limiting)
MAX_RETRIES = 3  # Número máximo de tentativas por ação

# Modo SLOW - para evitar rate limiting agressivo do Yahoo Finance
SLOW_MODE_ENABLED = False  # Ativar com parâmetro --slow
SLOW_MODE_STOCK_DELAY = 10  # Delay entre ações no modo slow
SLOW_MODE_BATCH_DELAY = 30  # Delay entre batches no modo slow

# Lista de ações principais do Ibovespa
MAIN_STOCKS = [
    "PETR4.SA", "VALE3.SA", "ITUB4.SA", "BBDC4.SA", "ABEV3.SA",
    "B3SA3.SA", "RENT3.SA", "BBAS3.SA", "SUZB3.SA", "ELET3.SA",
    "VIVT3.SA", "PRIO3.SA", "COGN3.SA", "MGLU3.SA", "WEGE3.SA",
    "RADL3.SA", "RAIL3.SA", "EMBR3.SA", "KLBN11.SA", "GGBR4.SA",
    "JBSS3.SA", "BEEF3.SA", "HAPV3.SA", "LREN3.SA", "TOTS3.SA",
    "CSAN3.SA", "SBSP3.SA", "CYRE3.SA", "ENBR3.SA", "TAEE11.SA"
]


def setup_database():
    """Cria o banco de dados e tabelas se não existirem"""
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

    engine = create_engine(f"sqlite:///{DATABASE_PATH}")

    with engine.connect() as conn:
        # Verificar se a tabela existe e tem o schema correto
        try:
            result = conn.execute(text("SELECT symbol, date FROM stock_prices LIMIT 1"))
            result.fetchone()
        except Exception:
            # Schema incompatível ou tabela não existe - recriar
            print("   ⚠️  Schema incompatível detectado. Recriando tabela...")
            conn.execute(text("DROP TABLE IF EXISTS stock_prices"))
            conn.commit()

        # Criar tabela stock_prices se não existir
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS stock_prices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol VARCHAR(10) NOT NULL,
                date DATE NOT NULL,
                open DECIMAL(10, 2),
                high DECIMAL(10, 2),
                low DECIMAL(10, 2),
                close DECIMAL(10, 2),
                volume BIGINT,
                source VARCHAR(50) DEFAULT 'yahoo_finance',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(symbol, date)
            )
        """))

        # Criar índices
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_symbol ON stock_prices(symbol)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_date ON stock_prices(date)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_symbol_date ON stock_prices(symbol, date)"))

        conn.commit()

    return engine


def get_stats(engine):
    """Obtém estatísticas do banco de dados"""
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT
                COUNT(*) as total_records,
                COUNT(DISTINCT symbol) as total_stocks,
                MIN(date) as first_date,
                MAX(date) as last_date
            FROM stock_prices
        """)).fetchone()

        years_result = conn.execute(text("""
            SELECT DISTINCT strftime('%Y', date) as year
            FROM stock_prices
            ORDER BY year
        """)).fetchall()

        years = [int(row[0]) for row in years_result] if years_result else []

        return {
            'total_records': result[0] if result else 0,
            'total_stocks': result[1] if result else 0,
            'first_date': result[2] if result else None,
            'last_date': result[3] if result else None,
            'years': years,
            'coverage_complete': len(years) >= (datetime.now().year - HISTORICAL_START_YEAR)
        }


def print_stats(stats):
    """Imprime estatísticas formatadas"""
    print("\n📊 ESTATÍSTICAS DO BANCO DE DADOS:")
    print(f"   Fonte de dados: Yahoo Finance")
    print(f"   Total de registros: {stats['total_records']:,}")
    print(f"   Total de ações: {stats['total_stocks']}")
    print(f"   Primeira data: {stats['first_date'] or 'None'}")
    print(f"   Última data: {stats['last_date'] or 'None'}")
    print(f"   Cobertura completa: {'✅' if stats['coverage_complete'] else '❌'}")

    if stats['years']:
        years_str = ', '.join(map(str, stats['years'][:10]))
        if len(stats['years']) > 10:
            years_str += f", ... ({len(stats['years'])} anos total)"
        print(f"   Anos: {years_str}")
    else:
        print(f"   Anos: ")
    print()


def wait_for_rate_limit_reset(wait_minutes=15):
    """Aguarda o rate limit do Yahoo Finance expirar"""
    print(f"\n⏳ Aguardando {wait_minutes} minutos para rate limit expirar...")
    for remaining in range(wait_minutes * 60, 0, -30):
        mins = remaining // 60
        secs = remaining % 60
        print(f"   ⏱️  Tempo restante: {mins}m {secs}s", end='\r', flush=True)
        time.sleep(min(30, remaining))
    print("\n   ✅ Pronto para continuar!                    ")


def download_stock_data(symbol, start_date, end_date, retry_count=0):
    """Baixa dados de uma ação específica via yfinance com retry automático"""
    try:
        # Usar sessão configurada com User-Agent
        ticker = yf.Ticker(symbol, session=session)
        df = ticker.history(start=start_date, end=end_date, timeout=10)

        if df.empty:
            return []

        # Limpar símbolo (.SA)
        clean_symbol = symbol.replace('.SA', '')

        records = []
        for date, row in df.iterrows():
            records.append({
                'symbol': clean_symbol,
                'date': date.strftime('%Y-%m-%d'),
                'open': round(float(row['Open']), 2),
                'high': round(float(row['High']), 2),
                'low': round(float(row['Low']), 2),
                'close': round(float(row['Close']), 2),
                'volume': int(row['Volume']),
                'source': 'yahoo_finance'
            })

        return records

    except KeyboardInterrupt:
        raise  # Re-raise keyboard interrupt to allow clean exit
    except Exception as e:
        # Retry com backoff exponencial
        if retry_count < MAX_RETRIES:
            wait_time = 2 ** retry_count  # 1s, 2s, 4s
            if retry_count == 0:  # Mostrar erro apenas na primeira tentativa
                print(f"⚠️ Tentando novamente ({retry_count + 1}/{MAX_RETRIES})...", end=" ", flush=True)
            time.sleep(wait_time)
            return download_stock_data(symbol, start_date, end_date, retry_count + 1)
        # Após esgotar tentativas, retornar vazio
        return []


def insert_records(engine, records):
    """Insere registros no banco de dados"""
    if not records:
        return 0

    inserted = 0
    with engine.connect() as conn:
        for record in records:
            try:
                conn.execute(text("""
                    INSERT OR IGNORE INTO stock_prices
                    (symbol, date, open, high, low, close, volume, source)
                    VALUES
                    (:symbol, :date, :open, :high, :low, :close, :volume, :source)
                """), record)
                inserted += 1
            except Exception:
                pass

        conn.commit()

    return inserted


def download_batch(engine, years, batch_num, total_batches, slow_mode=False):
    """Baixa dados de um batch de anos"""
    start_year = min(years)
    end_year = max(years)

    start_date = f"{start_year}-01-01"
    end_date = f"{end_year}-12-31"

    # Determinar delays baseado no modo
    stock_delay = SLOW_MODE_STOCK_DELAY if slow_mode else STOCK_DELAY_SECONDS
    batch_delay = SLOW_MODE_BATCH_DELAY if slow_mode else BATCH_DELAY_SECONDS

    mode_label = " (MODO SLOW 🐌)" if slow_mode else ""
    print(f"\n📦 Batch {batch_num}/{total_batches}: {start_year}-{end_year}{mode_label}")
    print(f"   Período: {start_date} a {end_date}")
    print(f"   Baixando {len(MAIN_STOCKS)} ações...")
    if slow_mode:
        print(f"   ⏱️  Delay: {stock_delay}s entre ações, {batch_delay}s entre batches")

    total_records = 0
    successful_stocks = 0

    for i, symbol in enumerate(MAIN_STOCKS, 1):
        clean_symbol = symbol.replace('.SA', '')
        print(f"   [{i}/{len(MAIN_STOCKS)}] {clean_symbol}...", end=" ", flush=True)

        records = download_stock_data(symbol, start_date, end_date)

        if records:
            inserted = insert_records(engine, records)
            total_records += inserted
            successful_stocks += 1
            print(f"✓ {len(records)} registros")
        else:
            print(f"✗ Sem dados")

        # Delay entre ações para evitar rate limiting
        if i < len(MAIN_STOCKS):  # Não esperar após a última ação
            time.sleep(stock_delay)

    print(f"\n   ✅ Batch concluído: {total_records:,} registros de {successful_stocks} ações")

    return total_records, successful_stocks


def download_all(engine, slow_mode=False):
    """Baixa todos os dados históricos em batches"""
    current_year = datetime.now().year

    # Criar lista de anos desde 1994 até ano atual
    all_years = list(range(HISTORICAL_START_YEAR, current_year + 1))

    # Dividir em batches
    batches = []
    for i in range(0, len(all_years), BATCH_SIZE_YEARS):
        batch_years = all_years[i:i + BATCH_SIZE_YEARS]
        batches.append(batch_years)

    batch_delay = SLOW_MODE_BATCH_DELAY if slow_mode else BATCH_DELAY_SECONDS
    mode_label = " (MODO SLOW 🐌)" if slow_mode else ""

    print(f"\n{'='*60}")
    print(f"📥 DOWNLOAD COMPLETO VIA YAHOO FINANCE{mode_label}")
    print(f"{'='*60}")
    print(f"\n   📅 Período: {HISTORICAL_START_YEAR} até {current_year}")
    print(f"   📦 Total de batches: {len(batches)}")
    print(f"   📈 Ações: {len(MAIN_STOCKS)}")
    print(f"   ⏱️  Delay entre batches: {batch_delay}s")
    if slow_mode:
        print(f"   🐌 Modo SLOW ativo para evitar rate limiting")
    print(f"\n{'='*60}\n")

    total_records_all = 0
    total_stocks_all = 0

    for i, batch_years in enumerate(batches, 1):
        records, stocks = download_batch(engine, batch_years, i, len(batches), slow_mode)
        total_records_all += records
        total_stocks_all += stocks

        # Delay entre batches (exceto no último)
        if i < len(batches):
            print(f"\n   ⏳ Aguardando {batch_delay}s antes do próximo batch...")
            time.sleep(batch_delay)

    print(f"\n{'='*60}")
    print(f"✅ DOWNLOAD COMPLETO!")
    print(f"{'='*60}")
    print(f"\n   📊 Total de registros inseridos: {total_records_all:,}")
    print(f"   📈 Total de ações processadas: {len(MAIN_STOCKS)}")
    print(f"   📦 Total de batches: {len(batches)}")
    print(f"\n{'='*60}\n")


def download_year(engine, year):
    """Baixa dados de um ano específico"""
    print(f"\n📅 BAIXANDO DADOS DE {year}...\n")

    start_date = f"{year}-01-01"
    end_date = f"{year}-12-31"

    total_records = 0

    for i, symbol in enumerate(MAIN_STOCKS, 1):
        clean_symbol = symbol.replace('.SA', '')
        print(f"   [{i}/{len(MAIN_STOCKS)}] {clean_symbol}...", end=" ", flush=True)

        records = download_stock_data(symbol, start_date, end_date)

        if records:
            inserted = insert_records(engine, records)
            total_records += inserted
            print(f"✓ {len(records)} registros")
        else:
            print(f"✗ Sem dados")

        # Delay entre ações
        time.sleep(STOCK_DELAY_SECONDS)

    print(f"\n✅ CONCLUÍDO!")
    print(f"   Registros inseridos: {total_records:,}\n")


def download_test(engine):
    """Testa download com poucas ações nos últimos 6 meses"""
    print("\n🧪 MODO DE TESTE - Últimos 6 meses, 5 ações...\n")

    end_date = datetime.now()
    start_date = end_date - timedelta(days=180)  # ~6 meses

    # Apenas 5 ações principais para teste
    test_stocks = ['PETR4.SA', 'VALE3.SA', 'ITUB4.SA', 'BBDC4.SA', 'B3SA3.SA']

    total_records = 0
    successful = 0

    for i, symbol in enumerate(test_stocks, 1):
        clean_symbol = symbol.replace('.SA', '')
        print(f"   [{i}/{len(test_stocks)}] {clean_symbol}...", end=" ", flush=True)

        records = download_stock_data(
            symbol,
            start_date.strftime('%Y-%m-%d'),
            end_date.strftime('%Y-%m-%d')
        )

        if records:
            inserted = insert_records(engine, records)
            total_records += inserted
            successful += 1
            print(f"✓ {len(records)} registros")
        else:
            print(f"✗ Sem dados")

        time.sleep(1)  # Delay menor para teste

    print(f"\n✅ TESTE CONCLUÍDO!")
    print(f"   Ações com sucesso: {successful}/{len(test_stocks)}")
    print(f"   Registros inseridos: {total_records:,}")

    if successful == 0:
        print("\n⚠️  AVISO: Nenhuma ação foi baixada com sucesso!")
        print("   Possíveis causas:")
        print("   - Bloqueio do Yahoo Finance")
        print("   - Problema de rede")
        print("   - Necessário usar VPN")
    elif successful < len(test_stocks):
        print(f"\n⚠️  AVISO: Apenas {successful} de {len(test_stocks)} ações funcionaram")
    else:
        print("\n✅ Tudo funcionando! Pode rodar 'all' para download completo")
    print()


def download_daily(engine):
    """Baixa dados dos últimos 7 dias"""
    print("\n📅 ATUALIZANDO DADOS DIÁRIOS (últimos 7 dias)...\n")

    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)

    total_records = 0

    for i, symbol in enumerate(MAIN_STOCKS, 1):
        clean_symbol = symbol.replace('.SA', '')
        print(f"   [{i}/{len(MAIN_STOCKS)}] {clean_symbol}...", end=" ", flush=True)

        records = download_stock_data(
            symbol,
            start_date.strftime('%Y-%m-%d'),
            end_date.strftime('%Y-%m-%d')
        )

        if records:
            inserted = insert_records(engine, records)
            total_records += inserted
            print(f"✓ {len(records)} registros")
        else:
            print(f"✗ Sem dados")

        # Delay entre ações
        time.sleep(STOCK_DELAY_SECONDS)

    print(f"\n✅ CONCLUÍDO!")
    print(f"   Registros inseridos: {total_records:,}\n")


def main():
    """Função principal"""
    if len(sys.argv) < 2:
        print("\n🔥 BROKER - Download Standalone via Yahoo Finance")
        print("\n⚡ Este script NÃO precisa do backend rodando!")
        print("\nUso:")
        print("  python scripts/download_data_standalone.py stats          # Ver estatísticas")
        print("  python scripts/download_data_standalone.py test           # TESTAR com 5 ações (6 meses)")
        print("  python scripts/download_data_standalone.py all            # Baixar tudo (2000-2026)")
        print("  python scripts/download_data_standalone.py all --slow     # Modo SLOW (delays maiores)")
        print("  python scripts/download_data_standalone.py wait [minutos] # Aguardar rate limit expirar")
        print("  python scripts/download_data_standalone.py year 2023      # Baixar ano específico")
        print("  python scripts/download_data_standalone.py daily          # Atualizar últimos 7 dias")
        print("\n💡 Dicas:")
        print("   - Execute 'test' primeiro para verificar se está funcionando!")
        print("   - Use 'wait 15' se receber erro 429 (Too Many Requests)")
        print("   - Use '--slow' para evitar rate limiting agressivo")
        print()
        sys.exit(1)

    command = sys.argv[1]

    # Verificar se é comando wait
    if command == "wait":
        minutes = int(sys.argv[2]) if len(sys.argv) > 2 else 15
        wait_for_rate_limit_reset(minutes)
        return

    # Verificar modo slow
    slow_mode = "--slow" in sys.argv

    # Setup database
    print("\n🔧 Configurando banco de dados...")
    engine = setup_database()
    print("   ✅ Banco configurado\n")

    if command == "stats":
        stats = get_stats(engine)
        print_stats(stats)

    elif command == "test":
        download_test(engine)

    elif command == "all":
        stats = get_stats(engine)
        print_stats(stats)
        download_all(engine, slow_mode)
        stats = get_stats(engine)
        print_stats(stats)

    elif command == "year" and len(sys.argv) == 3:
        year = int(sys.argv[2])
        download_year(engine, year)
        stats = get_stats(engine)
        print_stats(stats)

    elif command == "daily":
        download_daily(engine)
        stats = get_stats(engine)
        print_stats(stats)

    else:
        print("❌ Comando inválido!")
        sys.exit(1)


if __name__ == "__main__":
    main()

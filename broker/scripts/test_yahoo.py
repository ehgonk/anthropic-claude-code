#!/usr/bin/env python3
"""
Script de diagnóstico para testar conexão com Yahoo Finance
"""

import sys
from pathlib import Path

# Adicionar o diretório backend ao path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

try:
    import yfinance as yf
    import requests
    from datetime import datetime, timedelta
except ImportError:
    print("\n❌ ERRO: Dependências não instaladas!")
    print("\nExecute primeiro:")
    print("  cd backend")
    print("  pip install -r requirements.txt")
    print()
    sys.exit(1)

print("\n🔍 DIAGNÓSTICO DE CONEXÃO COM YAHOO FINANCE\n")
print("="*60)

# 1. Testar requests básico
print("\n1️⃣  Testando conexão básica com Yahoo Finance...")
try:
    response = requests.get("https://finance.yahoo.com", timeout=5)
    print(f"   Status: {response.status_code}")
    print(f"   ✅ Conexão OK")
except Exception as e:
    print(f"   ❌ Erro: {e}")

# 2. Testar com User-Agent
print("\n2️⃣  Testando com User-Agent...")
try:
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    })
    response = session.get("https://finance.yahoo.com", timeout=5)
    print(f"   Status: {response.status_code}")
    print(f"   ✅ Conexão OK com User-Agent")
except Exception as e:
    print(f"   ❌ Erro: {e}")

# 3. Testar yfinance sem sessão customizada
print("\n3️⃣  Testando yfinance padrão (PETR4.SA)...")
try:
    ticker = yf.Ticker("PETR4.SA")
    info = ticker.info
    print(f"   ✅ Info obtida: {info.get('longName', 'N/A')}")
except Exception as e:
    print(f"   ❌ Erro: {e}")

# 4. Testar yfinance com sessão customizada
print("\n4️⃣  Testando yfinance com sessão customizada (PETR4.SA)...")
try:
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    })
    ticker = yf.Ticker("PETR4.SA", session=session)
    info = ticker.info
    print(f"   ✅ Info obtida: {info.get('longName', 'N/A')}")
except Exception as e:
    print(f"   ❌ Erro: {e}")

# 5. Testar download de histórico recente
print("\n5️⃣  Testando download de histórico (últimos 30 dias)...")
try:
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    })
    ticker = yf.Ticker("PETR4.SA", session=session)

    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)

    df = ticker.history(start=start_date.strftime('%Y-%m-%d'),
                       end=end_date.strftime('%Y-%m-%d'))

    if df.empty:
        print("   ❌ DataFrame vazio")
    else:
        print(f"   ✅ Dados obtidos: {len(df)} registros")
        print(f"   Primeiro dia: {df.index[0]}")
        print(f"   Último dia: {df.index[-1]}")
        print(f"   Último close: R$ {df['Close'].iloc[-1]:.2f}")
except Exception as e:
    print(f"   ❌ Erro: {e}")

# 6. Testar download de período antigo (2000-2002)
print("\n6️⃣  Testando período antigo (2000-2002)...")
try:
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    })
    ticker = yf.Ticker("PETR4.SA", session=session)

    df = ticker.history(start='2000-01-01', end='2002-12-31')

    if df.empty:
        print("   ⚠️  Sem dados para período antigo (esperado)")
    else:
        print(f"   ✅ Dados obtidos: {len(df)} registros")
        print(f"   Primeiro dia: {df.index[0]}")
        print(f"   Último dia: {df.index[-1]}")
except Exception as e:
    print(f"   ❌ Erro: {e}")

print("\n" + "="*60)
print("\n💡 RECOMENDAÇÕES:")
print("   - Se teste 1-2 falham: Problema de rede/firewall")
print("   - Se teste 3-4 falham: Problema com yfinance")
print("   - Se teste 5 falha: Yahoo Finance pode estar bloqueando")
print("   - Se teste 6 falha: Dados antigos não disponíveis (normal)")
print()

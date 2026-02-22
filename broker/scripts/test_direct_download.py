"""
Testar download direto via requests (sem yfinance)
Para contornar rate limiting do yfinance
"""
import requests
import time
from datetime import datetime, timedelta
import json

def test_direct_yahoo_api():
    """Testa API do Yahoo Finance diretamente"""
    print("🔍 TESTANDO DOWNLOAD DIRETO (SEM YFINANCE)")
    print("="*60)

    symbol = "PETR4.SA"

    # Datas
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)

    # Converter para timestamp Unix
    period1 = int(start_date.timestamp())
    period2 = int(end_date.timestamp())

    # URL da API do Yahoo Finance (v8)
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"

    params = {
        'period1': period1,
        'period2': period2,
        'interval': '1d',
        'includePrePost': 'false',
        'events': 'div,splits'
    }

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json',
        'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
        'Referer': 'https://finance.yahoo.com/',
        'Origin': 'https://finance.yahoo.com'
    }

    print(f"\n1️⃣  Testando {symbol} (últimos 30 dias)")
    print(f"   URL: {url}")
    print(f"   Período: {start_date.date()} a {end_date.date()}")

    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)

        print(f"\n   Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()

            # Extrair dados
            chart = data.get('chart', {})
            result = chart.get('result', [])

            if result:
                result_data = result[0]
                timestamps = result_data.get('timestamp', [])
                indicators = result_data.get('indicators', {})
                quote = indicators.get('quote', [{}])[0]

                opens = quote.get('open', [])
                highs = quote.get('high', [])
                lows = quote.get('low', [])
                closes = quote.get('close', [])
                volumes = quote.get('volume', [])

                print(f"   ✅ Sucesso!")
                print(f"   Registros: {len(timestamps)}")

                if len(timestamps) > 0:
                    print(f"\n   📊 Amostra dos primeiros 3 dias:")
                    for i in range(min(3, len(timestamps))):
                        dt = datetime.fromtimestamp(timestamps[i])
                        print(f"      {dt.date()}: O={opens[i]:.2f} H={highs[i]:.2f} L={lows[i]:.2f} C={closes[i]:.2f} V={volumes[i]:,}")

                return True
            else:
                print(f"   ❌ Resposta vazia")
                print(f"   Resposta: {data}")
                return False

        elif response.status_code == 429:
            print(f"   ❌ Rate limiting ainda ativo (429)")
            print(f"   Aguarde mais tempo ou tente novamente mais tarde")
            return False

        else:
            print(f"   ❌ Erro HTTP {response.status_code}")
            print(f"   Resposta: {response.text[:200]}")
            return False

    except Exception as e:
        print(f"   ❌ Erro: {e}")
        return False


def test_multiple_endpoints():
    """Testa diferentes endpoints do Yahoo Finance"""
    print("\n\n2️⃣  Testando endpoints alternativos...")

    symbol = "PETR4.SA"

    endpoints = [
        ("query1.finance.yahoo.com", "Query1 (primário)"),
        ("query2.finance.yahoo.com", "Query2 (alternativo)"),
    ]

    for host, label in endpoints:
        print(f"\n   Testando {label}...")
        url = f"https://{host}/v8/finance/chart/{symbol}"

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        try:
            response = requests.get(url, headers=headers, timeout=5)
            print(f"   Status: {response.status_code}")

            if response.status_code == 200:
                print(f"   ✅ Funcionando!")
            elif response.status_code == 429:
                print(f"   ❌ Rate limiting ativo")
            else:
                print(f"   ⚠️  Código: {response.status_code}")

        except Exception as e:
            print(f"   ❌ Erro: {e}")

        time.sleep(2)


def main():
    success = test_direct_yahoo_api()

    if not success:
        test_multiple_endpoints()

    print("\n" + "="*60)
    print("\n💡 CONCLUSÃO:")
    if success:
        print("   ✅ Download direto funciona!")
        print("   Podemos usar requests em vez de yfinance")
    else:
        print("   ❌ Ainda bloqueado")
        print("   Recomendações:")
        print("   1. Aguardar mais tempo (1-2 horas)")
        print("   2. Tentar em outro horário")
        print("   3. Usar API alternativa (Alpha Vantage)")
    print()


if __name__ == "__main__":
    main()

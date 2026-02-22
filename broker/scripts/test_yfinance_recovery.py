"""
Testar recuperação do yfinance após rate limiting
Monitora quando o bloqueio expira
"""
import yfinance as yf
import requests
import time
from datetime import datetime, timedelta

# Configurar sessão com User-Agent
session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/json',
    'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
})

def test_yfinance_single():
    """Testa yfinance com uma única ação"""
    symbol = "PETR4.SA"

    try:
        print(f"   Tentando baixar {symbol}...", end=" ", flush=True)

        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)

        ticker = yf.Ticker(symbol, session=session)
        df = ticker.history(
            start=start_date.strftime('%Y-%m-%d'),
            end=end_date.strftime('%Y-%m-%d'),
            timeout=10
        )

        if not df.empty:
            print(f"✅ SUCESSO! ({len(df)} registros)")
            print(f"\n   📊 Amostra:")
            print(df.head(3))
            return True
        else:
            print(f"❌ DataFrame vazio")
            return False

    except Exception as e:
        error_msg = str(e)
        if "429" in error_msg or "Too Many Requests" in error_msg:
            print(f"❌ Rate limiting ainda ativo (429)")
        else:
            print(f"❌ Erro: {error_msg[:100]}")
        return False


def monitor_recovery(check_interval_minutes=5, max_checks=12):
    """
    Monitora quando o yfinance volta a funcionar

    Args:
        check_interval_minutes: Intervalo entre tentativas (padrão: 5 min)
        max_checks: Máximo de tentativas (padrão: 12 = 1 hora)
    """
    print("🔄 MONITORANDO RECUPERAÇÃO DO YFINANCE")
    print("="*60)
    print(f"   Intervalo: {check_interval_minutes} minutos")
    print(f"   Máximo de tentativas: {max_checks} ({max_checks * check_interval_minutes} minutos)")
    print("="*60)

    for attempt in range(1, max_checks + 1):
        current_time = datetime.now().strftime("%H:%M:%S")
        print(f"\n⏰ Tentativa {attempt}/{max_checks} - {current_time}")

        if test_yfinance_single():
            print(f"\n{'='*60}")
            print(f"✅ YFINANCE RECUPERADO!")
            print(f"{'='*60}")
            print(f"   Tempo total: ~{attempt * check_interval_minutes} minutos")
            print(f"   Você pode usar yfinance normalmente agora!")
            print(f"\n💡 Execute:")
            print(f"   python scripts/download_data_standalone.py test")
            print()
            return True

        if attempt < max_checks:
            wait_seconds = check_interval_minutes * 60
            print(f"\n   ⏳ Aguardando {check_interval_minutes} minutos...")

            # Countdown
            for remaining in range(wait_seconds, 0, -30):
                mins = remaining // 60
                secs = remaining % 60
                print(f"      Próxima tentativa em: {mins}m {secs}s", end='\r', flush=True)
                time.sleep(min(30, remaining))

            print(" " * 50, end='\r')  # Limpar linha

    print(f"\n{'='*60}")
    print(f"⚠️  AINDA BLOQUEADO APÓS {max_checks * check_interval_minutes} MINUTOS")
    print(f"{'='*60}")
    print(f"\n💡 Recomendações:")
    print(f"   1. Aguardar mais tempo (2-4 horas)")
    print(f"   2. Tentar em outro horário (madrugada)")
    print(f"   3. Rodar o monitor novamente mais tarde")
    print(f"   4. Considerar baixar em múltiplas sessões (1 ano por dia)")
    print()
    return False


def main():
    import sys

    print("\n🔍 TESTE DE RECUPERAÇÃO DO YFINANCE")
    print("="*60)

    if len(sys.argv) > 1 and sys.argv[1] == "monitor":
        # Modo monitoramento contínuo
        interval = int(sys.argv[2]) if len(sys.argv) > 2 else 5
        max_checks = int(sys.argv[3]) if len(sys.argv) > 3 else 12
        monitor_recovery(interval, max_checks)
    else:
        # Teste único
        print("\n1️⃣  Testando yfinance agora...")
        success = test_yfinance_single()

        if success:
            print(f"\n✅ Yfinance funcionando!")
            print(f"   Você pode usar o download normalmente")
        else:
            print(f"\n❌ Ainda bloqueado")
            print(f"\n💡 Opções:")
            print(f"   1. Aguardar manualmente e testar novamente")
            print(f"   2. Usar modo monitor (testa automaticamente):")
            print(f"      python scripts/test_yfinance_recovery.py monitor")
            print(f"      python scripts/test_yfinance_recovery.py monitor 10 6  # 10min x 6 = 1h")
        print()


if __name__ == "__main__":
    main()

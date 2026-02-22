#!/usr/bin/env python3
"""
Script para download de dados históricos da B3
Usa a API do backend para baixar dados do Yahoo Finance
"""

import requests
import sys
from datetime import datetime

# URL da API
API_BASE_URL = "http://localhost:8001/api"


def check_stats():
    """Verifica estatísticas atuais dos dados"""
    print("📊 Verificando estatísticas dos dados...")
    response = requests.get(f"{API_BASE_URL}/data/stats")

    if response.status_code == 200:
        stats = response.json()
        print(f"\n📈 Estatísticas atuais:")
        print(f"   - Total de registros: {stats.get('total_records', 0):,}")
        print(f"   - Total de ações: {stats.get('total_stocks', 0)}")
        print(f"   - Primeira data: {stats.get('first_date', 'N/A')}")
        print(f"   - Última data: {stats.get('last_date', 'N/A')}")
        print(f"   - Ano esperado de início: {stats.get('expected_start_year', 1994)}")
        print(f"   - Cobertura completa: {'✅ Sim' if stats.get('coverage_complete') else '❌ Não'}")
        print(f"   - Anos com dados: {', '.join(map(str, stats.get('years', [])))}")
        return stats
    else:
        print(f"❌ Erro ao buscar estatísticas: {response.status_code}")
        return None


def download_historical_data(start_year=None, end_year=None, force=False):
    """Baixa dados históricos"""
    if start_year is None:
        start_year = 1994
    if end_year is None:
        end_year = datetime.now().year

    print(f"\n📥 Baixando dados históricos de {start_year} até {end_year}...")
    print(f"   Modo: {'Forçar re-download' if force else 'Apenas dados faltantes'}")

    params = {
        "start_year": start_year,
        "end_year": end_year,
        "force": force
    }

    try:
        response = requests.post(f"{API_BASE_URL}/update/download-historical", json=params)

        if response.status_code == 200:
            result = response.json()
            print(f"\n✅ Download concluído com sucesso!")
            print(f"   - Mensagem: {result.get('message', 'N/A')}")
            print(f"   - Registros inseridos: {result.get('records_inserted', 0):,}")
            print(f"   - Ações processadas: {result.get('stocks_processed', 0)}/{result.get('total_stocks', 0)}")
            return result
        else:
            print(f"❌ Erro ao baixar dados: {response.status_code}")
            try:
                error = response.json()
                print(f"   Detalhes: {error.get('detail', 'N/A')}")
            except:
                print(f"   Resposta: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Erro ao conectar com a API: {e}")
        return None


def update_daily_data():
    """Atualiza dados diários"""
    print("\n📅 Atualizando dados diários...")

    try:
        response = requests.post(f"{API_BASE_URL}/update/update-daily")

        if response.status_code == 200:
            result = response.json()
            print(f"\n✅ Atualização diária concluída!")
            print(f"   - Mensagem: {result.get('message', 'N/A')}")
            return result
        else:
            print(f"❌ Erro ao atualizar dados diários: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Erro ao conectar com a API: {e}")
        return None


def check_update_status():
    """Verifica status de updates em andamento"""
    print("\n🔄 Verificando status de updates...")

    try:
        response = requests.get(f"{API_BASE_URL}/update/status")

        if response.status_code == 200:
            status = response.json()
            print(f"\n📊 Status do update:")
            print(f"   - Em progresso: {'✅ Sim' if status.get('in_progress') else '❌ Não'}")
            if status.get('in_progress'):
                print(f"   - Tipo: {status.get('current_operation', 'N/A')}")
                print(f"   - Progresso: {status.get('progress', 0):.1f}%")
                print(f"   - Mensagem: {status.get('status_message', 'N/A')}")
            return status
        else:
            print(f"❌ Erro ao verificar status: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Erro ao conectar com a API: {e}")
        return None


def main():
    """Menu principal"""
    print("=" * 60)
    print("🔥 BROKER - Download de Dados Históricos da B3 🔥")
    print("=" * 60)

    while True:
        print("\n📋 MENU:")
        print("   1. Ver estatísticas dos dados")
        print("   2. Baixar dados históricos completos (1994-hoje)")
        print("   3. Baixar dados de um período específico")
        print("   4. Atualizar dados diários")
        print("   5. Verificar status de updates")
        print("   0. Sair")

        choice = input("\n👉 Escolha uma opção: ").strip()

        if choice == "1":
            check_stats()

        elif choice == "2":
            force = input("   Forçar re-download de dados existentes? (s/N): ").strip().lower() == 's'
            check_stats()
            confirm = input("\n   Confirmar download completo? (s/N): ").strip().lower()
            if confirm == 's':
                download_historical_data(force=force)
                check_stats()

        elif choice == "3":
            try:
                start_year = int(input("   Ano inicial (ex: 2020): ").strip())
                end_year = int(input("   Ano final (ex: 2024): ").strip())
                force = input("   Forçar re-download? (s/N): ").strip().lower() == 's'
                confirm = input(f"\n   Baixar dados de {start_year} até {end_year}? (s/N): ").strip().lower()
                if confirm == 's':
                    download_historical_data(start_year, end_year, force)
                    check_stats()
            except ValueError:
                print("❌ Anos inválidos!")

        elif choice == "4":
            confirm = input("   Atualizar dados diários? (s/N): ").strip().lower()
            if confirm == 's':
                update_daily_data()
                check_stats()

        elif choice == "5":
            check_update_status()

        elif choice == "0":
            print("\n👋 Até logo!")
            sys.exit(0)

        else:
            print("❌ Opção inválida!")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Script simples para download de dados históricos
Uso: python download_data.py [opção]
"""

import requests
import sys

API_BASE_URL = "http://localhost:8001/api"


def check_stats():
    """Verifica estatísticas"""
    response = requests.get(f"{API_BASE_URL}/data/stats")
    stats = response.json()

    print("\n📊 ESTATÍSTICAS DOS DADOS:")
    print(f"   Total de registros: {stats.get('total_records', 0):,}")
    print(f"   Total de ações: {stats.get('total_stocks', 0)}")
    print(f"   Primeira data: {stats.get('first_date', 'N/A')}")
    print(f"   Última data: {stats.get('last_date', 'N/A')}")
    print(f"   Cobertura completa: {'✅' if stats.get('coverage_complete') else '❌'}")
    print(f"   Anos: {', '.join(map(str, stats.get('years', [])))}\n")


def download_all():
    """Baixa todos os dados históricos"""
    print("\n📥 INICIANDO DOWNLOAD COMPLETO (1994-2026)...\n")

    response = requests.post(f"{API_BASE_URL}/update/download-historical", json={
        "start_year": 1994,
        "end_year": 2026,
        "force": False
    })

    result = response.json()
    print(f"\n✅ CONCLUÍDO!")
    print(f"   Registros inseridos: {result.get('records_inserted', 0):,}")
    print(f"   Ações processadas: {result.get('stocks_processed', 0)}\n")


def download_year(year):
    """Baixa dados de um ano específico"""
    print(f"\n📥 BAIXANDO DADOS DE {year}...\n")

    response = requests.post(f"{API_BASE_URL}/update/download-historical", json={
        "start_year": int(year),
        "end_year": int(year),
        "force": False
    })

    result = response.json()
    print(f"\n✅ CONCLUÍDO!")
    print(f"   Registros inseridos: {result.get('records_inserted', 0):,}\n")


def update_daily():
    """Atualiza dados diários"""
    print("\n📅 ATUALIZANDO DADOS DIÁRIOS...\n")

    response = requests.post(f"{API_BASE_URL}/update/update-daily")
    result = response.json()
    print(f"✅ {result.get('message', 'Concluído')}\n")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("\n🔥 BROKER - Download de Dados B3")
        print("\nUso:")
        print("  python download_data.py stats          # Ver estatísticas")
        print("  python download_data.py all            # Baixar tudo (1994-hoje)")
        print("  python download_data.py year 2023      # Baixar ano específico")
        print("  python download_data.py daily          # Atualizar dados diários\n")
        sys.exit(1)

    command = sys.argv[1]

    if command == "stats":
        check_stats()
    elif command == "all":
        check_stats()
        download_all()
        check_stats()
    elif command == "year" and len(sys.argv) == 3:
        download_year(sys.argv[2])
        check_stats()
    elif command == "daily":
        update_daily()
        check_stats()
    else:
        print("❌ Comando inválido!")

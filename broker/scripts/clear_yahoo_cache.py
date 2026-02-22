"""
Limpar cache do yfinance e testar download direto
"""
import os
import shutil
from pathlib import Path

def clear_yfinance_cache():
    """Limpa cache do yfinance"""
    cache_dirs = [
        Path.home() / ".cache" / "py-yfinance",
        Path.home() / ".yfinance",
        Path("/tmp") / "py-yfinance",
    ]

    print("🧹 Limpando cache do yfinance...")

    for cache_dir in cache_dirs:
        if cache_dir.exists():
            print(f"   Removendo: {cache_dir}")
            try:
                shutil.rmtree(cache_dir)
                print(f"   ✅ Removido")
            except Exception as e:
                print(f"   ❌ Erro: {e}")
        else:
            print(f"   ⏭️  Não existe: {cache_dir}")

    print("\n✅ Cache limpo!\n")

if __name__ == "__main__":
    clear_yfinance_cache()

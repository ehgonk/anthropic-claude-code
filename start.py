#!/usr/bin/env python3
"""
Script para iniciar o sistema Broker B3
Inicia backend (FastAPI) e frontend (Vite) simultaneamente
"""

import subprocess
import sys
import time
import os
from pathlib import Path

def main():
    print("=" * 60)
    print("🚀 INICIANDO SISTEMA BROKER B3")
    print("=" * 60)

    # Diretórios
    root_dir = Path(__file__).parent
    backend_dir = root_dir / "broker" / "backend"
    frontend_dir = root_dir / "broker" / "frontend"

    # Verificar se os diretórios existem
    if not backend_dir.exists():
        print(f"❌ Backend não encontrado: {backend_dir}")
        sys.exit(1)

    if not frontend_dir.exists():
        print(f"❌ Frontend não encontrado: {frontend_dir}")
        sys.exit(1)

    print(f"📂 Backend:  {backend_dir}")
    print(f"📂 Frontend: {frontend_dir}")
    print()

    # Iniciar backend
    print("[1/2] 🔧 Iniciando Backend (FastAPI)...")
    backend_cmd = [
        sys.executable, "-m", "uvicorn",
        "app.main:app",
        "--reload",
        "--host", "0.0.0.0",
        "--port", "8001"
    ]

    backend_process = subprocess.Popen(
        backend_cmd,
        cwd=str(backend_dir),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        bufsize=1
    )

    # Aguardar backend inicializar
    print("   Aguardando backend inicializar...")
    time.sleep(3)

    if backend_process.poll() is not None:
        print("❌ Backend falhou ao iniciar!")
        print(backend_process.stdout.read())
        sys.exit(1)

    print("   ✅ Backend iniciado!")
    print()

    # Iniciar frontend
    print("[2/2] 🎨 Iniciando Frontend (Vite)...")
    frontend_cmd = ["npm", "run", "dev", "--", "--host", "0.0.0.0"]

    frontend_process = subprocess.Popen(
        frontend_cmd,
        cwd=str(frontend_dir),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        bufsize=1
    )

    # Aguardar frontend inicializar
    print("   Aguardando frontend inicializar...")
    time.sleep(3)

    if frontend_process.poll() is not None:
        print("❌ Frontend falhou ao iniciar!")
        print(frontend_process.stdout.read())
        backend_process.terminate()
        sys.exit(1)

    print("   ✅ Frontend iniciado!")
    print()

    # Sistema pronto
    print("=" * 60)
    print("✅ SISTEMA INICIADO COM SUCESSO!")
    print("=" * 60)
    print()
    print("📊 Acesse:")
    print("   🌐 Frontend:  http://localhost:5174")
    print("   🔧 Backend:   http://localhost:8001")
    print("   📚 API Docs:  http://localhost:8001/docs")
    print()
    print("⚠️  Pressione Ctrl+C para parar os servidores")
    print("=" * 60)
    print()

    # Manter processos rodando
    try:
        while True:
            # Verificar se processos ainda estão vivos
            if backend_process.poll() is not None:
                print("\n❌ Backend parou inesperadamente!")
                break

            if frontend_process.poll() is not None:
                print("\n❌ Frontend parou inesperadamente!")
                break

            time.sleep(1)

    except KeyboardInterrupt:
        print("\n\n🛑 Parando servidores...")
        backend_process.terminate()
        frontend_process.terminate()

        # Aguardar processos terminarem
        backend_process.wait(timeout=5)
        frontend_process.wait(timeout=5)

        print("✅ Servidores parados!")
        print("=" * 60)

if __name__ == "__main__":
    main()

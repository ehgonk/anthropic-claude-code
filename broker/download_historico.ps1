# ============================================
# Download Histórico Automático - Broker
# ============================================
# Este script executa o download completo de dados históricos
# desde 1994 até o período mais recente, em batches otimizados
# ============================================

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  DOWNLOAD HISTÓRICO - BROKER PROJECT" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# ============================================
# PASSO 1: Verificar Python
# ============================================
Write-Host "[1/6] Verificando Python..." -ForegroundColor Yellow

try {
    $pythonVersion = python --version 2>&1
    Write-Host "  ✓ Python encontrado: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "  ✗ Python não encontrado!" -ForegroundColor Red
    Write-Host "  Instale Python 3.8+ de: https://www.python.org/downloads/" -ForegroundColor Red
    Write-Host "  Marque 'Add Python to PATH' durante instalação" -ForegroundColor Red
    exit 1
}

# ============================================
# PASSO 2: Verificar diretório
# ============================================
Write-Host "[2/6] Verificando diretório..." -ForegroundColor Yellow

if (-not (Test-Path "scripts\download_data.py")) {
    Write-Host "  ✗ Script não encontrado!" -ForegroundColor Red
    Write-Host "  Certifique-se de estar na pasta 'broker'" -ForegroundColor Red
    Write-Host "  Pasta atual: $(Get-Location)" -ForegroundColor Red
    exit 1
}

Write-Host "  ✓ Diretório correto" -ForegroundColor Green

# ============================================
# PASSO 3: Criar e ativar ambiente virtual
# ============================================
Write-Host "[3/6] Preparando ambiente virtual..." -ForegroundColor Yellow

if (-not (Test-Path "backend\venv")) {
    Write-Host "  Criando venv..." -ForegroundColor Cyan
    python -m venv backend\venv
    Write-Host "  ✓ Venv criado" -ForegroundColor Green
} else {
    Write-Host "  ✓ Venv já existe" -ForegroundColor Green
}

# Ativar venv
Write-Host "  Ativando venv..." -ForegroundColor Cyan
& "backend\venv\Scripts\Activate.ps1"

# ============================================
# PASSO 4: Instalar dependências
# ============================================
Write-Host "[4/6] Instalando dependências..." -ForegroundColor Yellow

pip install -q -r backend\requirements.txt

if ($LASTEXITCODE -eq 0) {
    Write-Host "  ✓ Dependências instaladas" -ForegroundColor Green
} else {
    Write-Host "  ✗ Erro ao instalar dependências" -ForegroundColor Red
    exit 1
}

# ============================================
# PASSO 5: Verificar status atual
# ============================================
Write-Host "[5/6] Verificando banco de dados..." -ForegroundColor Yellow
Write-Host ""

python scripts\download_data.py stats

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan

# Perguntar se quer continuar
$resposta = Read-Host "Deseja iniciar o download completo (1994-2026)? (S/N)"

if ($resposta -ne "S" -and $resposta -ne "s") {
    Write-Host ""
    Write-Host "Download cancelado pelo usuário." -ForegroundColor Yellow
    exit 0
}

# ============================================
# PASSO 6: Download completo
# ============================================
Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "[6/6] Iniciando download..." -ForegroundColor Yellow
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "⏳ Isso pode levar 5-10 minutos..." -ForegroundColor Cyan
Write-Host "⏳ Processando 11 batches de 3 anos cada..." -ForegroundColor Cyan
Write-Host ""

# Executar download
python scripts\download_data.py all

# ============================================
# Verificar resultado
# ============================================
Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  RESULTADO FINAL" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

python scripts\download_data.py stats

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  ✅ PROCESSO CONCLUÍDO!" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Para iniciar a aplicação:" -ForegroundColor Yellow
Write-Host "  1. Backend:  cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8001" -ForegroundColor White
Write-Host "  2. Frontend: cd frontend && npm run dev" -ForegroundColor White
Write-Host "  3. Acesse:   http://localhost:5174" -ForegroundColor White
Write-Host ""

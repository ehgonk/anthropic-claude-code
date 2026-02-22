@echo off
REM ============================================
REM Download Histórico - Broker Project
REM ============================================
REM Execute este arquivo com duplo clique
REM ou via PowerShell para download automatizado
REM ============================================

echo.
echo ============================================
echo   DOWNLOAD HISTORICO - BROKER PROJECT
echo ============================================
echo.

REM Verificar Python
echo [1/6] Verificando Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo   X Python nao encontrado!
    echo   Instale Python 3.8+ de: https://www.python.org/downloads/
    echo   Marque 'Add Python to PATH' durante instalacao
    pause
    exit /b 1
)
echo   OK Python encontrado
echo.

REM Verificar diretório
echo [2/6] Verificando diretorio...
if not exist "scripts\download_data.py" (
    echo   X Script nao encontrado!
    echo   Certifique-se de estar na pasta 'broker'
    echo   Pasta atual: %CD%
    pause
    exit /b 1
)
echo   OK Diretorio correto
echo.

REM Criar venv se não existe
echo [3/6] Preparando ambiente virtual...
if not exist "backend\venv" (
    echo   Criando venv...
    python -m venv backend\venv
    echo   OK Venv criado
) else (
    echo   OK Venv ja existe
)
echo.

REM Ativar venv e instalar dependências
echo [4/6] Instalando dependencias...
call backend\venv\Scripts\activate.bat
pip install -q -r backend\requirements.txt
if errorlevel 1 (
    echo   X Erro ao instalar dependencias
    pause
    exit /b 1
)
echo   OK Dependencias instaladas
echo.

REM Verificar status
echo [5/6] Verificando banco de dados...
echo.
python scripts\download_data.py stats
echo.

echo ============================================
set /p resposta="Deseja iniciar o download completo (1994-2026)? (S/N): "
if /i not "%resposta%"=="S" (
    echo.
    echo Download cancelado pelo usuario.
    pause
    exit /b 0
)

REM Download completo
echo.
echo ============================================
echo [6/6] Iniciando download...
echo ============================================
echo.
echo Isso pode levar 5-10 minutos...
echo Processando 11 batches de 3 anos cada...
echo.

python scripts\download_data.py all

REM Resultado
echo.
echo ============================================
echo   RESULTADO FINAL
echo ============================================
echo.

python scripts\download_data.py stats

echo.
echo ============================================
echo   OK PROCESSO CONCLUIDO!
echo ============================================
echo.
echo Para iniciar a aplicacao:
echo   1. Backend:  cd backend ^&^& uvicorn app.main:app --reload
echo   2. Frontend: cd frontend ^&^& npm run dev
echo   3. Acesse:   http://localhost:5174
echo.

pause

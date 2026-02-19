# 📊 Download Histórico Completo da B3

Este script baixa **TODOS os dados históricos** disponíveis da B3 (anos 2000-2025).

## ⚠️ IMPORTANTE: Execute no Windows!

A B3 bloqueia servidores Linux/cloud com CAPTCHA. Este script **DEVE ser executado no seu computador Windows local**.

---

## 🚀 Como executar

### 1️⃣ Abra o PowerShell

```powershell
cd C:\Users\egonk\Documents\anthropic-claude-code\broker\backend
```

### 2️⃣ Ative o ambiente virtual Python

```powershell
.\.venv\Scripts\Activate.ps1
```

Se der erro de permissão, execute antes:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### 3️⃣ Execute o script

```powershell
python scripts\download_full_history_windows.py
```

---

## ⏱️ Tempo estimado

- **26 anos** (2000-2025)
- **~2-3 minutos por ano** = aproximadamente **1 hora total**
- Cada ano: ~5-30 MB

---

## 📊 O que o script faz?

1. ✅ Baixa COTAHIST de cada ano (2000-2025)
2. ✅ Extrai arquivos ZIP
3. ✅ Parseia dados (formato fixo-width)
4. ✅ Salva no banco de dados SQLite (`data/broker.db`)
5. ✅ Gera relatório com períodos baixados (YYYY-MM)
6. ✅ Evita duplicatas (unique constraint)

---

## 📁 Saída esperada

```
╔══════════════════════════════════════════════════════════════╗
║  B3 HISTORICAL DATA DOWNLOADER - Windows                     ║
║  Period: 2000 - 2026                                      ║
╚══════════════════════════════════════════════════════════════╝

============================================================
📅 Processing year: 2000
============================================================
Downloading COTAHIST from https://bvmf.bmfbovespa.com.br/InstDados/SerHist/COTAHIST_A2000.ZIP...
Downloaded 5.23 MB
Extracting COTAHIST_A2000.TXT...
Parsing COTAHIST file...
Parsed 342 symbols
💾 Saving 342 stocks to database...
✅ Saved: 342 new stocks, 0 updated stocks, 63852 price records

... (continua para cada ano)

============================================================
📊 DOWNLOAD SUMMARY
============================================================

✅ Years processed successfully: 26
❌ Years failed: 0
📈 Total stocks: 1,247
💹 Total price records: 1,234,567


============================================================
📅 PERIODS DOWNLOADED (YYYY-MM)
============================================================

Year     Months
------------------------------------------------------------
2000     01, 02, 03, 04, 05, 06, 07, 08, 09, 10, 11, 12
2001     01, 02, 03, 04, 05, 06, 07, 08, 09, 10, 11, 12
2002     01, 02, 03, 04, 05, 06, 07, 08, 09, 10, 11, 12
...
2025     01, 02

📊 Total unique periods: 302
📅 Date range: 2000-01 to 2025-02

✅ Download complete!
```

---

## 🔧 Troubleshooting

### ❌ Erro 403 Forbidden

Se aparecer erro 403, significa que:
1. Você NÃO está executando no Windows
2. Seu IP foi bloqueado temporariamente (aguarde 10 minutos)
3. A B3 mudou a política de acesso

### ❌ Erro de SSL/HTTPS

```powershell
pip install --upgrade certifi httpx
```

### ❌ Erro de permissão no banco

Feche qualquer conexão aberta ao `data/broker.db` (backend rodando, DB browser, etc.)

---

## 📄 Arquivos gerados

- `data/broker.db` - Banco de dados SQLite com todos os dados
- `data/download_summary.txt` - Resumo do download
- `data/cache/cotahist_YYYY.txt` - Cache dos arquivos baixados (um por ano)

---

## 🎯 Próximos passos

Após o download completo:

1. ✅ Verificar o resumo em `data/download_summary.txt`
2. ✅ Consultar o banco de dados:
   ```powershell
   python -c "from app.database import *; import asyncio; asyncio.run(...)"
   ```
3. ✅ Iniciar o backend para visualizar os dados:
   ```powershell
   uvicorn app.main:app --reload
   ```

---

## 📞 Suporte

Se encontrar problemas, verifique:
- ✅ Está executando no Windows (não no Linux)
- ✅ Tem conexão com a internet
- ✅ O firewall não está bloqueando Python
- ✅ Tem espaço em disco (~2 GB para tudo)

# 📥 Download Histórico - Guia PowerShell (Windows)

## 🎯 O que será feito:
- Download de dados de 1994 até 2026
- Processamento em 11 batches de 3 anos cada
- ~30 ações principais do Ibovespa
- Salvamento no banco SQLite unificado
- Filtro automático para cotações em R$

---

## 📋 PASSO 1: Preparar o ambiente

### Abrir PowerShell como Administrador
1. Pressione `Win + X`
2. Clique em **"Windows PowerShell (Admin)"** ou **"Terminal (Admin)"**

### Navegar para a pasta do projeto
```powershell
cd C:\caminho\para\anthropic-claude-code\broker
```

> ⚠️ **Substitua** `C:\caminho\para` pelo caminho real onde você clonou o projeto!

---

## 📋 PASSO 2: Verificar Python instalado

```powershell
python --version
```

**Deve mostrar:** `Python 3.8` ou superior

Se não tiver Python instalado:
1. Baixe em: https://www.python.org/downloads/
2. Marque **"Add Python to PATH"** durante instalação
3. Reinicie o PowerShell

---

## 📋 PASSO 3: Criar ambiente virtual (se ainda não existe)

```powershell
# Criar venv
python -m venv backend\venv

# Ativar venv
.\backend\venv\Scripts\Activate.ps1
```

**Se der erro de permissão:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.\backend\venv\Scripts\Activate.ps1
```

---

## 📋 PASSO 4: Instalar dependências

```powershell
# Instalar dependências do backend
pip install -r backend\requirements.txt
```

**Aguarde a instalação** (pode levar alguns minutos)

---

## 📋 PASSO 5: Verificar status do banco de dados

```powershell
python scripts\download_data.py stats
```

**Deve mostrar:**
```
📊 ESTATÍSTICAS DO BANCO DE DADOS:
   Total de registros: 0
   Total de ações: 0
   ...
```

---

## 📋 PASSO 6: Executar download completo 🚀

```powershell
python scripts\download_data.py all
```

### O que vai acontecer:

```
📥 DOWNLOAD COMPLETO VIA YAHOO FINANCE (1994-2026)...

Processing batch 1/11: 1994-1996
  ✓ PETR4: 756 registros
  ✓ VALE3: 756 registros
  ✓ ITUB4: 756 registros
  ...

Processing batch 2/11: 1997-1999
  ✓ PETR4: 756 registros
  ...

[... continua até batch 11/11: 2024-2026 ...]

✅ CONCLUÍDO!
   Registros inseridos: 285,432
   Ações processadas: 30
```

**Tempo estimado:** 5-10 minutos (depende da conexão)

---

## 📋 PASSO 7: Verificar resultado

```powershell
python scripts\download_data.py stats
```

**Deve mostrar algo como:**
```
📊 ESTATÍSTICAS DO BANCO DE DADOS:
   Total de registros: 285,432
   Total de ações: 30
   Primeira data: 1994-07-01
   Última data: 2026-02-21
   Cobertura completa: ✅
   Anos: 1994, 1995, 1996, ..., 2024, 2025, 2026
```

---

## 📋 PASSO 8: Iniciar aplicação (opcional)

### Terminal 1 - Backend:
```powershell
cd backend
.\venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

### Terminal 2 - Frontend:
```powershell
cd frontend
npm install
npm run dev
```

Acesse: http://localhost:5174

---

## ⚠️ Solução de Problemas

### ❌ Erro: "scripts\download_data.py não encontrado"
**Solução:** Certifique-se de estar na pasta `broker`
```powershell
pwd  # Deve mostrar: C:\...\anthropic-claude-code\broker
```

### ❌ Erro: "No module named 'yfinance'"
**Solução:** Ativar venv e reinstalar dependências
```powershell
.\backend\venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
```

### ❌ Erro: "Temporary failure in name resolution"
**Solução:** Verificar conexão com internet
```powershell
Test-NetConnection -ComputerName finance.yahoo.com -Port 443
```

### ❌ Download muito lento
**Solução:** O sistema já tem delay de 2s entre batches. Isso é normal para evitar bloqueio.

---

## 📊 Comandos úteis adicionais

### Ver últimos 50 registros inseridos:
```powershell
python scripts\download_data.py query "SELECT * FROM stock_prices ORDER BY date DESC LIMIT 50"
```

### Ver estatísticas por ação:
```powershell
python scripts\download_data.py query "SELECT symbol, COUNT(*) as total FROM stock_prices GROUP BY symbol ORDER BY total DESC"
```

### Limpar banco e recomeçar (use com cuidado!):
```powershell
Remove-Item backend\data\broker.db -Force
python scripts\download_data.py all
```

---

## ✅ Checklist final

- [ ] Python 3.8+ instalado
- [ ] PowerShell aberto na pasta `broker`
- [ ] Venv ativado (`(venv)` aparece no prompt)
- [ ] Dependências instaladas
- [ ] Download completo executado
- [ ] Estatísticas mostram > 200.000 registros
- [ ] Aplicação funcionando

---

## 🎉 Pronto!

Seu banco de dados agora contém:
- ✅ 33 anos de histórico (1994-2026)
- ✅ ~30 ações principais
- ✅ ~300.000 registros de cotações
- ✅ Dados em R$ (Real brasileiro)
- ✅ Banco SQLite unificado

**Aproveite o sistema completo!** 🚀

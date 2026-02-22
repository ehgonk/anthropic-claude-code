# 📋 Resumo da Instalação - Windows PowerShell

## ✅ Arquivos Criados para Você

```
broker/
├── 🚀_COMECE_AQUI.txt          ← COMECE POR AQUI!
├── download_historico.bat      ← Duplo clique (mais fácil)
├── download_historico.ps1      ← Script PowerShell
├── LEIA-ME-WINDOWS.md          ← Guia rápido
└── DOWNLOAD_WINDOWS.md         ← Guia completo detalhado
```

---

## 🎯 Como Executar (3 opções)

### ⭐ **OPÇÃO 1: Mais Fácil - Duplo Clique**

1. Abra a pasta `broker` no Windows Explorer
2. **Duplo clique** em `download_historico.bat`
3. Siga as instruções
4. Pronto! ✅

---

### 🚀 **OPÇÃO 2: Script PowerShell**

```powershell
# 1. Abra PowerShell na pasta broker (Shift + Clique direito)

# 2. Permitir scripts (apenas primeira vez)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# 3. Executar
.\download_historico.ps1
```

---

### 📝 **OPÇÃO 3: Comandos Manuais**

```powershell
# 1. Navegar para pasta
cd C:\caminho\para\anthropic-claude-code\broker

# 2. Criar ambiente virtual
python -m venv backend\venv

# 3. Ativar venv
.\backend\venv\Scripts\Activate.ps1

# 4. Instalar dependências
pip install -r backend\requirements.txt

# 5. Executar download
python scripts\download_data.py all

# 6. Verificar resultado
python scripts\download_data.py stats
```

---

## 📊 O que será baixado

| Item | Valor |
|------|-------|
| **Período** | 1994 até 2026 (33 anos) |
| **Batches** | 11 batches de 3 anos cada |
| **Ações** | ~30 principais do Ibovespa |
| **Registros** | ~300.000 cotações |
| **Moeda** | R$ (Real brasileiro) |
| **Formato** | SQLite unificado |
| **Tempo** | 5-10 minutos |
| **Tamanho** | ~100 MB |

---

## 🔄 Processo de Download

```
1994-1996 ━━━━━━━━━━ Batch 1/11 ✓
1997-1999 ━━━━━━━━━━ Batch 2/11 ✓
2000-2002 ━━━━━━━━━━ Batch 3/11 ✓
2003-2005 ━━━━━━━━━━ Batch 4/11 ✓
2006-2008 ━━━━━━━━━━ Batch 5/11 ✓
2009-2011 ━━━━━━━━━━ Batch 6/11 ✓
2012-2014 ━━━━━━━━━━ Batch 7/11 ✓
2015-2017 ━━━━━━━━━━ Batch 8/11 ✓
2018-2020 ━━━━━━━━━━ Batch 9/11 ✓
2021-2023 ━━━━━━━━━━ Batch 10/11 ✓
2024-2026 ━━━━━━━━━━ Batch 11/11 ✓

✅ 300.000+ registros salvos!
```

---

## ⚙️ Após o Download - Iniciar Aplicação

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

**Acesse:** http://localhost:5174

---

## ⚠️ Solução de Problemas

| Problema | Solução |
|----------|---------|
| ❌ Python não encontrado | Instale de https://python.org (marque "Add to PATH") |
| ❌ Script não executa | `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser` |
| ❌ "Não encontrado" | Certifique-se de estar na pasta `broker` |
| ❌ Erro de rede | Verifique conexão com internet |
| ❌ Download lento | Normal! Delay de 2s entre batches |

---

## 📞 Documentação Adicional

| Arquivo | Descrição |
|---------|-----------|
| `🚀_COMECE_AQUI.txt` | Índice visual rápido |
| `LEIA-ME-WINDOWS.md` | Guia rápido resumido |
| `DOWNLOAD_WINDOWS.md` | Guia completo detalhado |
| `README.md` | Documentação do projeto |

---

## ✅ Verificar Sucesso

Após o download, execute:

```powershell
python scripts\download_data.py stats
```

**Deve mostrar:**
```
📊 ESTATÍSTICAS DO BANCO DE DADOS:
   Total de registros: 285,432
   Total de ações: 30
   Primeira data: 1994-07-01
   Última data: 2026-02-21
   Cobertura completa: ✅
   Anos: 1994, 1995, ..., 2025, 2026
```

---

## 🎉 Pronto!

Seu banco de dados agora tem **33 anos de histórico** da Bolsa de Valores brasileira!

**Aproveite o sistema completo!** 🚀

---

## 📝 Comandos Úteis Adicionais

### Ver últimas cotações:
```powershell
python scripts\download_data.py query "SELECT * FROM stock_prices ORDER BY date DESC LIMIT 50"
```

### Ver estatísticas por ação:
```powershell
python scripts\download_data.py query "SELECT symbol, COUNT(*) as total FROM stock_prices GROUP BY symbol ORDER BY total DESC"
```

### Limpar e recomeçar (⚠️ cuidado!):
```powershell
Remove-Item backend\data\broker.db -Force
python scripts\download_data.py all
```

---

**Desenvolvido com ❤️ para análise de ações brasileiras**

# ⚡ Início Rápido - Windows

## 🎯 Execute Agora! (Sem backend necessário)

O novo script **standalone** NÃO precisa do backend rodando! 🎉

---

## ✨ MÉTODO 1: Duplo Clique (MAIS FÁCIL)

1. Dê **duplo clique** em `download_historico.bat`
2. Pressione `S` quando perguntar
3. Aguarde 5-10 minutos
4. Pronto! ✅

---

## 🚀 MÉTODO 2: PowerShell (Recomendado)

```powershell
# 1. Abra PowerShell na pasta broker (Shift + Clique direito)

# 2. Ativar ambiente virtual
.\backend\venv\Scripts\Activate.ps1

# 3. Executar download standalone
python scripts\download_data_standalone.py all
```

**Pronto!** Não precisa do backend rodando! 🎉

---

## 📝 MÉTODO 3: Comandos Individuais

### Ver estatísticas atuais:
```powershell
python scripts\download_data_standalone.py stats
```

### Download completo (1994-2026):
```powershell
python scripts\download_data_standalone.py all
```

### Download de ano específico:
```powershell
python scripts\download_data_standalone.py year 2023
```

### Atualizar últimos 7 dias:
```powershell
python scripts\download_data_standalone.py daily
```

---

## ❌ ERRO: "can't open file"

Se você está vendo este erro:
```
python.exe: can't open file 'C:\\...\\scripts\\download_data.py': [Errno 2] No such file or directory
```

**SOLUÇÃO:**

### Opção A: Fazer git pull (Recomendado)
```powershell
git pull origin claude/create-broker-project-IYVgL
```

### Opção B: Usar script standalone
```powershell
python scripts\download_data_standalone.py all
```

### Opção C: Verificar se está na pasta correta
```powershell
# Deve estar em: C:\...\anthropic-claude-code\broker
pwd

# Se não estiver, navegue:
cd C:\caminho\para\anthropic-claude-code\broker
```

---

## 📊 Saída Esperada

```
🔧 Configurando banco de dados...
   ✅ Banco configurado

📊 ESTATÍSTICAS DO BANCO DE DADOS:
   Fonte de dados: Yahoo Finance
   Total de registros: 0
   Total de ações: 0
   Primeira data: None
   Última data: None
   Cobertura completa: ❌
   Anos:

============================================================
📥 DOWNLOAD COMPLETO VIA YAHOO FINANCE
============================================================

   📅 Período: 1994 até 2026
   📦 Total de batches: 11
   📈 Ações: 30
   ⏱️  Delay entre batches: 2s

============================================================

📦 Batch 1/11: 1994-1996
   Período: 1994-01-01 a 1996-12-31
   Baixando 30 ações...
   [1/30] PETR4... ✓ 756 registros
   [2/30] VALE3... ✓ 756 registros
   [3/30] ITUB4... ✓ 756 registros
   ...

   ✅ Batch concluído: 22,680 registros de 30 ações

   ⏳ Aguardando 2s antes do próximo batch...

... (continua até batch 11/11) ...

============================================================
✅ DOWNLOAD COMPLETO!
============================================================

   📊 Total de registros inseridos: 285,432
   📈 Total de ações processadas: 30
   📦 Total de batches: 11

============================================================
```

---

## ⚠️ Requisitos Mínimos

- ✅ Python 3.8+
- ✅ Conexão com internet
- ✅ ~100 MB de espaço
- ✅ Dependências instaladas (`pip install -r backend/requirements.txt`)

---

## 🔧 Primeira Execução (Setup)

Se é a primeira vez executando:

```powershell
# 1. Criar ambiente virtual
python -m venv backend\venv

# 2. Ativar ambiente
.\backend\venv\Scripts\Activate.ps1

# 3. Instalar dependências
pip install -r backend\requirements.txt

# 4. Executar download
python scripts\download_data_standalone.py all
```

---

## 🎉 Após o Download

Você terá:
- ✅ 33 anos de histórico (1994-2026)
- ✅ ~300.000 registros de cotações
- ✅ 30 ações principais do Ibovespa
- ✅ Banco SQLite em `backend/data/broker.db`

### Iniciar a aplicação:

**Terminal 1 - Backend:**
```powershell
cd backend
.\venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

**Terminal 2 - Frontend:**
```powershell
cd frontend
npm install
npm run dev
```

**Acesse:** http://localhost:5174

---

## 📚 Mais Informações

- `🚀_COMECE_AQUI.txt` - Índice visual
- `LEIA-ME-WINDOWS.md` - Guia rápido resumido
- `DOWNLOAD_WINDOWS.md` - Guia completo detalhado
- `RESUMO_INSTALACAO.md` - Resumo + comandos úteis

---

## 💡 Dica Pro

Execute o script standalone diretamente sem precisar do backend:

```powershell
# Ver ajuda
python scripts\download_data_standalone.py

# Download rápido
python scripts\download_data_standalone.py all
```

**Muito mais fácil!** 🚀

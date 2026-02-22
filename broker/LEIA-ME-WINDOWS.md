# 🪟 Guia Rápido - Windows

## 🎯 3 Formas de Executar o Download

---

## ✨ **FORMA 1: Duplo Clique (MAIS FÁCIL)**

1. Abra a pasta `broker` no Windows Explorer
2. Dê **duplo clique** em `download_historico.bat`
3. Siga as instruções na tela
4. Aguarde o download completo
5. Pronto! ✅

---

## 🚀 **FORMA 2: Script PowerShell Automatizado**

1. **Abrir PowerShell na pasta do projeto:**
   - Abra a pasta `broker` no Windows Explorer
   - Segure `Shift` + Clique direito em área vazia
   - Clique em **"Abrir janela do PowerShell aqui"**

2. **Permitir execução de scripts (apenas primeira vez):**
   ```powershell
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   ```

3. **Executar o script:**
   ```powershell
   .\download_historico.ps1
   ```

4. **Aguardar conclusão** ✅

---

## 📝 **FORMA 3: Comandos Manuais (PASSO A PASSO)**

### 1️⃣ Abrir PowerShell
```powershell
# Navegar para a pasta
cd C:\caminho\para\anthropic-claude-code\broker
```

### 2️⃣ Criar ambiente virtual
```powershell
python -m venv backend\venv
.\backend\venv\Scripts\Activate.ps1
```

### 3️⃣ Instalar dependências
```powershell
pip install -r backend\requirements.txt
```

### 4️⃣ Verificar status atual
```powershell
python scripts\download_data.py stats
```

### 5️⃣ Executar download completo 🚀
```powershell
python scripts\download_data.py all
```

### 6️⃣ Verificar resultado
```powershell
python scripts\download_data.py stats
```

---

## 📊 O que será baixado?

- ✅ **Período:** 1994 até 2026 (33 anos)
- ✅ **Batches:** 11 batches de 3 anos cada
- ✅ **Ações:** ~30 principais do Ibovespa
- ✅ **Registros:** ~300.000 cotações históricas
- ✅ **Moeda:** Apenas cotações em R$ (Real)
- ✅ **Destino:** SQLite unificado (`broker.db`)
- ✅ **Tempo:** 5-10 minutos (depende da internet)

---

## 📂 Arquivos Criados

Após o download, você terá:

```
broker/
├── backend/
│   └── data/
│       └── broker.db          ← Banco SQLite com ~300k registros
├── download_historico.bat     ← Duplo clique (Windows)
├── download_historico.ps1     ← Script PowerShell
└── DOWNLOAD_WINDOWS.md        ← Guia completo detalhado
```

---

## ⚙️ Iniciar a Aplicação (após download)

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

## ⚠️ Problemas Comuns

### ❌ "Python não é reconhecido"
**Solução:** Instale Python de https://www.python.org/downloads/
✅ Marque **"Add Python to PATH"** durante instalação

### ❌ "Não é possível executar scripts"
**Solução:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### ❌ "scripts\download_data.py não encontrado"
**Solução:** Certifique-se de estar na pasta `broker`:
```powershell
pwd  # Deve mostrar: ...\anthropic-claude-code\broker
```

### ❌ Download muito lento
**✅ Normal!** O sistema tem delay de 2s entre batches para evitar bloqueio do Yahoo Finance.

---

## 📞 Ajuda Adicional

- **Guia Completo:** Veja `DOWNLOAD_WINDOWS.md`
- **Documentação:** Veja `README.md`
- **Logs:** Verifique `backend/backend.log`

---

## ✅ Checklist de Sucesso

- [ ] Python 3.8+ instalado
- [ ] Executou um dos 3 métodos acima
- [ ] Download completou sem erros
- [ ] Comando `stats` mostra > 200.000 registros
- [ ] Banco `broker.db` existe em `backend/data/`
- [ ] Aplicação iniciada com sucesso

---

## 🎉 Pronto para usar!

Seu sistema agora tem **33 anos de histórico** de cotações da bolsa brasileira! 🚀

**Aproveite!**

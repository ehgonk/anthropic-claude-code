# 🚀 Rodar o Broker Localmente no Windows

## 📋 Pré-requisitos

Antes de começar, instale:

1. **Python 3.11+** → https://www.python.org/downloads/
   - ⚠️ Durante instalação, marque: **"Add Python to PATH"**

2. **Node.js 18+** → https://nodejs.org/
   - Baixe a versão LTS (recomendada)

3. **Git** → https://git-scm.com/download/win
   - Use as configurações padrão

---

## 🔧 Instalação

### 1️⃣ Clone o repositório

Abra o **PowerShell** ou **CMD** e execute:

```powershell
cd C:\Users\%USERNAME%\Documents
git clone https://github.com/ehgonk/anthropic-claude-code.git
cd anthropic-claude-code\broker
```

---

### 2️⃣ Configure o Backend (Python/FastAPI)

```powershell
cd backend

# Crie o ambiente virtual
python -m venv .venv

# Ative o ambiente virtual
.venv\Scripts\activate

# Instale as dependências
pip install -r requirements.txt
```

**Inicie o backend:**

```powershell
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

✅ Você deve ver:
```
INFO:     Uvicorn running on http://0.0.0.0:8001
```

**Deixe esse terminal aberto!**

---

### 3️⃣ Configure o Frontend (React/Vite)

Abra um **NOVO terminal PowerShell** e execute:

```powershell
cd C:\Users\%USERNAME%\Documents\anthropic-claude-code\broker\frontend

# Instale as dependências
npm install

# Inicie o servidor de desenvolvimento
npm run dev
```

✅ Você deve ver:
```
VITE v6.4.1  ready in XXX ms
Local:   http://localhost:5174/
```

---

## 🌐 Acesse a aplicação

Abra seu navegador e acesse:

```
http://localhost:5174
```

🎉 **Pronto! A aplicação está rodando localmente!**

---

## 🛠️ Comandos Úteis

### Parar os servidores
Pressione `Ctrl + C` em cada terminal

### Reiniciar
```powershell
# Backend
cd backend
.venv\Scripts\activate
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload

# Frontend (outro terminal)
cd frontend
npm run dev
```

---

## ❓ Problemas Comuns

### "Python não é reconhecido como comando"
- Reinstale o Python e marque **"Add Python to PATH"**
- Reinicie o PowerShell

### "npm não é reconhecido como comando"
- Reinstale o Node.js
- Reinicie o PowerShell

### Porta 8001 ou 5174 já está em uso
```powershell
# Windows: matar processo na porta
netstat -ano | findstr :8001
taskkill /PID [numero_do_pid] /F
```

### Backend retorna erro 500
- Verifique se as dependências foram instaladas: `pip list`
- Veja os logs no terminal do backend

---

## 📦 Estrutura do Projeto

```
broker/
├── backend/           # API FastAPI (Python)
│   ├── app/
│   │   ├── main.py   # Ponto de entrada
│   │   ├── api/      # Rotas da API
│   │   ├── models/   # Modelos do banco de dados
│   │   └── services/ # Lógica de negócio
│   └── requirements.txt
│
└── frontend/          # Interface React (TypeScript)
    ├── src/
    │   ├── App.tsx   # Componente principal
    │   ├── services/ # Chamadas à API
    │   └── utils/    # Funções auxiliares
    └── package.json
```

---

## 🎯 Próximos Passos

Após rodar localmente:

1. ✅ Acesse `http://localhost:5174` no navegador
2. 📊 Veja a lista de ações da B3
3. 📈 Clique em uma ação para ver o gráfico de candlestick
4. 🔧 Faça modificações no código e veja hot-reload automático!

---

**Feito com ❤️ usando Claude Code**

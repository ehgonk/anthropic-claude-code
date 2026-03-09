# 🌐 Como Acessar o Broker B3

## ✅ Servidores Rodando

Os servidores estão configurados e rodando:

- **Frontend (Vite/React)**: Porta `5174`
- **Backend (FastAPI)**: Porta `8001`

## 🔐 Acesso no Claude Code Web

Como você está usando o Claude Code Web (remoto), siga estes passos:

### 1. Port Forwarding

Na interface do Claude Code Web:
- Procure pelo menu/ícone de **"Ports"** ou **"Port Forwarding"**
- Adicione a porta **5174** (Frontend)
- Adicione a porta **8001** (Backend - opcional)

### 2. Acessar a Aplicação

- A plataforma irá gerar uma URL pública (algo como `https://xxx-5174.app`)
- Use essa URL para acessar o frontend da aplicação

## 🏠 Acesso Local (se rodar localmente)

Se você clonar o repositório e rodar localmente:

```bash
# Instalar e iniciar
./start.py

# Acessar:
Frontend:  http://localhost:5174
Backend:   http://localhost:8001
API Docs:  http://localhost:8001/docs
```

## 📊 Verificar Status

Para verificar se os servidores estão rodando:

```bash
# Ver processos
ps aux | grep -E 'vite|uvicorn'

# Ver logs
tail -f /tmp/broker-frontend.log
tail -f /tmp/broker-backend.log

# Testar conectividade
curl http://localhost:5174
curl http://localhost:8001/api/health
```

## ⚠️ Importante

- **ERR_CONNECTION_REFUSED**: Significa que você está tentando acessar `localhost` de um navegador externo. Use o Port Forwarding!
- Os servidores estão configurados com `host: 0.0.0.0` para aceitar conexões de qualquer origem
- O frontend faz proxy das chamadas `/api` para o backend automaticamente

# 🚀 Guia de Deployment - Broker B3

## 📋 Resumo

Esta aplicação pode ser deployada em diversos serviços de cloud. Abaixo estão as opções recomendadas:

---

## ✅ Opção 1: Render.com (RECOMENDADO - GRÁTIS)

O Render.com oferece plano gratuito e já está configurado neste repositório.

### Passo a Passo:

1. **Acesse [Render.com](https://render.com)** e faça login/cadastro

2. **Conecte seu repositório GitHub:**
   - No dashboard, clique em "New +"
   - Selecione "Blueprint"
   - Conecte sua conta do GitHub
   - Selecione o repositório `anthropic-claude-code`
   - O Render vai detectar automaticamente o arquivo `render.yaml`

3. **Deploy automático:**
   - O Render vai criar automaticamente 2 serviços:
     - `broker-backend` (FastAPI)
     - `broker-frontend` (React/Vite)
   - Aguarde o build completar (~5 minutos)

4. **Acesse sua aplicação:**
   - O Render fornecerá URLs públicas para ambos os serviços
   - Exemplo: `https://broker-frontend.onrender.com`

### ⚠️ Limitações do Plano Gratuito:
- Serviços podem "dormir" após 15 minutos de inatividade
- Primeiro acesso após período de inatividade pode demorar ~30s

---

## 🔧 Opção 2: Railway.app

Railway também oferece plano gratuito generoso.

### Passo a Passo:

1. **Acesse [Railway.app](https://railway.app)** e faça login com GitHub

2. **Criar novo projeto:**
   - Clique em "New Project"
   - Selecione "Deploy from GitHub repo"
   - Escolha `anthropic-claude-code`

3. **Configurar Backend:**
   - Railway detectará o Dockerfile automaticamente
   - Configure a porta: `8001`
   - Defina o diretório raiz: `broker/backend`

4. **Configurar Frontend:**
   - Adicione novo serviço no mesmo projeto
   - Diretório raiz: `broker/frontend`
   - Build command: `npm install && npm run build`
   - Start command: `npm run preview -- --host 0.0.0.0 --port $PORT`
   - Variável de ambiente: `VITE_API_URL` = URL do backend

---

## 🌐 Opção 3: Vercel (Frontend) + Render (Backend)

### Frontend no Vercel:

1. **Acesse [Vercel.com](https://vercel.com)**
2. **Import seu repositório GitHub**
3. **Configure:**
   - Framework Preset: `Vite`
   - Root Directory: `broker/frontend`
   - Build Command: `npm run build`
   - Output Directory: `dist`
4. **Adicione variável de ambiente:**
   - `VITE_API_URL` = URL do backend no Render

### Backend no Render:

1. **Acesse [Render.com](https://render.com)**
2. **New + → Web Service**
3. **Configure:**
   - Repository: `anthropic-claude-code`
   - Root Directory: `broker/backend`
   - Runtime: `Docker`
   - Dockerfile Path: `./Dockerfile`

---

## 🔐 Variáveis de Ambiente

### Backend:
- `PORT` - Porta do servidor (padrão: 8001)
- `DATABASE_URL` - URL do banco SQLite (opcional)

### Frontend:
- `VITE_API_URL` - URL do backend (ex: `https://broker-backend.onrender.com`)

---

## 📊 Verificação de Deployment

Após o deployment, verifique:

### Backend:
```bash
curl https://seu-backend.onrender.com/api/health
```

Deve retornar: `{"status": "healthy"}`

### Frontend:
- Acesse a URL fornecida
- Verifique se o dashboard carrega
- Teste a listagem de ações

---

## 🆘 Troubleshooting

### Backend não inicia:
- Verifique logs no painel do Render/Railway
- Confirme que o Dockerfile está correto
- Verifique se todas as dependências estão no requirements.txt

### Frontend não conecta ao Backend:
- Verifique a variável `VITE_API_URL`
- Confirme que o backend está rodando
- Verifique CORS no backend

### Dados não aparecem:
- O backend precisa baixar os dados na primeira execução
- Isso pode demorar alguns minutos
- Verifique os logs do backend

---

## 🔄 Atualizações Automáticas

Todos os serviços estão configurados para fazer deploy automático quando você fizer push para o branch principal:

```bash
git push origin main
```

O Render/Railway/Vercel detectarão as mudanças e farão novo deployment automaticamente.

---

## 💰 Custos

| Serviço | Plano Gratuito | Limitações |
|---------|----------------|------------|
| Render | 750h/mês | Sleep após 15min inativo |
| Railway | $5 crédito/mês | ~500h/mês |
| Vercel | 100GB bandwidth | Sem sleep, mas só frontend |

**Recomendação:** Comece com Render (totalmente gratuito) e migre para planos pagos se necessário.

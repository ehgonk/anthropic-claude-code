# 🚀 DEPLOY AGORA - Guia Rápido

## ✅ Configuração Completa!

Tudo está pronto para deployment! Escolha uma das opções abaixo:

---

## 🎯 OPÇÃO 1: Render.com (MAIS FÁCIL)

### 1. Acesse e Conecte
- Vá em: https://render.com
- Faça login com GitHub
- Clique em **"New +"** → **"Blueprint"**

### 2. Selecione o Repositório
- Conecte sua conta GitHub
- Escolha: **`anthropic-claude-code`**
- O Render detectará automaticamente o `render.yaml`

### 3. Clique em "Apply"
- O Render criará automaticamente:
  - ✅ Backend: `broker-backend`
  - ✅ Frontend: `broker-frontend`

### 4. Aguarde o Build
- Primeiro deploy: ~5-10 minutos
- URLs ficarão disponíveis assim que completar

### 5. Configure CORS (após deployment)
- Vá em **broker-backend** → **Environment**
- Edite `BROKER_CORS_ORIGINS`
- Adicione a URL do frontend: `https://broker-frontend.onrender.com`
- Salve e aguarde redeploy

---

## 🎯 OPÇÃO 2: Vercel (Apenas Frontend)

Se preferir Vercel para o frontend:

### 1. Frontend no Vercel
```bash
# No seu computador local
git clone https://github.com/ehgonk/anthropic-claude-code.git
cd anthropic-claude-code

# Login no Vercel
vercel login

# Deploy
cd broker/frontend
vercel --prod
```

### 2. Backend no Render
- Siga os passos da Opção 1
- Mas só para o backend

### 3. Configure Variáveis
No Vercel:
- `VITE_API_URL` = URL do backend no Render

No Render (backend):
- `BROKER_CORS_ORIGINS` = URL do Vercel

---

## 📊 Verificar se Funcionou

### Teste o Backend:
```bash
curl https://broker-backend.onrender.com/api/health
```

Deve retornar: `{"status":"healthy"}`

### Teste o Frontend:
Acesse a URL fornecida e veja se o dashboard carrega!

---

## 🆘 Problemas?

### Backend demora para responder na primeira vez?
- **Normal!** Plano gratuito "dorme" após inatividade
- Primeira requisição acorda o serviço (~30s)

### Frontend não conecta ao backend?
1. Verifique `BROKER_CORS_ORIGINS` no backend
2. Verifique `VITE_API_URL` no frontend
3. Confirme que backend está online

### Dados não aparecem?
- Backend baixa dados na primeira execução
- Pode demorar ~5 minutos
- Veja logs: Render Dashboard → Backend → Logs

---

## 💡 Dicas

### URLs Típicas:
- **Backend**: `https://broker-backend.onrender.com`
- **Frontend**: `https://broker-frontend.onrender.com`
- **API Docs**: `https://broker-backend.onrender.com/docs`

### Monitorar Logs:
- Render Dashboard → Serviço → **Logs** (tab)

### Forçar Novo Deploy:
- Render Dashboard → Serviço → **Manual Deploy**

---

## 📚 Documentação Completa

Para mais detalhes, veja: **DEPLOYMENT.md**

---

## ✨ Pronto!

Sua aplicação de bolsa de valores estará online em minutos! 🎉

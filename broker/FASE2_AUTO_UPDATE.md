# ⚡ FASE 2: Sistema de Auto-Update

Sistema completo de atualização automática de dados da B3 usando Yahoo Finance API.

---

## 🎯 Funcionalidades

### ✅ **1. Auto-Update Service**
Serviço inteligente que:
- **Detecta automaticamente** dados faltantes no banco
- **Update incremental**: baixa apenas anos novos
- **Update forçado**: re-download completo quando necessário
- **Tracking de status**: acompanha execuções, erros e estatísticas

### ✅ **2. API REST Completa**

#### `GET /api/update/status`
Retorna status da última atualização:
```json
{
  "last_run": "2026-02-20T22:00:01.312124",
  "last_success": "2026-02-20T22:00:01.324030",
  "last_error": null,
  "is_running": false,
  "stats": {
    "status": "success",
    "years": 2,
    "stocks": 10,
    "prices": 5000
  }
}
```

#### `GET /api/update/last-update-date`
Retorna data da última atualização formatada:
```json
{
  "last_update": "19/02/2026",
  "raw_date": "2026-02-19"
}
```

#### `POST /api/update/run?force=false`
Executa atualização em background:
```bash
curl -X POST "http://localhost:8001/api/update/run?force=false"
```

#### `POST /api/update/run-sync`
Executa atualização síncrona (espera completar):
```bash
curl -X POST "http://localhost:8001/api/update/run-sync"
```
⚠️ **Atenção**: Pode demorar vários minutos!

### ✅ **3. Update Automático no Startup**
- **Atualização incremental** ao iniciar a aplicação
- Detecta automaticamente dados faltantes
- Baixa apenas anos novos (não re-baixa dados existentes)
- Executa em background durante o startup
- **Data da última atualização** exibida no headline (dd/mm/aaaa)

### ✅ **4. Logging Estruturado**
Logs coloridos e organizados:
```
2026-02-20 22:00:01 | INFO     | app.services.auto_update | Starting update...
2026-02-20 22:00:02 | INFO     | app.services.auto_update | Update completed: 10 stocks, 5000 prices
```

---

## 🚀 Como Usar

### Iniciar o Servidor
```bash
cd broker/backend
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8001
```

### Testar Manualmente
```bash
# Ver status
curl http://localhost:8001/api/update/status | jq

# Ver data da última atualização
curl http://localhost:8001/api/update/last-update-date | jq

# Forçar update manual
curl -X POST "http://localhost:8001/api/update/run?force=true"
```

---

## 📁 Arquitetura

```
broker/
├── backend/app/
│   ├── services/
│   │   └── auto_update.py       # Lógica de update incremental
│   ├── api/
│   │   └── update.py            # Endpoints REST
│   ├── logging_config.py        # Configuração de logs
│   └── main.py                  # Integração com FastAPI
└── frontend/src/
    ├── services/
    │   └── api.ts               # Cliente HTTP
    ├── components/
    │   └── TopBar.tsx           # Exibe data da última atualização
    └── App.tsx                  # Carrega dados no startup
```

### Fluxo de Update

```
┌─────────────────────────┐
│  App Startup            │
│  (Frontend/Backend)     │
└──────────┬──────────────┘
           │
           ▼
┌─────────────────────────┐
│  AutoUpdateService      │
│  - Check last date      │
│  - Calculate missing    │
└──────────┬──────────────┘
           │
           ▼
┌─────────────────────────┐
│  For each year:         │
│  - Fetch from Yahoo API │
│  - Parse JSON data      │
│  - Update database      │
└──────────┬──────────────┘
           │
           ▼
┌─────────────────────────┐
│  Update Status          │
│  - Log results          │
│  - Store stats          │
│  - Frontend displays    │
└─────────────────────────┘
```

---

## 🎨 Frontend Integration

O frontend exibe a data da última atualização no **headline** (barra superior):

```
╔════════════════════════════════════════════════════════════╗
║ Broker  |  PETR4  R$ 34.50  +1.23%  |  📊 Última atualização: 19/02/2026 ║
╚════════════════════════════════════════════════════════════╝
```

A data é:
- ✅ Formatada em **dd/mm/aaaa** (padrão brasileiro)
- ✅ Buscada do endpoint `/api/update/last-update-date`
- ✅ Atualizada automaticamente no startup

---

## 🐛 Troubleshooting

### Update não executou
Verifique os logs do startup:
```bash
tail -100 /tmp/uvicorn*.log | grep "auto-update"
```

### Data não aparece no frontend
Teste o endpoint:
```bash
curl http://localhost:8001/api/update/last-update-date
```

---

## 📊 Estatísticas

O sistema rastreia:
- **last_run**: Última tentativa de update
- **last_success**: Última atualização bem-sucedida
- **last_error**: Último erro (se houver)
- **stats**: Detalhes da última execução
  - `years`: Quantos anos foram atualizados
  - `stocks`: Quantas ações foram processadas
  - `prices`: Quantos registros de preço foram adicionados

---

## ✅ Testes

Sistema testado e funcionando:
- ✅ Update incremental no startup
- ✅ Endpoint de data formatada (dd/mm/aaaa)
- ✅ Frontend exibe data no headline
- ✅ Update manual via API
- ✅ Logging estruturado
- ✅ Tratamento de erros

---

## 🚀 Próximos Passos

**FASE 3**: Interface Web
- Dashboard com gráficos interativos
- Visualização de histórico
- Controle manual do auto-update
- Indicadores de performance

---

**Desenvolvido em**: Fase 2 do projeto Broker
**Data**: 2026-02-20
**Status**: ✅ Concluído e Testado

# ⚡ FASE 2: Sistema de Auto-Update

Sistema completo de atualização automática de dados da B3.

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

#### `GET /api/update/schedule`
Informações sobre agendamento:
```json
{
  "enabled": true,
  "next_run": "2026-02-21T19:00:00+00:00",
  "timezone": "America/Sao_Paulo",
  "schedule": "Daily at 19:00 (7 PM Brazil time)"
}
```

### ✅ **3. Scheduler Automático**
- **APScheduler** integrado com FastAPI
- **Agendamento diário** às 19:00 (horário de Brasília)
- Executa após fechamento do mercado
- Startup/shutdown automático com o servidor

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

⚠️ **IMPORTANTE**: **NÃO use `--reload`** - causa conflito com APScheduler!

### Testar Manualmente
```bash
# Ver status
curl http://localhost:8001/api/update/status | jq

# Forçar update manual
curl -X POST "http://localhost:8001/api/update/run?force=true"

# Ver próxima execução agendada
curl http://localhost:8001/api/update/schedule | jq
```

---

## 📁 Arquitetura

```
broker/backend/app/
├── services/
│   └── auto_update.py       # Lógica de update incremental
├── api/
│   └── update.py            # Endpoints REST
├── scheduler.py             # APScheduler integration
├── logging_config.py        # Configuração de logs
└── main.py                  # Integração com FastAPI
```

### Fluxo de Update

```
┌─────────────────────────┐
│  Scheduler (19:00)      │
│  ou Manual Trigger      │
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
│  - Download COTAHIST    │
│  - Parse data           │
│  - Update database      │
└──────────┬──────────────┘
           │
           ▼
┌─────────────────────────┐
│  Update Status          │
│  - Log results          │
│  - Store stats          │
└─────────────────────────┘
```

---

## 🔧 Configuração

### Alterar Horário do Scheduler
Edite `app/main.py`:
```python
scheduler.start(
    hour=19,              # Hora (0-23)
    minute=0,             # Minuto (0-59)
    timezone="America/Sao_Paulo"
)
```

### Alterar Nível de Logs
Edite `app/main.py`:
```python
setup_logging(level="DEBUG")  # DEBUG, INFO, WARNING, ERROR
```

---

## 🐛 Troubleshooting

### Servidor trava no startup
**Causa**: Uso do `--reload` com APScheduler

**Solução**: Remova a flag `--reload` do uvicorn:
```bash
# ❌ NÃO fazer
uvicorn app.main:app --reload

# ✅ Fazer
uvicorn app.main:app
```

### Update falha
Verifique os logs:
```bash
curl http://localhost:8001/api/update/status
```

Rode manualmente para ver erro:
```bash
curl -X POST http://localhost:8001/api/update/run-sync
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
- ✅ Update incremental (apenas dados novos)
- ✅ Update forçado (re-download completo)
- ✅ Endpoints REST (status, run, schedule)
- ✅ Scheduler automático (diário)
- ✅ Logging estruturado
- ✅ Tratamento de erros
- ✅ Background tasks

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

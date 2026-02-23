# 📊 EXEMPLOS DE USO - BROKER B3 (118 Ações)

## 🎯 Download por Setor

### 🏦 BANCOS & SEGUROS (10 ações)
```bash
curl -X POST "http://localhost:8001/api/stocks/download/investing?symbols=ITUB4,ITUB3,BBDC4,BBDC3,BBAS3,SANB11,BBSE3,ITSA4,BPAC11,SULA11&days=365"
```

### 🛢️ PETRÓLEO & GÁS (6 ações)
```bash
curl -X POST "http://localhost:8001/api/stocks/download/investing?symbols=PETR4,PETR3,PRIO3,RRRP3,RECV3,UGPA3&days=365"
```

### ⛏️ MINERAÇÃO & SIDERURGIA (9 ações)
```bash
curl -X POST "http://localhost:8001/api/stocks/download/investing?symbols=VALE3,GGBR4,GGBR3,CSNA3,USIM5,USIM3,GOAU4,KLBN11,KLBN4&days=365"
```

### ⚡ ENERGIA ELÉTRICA (15 ações)
```bash
curl -X POST "http://localhost:8001/api/stocks/download/investing?symbols=ELET3,ELET6,ENGI11,CPLE6,CPLE3,CMIG4,CMIG3,EGIE3,TAEE11,TRPL4,NEOE3,CPFE3,EQTL3,AESB3,ALUP11&days=365"
```

### 💧 SANEAMENTO & GÁS (5 ações)
```bash
curl -X POST "http://localhost:8001/api/stocks/download/investing?symbols=SAPR11,SBSP3,CSAN3,CGAS5,DASA3&days=365"
```

### 🛒 VAREJO & E-COMMERCE (10 ações)
```bash
curl -X POST "http://localhost:8001/api/stocks/download/investing?symbols=MGLU3,LREN3,ARZZ3,VVAR3,PCAR3,CRFB3,ASAI3,SOMA3,VIIA3,CEAB3&days=365"
```

### 🥩 ALIMENTOS & BEBIDAS (8 ações)
```bash
curl -X POST "http://localhost:8001/api/stocks/download/investing?symbols=ABEV3,BRFS3,JBSS3,MRFG3,BEEF3,SMTO3,CAML3,MDIA3&days=365"
```

### 📞 TELECOM (3 ações)
```bash
curl -X POST "http://localhost:8001/api/stocks/download/investing?symbols=VIVT3,TIMS3,OIBR3&days=365"
```

### 🏗️ CONSTRUÇÃO & IMOBILIÁRIO (8 ações)
```bash
curl -X POST "http://localhost:8001/api/stocks/download/investing?symbols=CYRE3,MRVE3,EZTC3,CVCB3,TEND3,DIRR3,JHSF3,MULT3&days=365"
```

### 🚛 LOGÍSTICA & TRANSPORTE (10 ações)
```bash
curl -X POST "http://localhost:8001/api/stocks/download/investing?symbols=RAIL3,CCRO3,ECOR3,AZUL4,GOLL4,EMBR3,VBBR3,RADL3,BRML3,GRND3&days=365"
```

### 🏥 SAÚDE & FARMACÊUTICO (7 ações)
```bash
curl -X POST "http://localhost:8001/api/stocks/download/investing?symbols=RADL3,HAPV3,FLRY3,GNDI3,QUAL3,PNVL3,ODPV3&days=365"
```

### 💳 FINANCEIRAS & SERVIÇOS (8 ações)
```bash
curl -X POST "http://localhost:8001/api/stocks/download/investing?symbols=B3SA3,RENT3,CIEL3,PAGS34,RDOR3,PRIO3,LWSA3,CASH3&days=365"
```

### ⚙️ INDÚSTRIA & TECNOLOGIA (10 ações)
```bash
curl -X POST "http://localhost:8001/api/stocks/download/investing?symbols=WEGE3,EMBR3,SUZB3,TOTS3,RAIZ4,BRKM5,PCAR3,POSI3,INTB3,LEVE3&days=365"
```

### 🌾 AGRONEGÓCIO (5 ações)
```bash
curl -X POST "http://localhost:8001/api/stocks/download/investing?symbols=SLCE3,TTEN3,FRAS3,AGRO3,BRSR6&days=365"
```

### 🎓 EDUCAÇÃO (4 ações)
```bash
curl -X POST "http://localhost:8001/api/stocks/download/investing?symbols=YDUQ3,COGN3,ANIM3,SEER3&days=365"
```

### 🎬 MÍDIA & ENTRETENIMENTO (3 ações)
```bash
curl -X POST "http://localhost:8001/api/stocks/download/investing?symbols=TIMB3,MOVI3,ORVR3&days=365"
```

---

## 🏆 Downloads Especiais

### TOP 10 Maiores Empresas Brasil (Market Cap)
```bash
curl -X POST "http://localhost:8001/api/stocks/download/investing?symbols=PETR4,VALE3,ITUB4,BBDC4,ABEV3,BBAS3,B3SA3,WEGE3,RENT3,SUZB3&days=365"
```

### TOP 20 Ibovespa (Mais Líquidas)
```bash
curl -X POST "http://localhost:8001/api/stocks/download/investing?symbols=PETR4,VALE3,ITUB4,BBDC4,ABEV3,B3SA3,WEGE3,RENT3,SUZB3,MGLU3,LREN3,RAIL3,VIVT3,GGBR4,EMBR3,JBSS3,BBAS3,ELET3,RADL3,CCRO3&days=365"
```

### COMPLETO - Todas 118 Ações (Histórico desde 1994)
```bash
curl -X POST "http://localhost:8001/api/stocks/download/investing?days=11680"
```
**Tempo estimado:** ~10-12 minutos
**Dados:** ~30 anos de histórico (1994-07-01 até hoje)

---

## 📊 Consultas de Dados

### Listar ações disponíveis
```bash
curl http://localhost:8001/api/stocks/list
```

### Obter dados de uma ação (últimos 30 dias)
```bash
curl "http://localhost:8001/api/stocks/PETR4?days=30"
```

### Obter dados por período específico
```bash
curl "http://localhost:8001/api/stocks/VALE3?start_date=2024-01-01&end_date=2026-02-23"
```

### Status do download
```bash
curl http://localhost:8001/api/stocks/download/status
```

---

## ⚙️ Configurações do Sistema

### Rate Limiting
```
✅ Batch Size: 6 ações por lote
✅ Delay: 6 segundos entre batches
✅ Max: 10 requisições/minuto
✅ Retry: Backoff exponencial (3s → 6s → 12s)
```

### Filtro de Data
```
✅ Data mínima: 1994-07-01 (início do Plano Real)
✅ Remoção automática de dados inconsistentes
✅ Validação de integridade
```

### Performance Estimada
| Ações | Batches | Tempo |
|-------|---------|-------|
| 6 | 1 | ~20s |
| 18 | 3 | ~1m |
| 30 | 5 | ~2m |
| 60 | 10 | ~4m |
| 118 | 20 | ~10-12m |

---

## 🌐 Acesso Web

```
Frontend:  http://localhost:5174
Backend:   http://localhost:8001
API Docs:  http://localhost:8001/docs (Swagger UI)
```

---

## 📈 Cobertura do Mercado

```
✅ 118 símbolos configurados
✅ 16 setores da economia
✅ >90% do volume negociado na B3
✅ TODAS ações do Ibovespa
✅ Principais mid-caps líquidas
✅ Blue chips + Growth stocks
```

---

## 🎯 Casos de Uso

### 1. Análise de Setor
Baixar todas ações de energia para análise comparativa:
```bash
curl -X POST "http://localhost:8001/api/stocks/download/investing?symbols=ELET3,ENGI11,CPLE6,CMIG4,EGIE3,TAEE11,NEOE3,CPFE3,EQTL3&days=730"
```

### 2. Portfólio Diversificado
Baixar 1 ação de cada setor:
```bash
curl -X POST "http://localhost:8001/api/stocks/download/investing?symbols=ITUB4,PETR4,VALE3,ELET3,MGLU3,ABEV3,VIVT3,CYRE3,RAIL3,RADL3,B3SA3,WEGE3&days=365"
```

### 3. Backtest Completo
Baixar histórico completo de 30 anos:
```bash
curl -X POST "http://localhost:8001/api/stocks/download/investing?symbols=PETR4,VALE3,ITUB4&days=11680"
```

### 4. Monitoramento Diário
Baixar apenas últimos 30 dias (rápido):
```bash
curl -X POST "http://localhost:8001/api/stocks/download/investing?symbols=PETR4,VALE3,ITUB4,BBDC4&days=30"
```

---

## 📝 Notas Importantes

1. **Internet Required**: Sistema precisa de conectividade para web scraping
2. **Rate Limiting**: Respeita limites do Investing.com (10 req/min)
3. **Dados Históricos**: Limitados à disponibilidade no Investing.com
4. **Filtro Plano Real**: Dados antes de Jul/1994 são removidos
5. **Batching**: Downloads grandes são processados em lotes de 6

---

## 🚀 Próximos Passos

1. Iniciar servidores: `python start.py`
2. Acessar frontend: http://localhost:5174
3. Testar API: http://localhost:8001/docs
4. Download primeiro lote: `curl -X POST "http://localhost:8001/api/stocks/download/investing?symbols=PETR4,VALE3,ITUB4&days=365"`
5. Verificar dados: `curl http://localhost:8001/api/stocks/list`

**Happy Trading! 📈🇧🇷**

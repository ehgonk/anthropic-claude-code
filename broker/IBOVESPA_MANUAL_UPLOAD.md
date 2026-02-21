# 📊 Ibovespa - Upload Manual (B3)

Sistema de upload manual de dados históricos do **Índice Ibovespa** direto da fonte B3.

---

## 🎯 **Visão Geral**

- ✅ **Upload Manual** - Você baixa da B3 e faz upload
- ✅ **Fonte Oficial** - Dados direto da B3
- ✅ **Formato CSV** - Suporte ao formato B3
- ✅ **Sem Dependências Externas** - Não usa Yahoo Finance
- ✅ **Mesmo Banco de Dados** - Integrado com ações

---

## 📥 **Como Usar:**

### **Passo 1: Baixar Dados da B3**

1. Acesse: https://www.b3.com.br/pt_br/market-data-e-indices/indices/indices-amplos/indice-ibovespa-ibovespa-estatisticas-historicas.htm

2. Clique em **"Download"** para baixar o arquivo histórico

3. Salve o arquivo CSV no seu computador

### **Passo 2: Fazer Upload**

```bash
# Via curl
curl -X POST "http://localhost:8001/api/ibovespa/upload/csv" \
  -F "file=@ibovespa_historico.csv"

# Via Python
import httpx

with open("ibovespa_historico.csv", "rb") as f:
    response = httpx.post(
        "http://localhost:8001/api/ibovespa/upload/csv",
        files={"file": f}
    )
    print(response.json())
```

### **Passo 3: Verificar Dados**

```bash
# Ver informações do Ibovespa
curl http://localhost:8001/api/ibovespa/info | jq

# Ver no frontend (como qualquer ação)
curl http://localhost:8001/api/stocks/IBOV/candles | jq
```

---

## 📄 **Formato do CSV**

### **Formato Esperado (B3):**

```csv
Data,Abertura,Máxima,Mínima,Fechamento,Volume
01/07/1994,100.00,105.00,98.00,103.50,1000000
02/07/1994,103.50,108.00,102.00,106.25,1200000
```

### **Colunas Aceitas:**

| Português | Inglês | Obrigatório |
|-----------|--------|-------------|
| Data | Date | ✅ Sim |
| Abertura | Open | ✅ Sim |
| Máxima | High | ✅ Sim |
| Mínima | Low | ✅ Sim |
| Fechamento | Close | ✅ Sim |
| Volume | Volume | ⚠️ Opcional |

### **Formato de Data:**

- ✅ **dd/mm/yyyy** (padrão B3)
- ❌ **yyyy-mm-dd** (não suportado)
- ❌ **mm/dd/yyyy** (não suportado)

### **Encoding:**

- ✅ UTF-8
- ✅ UTF-8-BOM (com BOM)
- ❌ Latin-1 (não recomendado)

---

## 🔧 **API Endpoints**

### **POST /api/ibovespa/upload/csv**

Upload de arquivo CSV com dados do Ibovespa.

**Request:**
```bash
curl -X POST "http://localhost:8001/api/ibovespa/upload/csv" \
  -F "file=@dados_ibovespa.csv"
```

**Response:**
```json
{
  "status": "success",
  "records_processed": 8000,
  "records_inserted": 7500,
  "records_skipped": 500,
  "first_date": "1994-01-01",
  "last_date": "2026-02-21"
}
```

**Erros:**
- `400`: Arquivo inválido ou formato incorreto
- `500`: Erro ao processar dados

---

### **GET /api/ibovespa/info**

Informações sobre dados do Ibovespa no banco.

**Request:**
```bash
curl http://localhost:8001/api/ibovespa/info | jq
```

**Response:**
```json
{
  "status": "available",
  "symbol": "IBOV",
  "name": "Índice Bovespa",
  "current_price": 132500.00,
  "change_percent": 0.85,
  "total_records": 7500,
  "first_date": "1994-01-01",
  "last_date": "2026-02-20",
  "upload_url": "/api/ibovespa/upload/csv"
}
```

**Quando não há dados:**
```json
{
  "status": "not_found",
  "message": "Ibovespa data not available. Please upload CSV file.",
  "total_records": 0
}
```

---

### **GET /api/ibovespa/download-instructions**

Instruções passo-a-passo para download.

**Request:**
```bash
curl http://localhost:8001/api/ibovespa/download-instructions | jq
```

**Response:**
```json
{
  "title": "Como baixar dados do Ibovespa da B3",
  "steps": [
    {
      "step": 1,
      "description": "Acesse o site da B3",
      "url": "https://www.b3.com.br/..."
    },
    ...
  ],
  "csv_format": {
    "columns": ["Data", "Abertura", "Máxima", "Mínima", "Fechamento", "Volume"],
    "date_format": "dd/mm/yyyy"
  }
}
```

---

## 📊 **Regras de Processamento**

### **1. Filtro de Data:**
```python
# Apenas dados do Real (1994+)
if date.year < 1994:
    skip_record()
```

### **2. Duplicatas:**
```python
# Registros duplicados são IGNORADOS
existing_dates = get_existing_dates()
if record.date in existing_dates:
    skip_record()
```

### **3. Validação:**
```python
# Todos os campos são validados
if not (open and high and low and close):
    skip_record()
```

---

## 🗄️ **Banco de Dados**

Mesma estrutura das ações:

```sql
-- Stock entry
INSERT INTO stocks (symbol, name, price, change_percent, volume)
VALUES ('IBOV', 'Índice Bovespa', 132500.00, 0.85, 1000000);

-- Historical prices
INSERT INTO stock_prices (stock_id, date, open, high, low, close, volume)
VALUES (1, '2026-02-20', 131800, 132700, 131500, 132500, 1000000);
```

---

## 🎨 **Frontend Integration**

O Ibovespa aparece como uma "ação" normal:

```typescript
// Buscar todas as ações (inclui IBOV)
const stocks = await api.getStocks();
const ibov = stocks.find(s => s.symbol === 'IBOV');

// Exibir no gráfico
const candleData = await api.getCandleData('IBOV');

// Comparar com outras ações
const petr4 = stocks.find(s => s.symbol === 'PETR4');
compareWithIndex(petr4, ibov);
```

---

## ⚠️ **Importante**

### **Por que Upload Manual?**

1. 🔒 **B3 tem Captcha**
   - Impede downloads automatizados
   - Requer interação humana

2. 🚫 **Proxy/Firewall**
   - Ambientes corporativos bloqueiam
   - VPN/Proxy interferem

3. ✅ **Controle Total**
   - Você escolhe quando atualizar
   - Valida os dados antes do upload
   - Sem surpresas

### **Vantagens:**

- ✅ Fonte oficial (B3)
- ✅ Sem dependências externas
- ✅ Funciona em qualquer ambiente
- ✅ Dados validados por você
- ✅ Upload incremental automático

### **Desvantagens:**

- ⚠️ Requer ação manual
- ⚠️ Não atualiza automaticamente
- ⚠️ Precisa baixar da B3 periodicamente

---

## 🐛 **Troubleshooting**

### **Erro: "File must be CSV format"**
- Verifique extensão do arquivo (.csv)
- Não envie .xlsx ou .xls

### **Erro: "No valid records found"**
- Verifique formato das colunas
- Data deve estar em dd/mm/yyyy
- Arquivo deve ter header

### **Erro: "Invalid file encoding"**
- Salve como UTF-8
- Excel: "Save As" → Encoding → UTF-8
- LibreOffice: "Save As" → Character Set → UTF-8

### **Registros Skipped:**
- Duplicatas são normais
- Datas antes de 1994 são ignoradas
- Linhas inválidas são puladas

---

## 📚 **Exemplo Completo**

### **1. Baixar da B3:**
```bash
# Acesse:
https://www.b3.com.br/pt_br/market-data-e-indices/indices/indices-amplos/indice-ibovespa-ibovespa-estatisticas-historicas.htm

# Download: ibovespa_historico.csv
```

### **2. Upload:**
```bash
curl -X POST "http://localhost:8001/api/ibovespa/upload/csv" \
  -F "file=@ibovespa_historico.csv"
```

### **3. Verificar:**
```bash
# Info
curl http://localhost:8001/api/ibovespa/info

# Ver no frontend
http://localhost:5174
# Selecionar: IBOV
```

---

## 🚀 **Arquitetura**

```
┌─────────────────────┐
│   Usuário           │
│  (Navegador/API)    │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│   POST /upload/csv  │
│  (FastAPI Endpoint) │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│   Parse CSV         │
│  - Validate format  │
│  - Filter >= 1994   │
│  - Skip duplicates  │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│   Database          │
│  - stocks (IBOV)    │
│  - stock_prices     │
└─────────────────────┘
```

---

## ✅ **Status**

| Feature | Status |
|---------|--------|
| Upload Manual CSV | ✅ Implementado |
| Parse B3 Format | ✅ Implementado |
| Validação de Dados | ✅ Implementado |
| Skip Duplicatas | ✅ Implementado |
| Info Endpoint | ✅ Implementado |
| Instructions Endpoint | ✅ Implementado |
| Frontend Integration | ✅ Compatível |
| Auto-Update | ❌ Desabilitado (manual only) |

---

## 📝 **Notas**

- **Sem Yahoo Finance**: Sistema não depende de fontes externas
- **Sem Auto-Update**: Requer upload manual periódico
- **B3 Oficial**: Dados direto da fonte oficial
- **Incremental**: Upload múltiplo funciona (skip automático)

---

**Desenvolvido em**: Fase 2 do projeto Broker
**Data**: 2026-02-21
**Status**: ✅ Implementado
**Modo**: Manual Upload Only

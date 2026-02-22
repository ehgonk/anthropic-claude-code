# 🔧 Yahoo Finance - Guia de Troubleshooting

## ⚠️ Erro 429: Too Many Requests

Este é o erro mais comum ao fazer download de dados históricos.

### O que significa?

O Yahoo Finance está bloqueando temporariamente suas requisições por **rate limiting** (limite de requisições por tempo).

### Sintomas:

```
429 Client Error: Too Many Requests for url: https://query2.finance.yahoo.com/...
Failed to get ticker 'PETR4.SA' reason: Expecting value: line 1 column 1 (char 0)
$PETR4.SA: possibly delisted; no timezone found
```

### Soluções:

#### 1️⃣ Aguardar (Recomendado)

O rate limit geralmente expira em 15-30 minutos. Use o comando wait:

```bash
python scripts/download_data_standalone.py wait 15
```

Ou aguarde manualmente e tente novamente depois.

#### 2️⃣ Usar Modo SLOW

O modo slow usa delays muito maiores entre requisições:

```bash
python scripts/download_data_standalone.py all --slow
```

**Configuração do modo SLOW:**
- Delay entre ações: 10s (normal: 3s)
- Delay entre batches: 30s (normal: 5s)

⏱️ **Tempo estimado modo SLOW:**
- 30 ações × 9 batches × 10s = ~45 minutos total
- Modo normal: ~15 minutos

#### 3️⃣ Usar Modo TEST primeiro

Sempre teste com poucas ações antes do download completo:

```bash
python scripts/download_data_standalone.py test
```

Isso baixa apenas 5 ações dos últimos 6 meses para validar que está funcionando.

#### 4️⃣ Diagnosticar o problema

Execute o script de diagnóstico:

```bash
python scripts/test_yahoo.py
```

Isso testa 6 cenários diferentes e identifica onde está o problema.

## 🔍 Diagnóstico de Erros

### Erro: "Expecting value: line 1 column 1 (char 0)"

**Causa:** Yahoo Finance retornou resposta vazia ou HTML em vez de JSON.

**Soluções:**
1. Aguardar rate limit expirar (15-30 min)
2. Usar modo SLOW
3. Verificar conexão com internet

### Erro: "possibly delisted; no timezone found"

**Causa:** yfinance não conseguiu obter dados da ação.

**Possíveis motivos:**
1. Rate limiting ativo (erro 429)
2. Ação realmente não existe para o período
3. Ticker incorreto

**Solução:**
- Se TODAS as ações falharem: é rate limiting
- Se APENAS ALGUMAS falharem: pode ser ticker incorreto ou dados não disponíveis

### Status 429 no test_yahoo.py

**Teste 1-2:**
- Status 429: Problema de rede ou bloqueio geral
- Status 200: Conexão OK

**Teste 3-6:**
- Erro 429: Rate limiting ativo, aguarde 15-30 minutos

## 📊 Fluxo de Trabalho Recomendado

### Para primeira vez:

```bash
# 1. Diagnosticar
python scripts/test_yahoo.py

# 2. Se diagnóstico OK, testar download
python scripts/download_data_standalone.py test

# 3. Se teste OK, baixar tudo em modo SLOW (mais seguro)
python scripts/download_data_standalone.py all --slow
```

### Se receber erro 429:

```bash
# 1. Aguardar 15 minutos
python scripts/download_data_standalone.py wait 15

# 2. Testar novamente
python scripts/download_data_standalone.py test

# 3. Se OK, continuar com modo SLOW
python scripts/download_data_standalone.py all --slow
```

### Para atualizações diárias:

```bash
# Atualizar últimos 7 dias (mais leve)
python scripts/download_data_standalone.py daily
```

## ⚙️ Configurações Avançadas

Para ajustar delays manualmente, edite `scripts/download_data_standalone.py`:

```python
# Configurações normais
BATCH_DELAY_SECONDS = 5
STOCK_DELAY_SECONDS = 3

# Modo SLOW
SLOW_MODE_STOCK_DELAY = 10
SLOW_MODE_BATCH_DELAY = 30
```

Valores recomendados:
- **Normal:** delays atuais (pode dar rate limiting)
- **SLOW:** delays 2-3x maiores (mais seguro)
- **VERY SLOW:** delays 5x maiores (se SLOW não funcionar)

## 🌐 Alternativas

Se Yahoo Finance continuar bloqueando:

1. **Usar VPN** - Trocar IP pode resetar rate limit
2. **Dividir downloads** - Baixar em sessões diferentes (dias diferentes)
3. **Usar Alpha Vantage** - API alternativa (requer chave gratuita)
4. **Usar Polygon.io** - API alternativa (requer chave)

## 💡 Dicas

- ✅ **SEMPRE** use modo `test` antes de download completo
- ✅ **SEMPRE** use modo `--slow` na primeira vez
- ✅ Evite rodar o script múltiplas vezes seguidas
- ✅ Se der erro, aguarde 15-30 minutos
- ❌ NÃO reduza os delays (vai piorar o rate limiting)
- ❌ NÃO force múltiplas tentativas sem aguardar

## 📝 Logs e Estatísticas

Verificar estatísticas do banco:

```bash
python scripts/download_data_standalone.py stats
```

Mostra:
- Total de registros
- Período de cobertura
- Ações com dados
- Anos disponíveis

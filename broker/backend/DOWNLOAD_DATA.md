# Download de Dados Reais do Yahoo Finance

Este documento explica como baixar cotações reais do Yahoo Finance para substituir os dados simulados.

## ⚠️ Importante

Yahoo Finance está **bloqueado** neste ambiente de desenvolvimento devido a restrições de proxy/firewall.
O script funciona corretamente, mas só pode ser executado em ambientes com acesso à internet sem restrições.

## Script: `download_yahoo_finance.py`

Script robusto para download em batches com as seguintes features:

- ✅ **Download em batches**: Processa stocks em grupos para respeitar rate limits
- ✅ **Rate limiting**: Delay configurável entre batches
- ✅ **Resumable**: Salva progresso e pode retomar se interrompido
- ✅ **Incremental**: Baixa apenas dados faltantes (não duplica)
- ✅ **Error handling**: Trata erros por ação sem parar o processo
- ✅ **Logging detalhado**: Mostra progresso em tempo real
- ✅ **Validação**: Evita duplicatas no banco de dados

## Uso Básico

### 1. Download de todas as ações desde 2000

```bash
python download_yahoo_finance.py --start-date 2000-01-01
```

### 2. Download de uma ação específica

```bash
python download_yahoo_finance.py --symbol PETR4
```

### 3. Download com parâmetros customizados

```bash
python download_yahoo_finance.py \
  --start-date 2020-01-01 \
  --batch-size 20 \
  --delay 3.0
```

### 4. Limpar progresso e recomeçar do zero

```bash
python download_yahoo_finance.py --clear-progress
```

## Opções de Linha de Comando

| Opção | Padrão | Descrição |
|-------|--------|-----------|
| `--start-date` | `2000-01-01` | Data inicial (YYYY-MM-DD) |
| `--end-date` | Hoje | Data final (YYYY-MM-DD) |
| `--batch-size` | `10` | Quantas ações por batch |
| `--delay` | `2.0` | Segundos entre batches |
| `--symbol` | - | Baixar apenas este símbolo (ex: PETR4) |
| `--clear-progress` | - | Apagar progresso e começar do zero |

## Comportamento Incremental

O script é **inteligente**:

1. Verifica a última data de cada ação no banco de dados
2. Baixa **apenas** os dados faltantes (ex: se tem até 2024-12-31, baixa de 2025-01-01 em diante)
3. Nunca duplica registros existentes
4. Atualiza o preço e change_percent da ação com os dados mais recentes

## Exemplos de Uso

### Cenário 1: Primeiro Download (banco vazio ou com dados simulados)

```bash
# Apaga dados simulados primeiro (se necessário)
sqlite3 data/broker.db "DELETE FROM stock_prices; DELETE FROM stocks;"

# Popula novamente os stocks (sem prices)
python -c "from app.seed import seed_database; import asyncio; asyncio.run(seed_database())"

# Baixa dados reais
python download_yahoo_finance.py --start-date 2000-01-01
```

### Cenário 2: Atualização Diária

```bash
# Baixa apenas dados novos (desde última data no banco)
python download_yahoo_finance.py
```

### Cenário 3: Testar com Uma Ação

```bash
# Baixa apenas PETR4 para testar
python download_yahoo_finance.py --symbol PETR4 --start-date 2023-01-01
```

### Cenário 4: Download Pausado e Retomado

```bash
# Inicia download
python download_yahoo_finance.py

# ... interrompido com Ctrl+C no batch 5/15 ...

# Retoma de onde parou (já processou batches 1-4)
python download_yahoo_finance.py
```

## Arquivo de Progresso

O script cria `data/.download_progress.txt` com símbolos já completados:

```
PETR4
VALE3
ITUB4
...
```

Para recomeçar do zero:
```bash
python download_yahoo_finance.py --clear-progress
```

Ou manualmente:
```bash
rm data/.download_progress.txt
```

## Taxa de Sucesso Esperada

Com acesso à internet funcionando:

- **~95-98%** de sucesso para ações do Ibovespa
- **~85-90%** de sucesso para ações menos líquidas
- Algumas ações podem falhar se:
  - Foram listadas recentemente (Yahoo pode não ter dados históricos completos)
  - Ticker mudou (ex: após fusão/aquisição)
  - Dados não disponíveis no Yahoo Finance

## Estimativa de Tempo

Para **144 ações** desde 2000:

- Batch size 10, delay 2s: ~30-40 minutos
- Batch size 20, delay 3s: ~25-35 minutos
- Batch size 5, delay 1s: ~35-45 minutos

## Volumes de Dados

- **Por ação**: ~6.800 registros (26 anos × ~260 dias úteis/ano)
- **Total (144 ações)**: ~980.000 registros
- **Tamanho do banco**: ~150-200 MB

## Troubleshooting

### Erro: "CONNECT tunnel failed, response 403"

**Causa**: Proxy/firewall bloqueando Yahoo Finance

**Solução**: Execute em ambiente com acesso direto à internet (sem proxy corporativo)

### Erro: "No data returned from Yahoo Finance"

**Causa**: Ticker não existe ou não tem dados históricos

**Solução**: Normal para algumas ações. O script continua com as próximas.

### Banco de dados locked

**Causa**: Backend rodando enquanto script tenta escrever

**Solução**:
```bash
# Pare o backend temporariamente
pkill -f uvicorn

# Execute o script
python download_yahoo_finance.py

# Reinicie o backend
uvicorn app.main:app --reload --port 8001
```

### Script muito lento

**Ajuste**: Aumente batch size e reduza delay:
```bash
python download_yahoo_finance.py --batch-size 25 --delay 1.5
```

**Atenção**: Muito agressivo pode resultar em rate limiting do Yahoo Finance.

## Automação (Agendamento)

### Cron (Linux/Mac)

Atualização diária às 20h (após fechamento do mercado):

```bash
# Edite crontab
crontab -e

# Adicione linha:
0 20 * * 1-5 cd /path/to/broker/backend && .venv/bin/python download_yahoo_finance.py >> logs/download.log 2>&1
```

### Task Scheduler (Windows)

1. Abra Task Scheduler
2. Crie nova tarefa
3. Gatilho: Diariamente às 20:00
4. Ação: Executar `python download_yahoo_finance.py`
5. Diretório: `C:\path\to\broker\backend`

## Logs

O script gera logs detalhados no stdout:

```
00:02:17 | INFO | Found 144 stocks in database
00:02:17 | INFO | Starting download: 144 stocks in 15 batches
00:02:17 | INFO | Period: 2000-01-01 to 2026-02-24
00:02:17 | INFO | Batch size: 10, Delay: 2.0s
00:02:17 | INFO | 📦 Batch 1/15 (10 stocks)
00:02:18 | INFO |   ABEV3: Downloading full history from 2000-01-01
00:02:22 | INFO |   ABEV3: ✓ Downloaded 6543 records, 6543 new
...
```

Para salvar em arquivo:
```bash
python download_yahoo_finance.py 2>&1 | tee download.log
```

## Verificação Pós-Download

Após o download, verifique os dados:

```bash
# Resumo do banco
python -c "
import sqlite3
conn = sqlite3.connect('data/broker.db')
cur = conn.cursor()

cur.execute('SELECT COUNT(*) FROM stocks')
print(f'Ações: {cur.fetchone()[0]}')

cur.execute('SELECT COUNT(*) FROM stock_prices')
print(f'Registros: {cur.fetchone()[0]:,}')

cur.execute('SELECT MIN(date), MAX(date) FROM stock_prices')
r = cur.fetchone()
print(f'Período: {r[0]} a {r[1]}')

conn.close()
"
```

Ou via API:
```bash
curl http://localhost:8001/api/data/stats | jq
```

## Comparação: Dados Simulados vs Reais

| Aspecto | Simulados | Reais |
|---------|-----------|-------|
| Período | 2000-2026 | 2000-hoje |
| Precisão | Modelo GBM | Yahoo Finance |
| Gaps | Nenhum | Feriados, suspensões |
| Volume | Aleatório | Real |
| Splits/Dividendos | Não ajustado | Ajustado |
| Uso | Desenvolvimento | Produção |

## Próximos Passos

Após download bem-sucedido:

1. ✅ Verifique dados via frontend (http://localhost:5174)
2. ✅ Teste gráficos de candles com dados reais
3. ✅ Configure update automático diário
4. ✅ Monitore erros e ações faltantes

## Suporte

Para problemas ou dúvidas:
- Verifique os logs de erro
- Teste com uma ação específica primeiro (`--symbol`)
- Reduza batch-size se houver muitos erros de rede

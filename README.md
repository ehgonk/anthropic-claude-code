# Anthropic Claude Code - Projects Repository

Este repositório contém dois projetos de análise do mercado de ações brasileiro (B3).

## 📂 Estrutura do Repositório

```
.
├── y-project/          # Y Project - Análise de Insider Trading
│   ├── backend/        # API FastAPI + scoring engine
│   ├── frontend/       # Dashboard React
│   └── data/           # Banco de dados SQLite
│
└── broker/             # Home Broker - Plataforma de Visualização
    ├── backend/        # API FastAPI
    ├── frontend/       # Interface React com gráficos
    └── data/           # Banco de dados SQLite
```

---

## 🔍 Y Project - Análise de Insider Trading B3

**Localização:** `y-project/`

Plataforma de análise de mercado brasileiro focada em insider trading lícito.
Cruza dados de negociações de administradores (CVM) com cotações (B3) para gerar
um score de tendência por ativo de -100 a +100.

### Features

- ✅ Score de tendência (-100 a +100)
- ✅ Análise de insider trading (40%)
- ✅ Short interest (20%)
- ✅ Fluxo estrangeiro (20%)
- ✅ Momentum técnico (20%)
- ✅ Detecção de anomalias
- ✅ Dados públicos (CVM + B3)

### Tech Stack

- **Backend:** Python 3.12+ / FastAPI / SQLAlchemy / SQLite
- **Frontend:** React 18 / TypeScript / Vite / TailwindCSS / Recharts
- **Dados:** CVM (VLMO) + B3 (COTAHIST)

### Quick Start

```bash
cd y-project

# Backend
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m app.seed
uvicorn app.main:app --reload --port 8000

# Frontend (novo terminal)
cd frontend
npm install
npm run dev
```

Acesse: http://localhost:5173

📖 [Documentação completa](./y-project/README.md)

---

## 📈 Home Broker - Plataforma de Visualização B3

**Localização:** `broker/`

Plataforma moderna de visualização de ações da B3 com gráficos interativos
de candlestick estilo TradingView.

### Features

- ✅ Gráficos candlestick interativos
- ✅ 15 ações principais da B3
- ✅ Dados históricos (365 dias)
- ✅ Interface dark theme
- ✅ Real-time quotes
- ✅ Volume tracking

### Tech Stack

- **Backend:** Python 3.11+ / FastAPI / SQLite
- **Frontend:** React 18 / TypeScript / Vite / TailwindCSS
- **Charts:** Lightweight Charts (TradingView)
- **Dados:** brapi.dev API / Mock data

### Quick Start

```bash
cd broker

# Backend
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m app.seed
uvicorn app.main:app --reload --port 8001

# Frontend (novo terminal)
cd frontend
npm install
npm run dev
```

Acesse: http://localhost:5174

📖 [Documentação completa](./broker/README.md)

---

## 🚀 Desenvolvimento

### Ambos os projetos

```bash
# Y Project (Backend na porta 8000, Frontend na 5173)
cd y-project
make setup
make seed
make backend  # Terminal 1
make frontend # Terminal 2

# Home Broker (Backend na porta 8001, Frontend na 5174)
cd broker
make setup
make seed
make backend  # Terminal 3
make frontend # Terminal 4
```

---

## 📊 Comparação dos Projetos

| Aspecto          | Y Project                    | Home Broker                  |
|------------------|------------------------------|------------------------------|
| **Foco**         | Análise de insider trading   | Visualização de cotações     |
| **Dados**        | CVM + B3 (públicos)          | brapi.dev / Mock             |
| **Features**     | Score, ranking, anomalias    | Gráficos, preços, volume     |
| **Portas**       | 8000 (API) / 5173 (UI)       | 8001 (API) / 5174 (UI)       |
| **Complexidade** | Alta (scoring engine)        | Média (visualização)         |

---

## 📄 Licença

Este projeto é distribuído sob a licença MIT.

## 🤝 Contribuindo

Contribuições são bem-vindas! Abra uma issue ou pull request.

---

**Desenvolvido com Claude Code** 🚀

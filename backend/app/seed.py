"""
Seed script — popula o banco com dados de demonstração realistas.
Útil para testar o frontend sem depender de download da CVM/B3.

Uso: python -m app.seed
"""

import asyncio
import random
from datetime import date, timedelta

from app.database import async_session, init_db
from app.models.stock import Company, InsiderScore, InsiderTrade, StockPrice
from app.services.scoring import calculate_score

# Empresas reais da B3 para demo
DEMO_COMPANIES = [
    ("PETR4", "PETROBRAS PN", "33.000.167/0001-01", "Petróleo e Gás"),
    ("VALE3", "VALE ON", "33.592.510/0001-54", "Mineração"),
    ("ITUB4", "ITAUUNIBANCO PN", "60.872.504/0001-23", "Bancos"),
    ("BBDC4", "BRADESCO PN", "60.746.948/0001-12", "Bancos"),
    ("ABEV3", "AMBEV ON", "07.526.557/0001-00", "Bebidas"),
    ("WEGE3", "WEG ON", "84.429.695/0001-11", "Máquinas"),
    ("RENT3", "LOCALIZA ON", "16.670.085/0001-55", "Aluguel de Carros"),
    ("BBAS3", "BANCO DO BRASIL ON", "00.000.000/0001-91", "Bancos"),
    ("MGLU3", "MAGAZINE LUIZA ON", "47.960.950/0001-21", "Varejo"),
    ("ELET3", "ELETROBRAS ON", "00.001.180/0001-26", "Energia"),
    ("SUZB3", "SUZANO ON", "16.404.287/0001-55", "Papel e Celulose"),
    ("JBSS3", "JBS ON", "02.916.265/0001-60", "Alimentos"),
    ("HAPV3", "HAPVIDA ON", "63.554.067/0001-98", "Saúde"),
    ("RADL3", "RAIA DROGASIL ON", "61.585.865/0001-51", "Farmácias"),
    ("RAIL3", "RUMO ON", "02.387.241/0001-60", "Logística"),
]

INSIDER_NAMES = [
    "Carlos Eduardo Silva", "Ana Maria Santos", "Roberto Ferreira Lima",
    "Marcos Vinícius Costa", "Fernanda Oliveira Rocha", "Paulo Henrique Almeida",
    "Juliana Martins Pereira", "Ricardo Barbosa Filho", "Patricia Souza Mendes",
    "André Luís Gomes",
]

INSIDER_ROLES = [
    "Diretor Presidente", "Diretor Financeiro", "Diretor de Relações com Investidores",
    "Conselheiro de Administração", "Diretor Executivo", "Vice-Presidente",
]


def _gen_prices(ticker: str, base_price: float, days: int = 180) -> list[dict]:
    """Gera série de preços realista com random walk."""
    prices = []
    price = base_price
    today = date.today()
    start = today - timedelta(days=days)

    for i in range(days):
        d = start + timedelta(days=i)
        if d.weekday() >= 5:  # Pula fins de semana
            continue
        # Random walk com drift
        change = random.gauss(0.0003, 0.02)
        price *= 1 + change
        price = max(price * 0.5, price)  # Floor

        high = price * (1 + abs(random.gauss(0, 0.01)))
        low = price * (1 - abs(random.gauss(0, 0.01)))
        open_p = price * (1 + random.gauss(0, 0.005))

        prices.append({
            "ticker": ticker,
            "trade_date": d,
            "open_price": round(open_p, 2),
            "high_price": round(high, 2),
            "low_price": round(low, 2),
            "close_price": round(price, 2),
            "volume": round(random.uniform(50_000_000, 500_000_000), 2),
            "num_trades": random.randint(5000, 50000),
            "market_type": 10,
        })

    return prices


def _gen_insider_trades(ticker: str, company_name: str, base_price: float) -> list[dict]:
    """Gera trades de insiders realistas."""
    trades = []
    today = date.today()
    num_trades = random.randint(3, 15)

    for _ in range(num_trades):
        days_ago = random.randint(1, 120)
        trade_date = today - timedelta(days=days_ago)
        if trade_date.weekday() >= 5:
            trade_date -= timedelta(days=trade_date.weekday() - 4)

        insider = random.choice(INSIDER_NAMES)
        role = random.choice(INSIDER_ROLES)
        trade_type = random.choices(["Compra", "Venda"], weights=[0.55, 0.45])[0]
        quantity = random.choice([1000, 5000, 10000, 25000, 50000, 100000])
        price = base_price * (1 + random.gauss(0, 0.05))
        price = round(max(1, price), 2)

        trades.append({
            "ticker": ticker,
            "company_name": company_name,
            "cnpj": "",
            "insider_name": insider,
            "insider_role": role,
            "trade_type": trade_type,
            "quantity": quantity,
            "price": price,
            "volume": round(quantity * price, 2),
            "trade_date": trade_date,
            "report_date": trade_date + timedelta(days=random.randint(1, 5)),
            "intermediary": random.choice(["XP Investimentos", "BTG Pactual", "Itaú BBA", "Morgan Stanley"]),
        })

    return trades


BASE_PRICES = {
    "PETR4": 38.5, "VALE3": 62.0, "ITUB4": 34.5, "BBDC4": 14.8,
    "ABEV3": 12.3, "WEGE3": 42.0, "RENT3": 48.5, "BBAS3": 28.0,
    "MGLU3": 8.5, "ELET3": 44.0, "SUZB3": 55.0, "JBSS3": 35.0,
    "HAPV3": 3.8, "RADL3": 26.5, "RAIL3": 22.0,
}


async def seed():
    """Popula banco com dados de demonstração."""
    await init_db()

    async with async_session() as db:
        # Companies
        for ticker, name, cnpj, sector in DEMO_COMPANIES:
            db.add(Company(ticker=ticker, name=name, cnpj=cnpj, sector=sector))
        await db.flush()

        # Prices + Insider trades
        for ticker, name, cnpj, sector in DEMO_COMPANIES:
            base = BASE_PRICES.get(ticker, 30.0)

            # Prices
            for p in _gen_prices(ticker, base):
                db.add(StockPrice(**p))

            # Insider trades
            for t in _gen_insider_trades(ticker, name, base):
                db.add(InsiderTrade(**t))

        await db.flush()

        # Calculate scores
        for ticker, *_ in DEMO_COMPANIES:
            try:
                score = await calculate_score(db, ticker)
                db.add(score)
            except Exception as e:
                print(f"Erro calculando score para {ticker}: {e}")

        await db.commit()
        print(f"Seed concluído: {len(DEMO_COMPANIES)} empresas com preços, trades e scores.")


if __name__ == "__main__":
    asyncio.run(seed())

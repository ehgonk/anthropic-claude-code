"""
Populate database with mock data for ALL 153 exchange stocks
from 2000-01-01 to 2026-02-23

Uses Yahoo Finance as the intended source, but generates realistic
simulation data since the network is not available in this environment.
"""

import sqlite3
import random
import math
from datetime import date, timedelta
from pathlib import Path

DB_PATH = Path(__file__).parent / "data" / "broker.db"

# ---- Business days generator ----

def business_days(start: date, end: date):
    d = start
    while d <= end:
        if d.weekday() < 5:  # Mon-Fri
            yield d
        d += timedelta(days=1)

# ---- Stock definitions ----
# (symbol, name, start_price_brl, drift_annual, volatility_daily, ipo_year)
STOCKS = [
    # Petróleo e Gás
    ("PETR3", "Petrobras ON", 3.80, 0.08, 0.022, 2000),
    ("PETR4", "Petrobras PN", 4.20, 0.08, 0.022, 2000),
    ("PRIO3", "Prio ON", 8.00, 0.18, 0.030, 2013),
    ("RECV3", "PetroReconcavo ON", 12.00, 0.15, 0.028, 2021),
    ("RRRP3", "3R Petroleum ON", 15.00, 0.14, 0.030, 2020),

    # Mineração
    ("VALE3", "Vale ON", 7.50, 0.10, 0.024, 2000),
    ("GOAU4", "Gerdau Metalúrgica PN", 2.50, 0.09, 0.022, 2000),
    ("GGBR4", "Gerdau PN", 3.00, 0.09, 0.022, 2000),
    ("CMIN3", "CSN Mineração ON", 5.00, 0.12, 0.026, 2021),
    ("USIM5", "Usiminas PNA", 4.00, 0.07, 0.025, 2000),

    # Bancos
    ("ITUB3", "Itaú Unibanco ON", 2.50, 0.12, 0.018, 2000),
    ("ITUB4", "Itaú Unibanco PN", 2.80, 0.12, 0.018, 2000),
    ("BBDC3", "Bradesco ON", 2.00, 0.11, 0.018, 2000),
    ("BBDC4", "Bradesco PN", 2.20, 0.11, 0.018, 2000),
    ("BBAS3", "Banco do Brasil ON", 3.50, 0.10, 0.019, 2000),
    ("SANB11", "Santander Brasil UNT", 8.00, 0.09, 0.018, 2009),
    ("BPAC11", "BTG Pactual UNT", 12.00, 0.15, 0.020, 2012),

    # Varejo
    ("MGLU3", "Magazine Luiza ON", 0.30, 0.25, 0.040, 2011),
    ("VIIA3", "Via ON", 1.50, 0.05, 0.040, 2005),
    ("AMER3", "Americanas ON", 5.00, 0.08, 0.035, 2007),
    ("LREN3", "Lojas Renner ON", 1.50, 0.14, 0.022, 2000),
    ("PETZ3", "Petz ON", 8.00, 0.18, 0.030, 2020),
    ("ARZZ3", "Arezzo ON", 15.00, 0.16, 0.022, 2011),
    ("SOMA3", "Grupo Soma ON", 8.00, 0.15, 0.025, 2020),
    ("GUAR3", "Guararapes ON", 10.00, 0.09, 0.022, 2000),
    ("BHIA3", "Casas Bahia ON", 3.00, 0.06, 0.040, 2021),

    # E-commerce e Tecnologia
    ("MELI34", "MercadoLibre BDR", 30.00, 0.22, 0.030, 2019),
    ("LWSA3", "Locaweb ON", 5.00, 0.20, 0.035, 2020),
    ("TOTS3", "TOTVS ON", 3.00, 0.13, 0.022, 2000),
    ("IFCM3", "Infracommerce ON", 5.00, 0.12, 0.030, 2021),

    # Alimentos e Bebidas
    ("ABEV3", "Ambev ON", 5.50, 0.09, 0.016, 2000),
    ("BRFS3", "BRF ON", 5.00, 0.08, 0.025, 2006),
    ("JBSS3", "JBS ON", 2.00, 0.12, 0.025, 2007),
    ("MRFG3", "Marfrig ON", 3.00, 0.10, 0.030, 2007),
    ("SMTO3", "São Martinho ON", 4.00, 0.11, 0.023, 2007),
    ("MYPK3", "Iochpe-Maxion ON", 8.00, 0.09, 0.022, 2000),

    # Energia Elétrica
    ("ELET3", "Eletrobras ON", 8.00, 0.06, 0.025, 2000),
    ("ELET6", "Eletrobras PNB", 7.50, 0.06, 0.025, 2000),
    ("ENGI11", "Energisa UNT", 10.00, 0.12, 0.018, 2014),
    ("CMIG4", "Cemig PN", 5.00, 0.08, 0.020, 2000),
    ("CPFE3", "CPFL Energia ON", 8.00, 0.09, 0.018, 2004),
    ("EGIE3", "Engie Brasil ON", 12.00, 0.10, 0.016, 2004),
    ("AURE3", "Auren ON", 10.00, 0.11, 0.020, 2022),

    # Telecomunicações
    ("VIVT3", "Telefônica Brasil ON", 20.00, 0.07, 0.016, 2000),
    ("TIMS3", "TIM ON", 5.00, 0.08, 0.020, 2000),
    ("OIBR3", "Oi ON", 8.00, -0.05, 0.045, 2002),

    # Saúde e Farmácia
    ("HAPV3", "Hapvida ON", 8.00, 0.18, 0.025, 2018),
    ("RDOR3", "Rede D'Or ON", 25.00, 0.16, 0.022, 2020),
    ("GNDI3", "Intermédica ON", 20.00, 0.17, 0.022, 2018),
    ("FLRY3", "Fleury ON", 10.00, 0.12, 0.020, 2009),
    ("HYPE3", "Hypera Pharma ON", 8.00, 0.13, 0.020, 2011),
    ("RADL3", "Raia Drogasil ON", 2.00, 0.18, 0.020, 2000),

    # Construção e Imobiliário
    ("CYRE3", "Cyrela Realty ON", 4.00, 0.10, 0.025, 2000),
    ("MRVE3", "MRV Engenharia ON", 3.00, 0.11, 0.025, 2007),
    ("EVEN3", "Even ON", 3.00, 0.09, 0.025, 2007),
    ("TGSA3", "Tegma ON", 8.00, 0.10, 0.022, 2007),

    # Logística e Transporte
    ("RAIL3", "Rumo ON", 2.00, 0.14, 0.022, 2011),
    ("GOLL4", "Gol PN", 8.00, 0.05, 0.040, 2004),
    ("AZUL4", "Azul PN", 12.00, 0.08, 0.040, 2017),
    ("EMBR3", "Embraer ON", 5.00, 0.10, 0.025, 2000),
    ("STBP3", "Santos Brasil ON", 5.00, 0.11, 0.022, 2006),
    ("LOGN3", "Log-In ON", 4.00, 0.09, 0.025, 2007),

    # Petroquímica e Química
    ("BRKM5", "Braskem PNA", 6.00, 0.08, 0.028, 2002),
    ("UNIP6", "Unipar PNB", 5.00, 0.10, 0.025, 2000),

    # Papel e Celulose
    ("SUZB3", "Suzano ON", 5.00, 0.11, 0.022, 2000),
    ("KLBN4", "Klabin PN", 4.00, 0.10, 0.020, 2000),
    ("DXCO3", "Dexco ON", 5.00, 0.10, 0.022, 2000),

    # Siderurgia e Metalurgia
    ("CSNA3", "CSN ON", 3.00, 0.07, 0.028, 2000),
    ("FESA4", "Ferbasa PN", 8.00, 0.09, 0.022, 2000),
    ("ROMI3", "Romi ON", 6.00, 0.08, 0.022, 2000),
    ("TUPY3", "Tupy ON", 5.00, 0.10, 0.022, 2000),

    # Serviços Financeiros
    ("B3SA3", "B3 ON", 5.00, 0.14, 0.018, 2017),
    ("CIELO3", "Cielo ON", 8.00, 0.04, 0.022, 2009),
    ("IRBR3", "IRB Brasil RE ON", 20.00, -0.05, 0.045, 2017),
    ("BRSR6", "Banrisul PNB", 8.00, 0.07, 0.020, 2007),

    # Infraestrutura
    ("CCRO3", "CCR ON", 2.00, 0.12, 0.020, 2002),
    ("EQTL3", "Equatorial ON", 3.00, 0.15, 0.018, 2006),
    ("TAEE11", "Transmissão Paulista UNT", 15.00, 0.10, 0.016, 2006),
    ("TRPL4", "Transmissão Paulista PN", 12.00, 0.09, 0.016, 2000),
    ("ENEV3", "Eneva ON", 5.00, 0.12, 0.022, 2007),

    # Consumo e Serviços
    ("RENT3", "Localiza ON", 1.00, 0.18, 0.022, 2005),
    ("MOVI3", "Movida ON", 4.00, 0.16, 0.025, 2017),
    ("VAMO3", "Vamos ON", 5.00, 0.18, 0.025, 2020),
    ("SIMH3", "Simpar ON", 4.00, 0.15, 0.025, 2020),
    ("ALLD3", "Allied ON", 6.00, 0.10, 0.025, 2020),

    # Agronegócio
    ("AGRO3", "BrasilAgro ON", 10.00, 0.12, 0.022, 2006),
    ("SLCE3", "SLC Agrícola ON", 8.00, 0.13, 0.022, 2007),
    ("TTEN3", "3Tentos ON", 8.00, 0.14, 0.022, 2021),

    # Educação
    ("COGN3", "Cogna ON", 2.00, 0.05, 0.040, 2000),
    ("ANIM3", "Ânima ON", 8.00, 0.10, 0.030, 2013),
    ("SEER3", "Ser Educacional ON", 8.00, 0.09, 0.030, 2013),
    ("YDUQ3", "Yduqs ON", 5.00, 0.08, 0.030, 2007),

    # Shopping e Imóveis
    ("MULT3", "Multiplan ON", 8.00, 0.12, 0.018, 2007),
    ("IGTI11", "Iguatemi UNT", 8.00, 0.11, 0.018, 2007),
    ("ALSO3", "Aliansce Sonae ON", 10.00, 0.10, 0.020, 2010),
    ("BRML3", "BR Malls ON", 10.00, 0.09, 0.022, 2007),

    # Utilities / Saneamento
    ("SBSP3", "Sabesp ON", 10.00, 0.09, 0.020, 2000),
    ("CSMG3", "Copasa ON", 8.00, 0.08, 0.020, 2006),
    ("SAPR11", "Sanepar UNT", 8.00, 0.09, 0.018, 2000),

    # Seguros
    ("IRBR3", "IRB RE ON", 20.00, -0.05, 0.040, 2017),
    ("BBSE3", "BB Seguridade ON", 22.00, 0.10, 0.016, 2013),
    ("PSSA3", "Porto Seguro ON", 20.00, 0.10, 0.018, 2004),

    # Holdings e Outros
    ("AXIA3", "Axia ON", 5.00, 0.10, 0.022, 2011),
    ("AXIA7", "Axia PN", 4.80, 0.10, 0.022, 2011),
    ("CPLE6", "Copel PNB", 8.00, 0.08, 0.020, 2000),
    ("TAEE4", "Transmissão Paulista PN", 14.00, 0.09, 0.016, 2000),

    # Adicionais
    ("POMO4", "Marcopolo PN", 3.00, 0.09, 0.022, 2000),
    ("KEPL3", "Kepler Weber ON", 5.00, 0.10, 0.022, 2000),
    ("ODER4", "Odontoprev PN", 3.00, 0.12, 0.020, 2006),
    ("NTCO3", "Natura ON", 3.00, 0.13, 0.022, 2004),
    ("LEVE3", "Metal Leve ON", 10.00, 0.09, 0.020, 2011),
    ("UGPA3", "Ultrapar ON", 8.00, 0.09, 0.018, 2000),
    ("GRND3", "Grendene ON", 5.00, 0.10, 0.018, 2004),
    ("ALPA4", "Alpargatas PN", 5.00, 0.09, 0.022, 2000),
    ("VBBR3", "Vibra Energia ON", 10.00, 0.10, 0.022, 2021),
    ("CRFB3", "Carrefour Brasil ON", 10.00, 0.08, 0.022, 2017),
    ("ASAI3", "Assaí ON", 8.00, 0.14, 0.022, 2021),
    ("PCAR3", "Pão de Açúcar ON", 15.00, 0.06, 0.025, 2000),
    ("INTB3", "Intelbras ON", 10.00, 0.12, 0.020, 2021),
    ("DESK3", "Desktop ON", 8.00, 0.10, 0.025, 2021),
    ("MDIA3", "M.Dias Branco ON", 20.00, 0.09, 0.018, 2006),
    ("HGTX3", "Cia Hering ON", 5.00, 0.08, 0.022, 2000),
    ("VULC3", "Vulcabras ON", 5.00, 0.10, 0.022, 2000),
    ("ENJU3", "Enjoei ON", 5.00, 0.08, 0.040, 2020),
    ("BMOB3", "Bemobi ON", 8.00, 0.12, 0.030, 2021),
    ("WIZC3", "Wiz ON", 6.00, 0.10, 0.025, 2016),
    ("PLPL3", "Plano&Plano ON", 5.00, 0.10, 0.025, 2021),
    ("ALPK3", "Alpar ON", 5.00, 0.08, 0.025, 2021),
    ("BIDI11", "Banco Inter UNT", 5.00, 0.15, 0.030, 2018),
    ("AMAR3", "Lojas Marisa ON", 3.00, 0.04, 0.035, 2007),
    ("MEAL3", "IMC ON", 3.00, 0.06, 0.030, 2013),
    ("MATD3", "Mater Dei ON", 8.00, 0.12, 0.022, 2021),
    ("ONCO3", "Oncoclinicas ON", 8.00, 0.12, 0.022, 2021),
    ("BPAN4", "Banco Pan PN", 3.00, 0.08, 0.025, 2000),
    ("PINE4", "Banco Pine PN", 4.00, 0.06, 0.025, 2007),
    ("RANI3", "Irani ON", 5.00, 0.10, 0.022, 2000),
    ("TGMA3", "Tegma ON", 8.00, 0.10, 0.022, 2007),
    ("SHOW3", "Time For Fun ON", 3.00, 0.05, 0.035, 2011),
    ("CEAB3", "CEA ON", 8.00, 0.08, 0.030, 2020),
    ("WEST3", "Westwing ON", 5.00, 0.08, 0.040, 2020),
    ("CASH3", "Méliuz ON", 4.00, 0.06, 0.045, 2020),
    ("PGMN3", "Pague Menos ON", 8.00, 0.10, 0.022, 2021),
    ("AESB3", "AES Brasil ON", 10.00, 0.09, 0.018, 2020),
    ("MDNE3", "Moura Dubeux ON", 8.00, 0.10, 0.025, 2020),
    ("BAHI3", "Bahema ON", 5.00, 0.08, 0.025, 2000),
]

# Remove duplicates (IRBR3 appears twice)
seen = set()
unique_stocks = []
for s in STOCKS:
    if s[0] not in seen:
        seen.add(s[0])
        unique_stocks.append(s)
STOCKS = unique_stocks


def generate_ohlcv(price, volatility, volume_base=10_000_000):
    """Generate OHLCV candle from closing price"""
    open_price = price * (1 + random.gauss(0, volatility * 0.3))
    high = max(open_price, price) * (1 + abs(random.gauss(0, volatility * 0.5)))
    low = min(open_price, price) * (1 - abs(random.gauss(0, volatility * 0.5)))
    volume = max(1000, int(volume_base * random.lognormvariate(0, 0.5)))
    return round(open_price, 2), round(high, 2), round(low, 2), round(price, 2), volume


def simulate_prices(start_price, drift_annual, volatility_daily, num_days):
    """Simulate stock price series using geometric Brownian motion"""
    dt = 1 / 252  # daily
    drift_daily = drift_annual * dt - 0.5 * volatility_daily ** 2 * dt
    prices = [start_price]

    for _ in range(num_days - 1):
        shock = random.gauss(0, 1)
        log_return = drift_daily + volatility_daily * math.sqrt(dt) * shock
        new_price = prices[-1] * math.exp(log_return)
        # Keep prices above 0.01
        prices.append(max(0.01, round(new_price, 2)))

    return prices


def main():
    # Set seed for reproducibility
    random.seed(42)

    print(f"Connecting to database: {DB_PATH}")
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    cur = conn.cursor()

    # Clear existing data
    print("Clearing existing data...")
    cur.execute("DELETE FROM stock_prices")
    cur.execute("DELETE FROM stocks")
    conn.commit()

    START_DATE = date(2000, 1, 1)
    END_DATE = date(2026, 2, 23)

    all_bdays = list(business_days(START_DATE, END_DATE))
    print(f"Business days from {START_DATE} to {END_DATE}: {len(all_bdays)}")

    total_records = 0

    for i, (symbol, name, start_price, drift, vol, ipo_year) in enumerate(STOCKS):
        # Determine stock start date
        ipo_date = date(ipo_year, 1, 1)
        stock_bdays = [d for d in all_bdays if d >= ipo_date]

        if not stock_bdays:
            continue

        num_days = len(stock_bdays)

        # Generate price series
        prices = simulate_prices(start_price, drift, vol, num_days)
        latest_price = prices[-1]
        prev_price = prices[-2] if len(prices) >= 2 else latest_price
        change_pct = ((latest_price - prev_price) / prev_price) * 100

        # Volume base varies by stock
        vol_base = random.randint(5_000_000, 100_000_000)

        # Insert stock
        cur.execute(
            "INSERT INTO stocks (symbol, name, price, change_percent, volume, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
            (symbol, name, round(latest_price, 2), round(change_pct, 4), vol_base, "2026-02-23T00:00:00")
        )
        stock_id = cur.lastrowid

        # Insert price records in bulk
        price_records = []
        for j, d in enumerate(stock_bdays):
            o, h, l, c, v = generate_ohlcv(prices[j], vol, vol_base)
            price_records.append((stock_id, d.strftime("%Y-%m-%d"), o, h, l, c, v))

        cur.executemany(
            "INSERT INTO stock_prices (stock_id, date, open, high, low, close, volume) VALUES (?, ?, ?, ?, ?, ?, ?)",
            price_records
        )

        total_records += len(price_records)

        if (i + 1) % 20 == 0 or (i + 1) == len(STOCKS):
            conn.commit()
            print(f"  [{i+1}/{len(STOCKS)}] {symbol}: {len(price_records)} registros (desde {ipo_year}) | total: {total_records:,}")

    conn.commit()
    conn.close()

    print(f"\n✅ Concluído!")
    print(f"   Ações: {len(STOCKS)}")
    print(f"   Registros de preços: {total_records:,}")
    print(f"   Período: {START_DATE} a {END_DATE}")


if __name__ == "__main__":
    main()

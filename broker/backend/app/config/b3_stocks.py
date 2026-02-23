"""
Lista de ações negociadas na bolsa de valores do Brasil

Esta lista inclui as principais ações por liquidez e volume.
Para baixar dados históricos do Yahoo Finance, adicione sufixo .SA

Atualizado: Fevereiro 2026
"""

# Ações do Ibovespa (principais índice) - 85+ ativos
IBOVESPA_STOCKS = [
    # Petróleo e Gás
    "PETR3", "PETR4",  # Petrobras
    "PRIO3",           # Prio
    "RECV3",           # PetroReconcavo
    "RRRP3",           # 3R Petroleum

    # Mineração
    "VALE3",           # Vale
    "GOAU4",           # Gerdau Metalúrgica
    "GGBR4",           # Gerdau
    "CMIN3",           # CSN Mineração
    "USIM5",           # Usiminas

    # Bancos
    "ITUB3", "ITUB4",  # Itaú Unibanco
    "BBDC3", "BBDC4",  # Bradesco
    "BBAS3",           # Banco do Brasil
    "SANB11",          # Santander
    "BPAC11",          # BTG Pactual

    # Varejo
    "MGLU3",           # Magazine Luiza
    "VIIA3",           # Via
    "AMER3",           # Americanas
    "LREN3",           # Lojas Renner
    "PETZ3",           # Petz
    "ARZZ3",           # Arezzo
    "SOMA3",           # Grupo Soma
    "GUAR3",           # Guararapes (Riachuelo)
    "BHIA3",           # Casas Bahia

    # E-commerce e Tecnologia
    "MELI34",          # MercadoLibre BDR
    "LWSA3",           # Locaweb
    "TOTS3",           # TOTVS
    "IFCM3",           # Infracommerce

    # Alimentos e Bebidas
    "ABEV3",           # Ambev
    "JBSS3",           # JBS
    "BRFS3",           # BRF
    "BEEF3",           # Minerva
    "MRFG3",           # Marfrig
    "SMTO3",           # São Martinho
    "CAML3",           # Camil

    # Energia Elétrica
    "ELET3", "ELET6",  # Eletrobras
    "ENBR3",           # Energias do Brasil
    "ENEV3",           # Eneva
    "ENGI11",          # Energisa
    "TAEE11",          # Taesa
    "CPFE3",           # CPFL Energia
    "CMIG4",           # Cemig
    "TRPL4",           # Transmissão Paulista
    "EQTL3",           # Equatorial
    "AESB3",           # AES Brasil
    "CPLE6",           # Copel
    "NEOE3",           # Neoenergia

    # Saneamento
    "SAPR11",          # Sanepar
    "SBSP3",           # Sabesp
    "CSMG3",           # Copasa

    # Construção e Imóveis
    "CYRE3",           # Cyrela
    "MRVE3",           # MRV
    "TEND3",           # Tenda
    "EVEN3",           # Even
    "EZTC3",           # EzTec
    "JHSF3",           # JHSF
    "LAVV3",           # Lavvi
    "LJQQ3",           # Quero-Quero

    # Locação de Veículos
    "RENT3",           # Localiza
    "MOVI3",           # Movida

    # Aviação
    "GOLL4",           # Gol
    "AZUL4",           # Azul
    "EMBR3",           # Embraer

    # Telecomunicações
    "VIVT3",           # Vivo (Telefônica Brasil)
    "TIMS3",           # TIM
    "OIBR3",           # Oi

    # Saúde
    "RADL3",           # Raia Drogasil
    "PNVL3",           # Dasa
    "HAPV3",           # Hapvida
    "FLRY3",           # Fleury
    "GNDI3",           # NotreDame Intermédica
    "QUAL3",           # Qualicorp

    # Papel e Celulose
    "SUZB3",           # Suzano
    "KLBN11",          # Klabin

    # Logística e Transporte
    "RAIL3",           # Rumo
    "CCRO3",           # CCR
    "ECOR3",           # Ecorodovias

    # Educação
    "YDUQ3",           # Yduqs (Estácio)
    "COGN3",           # Cogna

    # Seguro
    "BBSE3",           # BB Seguridade
    "SULA11",          # Sul América
    "PSSA3",           # Porto Seguro

    # Frigoríficos
    "BEEF3",           # Minerva

    # Indústria
    "WEGE3",           # WEG
    "EMBR3",           # Embraer
    "RAIZ4",           # Raízen
    "SLCE3",           # SLC Agrícola

    # Financeiro
    "B3SA3",           # B3 (Bolsa)
    "CSAN3",           # Cosan
    "IRBR3",           # IRB Brasil

    # Holdings e Participações
    "AXIA3", "AXIA7",  # Axia (ex-Hypera)
    "IGTI11",          # Iguatemi
    "MULT3",           # Multiplan
    "BRML3",           # BR Malls
]

# Ações adicionais (fora do Ibovespa mas com boa liquidez)
ADDITIONAL_STOCKS = [
    # Small Caps com liquidez
    "POMO4",           # Marcopolo
    "KEPL3",           # Kepler Weber
    "SIMH3",           # Simpar
    "ODER4",           # Odontoprev
    "NTCO3",           # Natura
    "LEVE3",           # Metal Leve
    "UGPA3",           # Ultrapar
    "GRND3",           # Grendene
    "ALPA4",           # Alpargatas
    "VBBR3",           # Vibra Energia
    "CSNA3",           # CSN
    "BRKM5",           # Braskem
    "CVCB3",           # CVC (saiu do Ibovespa)
    "CRFB3",           # Carrefour Brasil
    "ASAI3",           # Assaí
    "PCAR3",           # Grupo Pão de Açúcar
    "HYPE3",           # Hypera Pharma
    "AURE3",           # Auren
    "ALSO3",           # Aliansce Sonae
    "INTB3",           # Intelbras
    "DESK3",           # Desktop
    "MDIA3",           # M.Dias Branco
    "HGTX3",           # Cia Hering
    "VULC3",           # Vulcabras
    "ENJU3",           # Enjoei
    "VAMO3",           # Vamos
    "BMOB3",           # Bemobi
    "WIZC3",           # Wiz
    "PLPL3",           # Plano & Plano
    "ALPK3",           # Alparti
    "BIDI11",          # Banco Inter
    "TTEN3",           # 3Tentos
    "AMAR3",           # Lojas Marisa
    "MEAL3",           # IMC
    "MATD3",           # Mater Dei
    "ONCO3",           # Oncoclinicas
    "BPAN4",           # Banco Pan
    "PINE4",           # Banco Pine
    "AGRO3",           # BrasilAgro
    "RANI3",           # Irani
    "KLBN4",           # Klabin PN
    "STBP3",           # Santos Brasil
    "LOGN3",           # Log-In
    "TGMA3",           # Tegma
    "ROMI3",           # Romi
    "FESA4",           # Ferbasa
    "TUPY3",           # Tupy
    "SHOW3",           # Traveloka (Time For Fun)
    "CEAB3",           # CEA
    "WEST3",           # Westwing
    "CASH3",           # Méliuz
    "PGMN3",           # Pague Menos
    "DXCO3",           # Dexco
    "ANIM3",           # Ânima
    "SEER3",           # Ser Educacional
    "BAHI3",           # Bahema
    "MDNE3",           # Moura Dubeux
]

# Lista completa combinada
ALL_STOCKS = sorted(set(IBOVESPA_STOCKS + ADDITIONAL_STOCKS))
